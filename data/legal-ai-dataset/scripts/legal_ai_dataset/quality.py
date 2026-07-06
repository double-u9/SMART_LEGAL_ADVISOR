from __future__ import annotations

import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from .arabic import arabic_mark_ratio, arabic_ratio, compact_for_hash, corruption_score, standard_arabic_letter_ratio
from .models import FileReport, LegalChunk
from .utils import write_json

REQUIRED_FIELDS = [
    "id",
    "book_name",
    "page_number",
    "language",
    "chunk_text",
    "embedding_ready_text",
    "source_file",
    "token_count",
    "chunk_index",
]


def validate_dataset(chunks: list[LegalChunk], reports: list[FileReport], reports_dir: Path) -> dict[str, Any]:
    entries = [chunk.to_dataset_entry() for chunk in chunks]
    ids = {chunk.id for chunk in chunks}
    empty_chunks = [chunk.id for chunk in chunks if not chunk.chunk_text.strip()]
    invalid_metadata: list[dict[str, str]] = []
    broken_references: list[dict[str, str]] = []
    corrupted_arabic: list[dict[str, Any]] = []

    for entry in entries:
        for field in REQUIRED_FIELDS:
            if entry.get(field) in (None, ""):
                invalid_metadata.append({"id": entry.get("id", ""), "field": field})

    for chunk in chunks:
        if chunk.previous_chunk_id and chunk.previous_chunk_id not in ids:
            broken_references.append({"id": chunk.id, "missing_previous": chunk.previous_chunk_id})
        if chunk.next_chunk_id and chunk.next_chunk_id not in ids:
            broken_references.append({"id": chunk.id, "missing_next": chunk.next_chunk_id})
        ratio = arabic_ratio(chunk.chunk_text)
        standard_ratio = standard_arabic_letter_ratio(chunk.chunk_text)
        mark_ratio = arabic_mark_ratio(chunk.chunk_text)
        badness = corruption_score(chunk.chunk_text)
        if ratio < 0.20 or badness > 0.03 or standard_ratio < 0.70 or mark_ratio > 0.25:
            corrupted_arabic.append(
                {
                    "id": chunk.id,
                    "arabic_ratio": round(ratio, 4),
                    "standard_arabic_letter_ratio": round(standard_ratio, 4),
                    "arabic_mark_ratio": round(mark_ratio, 4),
                    "corruption_score": round(badness, 4),
                }
            )

    hashes = [compact_for_hash(chunk.chunk_text) for chunk in chunks if chunk.chunk_text.strip()]
    duplicates = {text_hash: count for text_hash, count in Counter(hashes).items() if count > 1}
    token_counts = [chunk.token_count for chunk in chunks]
    ocr_failures = [
        report.file_name
        for report in reports
        if report.ocr_required and not any(chunk.source_file == report.file_name and chunk.extraction_method.startswith("ocr:") for chunk in chunks)
    ]
    quality = {
        "total_files": len(reports),
        "total_chunks": len(chunks),
        "empty_chunks": empty_chunks,
        "invalid_metadata_count": len(invalid_metadata),
        "invalid_metadata": invalid_metadata[:100],
        "duplicate_exact_count": sum(count - 1 for count in duplicates.values()),
        "duplicate_groups": len(duplicates),
        "broken_references": broken_references,
        "corrupted_arabic_count": len(corrupted_arabic),
        "corrupted_arabic_samples": corrupted_arabic[:50],
        "ocr_failures_or_unavailable": ocr_failures,
        "token_statistics": token_statistics(token_counts),
        "retrieval_readiness_score": retrieval_readiness_score(
            chunks=chunks,
            invalid_metadata=len(invalid_metadata),
            duplicate_count=sum(count - 1 for count in duplicates.values()),
            empty_count=len(empty_chunks),
            corrupted_count=len(corrupted_arabic),
            broken_reference_count=len(broken_references),
            ocr_failure_count=len(ocr_failures),
        ),
    }
    write_json(reports_dir / "dataset_quality_report.json", quality)
    (reports_dir / "dataset_quality_report.md").write_text(render_quality_report(quality, reports), encoding="utf-8", newline="\n")
    return quality


def token_statistics(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"min": 0, "max": 0, "mean": 0, "median": 0}
    return {
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
    }


def retrieval_readiness_score(
    *,
    chunks: list[LegalChunk],
    invalid_metadata: int,
    duplicate_count: int,
    empty_count: int,
    corrupted_count: int,
    broken_reference_count: int,
    ocr_failure_count: int,
) -> float:
    if not chunks:
        return 0.0
    score = 100.0
    score -= min(30.0, empty_count * 5.0)
    score -= min(25.0, invalid_metadata * 0.5)
    score -= min(20.0, duplicate_count * 1.5)
    score -= min(20.0, corrupted_count * 2.0)
    score -= min(15.0, broken_reference_count * 3.0)
    score -= min(20.0, ocr_failure_count * 8.0)
    out_of_range = sum(1 for chunk in chunks if chunk.token_count < 150 or chunk.token_count > 1500)
    score -= min(15.0, out_of_range * 0.5)
    return round(max(score, 0.0), 2)


def render_quality_report(quality: dict[str, Any], reports: list[FileReport]) -> str:
    token_stats = quality["token_statistics"]
    lines = [
        "# Dataset Quality Report",
        "",
        f"- Total files: {quality['total_files']}",
        f"- Total chunks: {quality['total_chunks']}",
        f"- Retrieval-readiness score: {quality['retrieval_readiness_score']}/100",
        "",
        "## Extraction Quality",
        "",
        "| File | Text quality | OCR required | Difficulty | Extractor | Arabic ratio |",
        "|---|---|---:|---|---|---:|",
    ]
    for report in reports:
        lines.append(
            f"| {report.file_name.replace('|', '\\|')} | {report.text_quality} | {'yes' if report.ocr_required else 'no'} | {report.extraction_difficulty} | {report.extraction_method} | {report.arabic_ratio} |"
        )
    lines.extend(
        [
            "",
            "## Chunk Statistics",
            "",
            f"- Min tokens: {token_stats['min']}",
            f"- Median tokens: {token_stats['median']}",
            f"- Mean tokens: {token_stats['mean']}",
            f"- Max tokens: {token_stats['max']}",
            "",
            "## Duplicate Analysis",
            "",
            f"- Exact duplicate chunks: {quality['duplicate_exact_count']}",
            f"- Duplicate groups: {quality['duplicate_groups']}",
            "",
            "## Validation Findings",
            "",
            f"- Empty chunks: {len(quality['empty_chunks'])}",
            f"- Invalid metadata fields: {quality['invalid_metadata_count']}",
            f"- Broken previous/next references: {len(quality['broken_references'])}",
            f"- Corrupted Arabic candidates: {quality['corrupted_arabic_count']}",
            f"- OCR failures or unavailable OCR for scanned files: {len(quality['ocr_failures_or_unavailable'])}",
        ]
    )
    if quality["ocr_failures_or_unavailable"]:
        lines.extend(["", "## OCR Attention Needed", ""])
        for file_name in quality["ocr_failures_or_unavailable"]:
            lines.append(f"- `{file_name}` needs OCR, but no OCR output was used.")
    return "\n".join(lines) + "\n"
