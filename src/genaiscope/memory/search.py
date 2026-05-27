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
        match_type = "exact" if query.lower() in item.content.lower() else "keyword"
        results.append(
            MemorySearchResult(
                item=item,
                score=round(score, 4),
                match_type=match_type,
                matched_terms=matched,
            )
        )

    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]
