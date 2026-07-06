from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a FAISS index for Arabic legal chunks.")
    parser.add_argument("--records", type=Path, default=Path("vector_records.jsonl"))
    parser.add_argument("--index", type=Path, default=Path("legal_faiss.index"))
    parser.add_argument("--metadata", type=Path, default=Path("legal_faiss_metadata.json"))
    parser.add_argument("--model", default="BAAI/bge-m3")
    args = parser.parse_args()

    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer

    records = load_records(args.records)
    model = SentenceTransformer(args.model)
    embeddings = model.encode([record["document"] for record in records], normalize_embeddings=True, batch_size=16)
    matrix = np.asarray(embeddings, dtype="float32")
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    faiss.write_index(index, str(args.index))
    args.metadata.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote FAISS index with {len(records)} records to {args.index}.")


if __name__ == "__main__":
    main()

