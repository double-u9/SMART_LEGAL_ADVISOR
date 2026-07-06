"""Full ingestion pipeline — orchestrates extraction, cleaning, chunking, and storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from backend.ingestion.pdf_processor import PDFProcessor
from backend.ingestion.ocr_engine import OCREngine
from backend.ingestion.cleaner import TextCleaner
from backend.ingestion.arabic_normalizer import ArabicNormalizer
from backend.ingestion.chunker import LegalChunker
from backend.ingestion.metadata_engine import MetadataEngine
from backend.utils.logging_config import get_logger

logger = get_logger("pipeline")


class IngestionPipeline:
    """Orchestrates the full document processing pipeline."""

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.ocr_engine = OCREngine()
        self.cleaner = TextCleaner()
        self.normalizer = ArabicNormalizer()
        self.chunker = LegalChunker()
        self.metadata_engine = MetadataEngine()
        self._status: dict = {"state": "idle", "progress": 0, "message": ""}

    @property
    def status(self) -> dict:
        return self._status.copy()

    def ingest_from_jsonl(self, jsonl_path: str | Path) -> list[dict]:
        """Load preprocessed dataset from JSONL file.

        This is the PRIMARY ingestion method — uses the existing preprocessed data.
        """
        jsonl_path = Path(jsonl_path)
        if not jsonl_path.exists():
            raise FileNotFoundError(f"Dataset not found: {jsonl_path}")

        self._status = {"state": "loading", "progress": 0, "message": "جاري تحميل البيانات..."}

        documents = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    # Ensure chunk_id field exists
                    if "chunk_id" not in doc:
                        doc["chunk_id"] = doc.get("id", f"chunk_{i}")
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    logger.warning("Skipping invalid JSON at line %d: %s", i, e)

                if (i + 1) % 100 == 0:
                    self._status["progress"] = i + 1
                    self._status["message"] = f"تم تحميل {i + 1} سجل..."

        self._status = {
            "state": "complete",
            "progress": len(documents),
            "message": f"تم تحميل {len(documents)} سجل قانوني",
        }
        logger.info("Loaded %d documents from %s", len(documents), jsonl_path.name)
        return documents

    def ingest_from_pdfs(self, pdf_dir: str | Path) -> list[dict]:
        """Process raw PDF files through the full pipeline."""
        pdf_dir = Path(pdf_dir)
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning("No PDF files found in %s", pdf_dir)
            return []

        self._status = {"state": "processing", "progress": 0, "message": f"معالجة {len(pdf_files)} ملف PDF..."}

        all_chunks = []

        for pdf_idx, pdf_path in enumerate(pdf_files):
            logger.info("Processing %d/%d: %s", pdf_idx + 1, len(pdf_files), pdf_path.name)
            self._status["message"] = f"معالجة: {pdf_path.stem}..."

            try:
                # 1. Extract text
                if self.pdf_processor.is_scanned(pdf_path):
                    logger.info("Scanned PDF detected — applying OCR")
                    pages = self.ocr_engine.ocr_pdf(pdf_path)
                else:
                    pages = self.pdf_processor.extract_pages(pdf_path)

                if not pages:
                    logger.warning("No text extracted from %s", pdf_path.name)
                    continue

                # 2. Clean pages
                pages = self.cleaner.clean_pages(pages)

                # 3. Normalize Arabic
                for page in pages:
                    page["text"] = self.normalizer.normalize(page["text"])

                # 4. Concatenate text
                full_text = "\n\n".join(p["text"] for p in pages if p["text"])

                # 5. Chunk
                book_name = pdf_path.stem
                chunks = self.chunker.chunk_document(
                    text=full_text,
                    book_name=book_name,
                    source_file=pdf_path.name,
                    pages=pages,
                )

                # 6. Enrich with metadata
                for chunk in chunks:
                    chunk_dict = chunk.to_dict()
                    chunk_dict = self.metadata_engine.enrich_chunk(chunk_dict)
                    all_chunks.append(chunk_dict)

            except Exception as e:
                logger.error("Failed to process %s: %s", pdf_path.name, e)

            self._status["progress"] = pdf_idx + 1

        self._status = {
            "state": "complete",
            "progress": len(all_chunks),
            "message": f"تم معالجة {len(all_chunks)} قطعة نصية من {len(pdf_files)} ملف",
        }
        logger.info("Pipeline complete: %d chunks from %d PDFs", len(all_chunks), len(pdf_files))
        return all_chunks
