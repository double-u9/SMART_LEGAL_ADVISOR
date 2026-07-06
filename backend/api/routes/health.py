"""Health check endpoint."""

from fastapi import APIRouter
from backend.api.dependencies import get_vector_engine, get_bm25_engine
from backend.embeddings.embedding_service import get_embedding_service
from backend.rag.response_generator import ResponseGenerator
from backend.configs.settings import get_settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """System health check — verifies all services."""
    s = get_settings()
    checks = {}

    # Qdrant check
    try:
        ve = get_vector_engine()
        checks["qdrant"] = ve.health_check()
    except Exception as e:
        checks["qdrant"] = {"status": "error", "error": str(e)}

    # Ollama check
    try:
        gen = ResponseGenerator(base_url=s.OLLAMA_BASE_URL, model=s.OLLAMA_MODEL)
        checks["ollama"] = await gen.health_check()
    except Exception as e:
        checks["ollama"] = {"status": "error", "error": str(e)}

    # Embedding model check
    try:
        emb = get_embedding_service(s.EMBEDDING_MODEL)
        checks["embedding_model"] = {
            "status": "ok" if emb.is_loaded() else "not_loaded",
            "model": s.EMBEDDING_MODEL,
        }
    except Exception as e:
        checks["embedding_model"] = {"status": "error", "error": str(e)}

    # BM25 check
    try:
        bm25 = get_bm25_engine()
        checks["bm25"] = {"status": "ok" if bm25.is_ready else "not_indexed"}
    except Exception as e:
        checks["bm25"] = {"status": "error", "error": str(e)}

    # Overall status
    all_ok = all(
        c.get("status") == "ok"
        for c in checks.values()
        if isinstance(c, dict)
    )

    return {
        "status": "healthy" if all_ok else "degraded",
        "services": checks,
        "config": {
            "ollama_model": s.OLLAMA_MODEL,
            "embedding_model": s.EMBEDDING_MODEL,
            "qdrant_collection": s.QDRANT_COLLECTION,
        },
    }
