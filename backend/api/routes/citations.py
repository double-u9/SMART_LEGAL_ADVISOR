"""Citation lookup and book listing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from backend.api.dependencies import get_vector_engine

router = APIRouter(prefix="/api", tags=["citations"])


@router.get("/citations/{chunk_id}")
async def get_citation(chunk_id: str):
    """Get full citation details for a specific chunk."""
    ve = get_vector_engine()
    doc = ve.get_document_by_id(chunk_id)

    if not doc:
        raise HTTPException(status_code=404, detail="الاستشهاد غير موجود")

    payload = doc.get("payload", {})
    # Also get surrounding context
    context = ve.get_context_chunks(chunk_id)

    return {
        "citation": {
            "chunk_id": chunk_id,
            "book_name": payload.get("book_name", ""),
            "chapter": payload.get("chapter", ""),
            "article_number": payload.get("article_number", ""),
            "page_number": payload.get("page_number", ""),
            "text": payload.get("chunk_text", ""),
            "summary": payload.get("summary", ""),
        },
        "context_chunks": [
            {
                "chunk_id": c.get("payload", {}).get("id", ""),
                "text": c.get("payload", {}).get("chunk_text", "")[:300],
            }
            for c in context
        ],
    }


@router.get("/books")
async def list_books():
    """List all available law books in the collection."""
    ve = get_vector_engine()
    try:
        # Scroll through collection to find unique book names
        all_books = set()
        offset = None
        while True:
            results, offset = ve.client.scroll(
                collection_name=ve.collection,
                limit=100,
                offset=offset,
                with_payload=["book_name"],
            )
            for point in results:
                book = point.payload.get("book_name", "")
                if book:
                    all_books.add(book)
            if offset is None:
                break

        return {
            "books": sorted(list(all_books)),
            "total": len(all_books),
        }
    except Exception as e:
        return {"books": [], "total": 0, "error": str(e)}
