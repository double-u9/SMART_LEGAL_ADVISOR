"""Citation extraction and formatting engine for Arabic legal references."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
from backend.utils.logging_config import get_logger

logger = get_logger("citations")


@dataclass
class Citation:
    """Structured legal citation."""
    book_name: str = ""
    chapter: str = ""
    article_number: str = ""
    page_number: str = ""
    relevant_text: str = ""
    confidence: float = 0.0
    chunk_id: str = ""
    source_file: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def format_arabic(self) -> str:
        """Format citation in professional Arabic legal style."""
        parts = []
        if self.book_name:
            parts.append(f"📖 المصدر: {self.book_name}")
        if self.article_number:
            parts.append(f"📌 المادة: {self.article_number}")
        if self.chapter:
            parts.append(f"📂 الباب/الفصل: {self.chapter}")
        if self.page_number:
            parts.append(f"📄 الصفحة: {self.page_number}")
        return " | ".join(parts) if parts else "مصدر غير محدد"


class CitationEngine:
    """Extracts and manages citations from retrieved legal chunks."""

    def extract_citations(self, chunks: list[dict]) -> list[Citation]:
        """Extract structured citations from retrieved chunks."""
        citations = []
        seen = set()

        for chunk in chunks:
            payload = chunk.get("payload", {})

            citation = Citation(
                book_name=payload.get("book_name", ""),
                chapter=payload.get("chapter", "") or payload.get("section", ""),
                article_number=str(payload.get("article_number", "")),
                page_number=str(payload.get("page_number", payload.get("page_start", ""))),
                relevant_text=self._extract_relevant_text(payload),
                confidence=float(chunk.get("rerank_score", chunk.get("hybrid_score", chunk.get("score", 0)))),
                chunk_id=payload.get("id", payload.get("chunk_id", "")),
                source_file=payload.get("source_file", ""),
            )

            # Deduplicate by book + article
            dedup_key = f"{citation.book_name}:{citation.article_number}:{citation.page_number}"
            if dedup_key not in seen:
                seen.add(dedup_key)
                citations.append(citation)

        logger.info("Extracted %d unique citations from %d chunks", len(citations), len(chunks))
        return citations

    def _extract_relevant_text(self, payload: dict) -> str:
        """Extract the most relevant text excerpt for citation display.

        Priority order:
        1. chunk_text (the actual legal text content)
        2. embedding_ready_text (has citation headers + text)
        3. summary (auto-generated summary)
        """
        # Use chunk_text as the primary source — it's the actual legal content
        chunk_text = payload.get("chunk_text", "")
        embedding_text = payload.get("embedding_ready_text", "")

        # Pick the best available text
        text = chunk_text or embedding_text
        if not text:
            return ""

        # Clean up the text for display
        return text.strip()

    def format_context_for_llm(self, citations: list[Citation]) -> str:
        """Format citations as context block for the LLM prompt.

        Provides rich context with full legal text and clear source attribution.
        """
        if not citations:
            return "لا توجد مصادر قانونية متاحة."

        blocks = []
        for i, c in enumerate(citations, 1):
            block = f"【المصدر {i}】\n"
            block += f"الكتاب: {c.book_name}\n"
            if c.article_number:
                block += f"المادة: {c.article_number}\n"
            if c.chapter:
                block += f"الباب/الفصل: {c.chapter}\n"
            if c.page_number:
                block += f"الصفحة: {c.page_number}\n"
            block += f"النص:\n{c.relevant_text}\n"
            blocks.append(block)

        return "\n---\n".join(blocks)

    def deduplicate(self, citations: list[Citation]) -> list[Citation]:
        """Remove duplicate citations based on content similarity."""
        seen_keys = set()
        unique = []
        for c in citations:
            key = f"{c.book_name}|{c.article_number}|{c.page_number}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique.append(c)
        return unique
