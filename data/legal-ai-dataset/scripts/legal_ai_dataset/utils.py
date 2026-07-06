from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


def ensure_directories(root: Path, names: Iterable[str]) -> None:
    for name in names:
        (root / name).mkdir(parents=True, exist_ok=True)


def stable_id(*parts: object, prefix: str = "chunk") -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def safe_stem(name: str, max_length: int = 80) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w\u0600-\u06ff.-]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("._ ")
    if not stem:
        stem = stable_id(name, prefix="book")
    return stem[:max_length]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_text_lossless(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1256", "windows-1256", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)

