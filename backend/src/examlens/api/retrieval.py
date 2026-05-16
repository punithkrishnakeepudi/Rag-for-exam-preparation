from __future__ import annotations

import re
from dataclasses import dataclass
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class Chunk:
    id: str
    document_id: str
    text: str
    page_start: int | None = None
    page_end: int | None = None
    heading_path: str | None = None
    token_count: int = 0


def split_into_chunks(text: str, chunk_size: int = 2200, overlap: int = 300) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        candidate = f"{buffer}\n\n{para}".strip()
        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer.strip())
            if len(para) > chunk_size:
                start = 0
                while start < len(para):
                    chunks.append(para[start : start + chunk_size].strip())
                    start += chunk_size - overlap
                buffer = ""
            else:
                buffer = para
    if buffer:
        chunks.append(buffer.strip())
    return chunks


class HybridRetriever:
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        self._matrix = None
        self._chunks: list[Chunk] = []
        self._fitted = False

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        if not chunks:
            self._matrix = None
            self._fitted = False
            return
        corpus = [c.text for c in chunks]
        self._matrix = self.vectorizer.fit_transform(corpus)
        self._fitted = True

    def search(self, query: str, top_k: int = 6) -> list[tuple[Chunk, float]]:
        if not self._chunks:
            return []
        if not self._fitted:
            self.index(self._chunks)
        if self._matrix is None:
            return []

        q = self.vectorizer.transform([query])
        scores = (self._matrix @ q.T).toarray().ravel()
        ranked = np.argsort(scores)[::-1][:top_k]
        results: list[tuple[Chunk, float]] = []
        for idx in ranked:
            score = float(scores[idx])
            if score <= 0:
                continue
            results.append((self._chunks[int(idx)], score))
        return results


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text)]
    common = Counter(words)
    return [w for w, _ in common.most_common(limit)]
