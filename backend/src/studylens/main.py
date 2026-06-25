import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from .chroma import get_client, get_collection
from .config import ASSETS_PATH, ENABLE_IMAGE_GEN, IMAGE_GEN_MODEL, RAG_TOP_K, UPLOAD_PATH

os.makedirs(ASSETS_PATH, exist_ok=True)  # must exist before StaticFiles mounts
from .db import Document, Message, Notebook, create_db, engine, get_session
from .ingest import chunk_text, extract_text
from .ollama import embed, generate, json_generate, stream as ollama_stream
from .prompts import (
    MINDMAP_PROMPT,
    MINDMAP_SYSTEM,
    QUIZ_PROMPT,
    QUIZ_SYSTEM,
    RAG_PROMPT,
    RAG_SYSTEM,
    SLIDES_PROMPT,
    SLIDES_SYSTEM,
    SUMMARY_PROMPT,
    SUMMARY_SYSTEM,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_PATH, exist_ok=True)
    os.makedirs("data/chroma", exist_ok=True)
    os.makedirs(ASSETS_PATH, exist_ok=True)
    create_db()
    yield


app = FastAPI(title="StudyLens", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated slide images at /assets/<filename>
app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")


# ── Image Generation Pipeline (optional) ───────────────────────────────────────

_img_pipe = None  # module-level cache so we load the model once


def _load_pipe():
    global _img_pipe
    if _img_pipe is not None:
        return _img_pipe
    from diffusers import DiffusionPipeline  # type: ignore
    import torch  # type: ignore
    _img_pipe = DiffusionPipeline.from_pretrained(
        IMAGE_GEN_MODEL, torch_dtype=torch.float16, use_safetensors=True
    )
    if torch.cuda.is_available():
        _img_pipe = _img_pipe.to("cuda")
    return _img_pipe


def _sync_render_image(prompt: str, path: str):
    pipe = _load_pipe()
    img = pipe(prompt, num_inference_steps=4, guidance_scale=8.0).images[0]
    img.save(path)


async def _generate_slide_asset(filename: str, prompt: str):
    path = os.path.join(ASSETS_PATH, filename)
    if os.path.exists(path):
        return
    try:
        await asyncio.get_event_loop().run_in_executor(None, _sync_render_image, prompt, path)
        print(f"[image_gen] saved {filename}")
    except Exception as e:
        print(f"[image_gen] ERROR {filename}: {e}")


# ── Notebooks ──────────────────────────────────────────────────────────────────

class NotebookBody(BaseModel):
    name: str


@app.get("/api/notebooks")
def list_notebooks(session: Session = Depends(get_session)):
    return session.exec(select(Notebook).order_by(Notebook.created_at.desc())).all()


@app.post("/api/notebooks", status_code=201)
def create_notebook(body: NotebookBody, session: Session = Depends(get_session)):
    nb = Notebook(name=body.name)
    session.add(nb)
    session.commit()
    session.refresh(nb)
    return nb


@app.patch("/api/notebooks/{nb_id}")
def rename_notebook(nb_id: int, body: NotebookBody, session: Session = Depends(get_session)):
    nb = session.get(Notebook, nb_id)
    if not nb:
        raise HTTPException(404)
    nb.name = body.name
    session.add(nb)
    session.commit()
    session.refresh(nb)
    return nb


@app.delete("/api/notebooks/{nb_id}", status_code=204)
def delete_notebook(nb_id: int, session: Session = Depends(get_session)):
    nb = session.get(Notebook, nb_id)
    if not nb:
        raise HTTPException(404)
    try:
        get_client().delete_collection(f"notebook_{nb_id}")
    except Exception:
        pass
    docs = session.exec(select(Document).where(Document.notebook_id == nb_id)).all()
    for doc in docs:
        if doc.source_type != "url" and os.path.exists(doc.source_ref):
            os.remove(doc.source_ref)
        session.delete(doc)
    for msg in session.exec(select(Message).where(Message.notebook_id == nb_id)).all():
        session.delete(msg)
    session.delete(nb)
    session.commit()


# ── Chat History (persistent) ──────────────────────────────────────────────────

class SaveMessageBody(BaseModel):
    role: str
    content: str
    sources: list[dict] = []


@app.get("/api/notebooks/{nb_id}/messages")
def get_messages(nb_id: int, session: Session = Depends(get_session)):
    msgs = session.exec(
        select(Message).where(Message.notebook_id == nb_id).order_by(Message.created_at)
    ).all()
    return [
        {"role": m.role, "content": m.content, "sources": json.loads(m.sources_json or "[]")}
        for m in msgs
    ]


@app.post("/api/notebooks/{nb_id}/messages", status_code=201)
def save_message(nb_id: int, body: SaveMessageBody, session: Session = Depends(get_session)):
    msg = Message(
        notebook_id=nb_id,
        role=body.role,
        content=body.content,
        sources_json=json.dumps(body.sources),
    )
    session.add(msg)
    session.commit()
    return {"ok": True}


@app.delete("/api/notebooks/{nb_id}/messages", status_code=204)
def clear_messages(nb_id: int, session: Session = Depends(get_session)):
    for msg in session.exec(select(Message).where(Message.notebook_id == nb_id)).all():
        session.delete(msg)
    session.commit()


# ── Documents ──────────────────────────────────────────────────────────────────

def _get_doc_chunks(doc_id: int, notebook_id: int) -> str:
    """Return stored chunk text from ChromaDB — no re-fetch needed."""
    col = get_collection(notebook_id)
    results = col.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    if not results["documents"]:
        return ""
    pairs = sorted(
        zip(results["metadatas"], results["documents"]),
        key=lambda x: x[0].get("chunk_idx", 0),
    )
    return " ".join(doc for _, doc in pairs)


async def _index_document(doc_id: int):
    with Session(engine) as session:
        doc = session.get(Document, doc_id)
        if not doc:
            return
        try:
            text = await extract_text(doc.source_type, doc.source_ref)
            if not text.strip():
                print(f"[index] no text extracted from doc {doc_id}")
                return

            chunks = chunk_text(text)
            col = get_collection(doc.notebook_id)
            embeddings = await embed(chunks)

            col.add(
                ids=[f"doc{doc.id}_chunk{i}" for i in range(len(chunks))],
                embeddings=embeddings,
                documents=chunks,
                metadatas=[
                    {"doc_id": doc.id, "doc_name": doc.name, "chunk_idx": i}
                    for i in range(len(chunks))
                ],
            )

            # commit chunk_count first → UI can start chatting immediately
            doc.chunk_count = len(chunks)
            session.add(doc)
            session.commit()
            print(f"[index] doc {doc_id} ready: {len(chunks)} chunks")

            # summary after — non-blocking from user's perspective
            doc.summary = await generate(
                SUMMARY_PROMPT.format(text=text[:3000]), SUMMARY_SYSTEM
            )
            session.add(doc)
            session.commit()
            print(f"[index] doc {doc_id} summary done")
        except Exception as e:
            print(f"[index] ERROR doc {doc_id}: {e}")


@app.get("/api/notebooks/{nb_id}/documents")
def list_documents(nb_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Document).where(Document.notebook_id == nb_id)).all()


