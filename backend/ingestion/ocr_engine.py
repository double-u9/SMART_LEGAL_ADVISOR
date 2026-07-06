"""OCR engine for scanned Arabic PDF pages — PaddleOCR + Tesseract."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from backend.utils.logging_config import get_logger

logger = get_logger("ocr_engine")


class OCREngine:
    """OCR for scanned Arabic documents using PaddleOCR or Tesseract."""

    def __init__(self, languages: str = "ara+eng", dpi: int = 300):
        self.languages = languages
        self.dpi = dpi
        self._paddle_ocr = None
        self._engine: Optional[str] = None

    def _init_paddleocr(self):
        try:
            from paddleocr import PaddleOCR
            self._paddle_ocr = PaddleOCR(use_angle_cls=True, lang="ar", show_log=False)
            self._engine = "paddleocr"
            logger.info("PaddleOCR initialized for Arabic")
            return True
        except ImportError:
            logger.info("PaddleOCR not available")
            return False

    def _init_tesseract(self):
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._engine = "tesseract"
            logger.info("Tesseract OCR available")
            return True
        except Exception:
            logger.info("Tesseract not available")
            return False

    def ocr_page(self, image) -> tuple[str, float]:
        """OCR a single page image.

        Args:
            image: PIL Image or numpy array

        Returns:
            (text, confidence)
        """
        # Try PaddleOCR first
        if self._engine == "paddleocr" or (self._engine is None and self._init_paddleocr()):
            return self._ocr_paddle(image)

        # Fallback to Tesseract
        if self._engine == "tesseract" or (self._engine is None and self._init_tesseract()):
            return self._ocr_tesseract(image)

        logger.warning("No OCR engine available")
        return "", 0.0

    def ocr_pdf(self, pdf_path: str | Path) -> list[dict]:
        """OCR all pages of a PDF.

        Returns list of {page_number, text, confidence, ocr_engine}.
        """
        pdf_path = Path(pdf_path)
        pages = []

        try:
            import fitz  # PyMuPDF for rendering pages
            from PIL import Image
            import io

            doc = fitz.open(str(pdf_path))
            for i, page in enumerate(doc):
                # Render page as image
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))

                text, confidence = self.ocr_page(img)
                pages.append({
                    "page_number": i + 1,
                    "text": text.strip(),
                    "confidence": confidence,
                    "ocr_engine": self._engine or "none",
                    "char_count": len(text.strip()),
                })
            doc.close()

        except ImportError as e:
            logger.error("PyMuPDF required for OCR rendering: %s", e)
        except Exception as e:
            logger.error("OCR failed for %s: %s", pdf_path.name, e)

        logger.info("OCR completed: %d pages from %s", len(pages), pdf_path.name)
        return pages

    def _ocr_paddle(self, image) -> tuple[str, float]:
        import numpy as np
        from PIL import Image

        if isinstance(image, Image.Image):
            image = np.array(image)

        result = self._paddle_ocr.ocr(image, cls=True)
        if not result or not result[0]:
            return "", 0.0

        lines = []
        confidences = []
        for line in result[0]:
            text = line[1][0]
            conf = line[1][1]
            lines.append(text)
            confidences.append(conf)

        avg_conf = sum(confidences) / max(len(confidences), 1)
        return "\n".join(lines), avg_conf

    def _ocr_tesseract(self, image) -> tuple[str, float]:
        import pytesseract
        from PIL import Image

        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)

        data = pytesseract.image_to_data(image, lang=self.languages, output_type=pytesseract.Output.DICT)
        lines = []
        confidences = []

        for text, conf in zip(data["text"], data["conf"]):
            if text.strip() and int(conf) > 0:
                lines.append(text)
                confidences.append(int(conf))

        text = " ".join(lines)
        avg_conf = sum(confidences) / max(len(confidences), 1) / 100.0 if confidences else 0.0
        return text, avg_conf
