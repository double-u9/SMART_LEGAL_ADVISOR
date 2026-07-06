from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Arabic legal chunks into Pinecone.")
    parser.add_argument("--records", type=Path, default=Path("vector_records.jsonl"))
    parser.add_argument("--index", default="arabic-legal-books")
    parser.add_argument("--model", default="BAAI/bge-m3")
    parser.add_argument("--cloud", default="aws")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    from pinecone import Pinecone, ServerlessSpec
    from sentence_transformers import SentenceTransformer

    api_key = os.environ["PINECONE_API_KEY"]
    records = load_records(args.records)
    model = SentenceTransformer(args.model)
    vectors = model.encode([record["document"] for record in records], normalize_embeddings=True, batch_size=16).tolist()
    pc = Pinecone(api_key=api_key)
    existing = {item["name"] for item in pc.list_indexes()}
    if args.index not in existing:
        pc.create_index(
            name=args.index,
            dimension=len(vectors[0]),
            metric="cosine",
            spec=ServerlessSpec(cloud=args.cloud, region=args.region),
        )
    index = pc.Index(args.index)
    index.upsert(
        vectors=[
            {
                "id": record["id"],
                "values": vector,
                "metadata": {**record["metadata"], "document": record["document"]},
            }
            for record, vector in zip(records, vectors)
        ]
    )
    print(f"Loaded {len(records)} records into Pinecone index {args.index}.")


if __name__ == "__main__":
    main()

