# Hybrid Multimodal RAG System Plan

## 1. Project review summary

The current repository already has a strong base for a document-based AI assistant:

- FastAPI backend with REST endpoints
- React frontend for notebook-style interaction
- OpenRouter integration for chat, embeddings, and generation
- ChromaDB for vector search
- PDF/text/docx/web ingestion support

What is missing for the upgraded research-grade version:

- A true multimodal pipeline for scanned PDFs and image-heavy documents
- A Google-style knowledge-first retrieval layer instead of only chunk vector search
- Better handling of long documents such as 200-page PDFs
- A stronger web-page ingestion pipeline that improves retrieval quality from pasted URLs
- A more unique architecture that can be presented as a research contribution

---

## 2. Core vision

I propose a hybrid system that combines:

1. RAG for grounded answer generation
2. An OKF-inspired knowledge-first layer for structure, reasoning, and evidence organization
3. Multimodal understanding for images and scanned pages
4. Hybrid retrieval that improves over plain similarity search

This will make the system feel more like a research-grade knowledge engine than a normal chatbot.

---

## 3. OKF as an alternative or complement to RAG

The Open Knowledge Format (OKF) is a lightweight, structured way to represent knowledge in plain Markdown files with YAML metadata and explicit links. In simple terms, it gives AI systems a deterministic and human-readable knowledge layer instead of relying only on vector similarity over raw text chunks.

### Why OKF is relevant here

- RAG is strong for exploratory search across messy documents and web content.
- OKF is stronger for curated facts, rules, definitions, schemas, and structured knowledge that should remain consistent and explicit.
- In this project, OKF can act as the knowledge-first layer for core concepts, document summaries, section maps, and reusable reasoning structures.

### How it fits the proposed system

Instead of using only traditional RAG, the system can use a hybrid design:

- RAG for broad retrieval over long and messy documents
- OKF for precise, structured, and explainable knowledge access

This is especially useful for academic documents, where the system needs both deep retrieval and reliable organization of concepts, definitions, and relationships.

---

## 4. Proposed architecture: Hybrid Multimodal Knowledge RAG

### 3.1 High-level design

The system will be built in five layers:

1. Ingestion Layer
   - Accepts PDFs, web pages, images, text files, and DOCX files
   - Extracts text, layout, headings, tables, captions, metadata, and embedded images
   - Handles very long documents by creating page/section/document maps

2. Multimodal Understanding Layer
   - Uses Nvidia vision/OCR APIs for scanned pages and image-based content
   - Extracts text from images, figures, screenshots, charts, and diagrams
   - Stores image captions and OCR results as searchable evidence

3. Knowledge Structuring Layer
   - Builds a structured knowledge representation from the document
   - Organizes content into sections, subsections, entities, concepts, and relationships
   - Creates a lightweight knowledge graph or knowledge index for retrieval

4. Hybrid Retrieval Layer
   - Combines dense vector retrieval, sparse lexical retrieval, metadata matching, and graph-based relevance
   - Improves results for pasted web pages by using URL, title, headings, anchor text, and page structure
   - Uses a reranking stage to improve final evidence selection

5. Generation Layer
   - Uses OpenRouter for chat and reasoning
   - Answers are grounded with citations to page, section, image, and chunk evidence
   - Supports long-context reasoning across multiple evidence sources

---

## 4. Why this architecture is unique

The main novelty is not only “RAG + LLM”, but a hybrid system that merges:

- Retrieval-augmented generation
- Structured knowledge organization
- Multimodal document understanding
- Long-document processing
- Web-source enhancement

This makes the project suitable for a research paper because it introduces a new design angle:

> A knowledge-first multimodal RAG pipeline for long and image-rich academic documents.

That is much stronger than a basic chatbot over PDFs.

---

## 5. Core components to implement

### 5.1 Document ingestion module

Responsibilities:
- Parse PDFs with page-level structure
- Preserve headings, paragraphs, tables, and references
- Extract images and embedded visuals
- Split long documents into logical chunks

For 200-page PDFs, the system should:
- chunk by section and page rather than only by fixed token count
- keep a document map for navigation
- store page-level metadata for citation accuracy

### 5.2 OCR and vision processing

Responsibilities:
- Use Nvidia API for image OCR and visual understanding
- Extract text from scanned pages and screenshot-like content
- Generate image captions for figures and diagrams
- Link OCR output back to the source page

### 5.3 Knowledge graph / knowledge layer

