from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Arabic legal chunks into ChromaDB.")
    parser.add_argument("--records", type=Path, default=Path("vector_records.jsonl"))
    parser.add_argument("--persist-dir", type=Path, default=Path("chroma_store"))
    parser.add_argument("--collection", default="arabic_legal_books")
    parser.add_argument("--model", default="BAAI/bge-m3")
    args = parser.parse_args()

    import chromadb
    from sentence_transformers import SentenceTransformer

    records = load_records(args.records)
    model = SentenceTransformer(args.model)
    client = chromadb.PersistentClient(path=str(args.persist_dir))
    collection = client.get_or_create_collection(args.collection, metadata={"hnsw:space": "cosine"})
    documents = [record["document"] for record in records]
    embeddings = model.encode(documents, normalize_embeddings=True, batch_size=16).tolist()
    collection.upsert(
        ids=[record["id"] for record in records],
        documents=documents,
        metadatas=[record["metadata"] for record in records],
        embeddings=embeddings,
    )
    print(f"Loaded {len(records)} records into Chroma collection {args.collection}.")


if __name__ == "__main__":
    main()

