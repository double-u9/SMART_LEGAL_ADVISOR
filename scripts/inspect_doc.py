"""Inspect a sample document from the dataset."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\moham\Desktop\law books\legal-ai-dataset\legal_dataset.jsonl', 'r', encoding='utf-8') as f:
    docs = [json.loads(l) for l in f if l.strip()]

# Show fields from doc 150 (from a different book)
for idx in [0, 150, 500]:
    d = docs[idx]
    print(f"\n{'='*60}")
    print(f"Document {idx}:")
    print(f"  Keys: {list(d.keys())}")
    for k, v in d.items():
        val = str(v)
        if len(val) > 200:
            val = val[:200] + "..."
        print(f"  {k}: {val}")

# Count per book
from collections import Counter
books = Counter(d.get("book_name", d.get("source_file", "?")) for d in docs)
print(f"\n{'='*60}")
print("Documents per book:")
for book, count in books.most_common():
    print(f"  {book}: {count}")
