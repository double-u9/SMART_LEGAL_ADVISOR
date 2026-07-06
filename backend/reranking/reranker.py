"""Lightweight reranker — FlagEmbedding disabled by default for speed."""

from __future__ import annotations

from backend.utils.logging_config import get_logger

logger = get_logger("reranker")


class Reranker:
    """Reranker that passes through results by their original score.

    FlagEmbedding cross-encoder is disabled by default for faster startup.
    The hybrid retrieval + RRF already provides good ranking.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", enabled: bool = False):
        self.model_name = model_name
        self.enabled = enabled
        self._model = None

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """Return top-k documents, optionally reranked by cross-encoder."""
        if not documents:
            return []

        if not self.enabled or self._model is None:
            # Passthrough: use existing scores (hybrid RRF scores are good enough)
            results = documents[:top_k]
            for doc in results:
                score = doc.get("hybrid_score", doc.get("score", 0.5))
                doc["rerank_score"] = float(score)
            return results

        # Cross-encoder reranking (only if explicitly enabled)
        return self._rerank_with_model(query, documents, top_k)

    def _rerank_with_model(self, query: str, documents: list[dict], top_k: int) -> list[dict]:
        """Optional cross-encoder reranking."""
        try:
            pairs = []
            for doc in documents:
                payload = doc.get("payload", {})
                text = payload.get("chunk_text", "") or payload.get("embedding_ready_text", "")
                pairs.append([query, text])

            scores = self._model.compute_score(pairs, normalize=True)
            if isinstance(scores, (int, float)):
                scores = [scores]

            scored = []
            for doc, score in zip(documents, scores):
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = float(score)
                scored.append(doc_copy)

            scored.sort(key=lambda x: x["rerank_score"], reverse=True)
            return scored[:top_k]

        except Exception as e:
            logger.error("Reranking failed: %s", e)
            return documents[:top_k]

    def is_loaded(self) -> bool:
        return self._model is not None


def get_reranker(model_name: str = "BAAI/bge-reranker-v2-m3") -> Reranker:
    """Return a reranker (disabled by default for speed)."""
    return Reranker(model_name=model_name, enabled=False)
