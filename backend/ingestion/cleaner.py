"""Text cleaning pipeline — headers/footers removal, whitespace normalization."""

from __future__ import annotations

import re
from collections import Counter
from backend.utils.arabic_utils import normalize_unicode, normalize_whitespace
from backend.utils.logging_config import get_logger

logger = get_logger("cleaner")


class TextCleaner:
    """Clean extracted text while preserving legal content."""

    HEADER_FOOTER_RATIO = 0.30  # Line appears in >30% of pages = header/footer

    def clean(self, text: str) -> str:
        """Full cleaning pipeline for a single text block."""
        text = normalize_unicode(text)
        text = self._remove_page_numbers(text)
        text = self._remove_control_chars(text)
        text = normalize_whitespace(text)
        return text

    def clean_pages(self, pages: list[dict]) -> list[dict]:
        """Clean a list of page dicts and remove repeated headers/footers."""
        if not pages:
            return pages

        # Detect repeated headers/footers
        repeated = self._detect_repeated_lines(pages)

        cleaned = []
        for page in pages:
            text = page.get("text", "")
            text = normalize_unicode(text)

            # Remove repeated header/footer lines
            lines = text.split("\n")
            filtered_lines = [
                line for line in lines
                if line.strip() and line.strip() not in repeated
            ]
            text = "\n".join(filtered_lines)

            text = self._remove_page_numbers(text)
            text = self._remove_control_chars(text)
            text = normalize_whitespace(text)

            cleaned.append({**page, "text": text, "char_count": len(text)})

        removed_count = len(repeated)
        if removed_count:
            logger.info("Removed %d repeated header/footer patterns", removed_count)

        return cleaned

    def _detect_repeated_lines(self, pages: list[dict]) -> set[str]:
        """Find lines that repeat across many pages (likely headers/footers)."""
        line_counts: Counter = Counter()
        total_pages = len(pages)

        for page in pages:
            text = page.get("text", "")
            lines = text.split("\n")
            # Check first 3 and last 3 lines of each page
            check_lines = lines[:3] + lines[-3:]
            seen_in_page = set()
            for line in check_lines:
                stripped = line.strip()
                if stripped and len(stripped) > 3 and stripped not in seen_in_page:
                    seen_in_page.add(stripped)
                    line_counts[stripped] += 1

        threshold = max(3, int(total_pages * self.HEADER_FOOTER_RATIO))
        return {line for line, count in line_counts.items() if count >= threshold}

    def _remove_page_numbers(self, text: str) -> str:
        """Remove standalone page numbers."""
        # Match lines that are just a number (page numbers)
        text = re.sub(r"^\s*-?\s*\d{1,4}\s*-?\s*$", "", text, flags=re.MULTILINE)
        return text

    def _remove_control_chars(self, text: str) -> str:
        """Remove non-printable control characters (keep Arabic, newlines, spaces)."""
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
