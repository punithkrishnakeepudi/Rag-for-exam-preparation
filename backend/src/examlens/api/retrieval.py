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
    def __init__(self, db_conn=None) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        self._matrix = None
        self._chunks: list[Chunk] = []
        self._fitted = False
        self.db_conn = db_conn

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        if not chunks:
            self._matrix = None
            self._fitted = False
            return
        corpus = [c.text for c in chunks]
        self._matrix = self.vectorizer.fit_transform(corpus)
        self._fitted = True

    def _fts_search(self, query: str, document_ids: list[str] | None = None, top_k: int = 10) -> list[tuple[str, float]]:
        if not self.db_conn:
            return []

        q_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', query).strip()
        if not q_clean:
            return []

        sql = "SELECT chunk_id, rank FROM chunk_fts WHERE chunk_fts MATCH ? "
        params = [q_clean]

        if document_ids:
            sql += "AND document_id IN (" + ",".join("?" for _ in document_ids) + ") "
            params.extend(document_ids)

        sql += "ORDER BY rank LIMIT ?"
        params.append(top_k)

        try:
            rows = self.db_conn.execute(sql, params).fetchall()
            # FTS5 rank is better when lower, but we normalize it or just return it.
            # bm25-like: higher is better. In SQLite FTS5, smaller is better.
            return [(row["chunk_id"], 1.0 / (1.0 + row["rank"])) for row in rows]
        except Exception:
            return []

    def search(self, query: str, top_k: int = 6, document_ids: list[str] | None = None) -> list[tuple[Chunk, float]]:
        if not self._chunks:
            return []
        if not self._fitted:
            self.index(self._chunks)
        if self._matrix is None:
            return []

        # 1. TF-IDF Semantic-ish Search
        q_vec = self.vectorizer.transform([query])
        v_scores = (self._matrix @ q_vec.T).toarray().ravel()

        # 2. Lexical Search via FTS5
        fts_results = self._fts_search(query, document_ids, top_k=20)
        fts_scores = {cid: score for cid, score in fts_results}

        # 3. Hybrid RRF (simplified)
        combined: dict[str, float] = {}
        for i, chunk in enumerate(self._chunks):
            v_score = float(v_scores[i])
            f_score = fts_scores.get(chunk.id, 0.0)
            # Combine scores: weight FTS heavily for exam technicality
            score = (v_score * 0.4) + (f_score * 0.6)
            if score > 0:
                combined[chunk.id] = score

        ranked_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)[:top_k]
        id_to_chunk = {c.id: c for c in self._chunks}

        return [(id_to_chunk[cid], combined[cid]) for cid in ranked_ids]


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text)]
    common = Counter(words)
    return [w for w, _ in common.most_common(limit)]
