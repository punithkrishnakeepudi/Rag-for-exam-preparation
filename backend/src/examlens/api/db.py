from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from .config import settings


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  sha256 TEXT UNIQUE NOT NULL,
  filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  title TEXT,
  source_type TEXT NOT NULL,
  status TEXT NOT NULL,
  raw_text TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  page_start INTEGER,
  page_end INTEGER,
  heading_path TEXT,
  text TEXT NOT NULL,
  token_count INTEGER NOT NULL,
  checksum TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
  chunk_id,
  document_id,
  text,
  heading_path,
  tokenize = 'porter'
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  title TEXT,
  created_at TEXT NOT NULL,
  last_active_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL,
  mode TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS citations (
  id TEXT PRIMARY KEY,
  message_id TEXT NOT NULL,
  chunk_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  page_start INTEGER,
  page_end INTEGER,
  quote TEXT NOT NULL,
  score REAL NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_packs (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  topic_key TEXT NOT NULL,
  summary_md TEXT NOT NULL,
  concepts_json TEXT NOT NULL,
  qa_json TEXT NOT NULL,
  keywords_json TEXT NOT NULL,
  source_chunk_ids_json TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(document_id, topic_key)
);
"""


def _connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(SCHEMA)

