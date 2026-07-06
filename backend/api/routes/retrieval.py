"""Raw retrieval endpoint — returns ranked chunks without LLM generation."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from backend.api.dependencies import get_rag_engine
from backend.utils.validators import sanitize_input

router = APIRouter(prefix="/api", tags=["retrieval"])


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=50)
    filters: Optional[dict] = None


@router.post("/retrieve")
async def retrieve_documents(request: RetrievalRequest):
    """Retrieve relevant legal chunks without LLM generation."""
    query = sanitize_input(request.query)
    rag = get_rag_engine()

    # Use just the retrieval + reranking parts
    retrieved = rag.retriever.search(
        query=query,
        top_k=request.top_k * 2,
        filters=request.filters,
    )

    reranked = rag.reranker.rerank(
        query=query,
        documents=retrieved,
        top_k=request.top_k,
    )

    # Format results
    results = []
    for doc in reranked:
        payload = doc.get("payload", {})
        results.append({
            "chunk_id": payload.get("id", payload.get("chunk_id", "")),
            "book_name": payload.get("book_name", ""),
            "article_number": payload.get("article_number", ""),
            "chapter": payload.get("chapter", ""),
            "page_number": payload.get("page_number", ""),
            "text": payload.get("chunk_text", "")[:500],
            "score": doc.get("rerank_score", doc.get("hybrid_score", 0)),
        })

    return {"query": query, "results": results, "total": len(results)}
