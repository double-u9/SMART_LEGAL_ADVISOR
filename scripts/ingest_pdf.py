"""Standalone script to ingest directly from PDFs."""

import asyncio
import sys
import os
from pathlib import Path

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
    print("  Smart Legal Advisor — PDF Ingestion")
    print("=" * 60)
    
    pdf_dir = Path(s.DATA_DIR).parent / "new_dataset"
    
    print(f"\n[1/4] Processing PDFs from {pdf_dir}...")
    pipeline = IngestionPipeline()
    documents = pipeline.ingest_from_pdfs(pdf_dir)
    
    print(f"  ✓ Processed {len(documents)} chunks from PDFs")

    if not documents:
        print("  ✗ No documents found!")
        return

    # 2. Generate embeddings
    print(f"\n[2/4] Generating embeddings with {s.EMBEDDING_MODEL}...")
    embedding_svc = get_embedding_service(s.EMBEDDING_MODEL)
    texts = [
        doc.get("embedding_ready_text", "") or doc.get("chunk_text", "")
        for doc in documents
    ]
    vectors = embedding_svc.encode(texts, batch_size=32, show_progress=True)
    print(f"  ✓ Generated {len(vectors)} vectors (dim={len(vectors[0])})")

    # 3. Upsert into Qdrant
    print(f"\n[3/4] Upserting into Qdrant ({s.QDRANT_COLLECTION})...")
    ve = VectorSearchEngine(
        host=s.QDRANT_HOST,
        port=s.QDRANT_PORT,
        collection=s.QDRANT_COLLECTION,
        dim=s.EMBEDDING_DIM,
    )
    # Recreate collection to ensure clean state
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
