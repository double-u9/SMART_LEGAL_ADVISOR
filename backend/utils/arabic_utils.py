"""Arabic text utilities for normalization, search, and quality scoring."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


# ── Arabic character ranges & maps ────────────────────────────────────
_ALEF_VARIANTS = re.compile(r"[\u0622\u0623\u0625\u0671]")  # آ أ إ ٱ
_YAA_VARIANT = re.compile(r"\u0649")  # ى → ي
_TATWEEL = re.compile(r"\u0640+")
_DIACRITICS = re.compile(
    r"[\u064B-\u065F\u0670\u06D6-\u06ED\u08D3-\u08E1\u08E3-\u08FF]"
)
_ARABIC_LETTER = re.compile(r"[\u0600-\u06FF]")
_STANDARD_ARABIC = re.compile(r"[\u0621-\u064A]")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]")
_MULTI_SPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


def normalize_alef(text: str) -> str:
    """Normalize all alef variants (أ إ آ ٱ) to bare alef (ا)."""
    return _ALEF_VARIANTS.sub("\u0627", text)


def normalize_yaa(text: str) -> str:
    """Normalize alef-maqsura (ى) to yaa (ي)."""
    return _YAA_VARIANT.sub("\u064A", text)


def remove_tatweel(text: str) -> str:
    """Remove Arabic tatweel / kashida (ـ)."""
    return _TATWEEL.sub("", text)


def remove_diacritics(text: str) -> str:
    """Remove Arabic diacritical marks (tashkeel)."""
    return _DIACRITICS.sub("", text)


def normalize_unicode(text: str) -> str:
    """Apply NFKC normalization and remove control characters."""
    text = unicodedata.normalize("NFKC", text)
    text = _CONTROL_CHARS.sub("", text)
    return text


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs and excessive newlines."""
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def normalize_for_search(text: str) -> str:
    """Full normalization pipeline for search & embedding.

    Normalizes alef, yaa, removes tatweel/diacritics, collapses whitespace.
    This produces a canonical form for matching.
    """
    text = normalize_unicode(text)
    text = normalize_alef(text)
    text = normalize_yaa(text)
    text = remove_tatweel(text)
    text = remove_diacritics(text)
    text = normalize_whitespace(text)
    return text


def normalize_for_display(text: str) -> str:
    """Lighter normalization that preserves diacritics for display."""
    text = normalize_unicode(text)
    text = remove_tatweel(text)
    text = normalize_whitespace(text)
    return text


def is_arabic(text: str) -> bool:
    """Check if the majority of alphabetic characters are Arabic."""
    if not text:
        return False
    arabic_count = len(_ARABIC_LETTER.findall(text))
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count == 0:
        return False
    return (arabic_count / alpha_count) > 0.5


def standard_arabic_letter_ratio(text: str) -> float:
    """Ratio of standard Arabic letters to total characters."""
    if not text:
        return 0.0
    std = len(_STANDARD_ARABIC.findall(text))
    total = len(text.replace(" ", "").replace("\n", ""))
    return std / max(total, 1)


def arabic_corruption_score(text: str) -> float:
    """Score how likely the text is corrupted/garbled (0 = clean, 1 = garbage).

    Uses heuristics: low Arabic ratio, high non-printable chars, etc.
    """
    if not text or len(text) < 10:
        return 0.0

    ratio = standard_arabic_letter_ratio(text)
    non_print = sum(1 for c in text if not c.isprintable() and c not in "\n\r\t")
    non_print_ratio = non_print / max(len(text), 1)

    # A good Arabic legal text has >40% standard Arabic letters
    corruption = max(0.0, 1.0 - (ratio / 0.4))
    corruption = min(1.0, corruption + non_print_ratio * 2)
    return round(corruption, 3)


def tokenize_arabic(text: str) -> list[str]:
    """Simple Arabic-aware tokenizer for BM25: split on whitespace & punctuation."""
    text = normalize_for_search(text)
    tokens = re.split(r"[\s\u060C\u061B\u061F.,;:!?()\[\]{}\-/\\\"\']+", text)
    return [t for t in tokens if t and len(t) > 1]


def extract_article_number(text: str) -> Optional[str]:
    """Try to extract an article number from Arabic legal text."""
    patterns = [
        r"(?:المادة|مادة)\s*[:\-]?\s*(\d+)",
        r"(?:المادة|مادة)\s*\((\d+)\)",
        r"(?:م|مادة)(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None


def extract_chapter(text: str) -> Optional[str]:
    """Try to extract chapter/section from Arabic legal text."""
    patterns = [
        r"(?:الباب|باب)\s*(?:ال)?(\S+)",
        r"(?:الفصل|فصل)\s*(?:ال)?(\S+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None
