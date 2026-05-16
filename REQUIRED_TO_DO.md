# ExamLens: Required To-Do List

This document outlines the necessary steps and features to transform ExamLens into a robust, open-source RAG system for student exam preparation.

## 1. Multi-format Ingestion (OCR & Images)
- [ ] **OCR Integration**: Implement Tesseract or EasyOCR to extract text from images (JPG, PNG).
- [ ] **PDF Image Extraction**: Enhance the PDF parser to handle scanned PDFs using OCR.
- [ ] **File Type Expansion**: Support for additional formats like `.ppt`, `.pptx`, and `.csv`.
- [ ] **Image Processing Pipeline**: Add a preprocessing step to improve OCR accuracy (grayscale, deskewing).

## 2. Retrieval Enhancement (Hybrid Search)
- [ ] **Semantic Search Refinement**: Integrate local embeddings (e.g., FastEmbed or Sentence-Transformers) for better semantic retrieval.
- [ ] **Cross-Document Retrieval**: Optimize queries that span across multiple uploaded documents.
- [ ] **Re-ranking Implementation**: Use a lightweight re-ranker (e.g., Cohere-like local models) to prioritize the most relevant chunks.
- [ ] **Metadata Filtering**: Allow users to filter searches by document title, date, or custom tags.

## 3. Exam Mode Refinement (Answer Formatting)
- [ ] **Advanced Prompt Engineering**: Refine templates for 2-mark, 5-mark, and 10-mark answers to ensure strict adherence to exam patterns.
- [ ] **Comparison Table Logic**: Improve the model's ability to generate structured comparison tables.
- [ ] **Citation Accuracy**: Ensure every claim is precisely linked to the source [Doc:Page/Chunk].
- [ ] **Multi-lingual Support**: Enable support for exam preparation in languages other than English.

## 4. Local LLM Optimization
- [ ] **Model Selection**: Evaluate and support other lightweight models (e.g., Llama 3, Phi-3) for different hardware capabilities.
- [ ] **Context Window Management**: Optimize chunking and prompt construction to fit within the constraints of smaller models (1.5B - 3B).
- [ ] **Quantization**: Provide instructions or scripts for using quantized models to run on lower-end consumer hardware.

## 5. UI/UX Enhancements
- [ ] **Session Management**: Full implementation of creating, renaming, and deleting study sessions.
- [ ] **Export Options**: Enable exporting generated answers and notes to PDF, DOCX, or Markdown.
- [ ] **Dark Mode**: Add a "Focus Dark" theme for late-night study sessions.
- [ ] **Mobile Responsiveness**: Ensure the frontend is usable on tablets and mobile devices.
- [ ] **Interactive Diagrams**: Improve the Mermaid.js integration to allow users to edit or download diagrams.

## 6. Open Source & Community
- [ ] **Dockerization**: Provide a `docker-compose.yml` for one-click setup.
- [ ] **Contribution Guide**: Create `CONTRIBUTING.md` to help others contribute to the project.
- [ ] **Documentation**: Expand `README.md` with detailed installation steps and a troubleshooting guide.
- [ ] **Telemetry (Optional/Opt-in)**: Implement anonymous usage statistics (fully opt-in) to understand user needs.
