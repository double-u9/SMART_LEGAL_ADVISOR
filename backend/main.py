"""Smart Legal Advisor — FastAPI Application Entry Point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.configs.settings import get_settings
from backend.utils.logging_config import setup_logging, get_logger
from backend.api.middleware.security import RateLimitMiddleware

# Import route modules
from backend.api.routes import health, query, retrieval, citations, ingestion


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    s = get_settings()
    logger = setup_logging(s.LOG_LEVEL)
    log = get_logger("main")

    log.info("=" * 60)
    log.info("  Smart Legal Advisor — Starting Up")
    log.info("=" * 60)
    log.info("  Ollama: %s (model: %s)", s.OLLAMA_BASE_URL, s.OLLAMA_MODEL)
    log.info("  Qdrant: %s:%d (collection: %s)", s.QDRANT_HOST, s.QDRANT_PORT, s.QDRANT_COLLECTION)
    log.info("  Embedding: %s", s.EMBEDDING_MODEL)
    log.info("  Frontend: %s", s.FRONTEND_URL)
    log.info("=" * 60)

    yield

    log.info("Smart Legal Advisor — Shutting Down")


# Create FastAPI application
app = FastAPI(
    title="Smart Legal Advisor API",
    description="مستشار قانوني ذكي — Enterprise AI Legal Assistant for Arabic Law",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Middleware ---
s = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[s.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, max_requests=s.RATE_LIMIT_PER_MINUTE)

# --- Routes ---
app.include_router(health.router)
app.include_router(query.router)
app.include_router(retrieval.router)
app.include_router(citations.router)
app.include_router(ingestion.router)


@app.get("/")
async def root():
    return {
        "name": "Smart Legal Advisor",
        "name_ar": "المستشار القانوني الذكي",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=s.BACKEND_HOST,
        port=s.BACKEND_PORT,
        reload=True,
        log_level="info",
    )
