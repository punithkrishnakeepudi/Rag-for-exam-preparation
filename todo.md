# Implementation TODOs: Hybrid Multimodal RAG System

Based on the proposed architecture in `plan.md`, here is the checklist for implementing the upgraded research-grade RAG system.

## Phase 1: Foundation (Ingestion & OCR)
- [ ] **Environment Setup**
  - [ ] Configure `NVIDIA_API_KEY` and `NVIDIA_VISION_ENDPOINT`.
  - [ ] Ensure `OPENROUTER_API_KEY`, models, and database paths are set up.
- [ ] **Upgrade Ingestion Module (`backend/src/studylens/ingest.py`)**
  - [ ] Implement multi-modal document ingestion (PDFs, websites, images, DOCX).
  - [ ] Add page-level and section-aware chunking for long documents (200+ pages).
  - [ ] Preserve document structure (headings, paragraphs, tables, references).
  - [ ] Extract images and embedded visuals from documents.
- [ ] **Implement Vision/OCR Module (`backend/src/studylens/vision.py`)**
  - [ ] Integrate Nvidia vision/OCR API for image processing.
  - [ ] Extract text from scanned pages, screenshots, charts, and diagrams.
  - [ ] Generate captions for extracted figures and images.
  - [ ] Link OCR output/captions back to the original source page.

## Phase 2: Hybrid Retrieval
- [ ] **Upgrade Retriever (`backend/src/studylens/retriever.py`)**
  - [ ] Implement Dense vector similarity search.
  - [ ] Implement Sparse lexical overlap retrieval.
  - [ ] Implement Metadata relevance filtering (URL, title, heading, page-level).
  - [ ] Implement Graph-based neighborhood relevance.
  - [ ] Combine retrieval methods and implement a re-ranking stage for top candidates.

## Phase 3: Knowledge Layer
- [ ] **Implement Knowledge Extraction (`backend/src/studylens/knowledge.py`)**
  - [ ] Extract entities, key concepts, and relationships from ingested chunks.
  - [ ] Build a lightweight structured knowledge graph/index.
  - [ ] Connect document chunks to sections, entities, and source pages.

## Phase 4: Generation and Orchestration
- [ ] **Update Pipeline (`backend/src/studylens/pipeline.py`)**
  - [ ] Wire up ingestion -> knowledge structure -> hybrid retrieval -> answer generation.
- [ ] **Answer Generator**
  - [ ] Ground answers with citations to page, section, image, and chunk evidence.
  - [ ] Enable multi-hop reasoning over multiple evidence sources.
  - [ ] Return structured answer objects with source links and confidence hints.

## Phase 5: Frontend & Research-Grade Demo
- [ ] **Update Frontend UI (`frontend/src/components/`)**
  - [ ] Add support for displaying visual evidence (images, charts).
  - [ ] Add source explanation and evidence highlighting views.
  - [ ] Build a UI component to visualize the document graph or structured knowledge (optional but recommended for a "knowledge-first" feel).

## Phase 6: Evaluation and Paper Preparation
- [ ] Setup evaluation metrics (retrieval quality, grounding, answer usefulness).
- [ ] Compare the new hybrid system against basic RAG.
- [ ] Document experiment results and architecture for a research paper.