@app.post("/api/notebooks/{nb_id}/documents", status_code=201)
async def upload_document(
    nb_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    url: str = Form(None),
    session: Session = Depends(get_session),
):
    if not session.get(Notebook, nb_id):
        raise HTTPException(404, "Notebook not found")

    if file:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ("pdf", "docx", "txt", "md"):
            raise HTTPException(400, f"Unsupported type '.{ext}'. Use pdf, docx, txt, or md.")
        src_type = "txt" if ext == "md" else ext
        path = os.path.join(UPLOAD_PATH, f"{uuid.uuid4()}.{ext}")
        with open(path, "wb") as f:
            f.write(await file.read())
        doc = Document(notebook_id=nb_id, name=file.filename, source_type=src_type, source_ref=path)
    elif url:
        doc = Document(notebook_id=nb_id, name=url[:120], source_type="url", source_ref=url)
    else:
        raise HTTPException(400, "Provide a file or url field")

    session.add(doc)
    session.commit()
    session.refresh(doc)
    background_tasks.add_task(_index_document, doc.id)
    return doc


@app.delete("/api/notebooks/{nb_id}/documents/{doc_id}", status_code=204)
def delete_document(nb_id: int, doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(Document, doc_id)
    if not doc or doc.notebook_id != nb_id:
        raise HTTPException(404)
    try:
        col = get_collection(nb_id)
        col.delete(where={"doc_id": doc_id})
    except Exception:
        pass
    if doc.source_type != "url" and os.path.exists(doc.source_ref):
        os.remove(doc.source_ref)
    session.delete(doc)
    session.commit()


# ── Chat (streaming SSE) ───────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/api/notebooks/{nb_id}/chat")
async def chat(nb_id: int, body: ChatRequest):
    col = get_collection(nb_id)
    if col.count() == 0:
        raise HTTPException(404, "No documents indexed yet.")

    q_embeddings = await embed(body.question)
    results = col.query(
        query_embeddings=[q_embeddings[0]],
        n_results=min(RAG_TOP_K, col.count()),
    )

    chunks = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    if not chunks:
        raise HTTPException(404, "No relevant content found")

    context = "\n\n---\n\n".join(chunks)

    history_str = ""
    if body.history:
        recent = body.history[-4:]
        lines = [
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in recent
        ]
        history_str = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    prompt = RAG_PROMPT.format(context=context, history=history_str, question=body.question)

    seen, sources = set(), []
    for m in metas:
        name = m.get("doc_name", "")
        if name not in seen:
            seen.add(name)
            sources.append({"doc_name": name, "chunk_idx": m.get("chunk_idx", 0)})

    async def event_stream():
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        async for token in ollama_stream(prompt, RAG_SYSTEM):
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Quiz ───────────────────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    n: int = 5


@app.post("/api/documents/{doc_id}/quiz")
async def generate_quiz(doc_id: int, body: QuizRequest, session: Session = Depends(get_session)):
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    text = _get_doc_chunks(doc_id, doc.notebook_id)
    if not text.strip():
        raise HTTPException(400, "Document not indexed yet")
    doc_name = doc.name

    async def sse():
        accumulated = ""
        try:
            async for token in ollama_stream(QUIZ_PROMPT.format(n=body.n, text=text[:5000]), QUIZ_SYSTEM):
                accumulated += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except httpx.ReadTimeout:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Ollama timed out. Try qwen2.5:1.5b or reduce question count.'})}\n\n"
            return
        yield f"data: {json.dumps({'type': 'done', 'quiz_text': accumulated, 'doc_name': doc_name})}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


# ── Slide Deck ─────────────────────────────────────────────────────────────────

@app.post("/api/documents/{doc_id}/slides")
async def generate_slides(
    doc_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    text = _get_doc_chunks(doc_id, doc.notebook_id)
    if not text.strip():
        raise HTTPException(400, "Document not indexed yet")

    async def sse():
        accumulated = ""
        try:
            async for token in ollama_stream(
                SLIDES_PROMPT.format(text=text[:4000]), SLIDES_SYSTEM, format_json=True
            ):
                accumulated += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except httpx.ReadTimeout:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Ollama timed out — try qwen2.5:1.5b'})}\n\n"
            return

        try:
            from json_repair import repair_json  # type: ignore
            deck = json.loads(repair_json(accumulated))
        except Exception:
            deck = {}

        if "slides" not in deck or not isinstance(deck["slides"], list):
            yield f"data: {json.dumps({'type': 'error', 'message': 'Model returned invalid structure — try again'})}\n\n"
            return

        if ENABLE_IMAGE_GEN:
            for slide in deck["slides"]:
                prompt_text = slide.get("asset_generation_prompt", "").strip()
                slide_num = slide.get("slide_number", 0)
                if prompt_text:
                    fname = f"doc{doc_id}_slide{slide_num}.png"
                    slide["asset_path"] = fname
                    background_tasks.add_task(_generate_slide_asset, fname, prompt_text)

        yield f"data: {json.dumps({'type': 'done', **deck})}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


# ── Mind Map ───────────────────────────────────────────────────────────────────

@app.post("/api/documents/{doc_id}/mindmap")
async def generate_mindmap(doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    text = _get_doc_chunks(doc_id, doc.notebook_id)
    if not text.strip():
        raise HTTPException(400, "Document not indexed yet")

    async def sse():
        accumulated = ""
        try:
            async for token in ollama_stream(MINDMAP_PROMPT.format(text=text[:2500]), MINDMAP_SYSTEM):
                accumulated += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except httpx.ReadTimeout:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Ollama timed out. Try qwen2.5:1.5b.'})}\n\n"
            return
        try:
            start, end = accumulated.find("{"), accumulated.rfind("}") + 1
            graph = json.loads(accumulated[start:end])
        except Exception:
            graph = {"nodes": [], "edges": [], "parse_error": True}
        yield f"data: {json.dumps({'type': 'done', **graph})}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")
