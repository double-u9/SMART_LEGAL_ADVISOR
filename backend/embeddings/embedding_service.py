"""BAAI/bge-m3 embedding service — local, no API keys required."""

from __future__ import annotations

import numpy as np
from typing import Optional
from backend.utils.logging_config import get_logger

logger = get_logger("embeddings")

_instance: Optional["EmbeddingService"] = None


class EmbeddingService:
    """Singleton wrapper around sentence-transformers for BAAI/bge-m3."""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        self._model = None
        self._dim: int = 1024
        logger.info("EmbeddingService created — model=%s", model_name)

    def _load_model(self):
        if self._model is not None:
            return
        logger.info("Loading embedding model %s (this may take a minute)…", self.model_name)
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = SentenceTransformer(self.model_name, device=device)
            self._dim = self._model.get_sentence_embedding_dimension() or 1024
            logger.info(
                "Embedding model loaded — dim=%d, device=%s", self._dim, device
            )
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            raise

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: list[str], batch_size: int = 32, show_progress: bool = False) -> list[list[float]]:
        """Encode a batch of texts to dense vectors."""
        self._load_model()
        if not texts:
            return []

        logger.info("Encoding %d texts (batch_size=%d)…", len(texts), batch_size)
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
        )
        return embeddings.tolist() if isinstance(embeddings, np.ndarray) else [e.tolist() for e in embeddings]

    def encode_single(self, text: str) -> list[float]:
        """Encode a single text."""
        result = self.encode([text])
        return result[0]

    def is_loaded(self) -> bool:
        return self._model is not None

    def health_check(self) -> dict:
        try:
            self._load_model()
            test = self.encode_single("test")
            return {"status": "ok", "model": self.model_name, "dim": len(test)}
        except Exception as e:
            return {"status": "error", "error": str(e)}


def get_embedding_service(model_name: str = "BAAI/bge-m3") -> EmbeddingService:
    """Return singleton EmbeddingService."""
    global _instance
    if _instance is None:
        _instance = EmbeddingService(model_name)
    return _instance
