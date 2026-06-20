"""Utility helpers for local memory storage."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def default_db_path() -> Path:
    """Return the default local memory database path."""

    return Path(".genaiscope") / "memory.db"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def iso_now() -> str:
    """Return the current UTC timestamp as ISO text."""

    return utc_now().isoformat()


def parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO datetime, returning None for blank or invalid values."""

    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def json_dumps(value: Any) -> str:
    """Serialize JSON values consistently."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_loads(value: str | None, default: Any) -> Any:
    """Deserialize JSON with a defensive fallback."""

    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def normalize_memory_type(memory_type: str) -> str:
    """Normalize user-provided memory type text."""

    normalized = memory_type.strip().lower().replace(" ", "_")
    return normalized or "general"


def normalize_tags(tags: list[str] | None) -> list[str]:
    """Normalize tag lists by trimming, lowercasing, and deduplicating."""

    if not tags:
        return []
    seen: set[str] = set()
    normalized: list[str] = []
    for tag in tags:
        clean = tag.strip().lower()
        if clean and clean not in seen:
            seen.add(clean)
            normalized.append(clean)
    return normalized


def ensure_parent(path: Path) -> None:
    """Create the parent directory for a path."""

    path.parent.mkdir(parents=True, exist_ok=True)


def estimate_tokens(text: str) -> int:
    """Zero-dependency token estimate (~4 chars per token, no tiktoken)."""

    return max(1, len(text) // 4)
