from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PageText:
    source_file: str
    page_number: int
    text: str
    extraction_method: str
    ocr_confidence: float | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FileReport:
    file_name: str
    format: str
    page_count: int | None
    language: str
    ocr_required: bool
    scanned_pdf: bool
    extraction_difficulty: str
    text_quality: str
    extraction_method: str
    avg_chars_per_page: float
    arabic_ratio: float
    ocr_engine: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LegalUnit:
    book_name: str
    source_file: str
    chapter: str = ""
    section: str = ""
    article_number: str = ""
    page_start: int | None = None
    page_end: int | None = None
    text: str = ""
    extraction_method: str = ""
    ocr_confidence: float | None = None


@dataclass(slots=True)
class LegalChunk:
    id: str
    book_name: str
    chapter: str
    section: str
    article_number: str
    page_number: str
    language: str
    chunk_text: str
    summary: str
    keywords: list[str]
    legal_topics: list[str]
    embedding_ready_text: str
    source_file: str
    token_count: int
    chunk_index: int
    previous_chunk_id: str
    next_chunk_id: str
    page_start: int | None = None
    page_end: int | None = None
    extraction_method: str = ""
    ocr_confidence: float | None = None

    def to_dataset_entry(self) -> dict[str, Any]:
        data = asdict(self)
        # Keep the user-requested schema fields first when serialized.
        ordered_keys = [
            "id",
            "book_name",
            "chapter",
            "section",
            "article_number",
            "page_number",
            "language",
            "chunk_text",
            "summary",
            "keywords",
            "legal_topics",
            "embedding_ready_text",
            "source_file",
            "token_count",
            "chunk_index",
            "previous_chunk_id",
            "next_chunk_id",
            "page_start",
            "page_end",
            "extraction_method",
            "ocr_confidence",
        ]
        return {key: data.get(key) for key in ordered_keys}


def book_name_from_path(path: str | Path) -> str:
    return Path(path).stem.strip()
