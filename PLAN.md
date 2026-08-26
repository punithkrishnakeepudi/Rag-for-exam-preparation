# StudyLens — Open-Source Local NotebookLM Alternative

> A fully local, privacy-first AI study assistant. Upload documents, create notebooks, chat with your content, generate quizzes, and map concepts — all offline, powered by Ollama + Qwen.

---

## Stack

| Layer | Choice | Reason |
|---|---|---|
| LLM | Qwen (via Ollama) | Local, no API key, already installed |
| Embeddings | `nomic-embed-text` via Ollama | Same Ollama instance, fully offline |
| Vector DB | ChromaDB (persistent) | Zero server, single pip install, persists to disk |
| Backend | Python + FastAPI | Async, clean REST API, strong PDF/doc ecosystem |
| Frontend | React + Tailwind CSS | Component-based, easy NotebookLM-style layout |
| Install | `pip install` + `npm install` | No Docker required — anyone can clone and run |

---

## Features

### Core — Notebooks
- [ ] Create, rename, delete notebooks
- [ ] Each notebook has its own isolated document set, vector collection, and chat history
- [ ] Notebook list in sidebar with document count

### Core — Document Ingestion
- [ ] Upload **PDF** files (parse with `pymupdf` / `pdfplumber`)
- [ ] Upload **plain text / Markdown** (`.txt`, `.md`)
- [ ] Upload **Word documents** (`.docx` via `python-docx`)
- [ ] Ingest from **web URL** (scrape with `trafilatura` or `httpx` + `BeautifulSoup`)
- [ ] Chunking strategy: overlapping sliding window (512 tokens, 64 overlap)
- [ ] Embed chunks with `nomic-embed-text` → store in ChromaDB per notebook
- [ ] Show upload progress and indexing status in UI

### Core — RAG Chat
- [ ] Chat interface per notebook (multi-turn conversation history)
- [ ] Each question: embed → retrieve top-k chunks → build prompt → stream Qwen response
- [ ] **Source citations**: every answer shows the source document name + page/chunk reference
- [ ] Streaming response (token by token, like ChatGPT)

### Feature — Auto Document Summary
- [ ] On upload completion, auto-trigger a summary generation call to Qwen
- [ ] Summary stored alongside the document record
- [ ] Display as a collapsible "Overview" card in the document panel

### Feature — Quiz / Flashcard Generation
- [ ] User triggers "Generate Quiz" per document or per notebook
- [ ] Qwen generates N multiple-choice or fill-in-the-blank questions from the content
- [ ] Interactive quiz UI: show question → reveal answer
- [ ] Export quiz as JSON or plain text

### Feature — Mind Map / Concept Map
- [ ] User triggers "Generate Mind Map" per document or per notebook
- [ ] Qwen extracts key concepts and relationships → returns structured JSON
- [ ] Render as interactive graph in UI using `React Flow` or `D3.js`
- [ ] Export as PNG or JSON

### Feature — Source Citations
- [ ] Every RAG answer includes a "Sources" section
- [ ] Each source shows: document name, page number (if PDF), and the exact chunk text
- [ ] Clickable — clicking a citation highlights the chunk in a document preview panel

---

## Architecture

```
studylens/
├── backend/
│   ├── src/studylens/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── config.py            # Settings (Ollama URL, model names, ChromaDB path)
│   │   ├── db.py                # SQLite for notebooks/documents metadata (via SQLModel)
│   │   ├── chroma.py            # ChromaDB client wrapper
│   │   ├── ollama_client.py     # Ollama API calls (embed + generate + stream)
│   │   ├── ingestion/
│   │   │   ├── pdf.py           # PDF parsing
│   │   │   ├── docx.py          # Word doc parsing
│   │   │   ├── text.py          # Plain text / markdown
│   │   │   ├── url.py           # Web URL scraping
│   │   │   └── chunker.py       # Sliding window chunker
│   │   ├── api/
│   │   │   ├── notebooks.py     # CRUD /notebooks
│   │   │   ├── documents.py     # Upload + ingest /documents
│   │   │   ├── chat.py          # RAG Q&A + streaming /chat
│   │   │   ├── summary.py       # /summary
│   │   │   ├── quiz.py          # /quiz
│   │   │   └── mindmap.py       # /mindmap
│   │   └── prompts.py           # All prompt templates
│   ├── pyproject.toml
│   └── .python-version
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx         # Notebook list
│   │   │   └── Notebook.tsx     # Main workspace (docs + chat)
│   │   ├── components/
│   │   │   ├── Sidebar.tsx      # Notebook list + nav
│   │   │   ├── DocumentPanel.tsx # Upload, doc list, summaries
│   │   │   ├── ChatPanel.tsx    # Chat interface with citations
│   │   │   ├── QuizPanel.tsx    # Interactive quiz UI
│   │   │   ├── MindMapPanel.tsx # Graph visualization
│   │   │   └── SourceCitation.tsx
│   │   ├── api/                 # fetch wrappers for each backend endpoint
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── .env.example                 # OLLAMA_BASE_URL, MODEL_NAME, EMBED_MODEL
├── README.md
└── PLAN.md
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET/POST/DELETE | `/api/notebooks` | List, create, delete notebooks |
| GET/POST/DELETE | `/api/notebooks/{id}/documents` | List, upload, delete documents |
| POST | `/api/notebooks/{id}/chat` | RAG Q&A (streaming SSE) |
| GET | `/api/notebooks/{id}/chat/history` | Get chat history |
| POST | `/api/documents/{id}/summary` | Generate/fetch summary |
| POST | `/api/documents/{id}/quiz` | Generate quiz questions |
| POST | `/api/notebooks/{id}/mindmap` | Generate concept map JSON |

---

## RAG Pipeline

```
User question
     │
     ▼
