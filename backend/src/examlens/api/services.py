from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import uuid
from typing import Any

from .config import settings
from .db import get_db, init_db
from .parsing import parse_any, checksum_text
from .retrieval import Chunk, HybridRetriever, split_into_chunks, extract_keywords
from .ollama_client import OllamaClient
from .prompts import SYSTEM_PROMPT, exam_writer_prompt, notes_prompt, diagram_prompt


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_session(conn, session_id: str) -> None:
    row = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO sessions (id, title, created_at, last_active_at) VALUES (?, ?, ?, ?)",
            (session_id, "Study Session", now_iso(), now_iso()),
        )
    else:
        conn.execute("UPDATE sessions SET last_active_at = ? WHERE id = ?", (now_iso(), session_id))


def _store_document(path: Path, source_type: str) -> tuple[str, str]:
    parsed = parse_any(path, "application/octet-stream")
    doc_id = f"doc_{uuid.uuid4().hex[:10]}"
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, sha256, filename, mime_type, title, source_type, status, raw_text, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                checksum_text(parsed.text),
                path.name,
                path.suffix.lstrip(".") or source_type,
                parsed.title,
                source_type,
                "parsed",
                parsed.text,
                now_iso(),
                now_iso(),
            ),
        )
    return doc_id, parsed.text


def _chunk_and_index(document_id: str, text: str) -> list[Chunk]:
    chunk_texts = split_into_chunks(text)
    chunks: list[Chunk] = []
    with get_db() as conn:
        for i, chunk_text in enumerate(chunk_texts):
            chunk_id = f"chunk_{uuid.uuid4().hex[:10]}"
            c = Chunk(
                id=chunk_id,
                document_id=document_id,
                text=chunk_text,
                token_count=max(1, len(chunk_text.split())),
            )
            chunks.append(c)
            conn.execute(
                """
                INSERT INTO chunks (id, document_id, chunk_index, page_start, page_end, heading_path, text, token_count, checksum, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    c.id,
                    document_id,
                    i,
                    None,
                    None,
                    None,
                    chunk_text,
                    c.token_count,
                    checksum_text(chunk_text),
                    now_iso(),
                ),
            )
            conn.execute(
                "INSERT INTO chunk_fts (chunk_id, document_id, text, heading_path) VALUES (?, ?, ?, ?)",
                (c.id, document_id, chunk_text, None),
            )
    return chunks


def ingest_file(file_path: Path, source_type: str) -> str:
    init_db()
    document_id, text = _store_document(file_path, source_type)
    _chunk_and_index(document_id, text)
    return document_id


def ingest_paste(title: str, text: str) -> str:
    init_db()
    file_name = f"{title}.txt"
    tmp = settings.data_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    path = tmp / file_name
    path.write_text(text, encoding="utf-8")
    return ingest_file(path, "paste")


def list_documents() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, filename, title, source_type, status, created_at FROM documents ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def load_chunks(document_ids: list[str] | None = None) -> list[Chunk]:
    with get_db() as conn:
        if document_ids:
            qmarks = ",".join("?" for _ in document_ids)
            rows = conn.execute(
                f"SELECT id, document_id, text, page_start, page_end, heading_path, token_count FROM chunks WHERE document_id IN ({qmarks}) ORDER BY document_id, chunk_index",
                document_ids,
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, document_id, text, page_start, page_end, heading_path, token_count FROM chunks ORDER BY document_id, chunk_index"
            ).fetchall()
    return [Chunk(**dict(row)) for row in rows]


def get_retriever(conn, document_ids: list[str] | None = None) -> HybridRetriever:
    retriever = HybridRetriever(db_conn=conn)
    retriever.index(load_chunks(document_ids))
    return retriever


def format_context(results: list[tuple[Chunk, float]]) -> str:
    blocks = []
    for chunk, score in results:
        citation = f"[{chunk.document_id}:{chunk.page_start or 1}]"
        blocks.append(f"{citation} score={score:.3f}\n{chunk.text}")
    return "\n\n---\n\n".join(blocks)


def estimate_mode_tokens(answer_mode: str) -> int:
    return {
        "one-line": 40,
        "short": 90,
        "bullets": 140,
        "2-mark": 110,
        "5-mark": 220,
        "10-mark": 350,
        "15-mark": 500,
        "definition": 100,
        "comparison": 220,
        "notes": 700,
        "flowchart": 220,
        "mindmap": 220,
        "memorize": 160,
        "long": 350,
    }.get(answer_mode, 220)


def _fallback_answer(question: str, answer_mode: str, results: list[tuple[Chunk, float]]) -> str:
    if not results:
        return "Not found in the uploaded sources."
    if answer_mode in {"comparison", "flowchart", "mindmap"}:
        return "Not enough structured information for a reliable diagram."
    top = results[0][0].text
    if answer_mode in {"one-line", "short", "definition"}:
        return re.split(r"(?<=[.!?])\s+", top.strip())[0][:280]
    return top[:1200]


async def answer_question(session_id: str, question: str, answer_mode: str, document_scope: list[str] | None, temperature: float | None) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        _ensure_session(conn, session_id)
        message_id = f"msg_{uuid.uuid4().hex[:10]}"
        conn.execute(
            "INSERT INTO messages (id, session_id, role, mode, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (message_id, session_id, "user", answer_mode, question, now_iso()),
        )

        retriever = get_retriever(conn, document_scope)
        results = retriever.search(question, top_k=settings.top_k, document_ids=document_scope)
    context = format_context(results)
    prompt = exam_writer_prompt(question, answer_mode, context)

    client = OllamaClient(settings.ollama_host, settings.ollama_model)
    try:
        raw = await client.generate(
            SYSTEM_PROMPT + "\n\n" + prompt,
            temperature=temperature if temperature is not None else settings.temperature,
            max_tokens=estimate_mode_tokens(answer_mode),
        )
    except Exception:
        raw = _fallback_answer(question, answer_mode, results)

    if not raw.strip():
        raw = _fallback_answer(question, answer_mode, results)

    citations = []
    for chunk, score in results[:3]:
        citations.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "quote": chunk.text[:280],
                "score": round(score, 4),
            }
        )

    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET last_active_at = ? WHERE id = ?",
            (now_iso(), session_id),
        )
        for citation in citations:
            conn.execute(
                """
                INSERT INTO citations (id, message_id, chunk_id, document_id, page_start, page_end, quote, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"cit_{uuid.uuid4().hex[:10]}",
                    message_id,
                    citation["chunk_id"],
                    citation["document_id"],
                    citation["page_start"],
                    citation["page_end"],
                    citation["quote"],
                    citation["score"],
                    now_iso(),
                ),
            )
        conn.execute(
            "INSERT INTO messages (id, session_id, role, mode, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (f"msg_{uuid.uuid4().hex[:10]}", session_id, "assistant", answer_mode, raw, now_iso()),
        )

    return {
        "message_id": message_id,
        "answer_mode": answer_mode,
        "answer": raw,
        "citations": citations,
        "grounded": bool(citations),
        "retrieval": {
            "top_k": settings.top_k,
            "matched_chunks": [c.id for c, _ in results],
        },
    }


