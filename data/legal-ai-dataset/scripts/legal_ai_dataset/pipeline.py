from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from .analyze import analyze_books, discover_files
from .chunk import LegalChunker
from .clean import clean_pages, write_page_texts
from .config import load_config
from .export import (
    export_chunks_for_book,
    export_dataset,
    export_extracted_pages,
    export_file_reports,
    write_embedding_model_recommendation,
)
from .extract import BookExtractor
from .models import FileReport, LegalChunk
from .quality import validate_dataset
from .utils import ensure_directories

LOGGER = logging.getLogger(__name__)

PROJECT_DIRS = [
    "books",
    "extracted",
    "cleaned",
    "clean_text",
    "chunks",
    "metadata",
    "embeddings_ready",
    "vector_exports",
    "reports",
    "scripts",
    "configs",
    "tests",
]


def setup_logging(output_root: Path, verbose: bool = False) -> None:
    log_dir = output_root / "reports"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_pipeline(
    *,
    books_dir: Path,
    output_root: Path,
    config_path: Path | None = None,
    ocr_mode: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    ensure_directories(output_root, PROJECT_DIRS)
    setup_logging(output_root, verbose=verbose)
    config = load_config(config_path)
    if ocr_mode:
        config["extraction"]["ocr"]["enabled"] = ocr_mode

    LOGGER.info("Analyzing books in %s", books_dir)
    reports = analyze_books(books_dir, config)
    export_file_reports(reports, output_root / "reports")
    report_by_name: dict[str, FileReport] = {report.file_name: report for report in reports}

    extractor = BookExtractor(config)
    chunker = LegalChunker(config)
    all_chunks: list[LegalChunk] = []
    files = discover_files(books_dir, config)
    LOGGER.info("Processing %d source files", len(files))

    for path in files:
        LOGGER.info("Extracting %s", path.name)
        report = report_by_name.get(path.name)
        pages = extractor.extract(path, report)
        export_extracted_pages(pages, output_root / "extracted")

        cleaned_pages = clean_pages(pages, config)
        write_page_texts(cleaned_pages, output_root / "cleaned", output_root / "clean_text")

        chunks = chunker.chunk_book(cleaned_pages, path.name)
        export_chunks_for_book(chunks, output_root / "chunks", output_root / "metadata")
        all_chunks.extend(chunks)
        LOGGER.info("Created %d chunks from %s", len(chunks), path.name)

    export_dataset(all_chunks, output_root)
    quality = validate_dataset(all_chunks, reports, output_root / "reports")
    write_embedding_model_recommendation(output_root / "reports" / "embedding_model_recommendation.md")
    LOGGER.info("Pipeline completed with %d chunks. Readiness score: %s", len(all_chunks), quality["retrieval_readiness_score"])
    return {"reports": [report.to_dict() for report in reports], "quality": quality, "chunk_count": len(all_chunks)}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an Arabic legal RAG dataset from law books.")
    parser.add_argument("--books-dir", type=Path, default=Path("books"), help="Directory containing PDF/DOCX/TXT law books.")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Project/output root.")
    parser.add_argument("--config", type=Path, default=Path("configs/pipeline.yaml"), help="YAML or JSON pipeline config.")
    parser.add_argument("--ocr", choices=["auto", "true", "false"], default=None, help="Override OCR mode.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    run_pipeline(
        books_dir=args.books_dir.resolve(),
        output_root=args.output_dir.resolve(),
        config_path=args.config.resolve() if args.config else None,
        ocr_mode=args.ocr,
        verbose=args.verbose,
    )
    return 0

