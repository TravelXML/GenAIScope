"""File loaders for local file memory."""

from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv"}


def load_file(path: str | Path) -> tuple[str, dict[str, Any]]:
    """Load supported file content as searchable text."""

    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix in {".txt", ".md"}:
        return _read_text(file_path), {"loader": suffix.lstrip("."), "invalid_json": False}
    if suffix == ".json":
        return _load_json(file_path)
    return _load_csv(file_path)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _load_json(path: Path) -> tuple[str, dict[str, Any]]:
    raw = _read_text(path)
    try:
        return json.dumps(json.loads(raw), indent=2, ensure_ascii=False), {
            "loader": "json",
            "invalid_json": False,
        }
    except json.JSONDecodeError:
        return raw, {"loader": "json", "invalid_json": True}


def _load_csv(path: Path) -> tuple[str, dict[str, Any]]:
    raw = _read_text(path)
    output: list[str] = []
    reader = csv.DictReader(StringIO(raw))
    if reader.fieldnames:
        for index, row in enumerate(reader, start=1):
            values = [f"{key}: {value}" for key, value in row.items()]
            output.append(f"Row {index}\n" + "\n".join(values))
    else:
        StringIO(raw).seek(0)
        rows = csv.reader(StringIO(raw))
        output.extend(", ".join(row) for row in rows)
    return "\n\n".join(output) or raw, {"loader": "csv", "invalid_json": False}
