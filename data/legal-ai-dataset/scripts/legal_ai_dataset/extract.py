from __future__ import annotations

import importlib.util
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .analyze import score_extraction_sample
from .models import FileReport, PageText
from .utils import read_text_lossless

LOGGER = logging.getLogger(__name__)


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


class OcrUnavailable(RuntimeError):
    pass


class OcrEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        ocr_config = config["extraction"]["ocr"]
        self.enabled = str(ocr_config.get("enabled", "auto")).lower()
        self.engine_order = list(ocr_config.get("engine_order", ["tesseract", "easyocr"]))
        self.languages = list(ocr_config.get("languages", ["ara", "eng"]))
        self.render_dpi = int(ocr_config.get("render_dpi", 300))
        self._easyocr_reader: Any = None

    def available_engine(self) -> str | None:
        if self.enabled in {"false", "off", "no", "0"}:
            return None
        for engine in self.engine_order:
            engine = engine.lower()
            if engine == "tesseract" and shutil.which("tesseract"):
                return "tesseract"
            if engine == "easyocr" and _has_module("easyocr"):
                return "easyocr"
        return None

    def render_pdf_page(self, page: Any, output_path: Path) -> None:
        if not _has_module("fitz"):
            raise OcrUnavailable("PyMuPDF is required to render PDF pages for OCR.")
        import fitz  # type: ignore

        zoom = self.render_dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(output_path)

    def ocr_image(self, image_path: Path) -> tuple[str, float | None, str]:
        engine = self.available_engine()
        if not engine:
            raise OcrUnavailable("No OCR engine is available. Install Tesseract Arabic or EasyOCR.")
        if engine == "tesseract":
            return self._ocr_tesseract(image_path)
        return self._ocr_easyocr(image_path)

    def _ocr_tesseract(self, image_path: Path) -> tuple[str, float | None, str]:
        lang = "+".join(self.languages)
        if _has_module("pytesseract"):
            import pytesseract  # type: ignore

            text = pytesseract.image_to_string(str(image_path), lang=lang)
            confidence = None
            try:
                data = pytesseract.image_to_data(str(image_path), lang=lang, output_type=pytesseract.Output.DICT)
                values = [float(x) for x in data.get("conf", []) if str(x).replace(".", "", 1).lstrip("-").isdigit() and float(x) >= 0]
                if values:
                    confidence = sum(values) / len(values)
            except Exception:
                confidence = None
            return text, confidence, "tesseract"

        exe = shutil.which("tesseract")
        if not exe:
            raise OcrUnavailable("Tesseract executable was not found.")
        with tempfile.TemporaryDirectory() as tmp:
            out_base = Path(tmp) / "ocr"
            cmd = [exe, str(image_path), str(out_base), "-l", lang, "--psm", "6"]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return out_base.with_suffix(".txt").read_text(encoding="utf-8", errors="replace"), None, "tesseract"

    def _ocr_easyocr(self, image_path: Path) -> tuple[str, float | None, str]:
        import easyocr  # type: ignore

        easyocr_langs = [lang.replace("ara", "ar").replace("eng", "en") for lang in self.languages]
        if self._easyocr_reader is None:
            self._easyocr_reader = easyocr.Reader(easyocr_langs, gpu=False)
        result = self._easyocr_reader.readtext(str(image_path), detail=1, paragraph=True)
        texts: list[str] = []
        confidences: list[float] = []
        for item in result:
            if len(item) >= 2:
                texts.append(str(item[1]))
            if len(item) >= 3:
                try:
                    confidences.append(float(item[2]) * 100)
                except (TypeError, ValueError):
                    pass
        confidence = sum(confidences) / len(confidences) if confidences else None
        return "\n".join(texts), confidence, "easyocr"


