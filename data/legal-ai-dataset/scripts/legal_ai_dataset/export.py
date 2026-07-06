from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import FileReport, LegalChunk, PageText
from .utils import safe_stem, write_json, write_jsonl


def export_file_reports(reports: list[FileReport], reports_dir: Path) -> None:
    records = [report.to_dict() for report in reports]
    write_json(reports_dir / "book_analysis_report.json", records)
    _write_csv(reports_dir / "book_analysis_report.csv", records)
    (reports_dir / "book_analysis_report.md").write_text(render_file_report_markdown(reports), encoding="utf-8", newline="\n")


def export_extracted_pages(pages: list[PageText], extracted_dir: Path) -> None:
    if not pages:
        return
    stem = safe_stem(pages[0].source_file)
    write_json(extracted_dir / f"{stem}.pages.json", [page.to_dict() for page in pages])
    text = "\n\n".join(f"[PAGE {page.page_number}]\n{page.text}" for page in pages)
    (extracted_dir / f"{stem}.txt").write_text(text, encoding="utf-8", newline="\n")


def export_chunks_for_book(chunks: list[LegalChunk], chunks_dir: Path, metadata_dir: Path) -> None:
    if not chunks:
        return
    stem = safe_stem(chunks[0].source_file)
    entries = [chunk.to_dataset_entry() for chunk in chunks]
    write_jsonl(chunks_dir / f"{stem}.chunks.jsonl", entries)
    write_json(chunks_dir / f"{stem}.chunks.json", entries)
    metadata = [
        {key: value for key, value in entry.items() if key not in {"chunk_text", "embedding_ready_text"}}
        for entry in entries
    ]
    write_json(metadata_dir / f"{stem}.metadata.json", metadata)


def export_dataset(chunks: list[LegalChunk], output_root: Path) -> None:
    entries = [chunk.to_dataset_entry() for chunk in chunks]
    write_json(output_root / "legal_dataset.json", entries)
    write_jsonl(output_root / "legal_dataset.jsonl", entries)
    _write_csv(output_root / "legal_dataset.csv", entries)
    export_embedding_ready(chunks, output_root / "embeddings_ready")
    export_vector_records(chunks, output_root / "vector_exports")


def export_embedding_ready(chunks: list[LegalChunk], embeddings_dir: Path) -> None:
    records = [
        {
            "id": chunk.id,
            "embedding_ready_text": chunk.embedding_ready_text,
            "metadata": {
                "book_name": chunk.book_name,
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "article_number": chunk.article_number,
                "language": chunk.language,
                "chunk_index": chunk.chunk_index,
                "keywords": chunk.keywords,
                "legal_topics": chunk.legal_topics,
            },
        }
        for chunk in chunks
    ]
    write_jsonl(embeddings_dir / "legal_embeddings_ready.jsonl", records)
    write_json(embeddings_dir / "legal_embeddings_ready.json", records)


def export_vector_records(chunks: list[LegalChunk], vector_dir: Path) -> None:
    records = [
        {
            "id": chunk.id,
            "document": chunk.embedding_ready_text,
            "metadata": {
                "book_name": chunk.book_name,
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "article_number": chunk.article_number,
                "summary": chunk.summary,
                "keywords": chunk.keywords,
                "legal_topics": chunk.legal_topics,
                "token_count": chunk.token_count,
                "chunk_index": chunk.chunk_index,
                "previous_chunk_id": chunk.previous_chunk_id,
                "next_chunk_id": chunk.next_chunk_id,
            },
        }
        for chunk in chunks
    ]
    write_jsonl(vector_dir / "vector_records.jsonl", records)
    write_json(vector_dir / "vector_records.json", records)


def render_file_report_markdown(reports: list[FileReport]) -> str:
    lines = [
        "# Book Analysis Report",
        "",
        "| File | Format | Pages | Language | OCR Required | Difficulty | Text Quality | Extractor | Avg chars/page | Arabic ratio |",
        "|---|---:|---:|---|---:|---|---|---|---:|---:|",
    ]
    for report in reports:
        lines.append(
            "| {file} | {fmt} | {pages} | {lang} | {ocr} | {difficulty} | {quality} | {method} | {avg} | {ratio} |".format(
                file=report.file_name.replace("|", "\\|"),
                fmt=report.format,
                pages=report.page_count if report.page_count is not None else "",
                lang=report.language,
                ocr="yes" if report.ocr_required else "no",
                difficulty=report.extraction_difficulty,
                quality=report.text_quality,
                method=report.extraction_method,
                avg=report.avg_chars_per_page,
                ratio=report.arabic_ratio,
            )
        )
    lines.extend(["", "## Notes", ""])
    for report in reports:
        if report.notes:
            lines.append(f"- `{report.file_name}`: {'; '.join(report.notes)}")
    if not any(report.notes for report in reports):
        lines.append("- No blocking analysis notes.")
    return "\n".join(lines) + "\n"


def write_embedding_model_recommendation(path: Path) -> None:
    path.write_text(
        """# Embedding Model Recommendation For Arabic Legal RAG

## Recommendation

Use `BAAI/bge-m3` as the default local/open-source embedding model for this corpus. It is the best fit for Arabic legal retrieval because it combines multilingual dense retrieval with sparse lexical weights and ColBERT-style multi-vector scoring. That matters for law: exact article numbers, procedural phrases, and named legal institutions often need lexical recall as much as semantic recall.

For a managed API baseline, use `text-embedding-3-large` and evaluate it against `bge-m3` on a small Arabic legal benchmark. It is strong and simple to operate, but it does not provide BGE-M3's native hybrid dense/sparse/multi-vector modes.

## Comparison

| Model | Strengths | Limits | Best use |
|---|---|---|---|
| `BAAI/bge-m3` | Multilingual, 1024 dimensions, up to 8192 tokens, dense + sparse + multi-vector retrieval | Heavier local serving than E5; best results may need FlagEmbedding-specific code | Default for Arabic legal RAG and hybrid retrieval |
| `intfloat/multilingual-e5-large` | Mature multilingual SentenceTransformers model, 1024 dimensions, strong Arabic score on Mr. TyDi | 512 token max in the model card; requires `query:` / `passage:` prefixes | Lightweight dense-only baseline |
| `jinaai/jina-embeddings-v3` | Multilingual, long-context up to 8192 tokens, task adapters | Requires `trust_remote_code` in common HF usage; API/local behavior should be pinned | Long-context experiments and late chunking |
| `text-embedding-3-large` | Managed API, strong English and non-English embedding model, easy ops | External API cost/data-governance considerations; dense-only | Production API baseline or low-maintenance deployment |

## Evaluation Plan

1. Create 50-100 Arabic legal queries with known source articles.
2. Measure Recall@5, MRR@10, citation accuracy, and false positive rate.
3. Compare dense-only against hybrid BM25 + dense retrieval.
4. Use a reranker for final answer contexts, especially for similar article language.

## Sources

- BGE-M3 model card: https://huggingface.co/BAAI/bge-m3
- Multilingual-E5-large model card: https://huggingface.co/intfloat/multilingual-e5-large
- Jina embeddings v3 model card: https://huggingface.co/jinaai/jina-embeddings-v3
- OpenAI text-embedding-3-large docs: https://developers.openai.com/api/docs/models/text-embedding-3-large
""",
        encoding="utf-8",
        newline="\n",
    )


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(records[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = {
                key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                for key, value in record.items()
            }
            writer.writerow(row)

