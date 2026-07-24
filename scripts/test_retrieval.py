"""Test script for the new vector database."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.configs.settings import get_settings
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.embeddings.embedding_service import get_embedding_service
from backend.retrieval.vector_search import VectorSearchEngine
from backend.retrieval.bm25_search import BM25SearchEngine

# Force utf-8 encoding for standard output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    s = get_settings()
    
    # Initialize the retriever directly to avoid full backend load
    embedding_svc = get_embedding_service(s.EMBEDDING_MODEL)
    ve = VectorSearchEngine(
        host=s.QDRANT_HOST,
        port=s.QDRANT_PORT,
        collection=s.QDRANT_COLLECTION,
        dim=s.EMBEDDING_DIM,
    )
    bm25 = BM25SearchEngine(index_path=s.BM25_INDEX_PATH)
    bm25.load_index()
    
    # The hybrid retriever expects these 3 services
    retriever = HybridRetriever(
        vector_engine=ve,
        bm25_engine=bm25,
        embedding_service=embedding_svc,
        semantic_weight=s.SEMANTIC_WEIGHT,
        bm25_weight=s.BM25_WEIGHT,
        rrf_k=s.RRF_K
    )
    
    query = "ما هي الشركة المساهمة وكيف يتم تأسيسها؟"
    print(f"Querying: {query}")
    
    results = retriever.search(query=query, top_k=3)
    
    print(f"Found {len(results)} results.\n")
    for i, res in enumerate(results):
        print(f"--- Result {i+1} ---")
        print(f"Score: {res.get('score', 0)}")
        print(f"Book: {res.get('book_name', '')}")
        print(f"Text snippet: {res.get('chunk_text', '')[:200]}...")
        print()

if __name__ == "__main__":
    asyncio.run(main())
