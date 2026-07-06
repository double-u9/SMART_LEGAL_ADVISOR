"""FastAPI dependency injection — singleton service initialization."""

from __future__ import annotations

from functools import lru_cache
from backend.configs.settings import get_settings
from backend.embeddings.embedding_service import get_embedding_service
from backend.retrieval.vector_search import VectorSearchEngine
from backend.retrieval.bm25_search import BM25SearchEngine
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.reranking.reranker import get_reranker
from backend.citations.citation_engine import CitationEngine
from backend.rag.response_generator import ResponseGenerator
from backend.rag.engine import RAGEngine
from backend.ingestion.pipeline import IngestionPipeline
from backend.utils.logging_config import get_logger

logger = get_logger("dependencies")

# Singletons
_rag_engine: RAGEngine | None = None
_ingestion_pipeline: IngestionPipeline | None = None
_vector_engine: VectorSearchEngine | None = None
_bm25_engine: BM25SearchEngine | None = None


def get_vector_engine() -> VectorSearchEngine:
    global _vector_engine
    if _vector_engine is None:
        s = get_settings()
        _vector_engine = VectorSearchEngine(
            host=s.QDRANT_HOST,
            port=s.QDRANT_PORT,
            collection=s.QDRANT_COLLECTION,
            dim=s.EMBEDDING_DIM,
        )
    return _vector_engine


def get_bm25_engine() -> BM25SearchEngine:
    global _bm25_engine
    if _bm25_engine is None:
        s = get_settings()
        _bm25_engine = BM25SearchEngine(index_path=s.BM25_INDEX_PATH)
        # Try to load existing index
        if not _bm25_engine.load_index():
            logger.info("No existing BM25 index found — will be built on ingestion")
    return _bm25_engine


def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        s = get_settings()
        embedding_svc = get_embedding_service(s.EMBEDDING_MODEL)
        vector_engine = get_vector_engine()
        bm25_engine = get_bm25_engine()

        retriever = HybridRetriever(
            vector_engine=vector_engine,
            bm25_engine=bm25_engine,
            embedding_service=embedding_svc,
            semantic_weight=s.SEMANTIC_WEIGHT,
            bm25_weight=s.BM25_WEIGHT,
            rrf_k=s.RRF_K,
        )
        reranker = get_reranker(s.RERANKER_MODEL)
        citation_engine = CitationEngine()
        generator = ResponseGenerator(
            base_url=s.OLLAMA_BASE_URL,
            model=s.OLLAMA_MODEL,
            timeout=s.OLLAMA_TIMEOUT,
        )

        _rag_engine = RAGEngine(
            retriever=retriever,
            reranker=reranker,
            citation_engine=citation_engine,
            response_generator=generator,
            top_k_retrieval=s.TOP_K_RETRIEVAL,
            top_k_rerank=s.TOP_K_RERANK,
        )
        logger.info("RAG engine initialized")
    return _rag_engine


def get_ingestion_pipeline() -> IngestionPipeline:
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = IngestionPipeline()
    return _ingestion_pipeline
