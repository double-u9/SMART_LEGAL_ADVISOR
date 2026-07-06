from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .arabic import normalize_for_search

LEGAL_TOPIC_LEXICON: dict[str, list[str]] = {
    "criminal law": ["عقوبة", "عقوبات", "جريمة", "جرائم", "جناية", "جنحة", "حبس", "سجن", "إعدام", "غرامة", "متهم", "ادعاء", "تحقيق"],
    "civil law": ["مدني", "التزام", "ملكية", "تعويض", "مسؤولية", "دين", "دائن", "مدين", "حق عيني", "حيازة"],
    "constitutional law": ["دستور", "الدستور", "حريات", "حقوق", "سيادة", "رئاسة الجمهورية", "مجلس النواب", "استفتاء"],
    "procedural law": ["دعوى", "الدعوى", "مرافعات", "محكمة", "اختصاص", "استئناف", "تمييز", "طعن", "تبليغ", "إجراءات", "حكم"],
    "contracts": ["عقد", "العقد", "بيع", "إيجار", "مقاولة", "وكالة", "فسخ", "بطلان", "رضا", "أهلية"],
    "evidence": ["إثبات", "بينة", "شهادة", "شهود", "قرينة", "يمين", "دليل", "اعتراف", "خبرة"],
    "companies": ["شركة", "الشركة", "شركات", "مساهم", "أسهم", "رأسمال", "مدير مفوض", "تصفية", "اندماج"],
    "property": ["عقار", "ملكية", "تصرف", "انتفاع", "رهن", "حيازة", "تسجيل عقاري"],
    "family law": ["زواج", "طلاق", "نفقة", "حضانة", "إرث", "وصية", "ميراث"],
    "administrative law": ["إداري", "قرار إداري", "موظف", "وظيفة", "سلطة", "إدارة"],
}

LEGAL_KEYWORDS = sorted({term for terms in LEGAL_TOPIC_LEXICON.values() for term in terms}, key=len, reverse=True)
STOPWORDS = {
    "التي",
    "الذي",
    "ذلك",
    "هذه",
    "هذا",
    "على",
    "الى",
    "إلى",
    "عن",
    "في",
    "من",
    "كل",
    "ولا",
    "كما",
    "اذا",
    "إذا",
    "كان",
    "تكون",
    "يكون",
    "بموجب",
    "القانون",
    "المادة",
}


def enrich_chunk_text(
    *,
    chunk_text: str,
    book_name: str,
    chapter: str,
    section: str,
    article_number: str,
    page_number: str,
    config: dict[str, Any],
) -> tuple[str, list[str], list[str], str]:
    max_keywords = int(config["metadata"].get("max_keywords", 16))
    max_topics = int(config["metadata"].get("max_topics", 8))
    summary = summarize(chunk_text, article_number, int(config["metadata"].get("summary_words", 45)))
    keywords = extract_keywords(chunk_text, max_keywords)
    topics = detect_topics(chunk_text, max_topics)
    embedding_ready = build_embedding_ready_text(
        book_name=book_name,
        chapter=chapter,
        section=section,
        article_number=article_number,
        page_number=page_number,
        chunk_text=chunk_text,
        keywords=keywords,
        topics=topics,
    )
    return summary, keywords, topics, embedding_ready


def summarize(text: str, article_number: str, max_words: int = 45) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return ""
    sentence = re.split(r"(?<=[.؟!])\s+", normalized, maxsplit=1)[0]
    words = sentence.split()
    if len(words) > max_words:
        sentence = " ".join(words[:max_words]) + "..."
    if article_number:
        return f"مقتطف من المادة {article_number}: {sentence}"
    return f"مقتطف قانوني: {sentence}"


def extract_keywords(text: str, max_keywords: int = 16) -> list[str]:
    found: list[str] = []
    search_text = normalize_for_search(text)
    for keyword in LEGAL_KEYWORDS:
        if normalize_for_search(keyword) in search_text and keyword not in found:
            found.append(keyword)
    tokens = re.findall(r"[\u0600-\u06ff]{4,}", text)
    counts = Counter(token for token in tokens if token not in STOPWORDS)
    for token, _ in counts.most_common(max_keywords * 2):
        if token not in found:
            found.append(token)
        if len(found) >= max_keywords:
            break
    return found[:max_keywords]


def detect_topics(text: str, max_topics: int = 8) -> list[str]:
    normalized = normalize_for_search(text)
    scored: list[tuple[str, int]] = []
    for topic, terms in LEGAL_TOPIC_LEXICON.items():
        score = sum(1 for term in terms if normalize_for_search(term) in normalized)
        if score:
            scored.append((topic, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return [topic for topic, _ in scored[:max_topics]]


def build_embedding_ready_text(
    *,
    book_name: str,
    chapter: str,
    section: str,
    article_number: str,
    page_number: str,
    chunk_text: str,
    keywords: list[str],
    topics: list[str],
) -> str:
    citation = [
        f"المصدر: {book_name}",
        f"الصفحة: {page_number}" if page_number else "",
        f"الفصل/الباب: {chapter}" if chapter else "",
        f"القسم: {section}" if section else "",
        f"المادة: {article_number}" if article_number else "",
    ]
    citation_text = "\n".join(part for part in citation if part)
    search_variant = normalize_for_search(chunk_text)
    tags = "، ".join(keywords[:10] + topics[:5])
    return f"{citation_text}\nالنص:\n{chunk_text}\nمصطلحات وسياق للبحث: {tags}\nنص بحثي موحد: {search_variant}"

