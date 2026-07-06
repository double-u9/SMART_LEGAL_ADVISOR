"""Standalone ingestion script — run once to index the legal dataset."""

import asyncio
import sys
import os
import pickle

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.configs.settings import get_settings
from backend.ingestion.pipeline import IngestionPipeline
from backend.embeddings.embedding_service import get_embedding_service
from backend.retrieval.vector_search import VectorSearchEngine
from backend.retrieval.bm25_search import BM25SearchEngine
from backend.utils.logging_config import setup_logging


async def main():
    setup_logging("INFO")
    s = get_settings()

    print("=" * 60)
    print("  Smart Legal Advisor — Data Ingestion")
    print("  المستشار القانوني الذكي — استيعاب البيانات")
    print("=" * 60)
    print(f"  Dataset: {s.DATA_DIR}")
    print(f"  Embedding model: {s.EMBEDDING_MODEL}")
    print(f"  Qdrant: {s.QDRANT_HOST}:{s.QDRANT_PORT}")
    print("=" * 60)

    # 1. Load dataset
    print("\n[1/4] Loading dataset from JSONL...")
    pipeline = IngestionPipeline()
    documents = pipeline.ingest_from_jsonl(s.dataset_jsonl_path)
    
    # Check for optional limit argument
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            documents = documents[:limit]
            print(f"  [DEBUG] Truncated dataset to first {limit} documents for fast testing")
        except ValueError:
            pass

    print(f"  ✓ Loaded {len(documents)} documents")

    if not documents:
        print("  ✗ No documents found!")
        return

    # 2. Generate embeddings
    cache_file = "vectors_cache.pkl"
    vectors = None
    
    if os.path.exists(cache_file):
        print(f"\n[2/4] Loading cached embeddings from {cache_file}...")
        with open(cache_file, "rb") as f:
            vectors = pickle.load(f)
            
        if len(vectors) != len(documents):
            print("  ⚠️ Cache size mismatch, regenerating...")
            vectors = None

    if vectors is None:
        print(f"\n[2/4] Generating embeddings with {s.EMBEDDING_MODEL}...")
        embedding_svc = get_embedding_service(s.EMBEDDING_MODEL)
        texts = [
            doc.get("embedding_ready_text", "") or doc.get("chunk_text", "")
            for doc in documents
        ]
        vectors = embedding_svc.encode(texts, batch_size=32, show_progress=True)
        
        # Save cache
        with open(cache_file, "wb") as f:
            pickle.dump(vectors, f)
            
        print(f"  ✓ Generated and cached {len(vectors)} vectors (dim={len(vectors[0])})")

    # 3. Upsert into Qdrant
    print(f"\n[3/4] Upserting into Qdrant ({s.QDRANT_COLLECTION})...")
    ve = VectorSearchEngine(
        host=s.QDRANT_HOST,
        port=s.QDRANT_PORT,
        collection=s.QDRANT_COLLECTION,
        dim=s.EMBEDDING_DIM,
    )
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
                "source_file": doc.get("source_file", ""),
            },
        })

    count = ve.upsert_documents(points)
    print(f"  ✓ Upserted {count} documents into Qdrant")

    # 4. Build BM25 index
    print(f"\n[4/4] Building BM25 index...")
    bm25 = BM25SearchEngine(index_path=s.BM25_INDEX_PATH)
    bm25.build_index(documents)
    bm25.save_index()
    print(f"  ✓ BM25 index built and saved to {s.BM25_INDEX_PATH}")

    print("\n" + "=" * 60)
    print("  ✅ Ingestion Complete!")
    print(f"  Documents indexed: {count}")
    info = ve.collection_info()
    print(f"  Qdrant collection: {info}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
