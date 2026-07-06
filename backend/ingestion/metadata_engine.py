"""Metadata extraction and enrichment engine for legal chunks."""

from __future__ import annotations

import re
from typing import Optional
from backend.utils.arabic_utils import (
    extract_article_number,
    extract_chapter,
    normalize_for_search,
    tokenize_arabic,
    is_arabic,
)
from backend.utils.logging_config import get_logger

logger = get_logger("metadata_engine")

# Legal topic keywords mapping
_TOPIC_KEYWORDS = {
    "criminal law": ["عقوبة", "جريمة", "جناية", "جنحة", "مخالفة", "حبس", "سجن", "غرامة", "متهم", "إدانة"],
    "civil law": ["مدني", "عقد", "التزام", "تعويض", "ملكية", "حيازة", "إيجار", "بيع", "شراء"],
    "procedural law": ["إجراءات", "محاكمة", "دعوى", "استئناف", "تمييز", "طعن", "مرافعة", "تبليغ"],
    "constitutional law": ["دستور", "حقوق", "حريات", "سلطة", "تشريعية", "تنفيذية", "قضائية"],
    "commercial law": ["تجاري", "شركة", "تأسيس", "مساهمة", "تصفية", "إفلاس", "تاجر"],
    "administrative law": ["إداري", "موظف", "وظيفة", "تعيين", "ترقية", "نقل", "فصل"],
    "labor law": ["عمل", "عامل", "أجر", "إجازة", "فصل", "تعويض", "ضمان"],
    "property": ["عقار", "ملكية", "تسجيل", "رهن", "إرث", "وقف", "أرض"],
}


class MetadataEngine:
    """Extract and enrich metadata for legal document chunks."""

    def extract_metadata(self, chunk_text: str, source_file: str = "") -> dict:
        """Extract metadata from a raw chunk text."""
        return {
            "article_number": extract_article_number(chunk_text) or "",
            "chapter": extract_chapter(chunk_text) or "",
            "keywords": self._extract_keywords(chunk_text),
            "legal_topics": self._classify_topics(chunk_text),
            "summary": self._generate_summary(chunk_text),
            "language": "ar" if is_arabic(chunk_text) else "unknown",
            "source_file": source_file,
        }

    def enrich_chunk(self, chunk: dict) -> dict:
        """Enrich a chunk dict with additional metadata."""
        text = chunk.get("chunk_text", "")
        metadata = self.extract_metadata(text, chunk.get("source_file", ""))

        # Merge — don't overwrite existing values
        for key, value in metadata.items():
            if not chunk.get(key):
                chunk[key] = value

        # Build embedding-ready text
        chunk["embedding_ready_text"] = self._build_embedding_text(chunk)
        return chunk

    def _extract_keywords(self, text: str, max_keywords: int = 16) -> list[str]:
        """Extract top keywords from Arabic text."""
        tokens = tokenize_arabic(text)
        if not tokens:
            return []

        # Count word frequencies (skip very short words)
        freq: dict[str, int] = {}
        for token in tokens:
            if len(token) >= 3:
                freq[token] = freq.get(token, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]

    def _classify_topics(self, text: str, max_topics: int = 8) -> list[str]:
        """Classify text into legal topic categories."""
        normalized = normalize_for_search(text)
        topics = []

        for topic, keywords in _TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in normalized)
            if score >= 2:
                topics.append(topic)

        return topics[:max_topics]

    def _generate_summary(self, text: str, max_words: int = 45) -> str:
        """Generate a short summary (extract first meaningful sentence)."""
        text = text.strip()
        if not text:
            return ""

        # Get first sentence or first N words
        sentences = re.split(r'[.،؛\n]', text)
        summary_parts = []
        word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            words = sentence.split()
            if word_count + len(words) > max_words:
                remaining = max_words - word_count
                if remaining > 0:
                    summary_parts.append(" ".join(words[:remaining]) + "...")
                break
            summary_parts.append(sentence)
            word_count += len(words)

        return " ".join(summary_parts) if summary_parts else text[:200] + "..."

    def _build_embedding_text(self, chunk: dict) -> str:
        """Build enriched text for embedding with citation prefix."""
        parts = []

        # Citation header
        book = chunk.get("book_name", "")
        if book:
            parts.append(f"المصدر: {book}")
        page = chunk.get("page_number", "")
        if page:
            parts.append(f"الصفحة: {page}")
        article = chunk.get("article_number", "")
        if article:
            parts.append(f"المادة: {article}")

        parts.append("النص:")
        parts.append(chunk.get("chunk_text", ""))

        # Append keywords and topics for searchability
        keywords = chunk.get("keywords", [])
        topics = chunk.get("legal_topics", [])
        if keywords or topics:
            extra = "مصطلحات وسياق للبحث: "
            extra += "، ".join(keywords + topics)
            parts.append(extra)

        return "\n".join(parts)
