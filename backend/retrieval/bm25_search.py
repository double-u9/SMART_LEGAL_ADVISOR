"""BM25 keyword search engine for Arabic legal text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from rank_bm25 import BM25Okapi
from backend.utils.arabic_utils import tokenize_arabic, normalize_for_search
from backend.utils.logging_config import get_logger

logger = get_logger("bm25_search")


class BM25SearchEngine:
    """BM25 keyword search over legal document chunks."""

    def __init__(self, index_path: Optional[str] = None):
        self._bm25: Optional[BM25Okapi] = None
        self._documents: list[dict] = []
        self._tokenized_corpus: list[list[str]] = []
        self._index_path = Path(index_path) if index_path else None

    @property
    def is_ready(self) -> bool:
        return self._bm25 is not None and len(self._documents) > 0

    def build_index(self, documents: list[dict]) -> None:
        """Build BM25 index from documents.

        Each document: {chunk_id, chunk_text, embedding_ready_text, ...metadata}
        """
        self._documents = documents
        self._tokenized_corpus = []

        for doc in documents:
            text = doc.get("embedding_ready_text", "") or doc.get("chunk_text", "")
            tokens = tokenize_arabic(text)
            self._tokenized_corpus.append(tokens)

        self._bm25 = BM25Okapi(self._tokenized_corpus)
        logger.info("BM25 index built — %d documents", len(documents))

    def search(self, query: str, top_k: int = 20,
               filters: Optional[dict] = None) -> list[dict]:
        """Search the BM25 index with an Arabic query."""
        if not self.is_ready:
            logger.warning("BM25 index not ready")
            return []

        query_tokens = tokenize_arabic(normalize_for_search(query))
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Pair scores with document indices
        scored_docs = list(enumerate(scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_docs[:top_k * 2]:  # Over-fetch for filtering
            if score <= 0:
                continue
            doc = self._documents[idx]

            # Apply metadata filters
            if filters:
                skip = False
                for key, value in filters.items():
                    if value and doc.get(key) and doc[key] != value:
                        skip = True
                        break
                if skip:
                    continue

            results.append({
                "id": doc.get("chunk_id", doc.get("id", str(idx))),
                "score": float(score),
                "payload": doc,
            })

            if len(results) >= top_k:
                break

        return results

    def save_index(self, path: Optional[str] = None) -> None:
        """Save the document corpus for later reloading."""
        save_path = Path(path) if path else self._index_path
        if not save_path:
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self._documents, f, ensure_ascii=False, indent=None)
        logger.info("BM25 corpus saved to %s", save_path)

    def load_index(self, path: Optional[str] = None) -> bool:
        """Load corpus and rebuild BM25 index."""
        load_path = Path(path) if path else self._index_path
        if not load_path or not load_path.exists():
            return False

        with open(load_path, "r", encoding="utf-8") as f:
            documents = json.load(f)

        self.build_index(documents)
        logger.info("BM25 index loaded from %s — %d documents", load_path, len(documents))
        return True

    def add_documents(self, documents: list[dict]) -> None:
        """Add new documents and rebuild the index."""
        self._documents.extend(documents)
        self.build_index(self._documents)
