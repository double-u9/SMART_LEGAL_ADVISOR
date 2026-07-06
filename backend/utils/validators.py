"""Input validation and security utilities."""

from __future__ import annotations

import re
from backend.utils.logging_config import get_logger

logger = get_logger("validators")

# Known prompt injection patterns
_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions",
    r"disregard\s+(?:all\s+)?(?:previous|above|prior)",
    r"forget\s+(?:everything|all|your\s+instructions)",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*",
    r"<\s*(?:script|system|admin)",
    r"(?:act|behave)\s+as\s+(?:if|though)",
    r"override\s+(?:your|all|the)\s+",
    r"jailbreak",
    r"DAN\s+mode",
]
_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS), re.IGNORECASE | re.DOTALL
)


def detect_prompt_injection(text: str) -> bool:
    """Return True if text contains suspected prompt injection."""
    return bool(_INJECTION_RE.search(text))


def sanitize_input(text: str) -> str:
    """Strip dangerous characters while preserving Arabic text."""
    # Remove null bytes and unusual control chars
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    return text.strip()


def validate_query(text: str, max_length: int = 2000) -> tuple[bool, str]:
    """Validate a user query.

    Returns:
        (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "الاستعلام فارغ. يرجى إدخال سؤال قانوني."

    text = text.strip()

    if len(text) > max_length:
        return False, f"الاستعلام طويل جدًا. الحد الأقصى {max_length} حرف."

    if len(text) < 3:
        return False, "الاستعلام قصير جدًا. يرجى إدخال سؤال أكثر تفصيلاً."

    if detect_prompt_injection(text):
        logger.warning("Prompt injection detected: %s", text[:100])
        return False, "تم رفض الاستعلام لأسباب أمنية."

    return True, ""


def validate_file_upload(filename: str, size_bytes: int, max_mb: int = 50) -> tuple[bool, str]:
    """Validate an uploaded file."""
    allowed_ext = {".pdf", ".docx", ".txt"}
    from pathlib import Path

    ext = Path(filename).suffix.lower()
    if ext not in allowed_ext:
        return False, f"نوع الملف غير مدعوم. الأنواع المسموحة: {', '.join(allowed_ext)}"

    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        return False, f"حجم الملف كبير جدًا. الحد الأقصى {max_mb} ميغابايت."

    return True, ""
