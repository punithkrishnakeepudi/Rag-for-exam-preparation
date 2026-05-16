# Project Requirements: ExamLens

ExamLens is an open-source, local-first AI study assistant designed to help students prepare for exams by transforming documents into grounded, exam-ready answers.

## 1. Document Ingestion
- **Multi-Format Support**: The system must support uploading and parsing various file formats, including:
  - PDF (.pdf)
  - Word Documents (.docx)
  - Text Files (.txt)
  - Markdown (.md)
  - Images (via OCR/Vision models if applicable, or as part of the ingestion pipeline)
  - Manual text pastes
- **Local Storage**: All uploaded files and processed data must be stored locally on the user's machine to ensure privacy and offline accessibility.

## 2. RAG (Retrieval-Augmented Generation) System
- **Hybrid Retrieval**: Combine lexical search (e.g., SQLite FTS5) with semantic search to provide high precision on technical terms and conceptual matches.
- **Grounded Answers**: Every response must be grounded in the uploaded documents, with clear citations (e.g., [Doc:Page] or [Doc:Chunk]).
- **Local LLM Integration**: Use local LLMs (e.g., via Ollama) to process queries and generate responses without sending data to external servers.

## 3. Exam-Oriented Features
- **Structured Answer Formatting**: Generate answers tailored to standard exam formats:
  - **Very Short (1-mark/Definition)**: Concise, one-line definitions.
  - **Short Answer (2-5 marks)**: Bulleted lists starting with a definition.
  - **Long Answer (10-15 marks)**: Comprehensive structure with Introduction, Headings, Key Points, and Conclusion.
  - **Comparison Tables**: Side-by-side comparison for "Difference between X and Y" queries.
- **Study Briefs**: Automatically generate summaries and key concept lists upon document ingestion.

## 4. User Interface & Experience
- **Chatbot Interface**: A conversational interface similar to NotebookLM, where users can query their documents.
- **Notebook Mode**: A multi-pane view showing the chat, document library, and generated study notes/diagrams.
- **Diagram Generation**: Ability to generate Mermaid.js flowcharts and mindmaps from hierarchical or procedural text.

## 5. Technical Requirements
- **Backend**: Python-based (FastAPI) for API and orchestration.
- **Frontend**: Modern web framework (React + Vite + Tailwind CSS).
- **Database**: Lightweight local database (SQLite) for metadata and chat history.
- **Open Source**: The project should be open-source and easily deployable by any student.

## 6. Optimization for Local Models
- The system should be optimized for small, efficient local models (e.g., Qwen 2.5 1.5B) to ensure smooth performance on consumer-grade hardware.
