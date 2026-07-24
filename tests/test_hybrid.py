import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from backend.configs.settings import get_settings
from backend.embeddings.embedding_service import get_embedding_service
from backend.retrieval.vector_search import VectorSearchEngine
from backend.retrieval.bm25_search import BM25SearchEngine
from backend.retrieval.hybrid_retriever import HybridRetriever

s = get_settings()

ve = VectorSearchEngine(
    host=s.QDRANT_HOST,
    port=s.QDRANT_PORT,
    collection=s.QDRANT_COLLECTION,
    dim=s.EMBEDDING_DIM,
)
bm25 = BM25SearchEngine(index_path=s.BM25_INDEX_PATH)
bm25.load_index()

embedding_svc = get_embedding_service(s.EMBEDDING_MODEL)

# TEST 1: Check what Semantic Search returns
query = "ما عقوبه اي مسؤول بالشركه يقوم باعطاء معلومات غير صحيحه للجهه رسميه"

vector = embedding_svc.encode_single(query)
semantic_res = ve.search(vector, top_k=20)
print("--- SEMANTIC ---")
for r in semantic_res:
    print(f"ID: {r.get('id')}, Score: {r.get('score')}, Article: {r.get('payload', {}).get('article_number')}")

bm25_res = bm25.search(query, top_k=20)
print("\n--- BM25 ---")
for r in bm25_res:
    print(f"ID: {r.get('id')}, Score: {r.get('score')}, Article: {r.get('payload', {}).get('article_number')}")

hybrid = HybridRetriever(ve, bm25, embedding_svc, semantic_weight=0.4, bm25_weight=0.6)
merged = hybrid.search(query, top_k=10)
print("\n--- HYBRID (0.5 / 0.5) ---")
for r in merged:
    print(f"Hybrid Score: {r.get('hybrid_score')}, Article: {r.get('payload', {}).get('article_number')}")

