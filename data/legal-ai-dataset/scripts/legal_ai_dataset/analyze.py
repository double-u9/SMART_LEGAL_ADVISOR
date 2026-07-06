from __future__ import annotations

import importlib.util
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

from .arabic import arabic_mark_ratio, arabic_ratio, corruption_score, standard_arabic_letter_ratio
from .models import FileReport
from .utils import file_size_mb, read_text_lossless

LOGGER = logging.getLogger(__name__)
ARTICLE_MARKER_RE = re.compile(r"(?:المادة|مادة)\s*[\(:\-]?\s*[0-9٠-٩۰-۹]+")


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def discover_files(books_dir: Path, config: dict[str, Any]) -> list[Path]:
    extensions = {ext.lower() for ext in config["input"]["extensions"]}
    iterator = books_dir.rglob("*") if config["input"].get("recursive", True) else books_dir.glob("*")
    return sorted(path for path in iterator if path.is_file() and path.suffix.lower() in extensions)


def analyze_books(books_dir: Path, config: dict[str, Any]) -> list[FileReport]:
    reports: list[FileReport] = []
    for path in discover_files(books_dir, config):
        try:
            reports.append(analyze_file(path, config))
        except Exception as exc:  # pragma: no cover - defensive reporting path
            LOGGER.exception("Failed to analyze %s", path)
            reports.append(
                FileReport(
                    file_name=path.name,
                    format=path.suffix.lower().lstrip("."),
                    page_count=None,
                    language="unknown",
                    ocr_required=False,
                    scanned_pdf=False,
                    extraction_difficulty="high",
                    text_quality="failed",
                    extraction_method="none",
                    avg_chars_per_page=0.0,
                    arabic_ratio=0.0,
                    notes=[f"analysis_error: {type(exc).__name__}: {exc}"],
                )
            )
    return reports


def analyze_file(path: Path, config: dict[str, Any]) -> FileReport:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return analyze_pdf(path, config)
    if suffix == ".docx":
        return analyze_docx(path)
    if suffix == ".txt":
        return analyze_txt(path)
    return FileReport(
        file_name=path.name,
        format=suffix.lstrip("."),
        page_count=None,
        language="unknown",
        ocr_required=False,
        scanned_pdf=False,
        extraction_difficulty="high",
        text_quality="unsupported",
        extraction_method="none",
        avg_chars_per_page=0.0,
        arabic_ratio=0.0,
        notes=["unsupported_extension"],
    )


def analyze_pdf(path: Path, config: dict[str, Any]) -> FileReport:
    sample_pages = int(config["extraction"].get("sample_pages_for_analysis", 5))
    min_chars = float(config["extraction"].get("scanned_avg_chars_threshold", 50))
    notes: list[str] = []
    candidates: list[tuple[str, int, list[str], float]] = []
    for method_name in config["extraction"].get("prefer_pdf_extractors", ["pymupdf", "pdfplumber", "pypdf"]):
        try:
            result = sample_pdf_text(path, str(method_name).lower(), sample_pages)
            if result is not None:
                candidate_method, page_count, sample_texts = result
                candidates.append((candidate_method, page_count, sample_texts, score_extraction_sample("\n".join(sample_texts))))
        except Exception as exc:
            notes.append(f"{method_name} sample failed: {type(exc).__name__}: {exc}")

    if not candidates:
        page_count = 0
        method = "none"
        sample_texts = []
        notes.append("No PDF text extractor installed.")
    else:
        method, page_count, sample_texts, _score = max(candidates, key=lambda item: item[3])
        if candidates[0][0] != method:
            notes.append(f"Selected {method} because it preserved more legal/Arabic structure than {candidates[0][0]}.")

    sample_text = "\n".join(sample_texts)
    sampled_count = max(len(sample_texts), 1)
    avg_chars = len(sample_text.strip()) / sampled_count
    ratio = arabic_ratio(sample_text)
    standard_ratio = standard_arabic_letter_ratio(sample_text)
    mark_ratio = arabic_mark_ratio(sample_text)
    scanned = bool(page_count and avg_chars < min_chars)
    encoded_text_problem = bool(avg_chars >= min_chars and ratio > 0.20 and (standard_ratio < 0.70 or mark_ratio > 0.25))
    ocr_required = scanned or encoded_text_problem
    language = infer_language(sample_text, ratio)
    quality = infer_text_quality(avg_chars, ratio, corruption_score(sample_text), scanned, standard_ratio, mark_ratio)
    difficulty = infer_difficulty(ocr_required, quality, file_size_mb(path), method)

    if scanned:
        notes.append("Low extractable text per sampled page; OCR is required or strongly recommended.")
    if encoded_text_problem:
        notes.append("Extractable text appears font-encoded or corrupted; OCR is recommended for reliable Arabic legal retrieval.")
    if quality in {"low", "failed"}:
        notes.append("Text quality is low; inspect OCR/extraction output before production indexing.")

    return FileReport(
        file_name=path.name,
        format="pdf",
        page_count=page_count,
        language=language,
        ocr_required=ocr_required,
        scanned_pdf=scanned,
        extraction_difficulty=difficulty,
        text_quality=quality,
        extraction_method=method,
        avg_chars_per_page=round(avg_chars, 2),
        arabic_ratio=round(ratio, 4),
        notes=notes,
    )