Embed with nomic-embed-text (Ollama)
     │
     ▼
ChromaDB similarity search (top 5 chunks, filtered to notebook)
     │
     ▼
Build prompt:
  [System] You are a study assistant. Answer using only the context below.
  [Context] chunk1 ... chunk2 ... chunk3 ...
  [Question] <user question>
     │
     ▼
Stream response from Qwen (Ollama)
     │
     ▼
Return: { answer: "...", sources: [{doc, page, chunk_text}] }
```

---

## UI Layout (NotebookLM-style)

```
┌─────────────┬──────────────────────────────┬──────────────────────┐
│  Sidebar    │     Document Sources          │     Chat             │
│             │                               │                      │
│  Notebooks  │  [+ Add source]               │  ┌────────────────┐  │
│  ─────────  │                               │  │ AI Answer      │  │
│  > CS101    │  📄 lecture1.pdf              │  │ ...            │  │
│    ML Notes │     [Overview ▼]              │  │ Sources: [1]   │  │
│    OS Exam  │                               │  └────────────────┘  │
│             │  📄 assignment2.docx          │                      │
│  [+ New]    │  🌐 https://...               │  [Quiz] [Mind Map]   │
│             │                               │                      │
│             │                               │  > Type a question   │
└─────────────┴──────────────────────────────┴──────────────────────┘
```

---

## Build Phases

### Phase 1 — Foundation (get something running)
1. FastAPI project setup + ChromaDB + SQLite (SQLModel)
2. Ollama client (embed + generate + stream)
3. Notebook CRUD API
4. PDF upload + chunking + indexing
5. Basic RAG chat endpoint (no streaming yet)
6. React skeleton: sidebar + document list + chat input

### Phase 2 — Full Ingestion
7. DOCX, plain text, Markdown support
8. Web URL scraping + indexing
9. Upload progress feedback in UI
10. Source citations in chat responses

### Phase 3 — AI Features
11. Auto document summary on upload
12. Quiz generation + interactive quiz UI
13. Mind map generation + React Flow visualization

### Phase 4 — Polish
14. Streaming SSE chat responses (token by token)
15. Document preview panel with chunk highlighting
16. README with setup instructions (Ollama model pull commands included)
17. `.env.example` + configuration guide

---

## Prerequisites for Anyone Cloning

```bash
# 1. Install Ollama (https://ollama.com)
ollama pull qwen2.5        # or whichever Qwen model you have
ollama pull nomic-embed-text

# 2. Clone and run backend
git clone <repo>
cd studylens/backend
pip install -e .
uvicorn studylens.main:app --reload

# 3. Run frontend
cd ../frontend
npm install
npm run dev
```

---

## Key Dependencies

**Backend**
- `fastapi`, `uvicorn` — web server
- `chromadb` — vector store
- `sqlmodel` — SQLite ORM for notebooks/docs metadata
- `pymupdf` (fitz) — PDF parsing
- `python-docx` — Word doc parsing
- `trafilatura` — web URL content extraction
- `httpx` — async HTTP (Ollama API calls)
- `python-multipart` — file upload

**Frontend**
- `react`, `react-router-dom` — app shell
- `tailwindcss` — styling
- `@xyflow/react` (React Flow) — mind map visualization
- `react-markdown` — render AI responses as markdown
- `eventsource` / native `EventSource` — streaming SSE
