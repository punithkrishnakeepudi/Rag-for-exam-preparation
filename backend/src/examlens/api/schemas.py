from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Literal


AnswerMode = Literal[
    "one-line",
    "short",
    "long",
    "bullets",
    "2-mark",
    "5-mark",
    "10-mark",
    "15-mark",
    "definition",
    "comparison",
    "notes",
    "flowchart",
    "mindmap",
    "memorize",
]


class UploadResponse(BaseModel):
    request_id: str
    document_ids: list[str]
    status: str


class AskRequest(BaseModel):
    session_id: str = "default"
    question: str
    answer_mode: AnswerMode = "short"
    document_scope: list[str] | None = None
    citation_mode: str = "inline"
    temperature: float | None = None


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    page_start: int | None = None
    page_end: int | None = None
    quote: str
    score: float


class AskResponse(BaseModel):
    request_id: str
    message_id: str
    answer_mode: AnswerMode
    answer: str
    citations: list[Citation]
    grounded: bool = True
    retrieval: dict[str, Any] = Field(default_factory=dict)


class NotesRequest(BaseModel):
    session_id: str = "default"
    document_id: str
    topic: str | None = None
    style: str = "chapter-wise"


class NotesResponse(BaseModel):
    request_id: str
    note_id: str
    markdown: str
    citations: list[Citation]


class DiagramRequest(BaseModel):
    session_id: str = "default"
    document_id: str
    topic: str
    diagram_type: Literal["flowchart", "mindmap"] = "flowchart"


class DiagramResponse(BaseModel):
    request_id: str
    diagram_id: str
    diagram_type: str
    mermaid: str
    status: str

