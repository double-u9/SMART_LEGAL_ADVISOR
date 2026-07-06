"""Qdrant vector search engine — compatible with qdrant-client 1.18+."""

from __future__ import annotations

import os
from typing import Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from backend.utils.logging_config import get_logger

logger = get_logger("vector_search")


class VectorSearchEngine:
    """Manages Qdrant collection and semantic search operations."""

    def __init__(self, host: str = "localhost", port: int = 6333,
                 collection: str = "legal_documents", dim: int = 1024,
                 local_path: str = "./vector_store/qdrant_data"):
        self.host = host
        self.port = port
        self.collection = collection
        self.dim = dim
        self.local_path = local_path
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            # Try remote Qdrant first, fall back to local file-based mode
            try:
                test_client = QdrantClient(host=self.host, port=self.port, timeout=3)
                test_client.get_collections()
                self._client = test_client
                logger.info("Connected to Qdrant server at %s:%d", self.host, self.port)
            except Exception:
                logger.info("Qdrant server not available — using local file-based mode")
                os.makedirs(self.local_path, exist_ok=True)
                self._client = QdrantClient(path=self.local_path)
                logger.info("Qdrant local mode initialized at %s", self.local_path)
        return self._client

    def create_collection(self) -> None:
        """Create the vector collection if it doesn't exist."""
        if self.client.collection_exists(self.collection):
            logger.info("Collection '%s' already exists", self.collection)
            return

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
        )
        logger.info("Created collection '%s' with dim=%d", self.collection, self.dim)

    def upsert_documents(self, points: list[dict]) -> int:
        """Upsert documents with vectors into Qdrant.

        Each point: {id: str, vector: list[float], payload: dict}
        """
        batch_size = 100
        total = 0
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            qdrant_points = []
            for idx, p in enumerate(batch):
                qdrant_points.append(
                    PointStruct(
                        id=i + idx,
                        vector=p["vector"],
                        payload=p["payload"],
                    )
                )
            self.client.upsert(collection_name=self.collection, points=qdrant_points)
            total += len(batch)
            if total % 200 == 0:
                logger.info("Upserted %d / %d points", total, len(points))

        logger.info("Upsert complete: %d points", total)
        return total

    def search(self, query_vector: list[float], top_k: int = 20,
               filters: Optional[dict] = None) -> list[dict]:
        """Semantic search using query_points (qdrant-client 1.18+ API)."""
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if value:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            if conditions:
                query_filter = Filter(must=conditions)

        try:
            response = self.client.query_points(
                collection_name=self.collection,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload or {},
                }
                for hit in response.points
            ]
        except Exception as e:
            logger.error("Search failed: %s", e)
            return []

    def get_document_by_id(self, chunk_id: str) -> Optional[dict]:
        """Retrieve a specific document by its chunk_id in the payload."""
        try:
            results = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id))]
                ),
                limit=1,
                with_payload=True,
            )
            points = results[0]
            if points:
                return {"id": str(points[0].id), "payload": points[0].payload}
        except Exception as e:
            logger.error("get_document_by_id failed: %s", e)
        return None

    def get_context_chunks(self, chunk_id: str) -> list[dict]:
        """Expand context using previous/next chunk links."""
        doc = self.get_document_by_id(chunk_id)
        if not doc:
            return []

        context = [doc]
        payload = doc.get("payload", {})

        prev_id = payload.get("previous_chunk_id")
        if prev_id:
            prev_doc = self.get_document_by_id(prev_id)
            if prev_doc:
                context.insert(0, prev_doc)

        next_id = payload.get("next_chunk_id")
        if next_id:
            next_doc = self.get_document_by_id(next_id)
            if next_doc:
                context.append(next_doc)

        return context

    def collection_info(self) -> dict:
        """Return collection stats."""
        try:
            if not self.client.collection_exists(self.collection):
                return {"name": self.collection, "points_count": 0, "status": "not_created"}
            info = self.client.get_collection(self.collection)
            return {
                "name": self.collection,
                "points_count": info.points_count,
                "vectors_count": getattr(info, "vectors_count", getattr(info, "indexed_vectors_count", 0)),
                "status": info.status.value if info.status else "unknown",
            }
        except Exception as e:
            return {"error": str(e), "points_count": 0}

    def health_check(self) -> dict:
        try:
            self.client.get_collections()
            return {"status": "ok", "host": self.host, "port": self.port}
        except Exception as e:
            return {"status": "error", "error": str(e)}
