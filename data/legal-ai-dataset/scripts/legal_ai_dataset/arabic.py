from __future__ import annotations

import re
import unicodedata

ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
STANDARD_ARABIC_RANGES = (
    (0x0621, 0x064A),
    (0x0671, 0x0671),
    (0x06A9, 0x06A9),
    (0x06AF, 0x06AF),
    (0x06C1, 0x06C1),
    (0x06CC, 0x06CC),
)
DIACRITICS_RE = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
CONTROL_RE = re.compile(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]")
BIDI_MARKS_RE = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")
TATWEEL = "\u0640"

ALEF_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا"})
YAA_MAP = str.maketrans({"ى": "ي", "ئ": "ي"})
TEH_MARBUTA_MAP = str.maketrans({"ة": "ه"})
ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalize_arabic_surface(
    text: str,
    *,
    unicode_form: str = "NFKC",
    remove_tatweel: bool = True,
    remove_diacritics: bool = False,
) -> str:
    """Light cleanup for legal text display without erasing legal distinctions."""

    text = unicodedata.normalize(unicode_form, text)
    text = CONTROL_RE.sub(" ", text)
    text = BIDI_MARKS_RE.sub("", text)
    text = text.replace("\ufeff", "")
    if remove_tatweel:
        text = text.replace(TATWEEL, "")
    if remove_diacritics:
        text = DIACRITICS_RE.sub("", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_for_search(text: str) -> str:
    """Stronger normalization used only inside embedding/search helper fields."""

    text = normalize_arabic_surface(text, remove_diacritics=True)
    text = text.translate(ALEF_MAP)
    text = text.translate(YAA_MAP)
    text = text.translate(ARABIC_INDIC_DIGITS)
    text = re.sub(r"[^\w\s\u0600-\u06ff/.-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def arabic_ratio(text: str) -> float:
    nonspace = [char for char in text if not char.isspace()]
    if not nonspace:
        return 0.0
    return sum(1 for char in nonspace if ARABIC_RE.match(char)) / len(nonspace)


def is_standard_arabic_letter(char: str) -> bool:
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in STANDARD_ARABIC_RANGES)


def standard_arabic_letter_ratio(text: str) -> float:
    arabic_chars = [char for char in text if ARABIC_RE.match(char)]
    if not arabic_chars:
        return 0.0
    return sum(1 for char in arabic_chars if is_standard_arabic_letter(char)) / len(arabic_chars)


def arabic_mark_ratio(text: str) -> float:
    arabic_chars = [char for char in text if ARABIC_RE.match(char)]
    if not arabic_chars:
        return 0.0
    marks = sum(1 for char in arabic_chars if unicodedata.category(char).startswith("M"))
    return marks / len(arabic_chars)


def corruption_score(text: str) -> float:
    if not text:
        return 1.0
    suspicious = sum(text.count(char) for char in ("�", "□", "■", "\ufffd"))
    suspicious += len(re.findall(r"[^\S\r\n]{6,}", text))
    return min(1.0, suspicious / max(len(text), 1))


def compact_for_hash(text: str) -> str:
    text = normalize_for_search(text).lower()
    return re.sub(r"\s+", " ", text).strip()
