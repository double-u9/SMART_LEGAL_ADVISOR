from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "input": {
        "recursive": True,
        "extensions": [".pdf", ".docx", ".txt"],
    },
    "extraction": {
        "prefer_pdf_extractors": ["pymupdf", "pdfplumber", "pypdf"],
        "sample_pages_for_analysis": 5,
        "min_text_chars_per_page": 80,
        "scanned_avg_chars_threshold": 50,
        "ocr": {
            "enabled": "auto",
            "engine_order": ["tesseract", "easyocr"],
            "languages": ["ara", "eng"],
            "render_dpi": 300,
            "min_confidence": 45.0,
        },
    },
    "cleaning": {
        "unicode_normalization": "NFKC",
        "remove_tatweel": True,
        "remove_diacritics": False,
        "normalize_alef_for_embeddings": True,
        "normalize_yaa_for_embeddings": True,
        "remove_repeated_headers_footers": True,
        "repeated_line_min_ratio": 0.30,
    },
    "chunking": {
        "target_min_tokens": 500,
        "target_max_tokens": 1200,
        "overlap_tokens": 150,
        "hard_max_tokens": 1500,
    },
    "metadata": {
        "language": "ar",
        "summary_words": 45,
        "max_keywords": 16,
        "max_topics": 8,
    },
    "quality": {
        "min_arabic_ratio": 0.20,
        "duplicate_similarity_hash": "normalized_exact",
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    if not path:
        return config

    config_path = Path(path)
    if not config_path.exists():
        return config

    if config_path.suffix.lower() == ".json":
        import json

        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        return _deep_merge(config, loaded)

    try:
        import yaml  # type: ignore
    except ImportError:
        # Keep the pipeline runnable in minimal environments. requirements.txt
        # installs PyYAML for production runs that rely on editable YAML config.
        return config

    loaded_yaml = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded_yaml, dict):
        return config
    return _deep_merge(config, loaded_yaml)