def analyze_docx(path: Path) -> FileReport:
    text = ""
    method = "python-docx"
    try:
        import docx  # type: ignore

        document = docx.Document(path)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception:
        method = "docx-zip-fallback"
        text = _read_docx_xml_fallback(path)
    ratio = arabic_ratio(text)
    return FileReport(
        file_name=path.name,
        format="docx",
        page_count=None,
        language=infer_language(text, ratio),
        ocr_required=False,
        scanned_pdf=False,
        extraction_difficulty="low" if text.strip() else "medium",
        text_quality=infer_text_quality(len(text), ratio, corruption_score(text), False),
        extraction_method=method,
        avg_chars_per_page=float(len(text)),
        arabic_ratio=round(ratio, 4),
    )


def analyze_txt(path: Path) -> FileReport:
    text = read_text_lossless(path)
    ratio = arabic_ratio(text)
    return FileReport(
        file_name=path.name,
        format="txt",
        page_count=1,
        language=infer_language(text, ratio),
        ocr_required=False,
        scanned_pdf=False,
        extraction_difficulty="low",
        text_quality=infer_text_quality(len(text), ratio, corruption_score(text), False),
        extraction_method="text",
        avg_chars_per_page=float(len(text)),
        arabic_ratio=round(ratio, 4),
    )


def infer_language(text: str, ratio: float | None = None) -> str:
    ratio = arabic_ratio(text) if ratio is None else ratio
    latin = sum(1 for char in text if "A" <= char <= "z")
    if ratio > 0.55 and latin > 50:
        return "ar+en"
    if ratio > 0.20:
        return "ar"
    if latin > 100:
        return "en"
    return "unknown"


def infer_text_quality(avg_chars: float, ratio: float, badness: float, scanned: bool, standard_ratio: float = 1.0, mark_ratio: float = 0.0) -> str:
    if avg_chars <= 0:
        return "failed"
    if scanned or avg_chars < 80 or badness > 0.03 or standard_ratio < 0.60 or mark_ratio > 0.35:
        return "low"
    if avg_chars < 300 or ratio < 0.20 or badness > 0.005 or standard_ratio < 0.85 or mark_ratio > 0.15:
        return "medium"
    return "high"


def infer_difficulty(ocr_required: bool, quality: str, size_mb: float, method: str) -> str:
    if method == "none" or quality == "failed":
        return "high"
    if ocr_required or quality == "low" or size_mb > 50:
        return "high"
    if quality == "medium":
        return "medium"
    return "low"


def sample_pdf_text(path: Path, method: str, sample_pages: int) -> tuple[str, int, list[str]] | None:
    if method == "pymupdf" and _has_module("fitz"):
        import fitz  # type: ignore

        with fitz.open(path) as doc:
            page_count = doc.page_count
            texts = [page.get_text("text", sort=True) or "" for page in doc[: min(sample_pages, page_count)]]
        return "pymupdf", page_count, texts
    if method == "pdfplumber" and _has_module("pdfplumber"):
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            texts = [page.extract_text(x_tolerance=1.5, y_tolerance=3) or "" for page in pdf.pages[: min(sample_pages, page_count)]]
        return "pdfplumber", page_count, texts
    if method == "pypdf" and _has_module("pypdf"):
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        texts = [page.extract_text() or "" for page in reader.pages[: min(sample_pages, page_count)]]
        return "pypdf", page_count, texts
    return None


def score_extraction_sample(text: str) -> float:
    text = unicodedata.normalize("NFKC", text)
    if not text.strip():
        return -1000.0
    avg_component = min(len(text.strip()) / 1000.0, 20.0)
    legal_markers = len(ARTICLE_MARKER_RE.findall(text))
    standard_ratio = standard_arabic_letter_ratio(text)
    mark_ratio = arabic_mark_ratio(text)
    score = avg_component + arabic_ratio(text) * 20 + standard_ratio * 35 + min(legal_markers, 60) * 3
    if standard_ratio < 0.70:
        score -= 40
    if mark_ratio > 0.25:
        score -= 30
    return score


def _read_docx_xml_fallback(path: Path) -> str:
    import re
    import zipfile
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")
        root = ET.fromstring(xml)
        texts = [node.text for node in root.iter() if node.tag.endswith("}t") and node.text]
        return "\n".join(texts)
    except Exception:
        return re.sub(r"\s+", " ", path.read_bytes().decode("utf-8", errors="ignore"))
