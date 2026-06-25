from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session, select
from .config import DB_URL

engine = create_engine(DB_URL)


class Notebook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    notebook_id: int = Field(foreign_key="notebook.id")
    name: str
    source_type: str  # pdf | docx | txt | url
    source_ref: str   # local path or URL
    summary: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    notebook_id: int = Field(foreign_key="notebook.id")
    role: str                       # 'user' | 'assistant'
    content: str
    sources_json: Optional[str] = None  # JSON array, assistant only
    created_at: datetime = Field(default_factory=datetime.utcnow)


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
