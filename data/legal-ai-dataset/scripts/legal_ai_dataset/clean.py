from __future__ import annotations

import collections
import re
from pathlib import Path
from typing import Any

from .arabic import normalize_arabic_surface
from .models import PageText
from .utils import safe_stem


STRUCTURAL_LINE_RE = re.compile(r"^\s*(?:المادة|مادة|الباب|الفصل|الكتاب|المبحث|الفرع)\b")


def clean_pages(pages: list[PageText], config: dict[str, Any]) -> list[PageText]:
    cleaning = config["cleaning"]
    normalized = [
        PageText(
            page.source_file,
            page.page_number,
            normalize_arabic_surface(
                page.text,
                unicode_form=cleaning.get("unicode_normalization", "NFKC"),
                remove_tatweel=bool(cleaning.get("remove_tatweel", True)),
                remove_diacritics=bool(cleaning.get("remove_diacritics", False)),
            ),
            page.extraction_method,
            page.ocr_confidence,
            list(page.warnings),
        )
        for page in pages
    ]
    if cleaning.get("remove_repeated_headers_footers", True):
        normalized = remove_repeated_headers_footers(
            normalized,
            min_ratio=float(cleaning.get("repeated_line_min_ratio", 0.30)),
        )
    return [PageText(p.source_file, p.page_number, post_clean_text(p.text), p.extraction_method, p.ocr_confidence, p.warnings) for p in normalized]


def post_clean_text(text: str) -> str:
    # Keep legal punctuation and article numbering. This removes extraction noise only.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"([.،؛:])\1{2,}", r"\1", text)
    text = re.sub(r"[^\S\r\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_repeated_headers_footers(pages: list[PageText], min_ratio: float = 0.30) -> list[PageText]:
    if len(pages) < 3:
        return pages

    candidates: collections.Counter[str] = collections.Counter()
    page_lines: dict[int, list[str]] = {}
    for page in pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        page_lines[page.page_number] = lines
        edge_lines = lines[:4] + lines[-4:]
        seen_on_page: set[str] = set()
        for line in edge_lines:
            key = normalize_repeated_line_key(line)
            if key and key not in seen_on_page:
                candidates[key] += 1
                seen_on_page.add(key)

    threshold = max(3, int(len(pages) * min_ratio))
    repeated = {key for key, count in candidates.items() if count >= threshold}
    if not repeated:
        return pages

    cleaned: list[PageText] = []
    for page in pages:
        kept: list[str] = []
        for line in page.text.splitlines():
            key = normalize_repeated_line_key(line)
            if key in repeated:
                continue
            kept.append(line)
        cleaned.append(PageText(page.source_file, page.page_number, "\n".join(kept), page.extraction_method, page.ocr_confidence, page.warnings))
    return cleaned


def normalize_repeated_line_key(line: str) -> str:
    line = re.sub(r"\d+", "#", line.strip())
    line = re.sub(r"\s+", " ", line)
    if len(line) < 4 or len(line) > 120:
        return ""
    if STRUCTURAL_LINE_RE.match(line):
        return ""
    return line


def write_page_texts(pages: list[PageText], output_dir: Path, compatibility_dir: Path | None = None) -> Path:
    if not pages:
        raise ValueError("Cannot write empty page text list.")
    stem = safe_stem(pages[0].source_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{stem}.txt"
    body = "\n\n".join(f"[PAGE {page.page_number}]\n{page.text}" for page in pages)
    path.write_text(body, encoding="utf-8", newline="\n")
    if compatibility_dir:
        compatibility_dir.mkdir(parents=True, exist_ok=True)
        (compatibility_dir / path.name).write_text(body, encoding="utf-8", newline="\n")
    return path

