"""Document ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.api.dependencies import (
    get_ingestion_pipeline,
    get_vector_engine,
    get_bm25_engine,
)
from backend.embeddings.embedding_service import get_embedding_service
from backend.configs.settings import get_settings
from backend.utils.logging_config import get_logger

logger = get_logger("ingestion_api")

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


class IngestDatasetRequest(BaseModel):
    dataset_path: Optional[str] = None  # Defaults to settings.DATA_DIR


@router.post("/dataset")
async def ingest_dataset(request: IngestDatasetRequest, background_tasks: BackgroundTasks):
    """Ingest the preprocessed JSONL dataset into Qdrant."""
    s = get_settings()
    dataset_path = request.dataset_path or str(s.dataset_jsonl_path)

    background_tasks.add_task(_run_ingestion, dataset_path)

    return {
        "status": "started",
        "message": "بدأت عملية استيعاب البيانات في الخلفية",
        "dataset_path": dataset_path,
    }


@router.get("/status")
async def ingestion_status():
    """Check ingestion progress."""
    pipeline = get_ingestion_pipeline()
    status = pipeline.status

    # Also check vector store count
    try:
        ve = get_vector_engine()
        info = ve.collection_info()
        status["vector_count"] = info.get("points_count", 0)
    except Exception:
        status["vector_count"] = 0

    return status


async def _run_ingestion(dataset_path: str):
    """Background task: ingest dataset and index into Qdrant + BM25."""
    s = get_settings()
    pipeline = get_ingestion_pipeline()

    try:
        # 1. Load documents
        logger.info("Starting ingestion from %s", dataset_path)
        documents = pipeline.ingest_from_jsonl(dataset_path)

        if not documents:
            logger.warning("No documents loaded")
            return

        # 2. Generate embeddings
        logger.info("Generating embeddings for %d documents...", len(documents))
        embedding_svc = get_embedding_service(s.EMBEDDING_MODEL)

        texts = [
            doc.get("embedding_ready_text", "") or doc.get("chunk_text", "")
            for doc in documents
        ]
        vectors = embedding_svc.encode(texts, batch_size=32, show_progress=True)

        # 3. Upsert into Qdrant
        logger.info("Upserting into Qdrant...")
        ve = get_vector_engine()
        ve.create_collection()

        points = []
        for doc, vector in zip(documents, vectors):
            points.append({
                "vector": vector,
                "payload": {
                    "chunk_id": doc.get("id", doc.get("chunk_id", "")),
                    "chunk_text": doc.get("chunk_text", ""),
                    "embedding_ready_text": doc.get("embedding_ready_text", ""),
                    "book_name": doc.get("book_name", ""),
                    "chapter": doc.get("chapter", ""),
                    "section": doc.get("section", ""),
                    "article_number": str(doc.get("article_number", "")),
                    "page_number": str(doc.get("page_number", doc.get("page_start", ""))),
                    "summary": doc.get("summary", ""),
                    "keywords": doc.get("keywords", []),
                    "legal_topics": doc.get("legal_topics", []),
                    "source_file": doc.get("source_file", ""),
                    "token_count": doc.get("token_count", 0),
                    "previous_chunk_id": doc.get("previous_chunk_id"),
                    "next_chunk_id": doc.get("next_chunk_id"),
                },
            })

        ve.upsert_documents(points)

        # 4. Build BM25 index
        logger.info("Building BM25 index...")
        bm25 = get_bm25_engine()
        bm25.build_index(documents)
        bm25.save_index(s.BM25_INDEX_PATH)

        logger.info("Ingestion complete: %d documents indexed", len(documents))

    except Exception as e:
        logger.error("Ingestion failed: %s", e, exc_info=True)