class BookExtractor:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.ocr = OcrEngine(config)
        self.min_text_chars = int(config["extraction"].get("min_text_chars_per_page", 80))

    def extract(self, path: Path, report: FileReport | None = None) -> list[PageText]:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self.extract_pdf(path, report)
        if suffix == ".docx":
            return self.extract_docx(path)
        if suffix == ".txt":
            return [PageText(path.name, 1, read_text_lossless(path), "text")]
        raise ValueError(f"Unsupported file type: {path}")

    def extract_pdf(self, path: Path, report: FileReport | None = None) -> list[PageText]:
        prefer = [name.lower() for name in self.config["extraction"].get("prefer_pdf_extractors", [])]
        errors: list[str] = []
        candidates: list[tuple[str, float, list[PageText]]] = []
        for extractor in prefer:
            try:
                if extractor == "pymupdf" and _has_module("fitz"):
                    pages = self._extract_pdf_pymupdf(path, report)
                elif extractor == "pdfplumber" and _has_module("pdfplumber"):
                    pages = self._extract_pdf_pdfplumber(path, report)
                elif extractor == "pypdf" and _has_module("pypdf"):
                    pages = self._extract_pdf_pypdf(path, report)
                else:
                    continue
                sample_text = "\n".join(page.text for page in pages[: min(len(pages), 10)])
                score = score_extraction_sample(sample_text)
                if any(page.extraction_method.startswith("ocr:") for page in pages):
                    score += 50
                candidates.append((extractor, score, pages))
            except Exception as exc:
                LOGGER.exception("PDF extractor %s failed for %s", extractor, path)
                errors.append(f"{extractor}: {type(exc).__name__}: {exc}")
        if candidates:
            method, score, pages = max(candidates, key=lambda item: item[1])
            LOGGER.info("Selected %s for %s (structure score %.2f)", method, path.name, score)
            if pages and candidates[0][0] != method:
                pages[0].warnings.append(f"Selected {method} because it preserved stronger Arabic/legal structure than {candidates[0][0]}.")
            return pages
        raise RuntimeError(f"No PDF extractor succeeded for {path.name}: {'; '.join(errors)}")

    def _needs_ocr(self, text: str, report: FileReport | None) -> bool:
        enabled = str(self.config["extraction"]["ocr"].get("enabled", "auto")).lower()
        if enabled in {"false", "off", "no", "0"}:
            return False
        if enabled in {"true", "on", "yes", "1"}:
            return True
        return len(text.strip()) < self.min_text_chars or bool(report and report.ocr_required)

    def _extract_pdf_pymupdf(self, path: Path, report: FileReport | None) -> list[PageText]:
        import fitz  # type: ignore

        pages: list[PageText] = []
        with fitz.open(path) as doc:
            for index, page in enumerate(doc, start=1):

                warnings: list[str] = []
                text = page.get_text("text", sort=True) or ""
                method = "pymupdf"
                confidence = None
                if self._needs_ocr(text, report):
                    engine = self.ocr.available_engine()
                    if not engine:
                        warnings.append("OCR is recommended for this page, but no Arabic OCR engine is available.")
                    else:
                        try:
                            with tempfile.TemporaryDirectory() as tmp:
                                image_path = Path(tmp) / f"page_{index}.png"
                                self.ocr.render_pdf_page(page, image_path)
                                ocr_text, confidence, engine = self.ocr.ocr_image(image_path)
                                if len(ocr_text.strip()) > len(text.strip()):
                                    text = ocr_text
                                    method = f"ocr:{engine}"
                                else:
                                    warnings.append("OCR produced no improvement; kept PyMuPDF text.")
                        except OcrUnavailable as exc:
                            warnings.append(str(exc))
                        except Exception as exc:  # pragma: no cover - external OCR errors
                            warnings.append(f"OCR failed: {type(exc).__name__}: {exc}")
                pages.append(PageText(path.name, index, text, method, confidence, warnings))
        return pages

    def _extract_pdf_pdfplumber(self, path: Path, report: FileReport | None) -> list[PageText]:
        import pdfplumber  # type: ignore

        pages: list[PageText] = []
        with pdfplumber.open(path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):

                text = page.extract_text(x_tolerance=1.5, y_tolerance=3, layout=False) or ""
                warnings = []
                if self._needs_ocr(text, report):
                    warnings.append("Page likely needs OCR, but pdfplumber cannot render pages in this pipeline path.")
                pages.append(PageText(path.name, index, text, "pdfplumber", None, warnings))
        return pages

    def _extract_pdf_pypdf(self, path: Path, report: FileReport | None) -> list[PageText]:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages: list[PageText] = []
        for index, page in enumerate(reader.pages, start=1):

            text = page.extract_text() or ""
            warnings = []
            if self._needs_ocr(text, report):
                warnings.append("Page likely needs OCR; install PyMuPDF plus Tesseract/EasyOCR for OCR extraction.")
            pages.append(PageText(path.name, index, text, "pypdf", None, warnings))
        return pages

    def extract_docx(self, path: Path) -> list[PageText]:
        try:
            import docx  # type: ignore

            document = docx.Document(path)
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            return [PageText(path.name, 1, text, "python-docx")]
        except Exception:
            from .analyze import _read_docx_xml_fallback

            return [PageText(path.name, 1, _read_docx_xml_fallback(path), "docx-zip-fallback")]
