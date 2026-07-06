from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Arabic legal chunks into Weaviate.")
    parser.add_argument("--records", type=Path, default=Path("vector_records.jsonl"))
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--collection", default="ArabicLegalChunk")
    parser.add_argument("--model", default="BAAI/bge-m3")
    args = parser.parse_args()

    import weaviate
    from sentence_transformers import SentenceTransformer
    from weaviate.classes.config import DataType, Property

    records = load_records(args.records)
    model = SentenceTransformer(args.model)
    vectors = model.encode([record["document"] for record in records], normalize_embeddings=True, batch_size=16).tolist()
    client = weaviate.connect_to_local(host=args.url.replace("http://", "").replace("https://", "").split(":")[0])
    try:
        if not client.collections.exists(args.collection):
            client.collections.create(
                args.collection,
                properties=[
                    Property(name="document", data_type=DataType.TEXT),
                    Property(name="book_name", data_type=DataType.TEXT),
                    Property(name="source_file", data_type=DataType.TEXT),
                    Property(name="page_number", data_type=DataType.TEXT),
                    Property(name="article_number", data_type=DataType.TEXT),
                ],
            )
        collection = client.collections.get(args.collection)
        with collection.batch.dynamic() as batch:
            for record, vector in zip(records, vectors):
                props = {"document": record["document"], **record["metadata"]}
                batch.add_object(properties=props, vector=vector, uuid=record["id"])
    finally:
        client.close()
    print(f"Loaded {len(records)} records into Weaviate collection {args.collection}.")


if __name__ == "__main__":
    main()