async def generate_notes(session_id: str, document_id: str, topic: str | None, style: str) -> dict[str, Any]:
    with get_db() as conn:
        retriever = get_retriever(conn, [document_id])
        query = topic or "chapter summary"
        results = retriever.search(query, top_k=settings.top_k, document_ids=[document_id])
    context = format_context(results)
    prompt = notes_prompt(query, context)
    client = OllamaClient(settings.ollama_host, settings.ollama_model)
    try:
        markdown = await client.generate(SYSTEM_PROMPT + "\n\n" + prompt, temperature=0.1, max_tokens=700)
    except Exception:
        markdown = f"# {query}\n\n## Summary\n{results[0][0].text[:1200] if results else 'Not found in the uploaded sources.'}"
    return {
        "note_id": f"note_{uuid.uuid4().hex[:10]}",
        "markdown": markdown,
        "citations": [
            {
                "chunk_id": c.id,
                "document_id": c.document_id,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "quote": c.text[:280],
                "score": round(score, 4),
            }
            for c, score in results[:3]
        ],
    }


async def generate_diagram(session_id: str, document_id: str, topic: str, diagram_type: str) -> dict[str, Any]:
    with get_db() as conn:
        retriever = get_retriever(conn, [document_id])
        results = retriever.search(topic, top_k=5, document_ids=[document_id])
    context = format_context(results)
    prompt = diagram_prompt(topic, context, diagram_type)
    client = OllamaClient(settings.ollama_host, settings.ollama_model)
    try:
        mermaid = await client.generate(SYSTEM_PROMPT + "\n\n" + prompt, temperature=0.0, max_tokens=250)
    except Exception:
        if diagram_type == "mindmap":
            mermaid = f"mindmap\n  root(({topic}))\n    {topic}\n      {results[0][0].text[:30] if results else 'Not found'}"
        else:
            mermaid = "flowchart TD\n  A[Not enough structured information] --> B[for a reliable diagram]"
    return {
        "diagram_id": f"diag_{uuid.uuid4().hex[:10]}",
        "diagram_type": diagram_type,
        "mermaid": mermaid,
        "status": "generated",
    }


def search_documents(query: str, document_id: str | None = None) -> list[dict[str, Any]]:
    with get_db() as conn:
        retriever = get_retriever(conn, [document_id] if document_id else None)
        results = retriever.search(query, top_k=settings.top_k, document_ids=[document_id] if document_id else None)
    return [
        {
            "chunk_id": c.id,
            "document_id": c.document_id,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "snippet": c.text[:300],
            "score": round(score, 4),
        }
        for c, score in results
    ]


def get_citations(message_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT chunk_id, document_id, page_start, page_end, quote, score FROM citations WHERE message_id = ? ORDER BY score DESC",
            (message_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_sessions() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, last_active_at FROM sessions ORDER BY last_active_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_session(session_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, title, created_at, last_active_at FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return dict(row) if row else None


def export_note_markdown(note_id: str) -> dict[str, Any]:
    return {
        "note_id": note_id,
        "markdown": f"# Exported note {note_id}\n\nThis endpoint will return persisted note content once note storage is wired in.",
    }
