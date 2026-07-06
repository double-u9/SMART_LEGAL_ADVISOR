from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Arabic legal chunks into Qdrant.")
    parser.add_argument("--records", type=Path, default=Path("vector_records.jsonl"))
    parser.add_argument("--url", default="http://localhost:6333")
    parser.add_argument("--collection", default="arabic_legal_books")
    parser.add_argument("--model", default="BAAI/bge-m3")
    args = parser.parse_args()

    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from sentence_transformers import SentenceTransformer

    records = load_records(args.records)
    model = SentenceTransformer(args.model)
    embeddings = model.encode([record["document"] for record in records], normalize_embeddings=True, batch_size=16).tolist()
    client = QdrantClient(url=args.url)
    client.recreate_collection(
        collection_name=args.collection,
        vectors_config=models.VectorParams(size=len(embeddings[0]), distance=models.Distance.COSINE),
    )
    client.upsert(
        collection_name=args.collection,
        points=[
            models.PointStruct(id=record["id"], vector=vector, payload={**record["metadata"], "document": record["document"]})
            for record, vector in zip(records, embeddings)
        ],
    )
    print(f"Loaded {len(records)} records into Qdrant collection {args.collection}.")


if __name__ == "__main__":
    main()

