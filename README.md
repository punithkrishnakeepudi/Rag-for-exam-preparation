# StudyLens

**Local, open-source alternative to NotebookLM — runs 100% on your machine.**

Upload your lecture notes, textbooks, or research papers and instantly get: streaming RAG chat with citations, auto-generated summaries, MCQ quizzes, interactive mind maps, and exportable slide decks — powered by configurable OpenRouter models and embeddings.

> Built as a college mini-project. Works offline. Your data never leaves your machine.

---

## Features

| Feature | Description |
|---|---|
| **Notebooks** | Isolated workspaces — each notebook has its own documents, chat history, and vector index |
| **Document ingestion** | Upload PDF, DOCX, TXT, Markdown files or paste a web URL |
| **RAG Chat** | Streaming answers grounded in your documents, with source citations and persistent history |
| **Auto-summary** | Each document gets a 3–5 sentence summary generated on upload |
| **Quiz Generator** | Generates MCQ questions from any document with real-time streaming progress |
| **Mind Map** | Interactive draggable concept graph extracted from document content |
| **Slide Deck** | 4-layout presentation engine with speaker notes + one-click offline HTML export |
| **Image Generation** | (Optional) AI-generated slide visuals via LCM Dreamshaper on CUDA GPU |

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — REST API + Server-Sent Events (SSE) streaming
- [ChromaDB](https://www.trychroma.com/) — local vector store for semantic search
- [SQLite](https://www.sqlite.org/) via [SQLModel](https://sqlmodel.tiangolo.com/) — persistent storage for notebooks, documents, chat history
- [OpenRouter](https://openrouter.ai/docs/api_reference/overview) — routed LLM generation and embeddings
- [PyMuPDF](https://pymupdf.readthedocs.io/) · [python-docx](https://python-docx.readthedocs.io/) · [trafilatura](https://trafilatura.readthedocs.io/) — document parsers

**Frontend**
- [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/) + [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/) — dark-mode UI
- [React Flow (@xyflow/react)](https://reactflow.dev/) — mind map graph
- [react-markdown](https://github.com/remarkjs/react-markdown) — renders LLM responses

---

## Prerequisites

Install these before anything else:

1. **[OpenRouter](https://openrouter.ai/keys)** — API key and model access
2. **Python ≥ 3.10**
3. **Node.js ≥ 18**

Create an OpenRouter API key, then set `OPENROUTER_MODEL` and `OPENROUTER_EMBED_MODEL` in `backend/.env`. Model IDs must include the provider prefix, such as `openai/gpt-4o-mini`.

> **Privacy note:** OpenRouter sends prompts, retrieved document chunks, and embeddings to the selected upstream provider. Do not upload sensitive material unless your institution permits it.

---

## Quick Start

```bash
git clone https://github.com/punithkrishnakeepudi/Rag-for-exam-preparation.git
cd Rag-for-exam-preparation
```

### Option A — One-command setup (Linux / macOS)

```bash
chmod +x setup.sh && ./setup.sh
```

This installs backend dependencies, frontend dependencies, copies `.env`, and prints the start commands.

### Option B — Manual setup

**1. Backend**

```bash
cd backend
cp ../.env.example .env          # copy default config (edit if needed)
pip install -r requirements.txt  # or: pip install -e .
```

**2. Frontend**

```bash
cd frontend
npm install
```

### Running the app

Open **two terminals**:

```bash
# Terminal 1 — backend (from repo root)
cd backend
PYTHONPATH=src uvicorn studylens.main:app --reload
# API → http://localhost:8000
```

```bash
# Terminal 2 — frontend (from repo root)
cd frontend
npm run dev
# UI  → http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Configuration

All settings live in `backend/.env` (copied from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | OpenRouter generation model ID |
| `OPENROUTER_EMBED_MODEL` | `openai/text-embedding-3-small` | OpenRouter embedding model ID |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API base URL |
| `OPENROUTER_API_KEY` | unset | Required API key (keep out of source control) |
| `OPENROUTER_APP_NAME` | `StudyLens` | Optional app attribution title |
| `OPENROUTER_HTTP_REFERER` | unset | Optional app attribution URL |
| `CHROMA_PATH` | `./data/chroma` | Where ChromaDB stores the vector index |
| `DB_URL` | `sqlite:///./data/studylens.db` | SQLite database path |
| `UPLOAD_PATH` | `./data/uploads` | Where uploaded files are stored |
| `CHUNK_SIZE` | `256` | Tokens per chunk during ingestion |
| `CHUNK_OVERLAP` | `32` | Overlap between adjacent chunks |
| `RAG_TOP_K` | `3` | Number of chunks retrieved per query |
| `ENABLE_IMAGE_GEN` | `false` | Set `true` to enable AI slide images (requires GPU + extra deps) |
| `IMAGE_GEN_MODEL` | `SimianLuo/LCM_Dreamshaper_v7` | HuggingFace diffusion model for slide images |

---

## Optional: AI Slide Image Generation

Generates a vector-style illustration for each slide using a 4-step LCM diffusion model. Tested on a GTX 1650 (4 GB VRAM), ~5 seconds per image.

```bash
# 1. Install GPU dependencies (inside the backend directory)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install diffusers accelerate Pillow transformers

# 2. Enable in .env
ENABLE_IMAGE_GEN=true
IMAGE_GEN_MODEL=SimianLuo/LCM_Dreamshaper_v7
```

The model (~2 GB) downloads automatically on first use.

---

## Project Structure

```
.
├── backend/
│   ├── .env.example             # copy to .env and edit
│   ├── requirements.txt         # pip dependencies
│   ├── pyproject.toml           # package metadata
│   └── src/studylens/
│       ├── main.py              # all FastAPI routes (notebooks, chat, quiz, slides, mindmap)
│       ├── config.py            # env-based settings
│       ├── db.py                # SQLite models: Notebook, Document, Message
│       ├── chroma.py            # ChromaDB collection helpers
│       ├── openrouter.py       # embeddings + generation + streaming wrapper
│       ├── ingest.py            # PDF / DOCX / TXT / URL parsers + chunker
│       └── prompts.py           # all LLM prompt templates
│
├── frontend/
│   └── src/
│       ├── api.ts               # all API calls + SSE stream helpers
│       ├── pages/
│       │   ├── Home.tsx         # notebook list / create / delete
│       │   └── Notebook.tsx     # main workspace with tabbed panels
│       └── components/
│           ├── DocumentPanel.tsx    # upload sidebar + document list
│           ├── ChatPanel.tsx        # streaming chat with persistent history
│           ├── QuizPanel.tsx        # interactive MCQ quiz with progress bar
│           ├── MindMapPanel.tsx     # React Flow draggable concept graph
│           ├── SlidesPanel.tsx      # slide deck viewer + offline HTML export
│           └── ProgressBar.tsx      # shared streaming progress component
│
├── .env.example                 # root env template
├── setup.sh                     # one-command dev setup script
└── Makefile                     # dev convenience commands
```

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/notebooks` | List all notebooks |
| `POST` | `/api/notebooks` | Create a notebook |
| `PATCH` | `/api/notebooks/:id` | Rename a notebook |
| `DELETE` | `/api/notebooks/:id` | Delete notebook + all its data |
| `GET` | `/api/notebooks/:id/documents` | List documents in a notebook |
| `POST` | `/api/notebooks/:id/documents` | Upload file or ingest URL |
| `DELETE` | `/api/notebooks/:id/documents/:doc_id` | Remove a document |
| `GET` | `/api/notebooks/:id/messages` | Get chat history |
| `POST` | `/api/notebooks/:id/messages` | Save a message |
| `DELETE` | `/api/notebooks/:id/messages` | Clear chat history |
| `POST` | `/api/notebooks/:id/chat` | SSE streaming RAG chat |
| `POST` | `/api/documents/:id/quiz` | SSE streaming quiz generation |
| `POST` | `/api/documents/:id/slides` | SSE streaming slide generation |
| `POST` | `/api/documents/:id/mindmap` | SSE streaming mind map extraction |

Interactive API docs available at [http://localhost:8000/docs](http://localhost:8000/docs) when the backend is running.

---

## Troubleshooting

**OpenRouter not responding**
Check that `OPENROUTER_API_KEY` is set, the selected model IDs are valid on OpenRouter, and your account has credits or access to the chosen models.

**Slow responses / timeouts**
Choose a faster OpenRouter model, reduce `RAG_TOP_K`, or reduce the requested quiz count.

**ChromaDB / SQLite errors on first run**
The backend creates `backend/data/` directories automatically on startup. If you see permission errors, make sure you're running from inside the `backend/` directory.

**CORS errors in browser**
The backend allows all origins by default (`allow_origins=["*"]`). If you've changed the frontend port, no changes are needed.

---

## Contributing

1. Fork the repo and create a feature branch
2. Make your changes
3. Open a pull request with a clear description of what changed and why

Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/punithkrishnakeepudi/Rag-for-exam-preparation/issues).

---

## License

MIT — do whatever you want with it.

## OpenRouter migration notes

The old Ollama client has been replaced by `backend/src/studylens/openrouter.py`. The client covers:

- `POST /chat/completions` for summaries and streamed chat, quizzes, slides, and mind maps
- `POST /embeddings` for document and query vectors
- OpenRouter JSON mode for structured slide output

Changing `OPENROUTER_EMBED_MODEL` changes the vector dimension or embedding space. Delete `backend/data/chroma/` and re-upload documents after changing the embedding model; otherwise old and new vectors may be incompatible.
