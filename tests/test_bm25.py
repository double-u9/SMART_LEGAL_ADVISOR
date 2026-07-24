import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from backend.retrieval.bm25_search import BM25SearchEngine
import json

bm25 = BM25SearchEngine(index_path="vector_store/bm25_index.json")
bm25.load_index()

query = "ما عقوبه اي مسؤول بالشركه يقوم باعطاء معلومات غير صحيحه للجهه رسميه"
results = bm25.search(query, top_k=10)

print("--- BM25 Search Results ---")
for result in results:
    score = result['score']
    doc = result['payload']
    print(f"Score: {score:.3f} | Article: {doc.get('article_number')} | Text: {doc.get('chunk_text')[:100]}")

print("\n--- Let's look for article 218 ---")
for doc in bm25.documents:
    if str(doc.get('article_number')) == '218' or '218' in doc.get('chunk_text', ''):
        print("FOUND 218:")
        print(doc.get('chunk_text'))
