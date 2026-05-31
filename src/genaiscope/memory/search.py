"""Lightweight local memory search."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from genaiscope.memory.models import MemoryItem, MemorySearchResult

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "how",
    "is",
    "of",
    "or",
    "the",
    "to",
    "what",
    "with",
}


def tokenize(text: str) -> list[str]:
    """Tokenize text for local keyword scoring."""

    return [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS]


def score_memory(query: str, content: str, tags: list[str]) -> tuple[float, list[str]]:
    """Score one memory using substring, token overlap, and tag boosts."""

    query_clean = query.strip().lower()
    content_clean = content.lower()
    query_tokens = tokenize(query)
    content_tokens = set(tokenize(content))
    tag_tokens = {tag.lower() for tag in tags}
    matched = sorted(
        {token for token in query_tokens if token in content_tokens or token in tag_tokens}
    )

    if not query_clean or not query_tokens:
        return 0.0, []

    score = 0.0
    if query_clean in content_clean:
        score += 2.5
    overlap = len({token for token in query_tokens if token in content_tokens})
    score += overlap / max(len(set(query_tokens)), 1)
    score += len({token for token in query_tokens if token in tag_tokens}) * 0.35
    return score, matched


def search_memories(
    memories: list[MemoryItem],
    query: str,
    *,
    limit: int = 10,
    mode: str = "hybrid",
    requested_scopes: dict[str, str | None] | None = None,
    memory_type: str | None = None,
) -> list[MemorySearchResult]:
    """Search memory items and return ranked results."""

    if not query.strip():
        return []

    now = datetime.now(UTC)
    results: list[MemorySearchResult] = []
    for item in memories:
        score, matched = score_memory(query, item.content, item.tags)
        if score <= 0:
            continue
        if mode == "hybrid":
            age_days = max((now - item.created_at).days, 0)
            score += max(0.0, 0.25 - min(age_days, 30) / 120)
            score += max(item.importance - 5, 0) * 0.05
            if memory_type and item.memory_type == memory_type:
                score += 0.15
            matched_scopes = [
                name
                for name, value in (requested_scopes or {}).items()
                if value is not None and getattr(item, name) == value
            ]
            score += len(matched_scopes) * 0.1
        else:
            matched_scopes = []
        match_type = "exact" if query.lower() in item.content.lower() else "keyword"
        reasons = [f"Matched query terms: {', '.join(matched) or 'phrase'}."]
        boosts = matched_scopes + (["importance"] if item.importance > 5 else [])
        if boosts:
            reasons.append(f"Boosted by {', '.join(boosts)}.")
        results.append(
            MemorySearchResult(
                item=item,
                score=round(score, 4),
                match_type=match_type,
                matched_terms=matched,
                ranking_reason=" ".join(reasons),
            )
        )

    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]
