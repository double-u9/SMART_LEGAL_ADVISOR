from __future__ import annotations

import re
from dataclasses import replace
from typing import Any, Iterable

from .enrich import enrich_chunk_text
from .models import LegalChunk, LegalUnit, PageText, book_name_from_path
from .utils import stable_id

ARTICLE_RE = re.compile(r"^\s*(?:المادة|مادة)\s*[\(:\-]?\s*([0-9٠-٩۰-۹]+(?:\s*(?:/|-|مكرر)\s*[0-9٠-٩۰-۹]+)?)", re.MULTILINE)
CHAPTER_RE = re.compile(r"^\s*((?:الكتاب|الباب|الفصل|المبحث|الفرع)\s+[^\n]{1,120})", re.MULTILINE)
SECTION_RE = re.compile(r"^\s*((?:القسم|المطلب)\s+[^\n]{1,120})", re.MULTILINE)


class TokenCounter:
    def __init__(self) -> None:
        self._encoding = None
        try:
            import tiktoken  # type: ignore

            self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoding = None

    def count(self, text: str) -> int:
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


class LegalChunker:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.counter = TokenCounter()
        chunking = config["chunking"]
        self.target_min = int(chunking.get("target_min_tokens", 500))
        self.target_max = int(chunking.get("target_max_tokens", 1200))
        self.overlap = int(chunking.get("overlap_tokens", 150))
        self.hard_max = int(chunking.get("hard_max_tokens", 1500))

    def chunk_book(self, pages: list[PageText], source_file: str) -> list[LegalChunk]:
        if not pages:
            return []
        units = self._build_units(pages, source_file)
        chunks: list[LegalChunk] = []
        buffer: list[LegalUnit] = []
        buffer_tokens = 0

        for unit in units:
            unit_tokens = self.counter.count(unit.text)
            if unit_tokens > self.hard_max:
                if buffer:
                    chunks.append(self._make_chunk(buffer, source_file, len(chunks)))
                    buffer, buffer_tokens = [], 0
                for split_unit in self._split_large_unit(unit):
                    chunks.append(self._make_chunk([split_unit], source_file, len(chunks)))
                continue

            would_exceed = buffer and buffer_tokens + unit_tokens > self.target_max
            if would_exceed and buffer_tokens >= self.target_min:
                chunks.append(self._make_chunk(buffer, source_file, len(chunks)))
                buffer, buffer_tokens = [], 0

            buffer.append(unit)
            buffer_tokens += unit_tokens

        if buffer:
            chunks.append(self._make_chunk(buffer, source_file, len(chunks)))

        for index, chunk in enumerate(chunks):
            chunk.previous_chunk_id = chunks[index - 1].id if index > 0 else ""
            chunk.next_chunk_id = chunks[index + 1].id if index + 1 < len(chunks) else ""
        return chunks

    def _build_units(self, pages: list[PageText], source_file: str) -> list[LegalUnit]:
        book_name = book_name_from_path(source_file)
        units: list[LegalUnit] = []
        current = LegalUnit(book_name=book_name, source_file=source_file)
        current_chapter = ""
        current_section = ""

        def flush() -> None:
            nonlocal current
            current.text = "\n".join(line for line in current.text.splitlines() if line.strip()).strip()
            if current.text:
                units.append(current)
            current = LegalUnit(book_name=book_name, source_file=source_file, chapter=current_chapter, section=current_section)

        for page in pages:
            blocks = self._paragraph_blocks(page.text)
            for block in blocks:
                chapter_match = CHAPTER_RE.match(block)
                section_match = SECTION_RE.match(block)
                article_match = ARTICLE_RE.match(block)
                if chapter_match:
                    current_chapter = chapter_match.group(1).strip()
                    if current.text and not current.article_number:
                        current.chapter = current_chapter
                    elif current.text:
                        flush()
                    continue
                if section_match:
                    current_section = section_match.group(1).strip()
                    if current.text and not current.article_number:
                        current.section = current_section
                    elif current.text:
                        flush()
                    continue
                if article_match:
                    if current.text:
                        flush()
                    current.article_number = article_match.group(1).strip()
                    current.chapter = current_chapter
                    current.section = current_section
                    current.page_start = page.page_number

                if current.page_start is None:
                    current.page_start = page.page_number
                current.page_end = page.page_number
                current.extraction_method = page.extraction_method
                if page.ocr_confidence is not None:
                    current.ocr_confidence = page.ocr_confidence
                current.text = f"{current.text}\n\n{block}".strip()

        if current.text:
            flush()
        return units

    @staticmethod
    def _paragraph_blocks(text: str) -> list[str]:
        blocks = [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]
        if len(blocks) <= 1:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return lines
        return blocks

    def _split_large_unit(self, unit: LegalUnit) -> Iterable[LegalUnit]:
        paragraphs = self._paragraph_blocks(unit.text)
        if len(paragraphs) <= 1:
            yield from self._split_by_words(unit)
            return

        buffer: list[str] = []
        buffer_tokens = 0
        for paragraph in paragraphs:
            paragraph_tokens = self.counter.count(paragraph)
            if buffer and buffer_tokens + paragraph_tokens > self.target_max:
                yield replace(unit, text="\n\n".join(buffer))
                overlap_buffer = self._paragraph_overlap(buffer)
                buffer = overlap_buffer[:]
                buffer_tokens = self.counter.count("\n\n".join(buffer))
            buffer.append(paragraph)
            buffer_tokens += paragraph_tokens
        if buffer:
            yield replace(unit, text="\n\n".join(buffer))

    def _paragraph_overlap(self, paragraphs: list[str]) -> list[str]:
        selected: list[str] = []
        total = 0
        for paragraph in reversed(paragraphs):
            tokens = self.counter.count(paragraph)
            if total + tokens > self.overlap and selected:
                break
            selected.insert(0, paragraph)
            total += tokens
        return selected

    def _split_by_words(self, unit: LegalUnit) -> Iterable[LegalUnit]:
        words = unit.text.split()
        if not words:
            return
        start = 0
        while start < len(words):
            end = min(len(words), start + self.target_max)
            yield replace(unit, text=" ".join(words[start:end]))
            if end >= len(words):
                break
            start = max(end - self.overlap, start + 1)

    def _make_chunk(self, units: list[LegalUnit], source_file: str, chunk_index: int) -> LegalChunk:
        first = units[0]
        last = units[-1]
        text = "\n\n".join(unit.text for unit in units).strip()
        page_start = min(unit.page_start or 0 for unit in units) or None
        page_end = max(unit.page_end or 0 for unit in units) or None
        if page_start and page_end and page_start != page_end:
            page_number = f"{page_start}-{page_end}"
        elif page_start:
            page_number = str(page_start)
        else:
            page_number = ""
        article_numbers = [unit.article_number for unit in units if unit.article_number]
        article_number = article_numbers[0] if len(set(article_numbers)) == 1 else ", ".join(article_numbers[:8])
        token_count = self.counter.count(text)
        chunk_id = stable_id(source_file, chunk_index, page_number, article_number, text[:160])
        summary, keywords, topics, embedding_ready = enrich_chunk_text(
            chunk_text=text,
            book_name=first.book_name,
            chapter=first.chapter or last.chapter,
            section=first.section or last.section,
            article_number=article_number,
            page_number=page_number,
            config=self.config,
        )
        extraction_methods = sorted({getattr(unit, "extraction_method", "") for unit in units if getattr(unit, "extraction_method", "")})
        confidences = [unit.ocr_confidence for unit in units if unit.ocr_confidence is not None]
        return LegalChunk(
            id=chunk_id,
            book_name=first.book_name,
            chapter=first.chapter or last.chapter,
            section=first.section or last.section,
            article_number=article_number,
            page_number=page_number,
            language=self.config["metadata"].get("language", "ar"),
            chunk_text=text,
            summary=summary,
            keywords=keywords,
            legal_topics=topics,
            embedding_ready_text=embedding_ready,
            source_file=source_file,
            token_count=token_count,
            chunk_index=chunk_index,
            previous_chunk_id="",
            next_chunk_id="",
            page_start=page_start,
            page_end=page_end,
            extraction_method=", ".join(extraction_methods),
            ocr_confidence=(sum(confidences) / len(confidences)) if confidences else None,
        )
