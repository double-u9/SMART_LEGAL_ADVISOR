from legal_ai_dataset.chunk import LegalChunker
from legal_ai_dataset.config import DEFAULT_CONFIG
from legal_ai_dataset.models import PageText


def test_chunker_preserves_article_numbers_and_pages() -> None:
    pages = [
        PageText(
            source_file="book.pdf",
            page_number=1,
            extraction_method="test",
            text="الباب الاول\n\nالمادة 1\nهذا نص قانوني عن الدعوى والاختصاص.\n\nالمادة 2\nهذا نص قانوني آخر عن المحكمة والطعن.",
        )
    ]
    config = DEFAULT_CONFIG.copy()
    config["chunking"] = {**DEFAULT_CONFIG["chunking"], "target_min_tokens": 1, "target_max_tokens": 100}
    chunks = LegalChunker(config).chunk_book(pages, "book.pdf")
    assert chunks
    assert chunks[0].article_number
    assert chunks[0].page_number == "1"
    assert "المادة 1" in chunks[0].chunk_text

