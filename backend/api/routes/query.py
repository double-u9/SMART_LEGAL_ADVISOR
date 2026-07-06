"""Main query endpoint — legal Q&A with streaming support."""

from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from backend.api.dependencies import get_rag_engine, get_vector_engine
from backend.utils.validators import validate_query, sanitize_input
from backend.utils.logging_config import get_logger

logger = get_logger("query_api")

router = APIRouter(prefix="/api", tags=["query"])

NO_DATA_MSG = (
    "⚠️ لم يتم استيعاب البيانات بعد!\n\n"
    "يجب أولاً تحميل الكتب القانونية في قاعدة البيانات. "
    "يرجى تشغيل أمر الاستيعاب أولاً:\n\n"
    "```\n"
    "POST http://localhost:8000/api/ingest/dataset\n"
    "```\n\n"
    "أو تشغيل السكريبت:\n"
    "```\n"
    "python scripts/ingest_data.py\n"
    "```"
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    filters: Optional[dict] = None
    stream: bool = True


class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    query: str
    confidence: float


def _check_data_ready() -> bool:
    """Quick check if any data has been ingested (no heavy model loading)."""
    try:
        ve = get_vector_engine()
        info = ve.collection_info()
        count = info.get("points_count", 0)
        return count is not None and count > 0
    except Exception:
        return False


@router.post("/query")
async def query_legal(request: QueryRequest):
    """Main legal Q&A endpoint.

    Supports both streaming (SSE) and non-streaming responses.
    """
    # Validate & sanitize
    question = sanitize_input(request.question)
    is_valid, error_msg = validate_query(question)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # ── Quick data check (no model loading) ──
    if not _check_data_ready():
        logger.warning("Query received but no data is ingested yet")
        if request.stream:
            async def no_data_stream():
                yield f"data: {json.dumps({'type': 'token', 'content': NO_DATA_MSG}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

            return StreamingResponse(
                no_data_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        else:
            return {
                "answer": NO_DATA_MSG,
                "citations": [],
                "query": question,
                "confidence": 0.0,
            }

    # ── Full RAG pipeline ──
    rag = get_rag_engine()

    if request.stream:
        async def event_generator():
            async for event in rag.query_stream(
                question=question,
                filters=request.filters,
            ):
                yield f"data: {event}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        result = await rag.query(
            question=question,
            filters=request.filters,
        )
        return result
