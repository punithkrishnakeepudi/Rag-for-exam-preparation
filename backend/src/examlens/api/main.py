from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .schemas import (
    AskRequest,
    AskResponse,
    DiagramRequest,
    DiagramResponse,
    NotesRequest,
    NotesResponse,
    UploadResponse,
)
from .services import (
    answer_question,
    generate_diagram,
    generate_notes,
    get_citations,
    get_session,
    ingest_file,
    ingest_paste,
    list_documents,
    list_sessions,
    export_note_markdown,
    search_documents,
)


app = FastAPI(title="ExamLens Local API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/api/v1/health")
def health():
    return {"ok": True}


@app.get("/api/v1/documents")
def documents():
    return {"request_id": f"req_{uuid.uuid4().hex[:8]}", "documents": list_documents()}


@app.get("/api/v1/sessions")
def sessions():
    return {"request_id": f"req_{uuid.uuid4().hex[:8]}", "sessions": list_sessions()}


@app.get("/api/v1/sessions/{session_id}")
def session(session_id: str):
    return {"request_id": f"req_{uuid.uuid4().hex[:8]}", "session": get_session(session_id)}


@app.post("/api/v1/documents/upload", response_model=UploadResponse)
async def upload_documents(
    session_id: str = Form("default"),
    source_type: str = Form("mixed"),
    paste_text: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
):
    ids: list[str] = []
    upload_dir = settings.data_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    if paste_text and paste_text.strip():
        ids.append(ingest_paste("pasted-notes", paste_text))
    if files:
        for file in files:
            target = upload_dir / file.filename
            with target.open("wb") as handle:
                shutil.copyfileobj(file.file, handle)
            ids.append(ingest_file(target, source_type or "mixed"))
    return UploadResponse(request_id=f"req_{uuid.uuid4().hex[:8]}", document_ids=ids, status="indexed")


@app.post("/api/v1/qa/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    result = await answer_question(req.session_id, req.question, req.answer_mode, req.document_scope, req.temperature)
    return AskResponse(
        request_id=f"req_{uuid.uuid4().hex[:8]}",
        **result,
    )


@app.get("/api/v1/qa/citations/{message_id}")
def fetch_citations(message_id: str):
    return {"request_id": f"req_{uuid.uuid4().hex[:8]}", "citations": get_citations(message_id)}


@app.post("/api/v1/notes/generate", response_model=NotesResponse)
async def notes(req: NotesRequest):
    result = await generate_notes(req.session_id, req.document_id, req.topic, req.style)
    return NotesResponse(request_id=f"req_{uuid.uuid4().hex[:8]}", **result)


@app.post("/api/v1/flowcharts/generate", response_model=DiagramResponse)
async def flowcharts(req: DiagramRequest):
    result = await generate_diagram(req.session_id, req.document_id, req.topic, req.diagram_type)
    return DiagramResponse(request_id=f"req_{uuid.uuid4().hex[:8]}", **result)


@app.get("/api/v1/documents/search")
def search(q: str, document_id: str | None = None):
    return {"request_id": f"req_{uuid.uuid4().hex[:8]}", "results": search_documents(q, document_id)}


@app.get("/api/v1/exports/notes/{note_id}")
def export_note(note_id: str):
    return {"request_id": f"req_{uuid.uuid4().hex[:8]}", **export_note_markdown(note_id)}
