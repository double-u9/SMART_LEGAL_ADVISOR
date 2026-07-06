"""Hierarchical legal chunker — splits on articles, chapters, sections."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional
from backend.utils.arabic_utils import extract_article_number, extract_chapter
from backend.utils.logging_config import get_logger

logger = get_logger("chunker")

# Legal article boundary patterns
_ARTICLE_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:المادة|مادة)\s*[:\-\(]?\s*\d+", re.MULTILINE
)
_CHAPTER_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:الباب|الفصل|القسم)\s+", re.MULTILINE
)


@dataclass
class LegalChunk:
    """A chunk of legal text with metadata."""
    id: str = ""
    chunk_text: str = ""
    book_name: str = ""
    chapter: str = ""
    section: str = ""
    article_number: str = ""
    page_number: str = ""
    page_start: int = 0
    page_end: int = 0
    chunk_index: int = 0
    token_count: int = 0
    previous_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
    source_file: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "chunk_text": self.chunk_text,
            "book_name": self.book_name,
            "chapter": self.chapter,
            "section": self.section,
            "article_number": self.article_number,
            "page_number": self.page_number,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
            "previous_chunk_id": self.previous_chunk_id,
            "next_chunk_id": self.next_chunk_id,
            "source_file": self.source_file,
        }


class LegalChunker:
    """Hierarchical chunker that respects legal document structure."""

    def __init__(
        self,
        min_tokens: int = 500,
        max_tokens: int = 1200,
        overlap_tokens: int = 150,
        hard_max: int = 1500,
    ):
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.hard_max = hard_max

    def chunk_document(
        self,
        text: str,
        book_name: str = "",
        source_file: str = "",
        pages: Optional[list[dict]] = None,
    ) -> list[LegalChunk]:
        """Chunk a legal document respecting article boundaries.

        Args:
            text: Full document text
            book_name: Name of the law book
            source_file: Source file name
            pages: Optional page data for page number mapping
        """
        # First split on article boundaries
        segments = self._split_on_articles(text)

        # Build chunks respecting size limits
        chunks = []
        for segment in segments:
            if self._token_count(segment) <= self.max_tokens:
                chunks.append(segment)
            else:
                # Segment is too large — split further
                sub_chunks = self._split_large_segment(segment)
                chunks.extend(sub_chunks)

        # Merge small chunks
        chunks = self._merge_small_chunks(chunks)

        # Build LegalChunk objects with metadata
        legal_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = self._generate_id(chunk_text)
            article = extract_article_number(chunk_text) or ""
            chapter = extract_chapter(chunk_text) or ""
            page = self._find_page(chunk_text, pages) if pages else ""

            legal_chunks.append(LegalChunk(
                id=chunk_id,
                chunk_text=chunk_text,
                book_name=book_name,
                chapter=chapter,
                article_number=article,
                page_number=str(page),
                chunk_index=i,
                token_count=self._token_count(chunk_text),
                source_file=source_file,
            ))

        # Link chunks (previous/next)
        for i, chunk in enumerate(legal_chunks):
            if i > 0:
                chunk.previous_chunk_id = legal_chunks[i - 1].id
            if i < len(legal_chunks) - 1:
                chunk.next_chunk_id = legal_chunks[i + 1].id

        logger.info(
            "Chunked '%s': %d chunks (avg %d tokens)",
            book_name[:30],
            len(legal_chunks),
            sum(c.token_count for c in legal_chunks) // max(len(legal_chunks), 1),
        )
        return legal_chunks

    def _split_on_articles(self, text: str) -> list[str]:
        """Split text on article boundaries."""
        splits = _ARTICLE_PATTERN.split(text)
        matches = _ARTICLE_PATTERN.findall(text)

        if not matches:
            return [text] if text.strip() else []

        segments = []
        if splits[0].strip():
            segments.append(splits[0].strip())

        for i, match in enumerate(matches):
            idx = i + 1
            if idx < len(splits):
                segment = match + splits[idx]
                if segment.strip():
                    segments.append(segment.strip())

        return segments if segments else [text]

    def _split_large_segment(self, text: str) -> list[str]:
        """Split an oversized segment into smaller chunks with overlap."""
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = min(start + self.max_tokens, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)

            # Move forward with overlap
            start = end - self.overlap_tokens
            if start >= len(words) - self.overlap_tokens:
                break

        return chunks

    def _merge_small_chunks(self, chunks: list[str]) -> list[str]:
        """Merge chunks that are too small with adjacent ones."""
        if not chunks:
            return chunks

        merged = []
        buffer = ""

        for chunk in chunks:
            if not buffer:
                buffer = chunk
                continue

            combined_tokens = self._token_count(buffer + " " + chunk)

            if self._token_count(buffer) < self.min_tokens and combined_tokens <= self.max_tokens:
                buffer = buffer + "\n\n" + chunk
            else:
                merged.append(buffer)
                buffer = chunk

        if buffer:
            merged.append(buffer)

        return merged

    @staticmethod
    def _token_count(text: str) -> int:
        """Approximate token count (words as proxy for Arabic)."""
        return len(text.split())

    @staticmethod
    def _generate_id(text: str) -> str:
        """Generate a stable chunk ID from text content."""
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"chunk_{h}"

    @staticmethod
    def _find_page(chunk_text: str, pages: list[dict]) -> str:
        """Find which page(s) a chunk comes from."""
        if not pages:
            return ""
        # Simple heuristic: check which pages contain the first 50 chars
        snippet = chunk_text[:50]
        for page in pages:
            if snippet in page.get("text", ""):
                return str(page.get("page_number", ""))
        return ""
