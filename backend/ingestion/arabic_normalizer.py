"""Arabic text normalizer — preserves original for citations, normalizes for search."""

from __future__ import annotations

from backend.utils.arabic_utils import (
    normalize_unicode,
    normalize_alef,
    normalize_yaa,
    remove_tatweel,
    remove_diacritics,
    normalize_whitespace,
)
from backend.utils.logging_config import get_logger

logger = get_logger("arabic_normalizer")


class ArabicNormalizer:
    """Arabic text normalization with dual-output: display & search versions."""

    def normalize(self, text: str) -> str:
        """Light normalization — keeps diacritics, fixes encoding issues."""
        text = normalize_unicode(text)
        text = remove_tatweel(text)
        text = normalize_whitespace(text)
        return text

    def normalize_for_embedding(self, text: str) -> str:
        """Full normalization for embedding — alef/yaa normalized, no diacritics."""
        text = normalize_unicode(text)
        text = normalize_alef(text)
        text = normalize_yaa(text)
        text = remove_tatweel(text)
        text = remove_diacritics(text)
        text = normalize_whitespace(text)
        return text

    def normalize_for_search(self, text: str) -> str:
        """Maximum normalization for keyword matching."""
        return self.normalize_for_embedding(text)

    def normalize_dual(self, text: str) -> tuple[str, str]:
        """Return both display and search versions.

        Returns:
            (display_text, search_text)
        """
        display = self.normalize(text)
        search = self.normalize_for_embedding(text)
        return display, search
