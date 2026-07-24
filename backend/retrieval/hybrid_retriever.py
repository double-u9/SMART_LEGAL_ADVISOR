"""Hybrid retrieval: semantic + BM25 + Reciprocal Rank Fusion."""

from __future__ import annotations

from typing import Optional
from backend.retrieval.vector_search import VectorSearchEngine
from backend.retrieval.bm25_search import BM25SearchEngine
from backend.embeddings.embedding_service import EmbeddingService
from backend.utils.arabic_utils import normalize_for_search
from backend.utils.logging_config import get_logger

logger = get_logger("hybrid_retriever")


class HybridRetriever:
    """Combines semantic and BM25 search with Reciprocal Rank Fusion."""

    def __init__(
        self,
        vector_engine: VectorSearchEngine,
        bm25_engine: BM25SearchEngine,
        embedding_service: EmbeddingService,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        rrf_k: int = 60,
    ):
        self.vector_engine = vector_engine
        self.bm25_engine = bm25_engine
        self.embedding_service = embedding_service
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Execute hybrid search with RRF merging.

        1. Embed query → semantic search
        2. Tokenize query → BM25 search
        3. Merge via Reciprocal Rank Fusion
        """
        normalized_query = normalize_for_search(query)

        # --- Semantic search ---
        query_vector = self.embedding_service.encode_single(normalized_query)
        semantic_results = self.vector_engine.search(
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )
        logger.debug("Semantic search returned %d results", len(semantic_results))

        # --- BM25 search ---
        bm25_results = self.bm25_engine.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )
        logger.debug("BM25 search returned %d results", len(bm25_results))

        # --- Reciprocal Rank Fusion ---
        merged = self._reciprocal_rank_fusion(
            semantic_results, bm25_results, top_k
        )
        logger.info(
            "Hybrid search: query=%s → %d results (sem=%d, bm25=%d)",
            query[:50], len(merged), len(semantic_results), len(bm25_results),
        )
        return merged

    def _reciprocal_rank_fusion(
        self,
        semantic: list[dict],
        bm25: list[dict],
        top_k: int,
    ) -> list[dict]:
        """Merge two ranked lists using RRF: score = Σ weight / (k + rank)."""
        doc_scores: dict[str, float] = {}
        doc_data: dict[str, dict] = {}

        # Score semantic results
        for rank, result in enumerate(semantic):
            doc_id = self._get_doc_id(result)
            rrf_score = self.semantic_weight / (self.rrf_k + rank + 1)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        # Score BM25 results
        for rank, result in enumerate(bm25):
            doc_id = self._get_doc_id(result)
            rrf_score = self.bm25_weight / (self.rrf_k + rank + 1)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        # Sort by combined score
        sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

        # Normalize scores to 0-1 range for frontend display
        # The theoretical maximum score is achieved if a document is rank 1 in both lists (rank=0)
        max_possible_score = (self.semantic_weight + self.bm25_weight) / (self.rrf_k + 1)

        results = []
        for doc_id in sorted_ids[:top_k]:
            entry = doc_data[doc_id].copy()
            normalized_score = min(1.0, doc_scores[doc_id] / max_possible_score)
            entry["hybrid_score"] = round(normalized_score, 4)
            results.append(entry)

        return results

    @staticmethod
    def _get_doc_id(result: dict) -> str:
        """Extract a stable document ID from a search result."""
        payload = result.get("payload", {})
        return payload.get("chunk_id", payload.get("id", result.get("id", "")))
