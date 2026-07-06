"""PDF text extraction with multi-strategy fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from backend.utils.logging_config import get_logger

logger = get_logger("pdf_processor")


class PDFProcessor:
    """Extract text from PDFs using PyMuPDF → pdfplumber → pypdf fallback."""

    SCANNED_CHAR_THRESHOLD = 50  # avg chars/page below this = scanned

    def extract_pages(self, pdf_path: str | Path) -> list[dict]:
        """Extract text page-by-page from a PDF.

        Returns list of {page_number, text, extraction_method, char_count}.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Try extractors in order of quality
        for method_name, method_fn in [
            ("pymupdf", self._extract_pymupdf),
            ("pdfplumber", self._extract_pdfplumber),
            ("pypdf", self._extract_pypdf),
        ]:
            try:
                pages = method_fn(pdf_path)
                if pages and self._has_enough_text(pages):
                    logger.info(
                        "Extracted %d pages from %s using %s",
                        len(pages), pdf_path.name, method_name,
                    )
                    return pages
            except ImportError:
                logger.debug("%s not available, trying next", method_name)
            except Exception as e:
                logger.warning("Extraction with %s failed: %s", method_name, e)

        logger.warning("All extractors failed for %s — may need OCR", pdf_path.name)
        return []

    def extract_text(self, pdf_path: str | Path) -> str:
        """Extract and concatenate all pages."""
        pages = self.extract_pages(pdf_path)
        return "\n\n".join(p["text"] for p in pages if p["text"])

    def is_scanned(self, pdf_path: str | Path) -> bool:
        """Detect if PDF is likely scanned (image-based)."""
        pages = self.extract_pages(pdf_path)
        if not pages:
            return True
        avg_chars = sum(p["char_count"] for p in pages) / max(len(pages), 1)
        return avg_chars < self.SCANNED_CHAR_THRESHOLD

    def _has_enough_text(self, pages: list[dict]) -> bool:
        total_chars = sum(p["char_count"] for p in pages)
        return total_chars > self.SCANNED_CHAR_THRESHOLD * len(pages)

    def _extract_pymupdf(self, pdf_path: Path) -> list[dict]:
        import fitz  # PyMuPDF

        pages = []
        with fitz.open(str(pdf_path)) as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text")
                pages.append({
                    "page_number": i + 1,
                    "text": text.strip(),
                    "extraction_method": "pymupdf",
                    "char_count": len(text.strip()),
                })
        return pages

    def _extract_pdfplumber(self, pdf_path: Path) -> list[dict]:
        import pdfplumber

        pages = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append({
                    "page_number": i + 1,
                    "text": text.strip(),
                    "extraction_method": "pdfplumber",
                    "char_count": len(text.strip()),
                })
        return pages

    def _extract_pypdf(self, pdf_path: Path) -> list[dict]:
        from pypdf import PdfReader

        pages = []
        reader = PdfReader(str(pdf_path))
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({
                "page_number": i + 1,
                "text": text.strip(),
                "extraction_method": "pypdf",
                "char_count": len(text.strip()),
            })
        return pages
