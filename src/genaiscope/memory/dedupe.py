"""Memory duplicate detection and cleanup."""

from __future__ import annotations

import re
from typing import Any

from genaiscope.memory.base import BaseMemoryStore
from genaiscope.memory.models import MemoryItem
from genaiscope.memory.search import tokenize


def _normalized(content: str) -> str:
    return re.sub(r"\s+", " ", content.strip().lower())


def _similar(left: MemoryItem, right: MemoryItem) -> bool:
    if left.memory_type != right.memory_type:
        return False
    if any(getattr(left, field) != getattr(right, field) for field in ("user_id", "project_id", "workspace_id")):
        return False
    if _normalized(left.content) == _normalized(right.content):
        return True
    left_tokens, right_tokens = set(tokenize(left.content)), set(tokenize(right.content))
    return bool(left_tokens and right_tokens) and len(left_tokens & right_tokens) / len(left_tokens | right_tokens) >= 0.9


def find_duplicates(store: BaseMemoryStore, user_id: str | None = None, project_id: str | None = None) -> list[list[MemoryItem]]:
    """Return groups of duplicate memories."""

    items = store.list(user_id=user_id, project_id=project_id, limit=100000)
    groups: list[list[MemoryItem]] = []
    consumed: set[str] = set()
    for item in items:
        if item.id in consumed:
            continue
        group = [candidate for candidate in items if candidate.id not in consumed and _similar(item, candidate)]
        if len(group) > 1:
            groups.append(group)
            consumed.update(candidate.id for candidate in group)
    return groups


def dedupe_memories(store: BaseMemoryStore, strategy: str = "keep_newest", dry_run: bool = True) -> dict[str, Any]:
    """Delete redundant memories according to a deterministic strategy."""

    strategies = {
        "keep_newest": lambda item: item.created_at,
        "keep_oldest": lambda item: item.created_at,
        "keep_highest_importance": lambda item: item.importance,
    }
    if strategy not in strategies:
        raise ValueError(f"Unknown dedupe strategy: {strategy}")
    deleted: list[str] = []
    for group in find_duplicates(store):
        reverse = strategy != "keep_oldest"
        ordered = sorted(group, key=strategies[strategy], reverse=reverse)
        for item in ordered[1:]:
            deleted.append(item.id)
            if not dry_run:
                store.delete(item.id)
    return {"strategy": strategy, "dry_run": dry_run, "duplicates_removed": len(deleted), "memory_ids": deleted}
