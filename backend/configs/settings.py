"""Application configuration using Pydantic settings with .env support."""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for Smart Legal Advisor."""

    # --- Ollama (Local LLM) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 120

    # --- Qdrant Vector Database ---
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "legal_documents"

    # --- Embedding Model ---
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024

    # --- Reranker Model ---
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # --- Data Paths ---
    DATA_DIR: str = r"./data/legal-ai-dataset"
    VECTOR_STORE_PATH: str = "./vector_store"
    BM25_INDEX_PATH: str = "./vector_store/bm25_index.json"

    # --- Chunking ---
    CHUNK_MIN_TOKENS: int = 500
    CHUNK_MAX_TOKENS: int = 1200
    CHUNK_OVERLAP: int = 150
    CHUNK_HARD_MAX: int = 1500

    # --- Search ---
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANK: int = 5
    BM25_WEIGHT: float = 0.3
    SEMANTIC_WEIGHT: float = 0.7
    RRF_K: int = 60

    # --- Server ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    # --- Security ---
    MAX_QUERY_LENGTH: int = 2000
    MAX_UPLOAD_SIZE_MB: int = 50
    RATE_LIMIT_PER_MINUTE: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @property
    def data_path(self) -> Path:
        return Path(self.DATA_DIR)

    @property
    def dataset_jsonl_path(self) -> Path:
        return self.data_path / "legal_dataset.jsonl"

    @property
    def vector_store(self) -> Path:
        p = Path(self.VECTOR_STORE_PATH)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
