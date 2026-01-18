from __future__ import annotations

import hashlib
from pathlib import Path

SUPPORTED_EXTS = (".pdf", ".epub")


def _book_id(path: Path) -> str:
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()


def scan_library(library_path: Path) -> list[dict]:
    items: list[dict] = []
    for file_path in library_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTS:
            continue
        items.append(
            {
                "id": _book_id(file_path),
                "title": file_path.stem,
                "path": str(file_path),
                "ext": file_path.suffix.lower(),
            }
        )
    return sorted(items, key=lambda item: item["title"].lower())
