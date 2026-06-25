from pathlib import Path
from .config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + CHUNK_SIZE]))
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]


def parse_pdf(path: str) -> str:
    import fitz
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


def parse_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


async def parse_url(url: str) -> str:
    """Async URL fetch — does not block the event loop."""
    import httpx
    import trafilatura
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    return trafilatura.extract(r.text) or ""


async def extract_text(source_type: str, source_ref: str) -> str:
    try:
        if source_type == "pdf":
            return parse_pdf(source_ref)
        if source_type == "docx":
            return parse_docx(source_ref)
        if source_type in ("txt", "md"):
            return parse_text(source_ref)
        if source_type == "url":
            return await parse_url(source_ref)
    except Exception as e:
        print(f"[ingest] failed ({source_type} {source_ref}): {e}")
    return ""