Responsibilities:
- Extract entities, key concepts, and relationships
- Build a lightweight graph from documents and websites
- Link chunks to sections, entities, and source pages

This layer is the “Google-style knowledge-first” portion of the architecture.

### 5.4 Hybrid retriever

The retriever should not depend only on vector similarity. It should combine:

- Dense vector similarity
- Sparse lexical overlap
- Metadata relevance
- Section/page-level relevance
- Graph-based neighborhood relevance

This is the main improvement for web pages and large documents.

### 5.5 Answer generator

Responsibilities:
- Use OpenRouter for chat responses
- Generate grounded answers with citations
- Support multi-hop reasoning over multiple retrieved evidence nodes
- Return structured answer objects with sources and confidence hints

---

## 6. Suggested retrieval strategy for web pages

To improve results when a user pastes a website URL or web content, the system should use a richer similarity strategy:

1. Extract title, headings, paragraphs, and anchor text
2. Build a structured representation of the page
3. Score relevance using:
   - semantic similarity
   - keyword overlap
   - heading/title match
   - section-level proximity
   - URL and domain context
4. Re-rank the top candidates before passing them to the LLM

This will make web ingestion significantly better than simple chunk embedding alone.

---

## 7. Handling large PDFs and images

The system must be designed for academic and research documents.

### Requirements
- Process PDFs with 200+ pages
- Preserve image context from figures, charts, and scanned pages
- Support mixed content: text + equations + diagrams + tables
- Provide accurate citations to pages and sections

### Approach
- Create a hierarchical document index:
  - document → chapter/section → page → chunk
- For every page, store:
  - extracted text
  - OCR text if needed
  - images or figure captions
  - page-level metadata
- Use a retrieval strategy that can retrieve evidence from either text or image-derived content

---

## 8. Architecture modules to add in this repository

The existing project structure can be extended like this:

- backend/src/studylens/ingest.py
  - upgrade for multi-modal ingestion
  - add page/section-aware chunking

- backend/src/studylens/vision.py
  - new Nvidia OCR/vision integration

- backend/src/studylens/knowledge.py
  - entity extraction and lightweight knowledge graph logic

- backend/src/studylens/retriever.py
  - hybrid retrieval orchestration

- backend/src/studylens/pipeline.py
  - orchestrates ingestion → structure → retrieval → answer generation

- frontend/src/components/
  - add visual evidence and source explanation views

---

## 9. Recommended backend configuration

### API keys
- OpenRouter API key for chat and reasoning
- Nvidia API key for vision/OCR processing

### Environment variables
- OPENROUTER_API_KEY
- OPENROUTER_MODEL
- OPENROUTER_EMBED_MODEL
- NVIDIA_API_KEY
- NVIDIA_VISION_ENDPOINT or equivalent
- CHROMA_PATH
- DB_URL
- UPLOAD_PATH

---

## 10. Research-paper angle

This project can be positioned as:

- A hybrid multimodal retrieval framework for academic documents
- A knowledge-first RAG system enhanced by OCR and structured knowledge organization
- A long-document processing pipeline that supports PDF, web, and image-rich content

### Possible paper title ideas
- Hybrid Multimodal RAG for Long and Image-Rich Academic Documents
- Knowledge-First Retrieval for Multimodal Document Understanding
- A Hybrid Retrieval Architecture for Research Document Intelligence

---

## 11. Implementation roadmap

### Phase 1: Foundation
- Upgrade ingestion for PDFs, websites, and images
- Add OCR/vision support using Nvidia APIs
- Preserve page-level and section-level metadata

### Phase 2: Hybrid retrieval
- Add dense + sparse + metadata + graph retrieval
- Improve ranking for web pages and long documents

### Phase 3: Knowledge layer
- Build lightweight structure extraction and document graph logic
- Connect chunks to concepts and sections

### Phase 4: Research-grade demo
- Add source explanation, evidence highlighting, and image-aware answers
- Prepare evaluation plan and paper-ready architecture explanation

### Phase 5: Evaluation and paper writing
- Compare basic RAG vs hybrid system
- Measure retrieval quality, grounding, and answer usefulness
- Write experiment results and architecture contributions

---

## 12. Expected final outcome

By the end of this work, the system should:

- accept PDF, web, and image-rich content
- process long academic documents effectively
- use Nvidia APIs for image and OCR understanding
- use OpenRouter for chat and reasoning
- provide better retrieval than simple vector-only RAG
- become a strong candidate for a research paper and presentation
