# ExamLens Local

Local-first AI study assistant for grounded document Q&A, exam-style answers, revision notes, and Mermaid diagrams.

## Stack

- Frontend: React + Vite
- Backend: FastAPI
- Local LLM: Ollama
- Storage: SQLite
- Retrieval: FTS5 + lightweight vector fallback
- Diagrams: Mermaid

## Run locally

1. Start Ollama and pull a local model:
   - `ollama pull qwen2.5:1.5b-instruct`
2. Start backend:
   - `cd backend`
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e .`
   - `uvicorn examlens.api.main:app --reload --port 8000`
3. Start frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## What is included

- Upload PDF, DOCX, TXT, MD, or pasted notes
- Parse and chunk documents
- Search inside uploaded sources
- Ask grounded questions
- Generate exam-style answers
- Generate notes and Mermaid diagrams
- Store session history locally

## Notes

This first scaffold is designed to be extended into a production-grade local RAG/CAG study assistant. Retrieval and generation are intentionally modular so you can swap in stronger local models or embeddings later.
# Rag-for-exam-preparation
