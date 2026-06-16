"""Memory search — keyword, vector, and fused hybrid modes."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from genaiscope.memory.models import MemoryItem, MemorySearchResult

if TYPE_CHECKING:
    from genaiscope.embeddings.base import BaseEmbedder
    from genaiscope.vector.base import BaseVectorStore

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
STOPWORDS = {
    "a", "an", "and", "are", "for", "how", "is", "of", "or", "the", "to", "what", "with",
}


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOPWORDS]


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


def _l2_norm(score: float, max_score: float) -> float:
    return score / max_score if max_score > 0 else 0.0


def search_memories(
    memories: list[MemoryItem],
    query: str,
    *,
    limit: int = 10,
    mode: str = "hybrid",
    requested_scopes: dict[str, str | None] | None = None,
    memory_type: str | None = None,
    embedder: BaseEmbedder | None = None,
    vector_store: BaseVectorStore | None = None,
    alpha: float = 0.5,
) -> list[MemorySearchResult]:
    """Search memory items and return ranked results.

    mode="keyword"  -> deterministic keyword scoring (v0.3.0 behaviour)
    mode="vector"   -> embedding cosine similarity only
    mode="hybrid"   -> fused keyword + vector scores with boosts
    """

    if not query.strip():
        return []

    now = datetime.now(UTC)
    embedder_name = embedder.name if embedder else "none"

    # ---------- keyword scores ----------
    kw_raw: dict[str, tuple[float, list[str]]] = {}
    for item in memories:
        raw, matched = score_memory(query, item.content, item.tags)
        kw_raw[item.id] = (raw, matched)

    max_kw = max((v[0] for v in kw_raw.values()), default=0.0)

    # ---------- vector scores ----------
    vec_scores: dict[str, float] = {}
    if mode in ("vector", "hybrid") and embedder and vector_store:
        try:
            q_vec = embedder.embed(query)
            scope_filters: dict[str, Any] = {}
            for key, val in (requested_scopes or {}).items():
                if val is not None:
                    scope_filters[key] = val
            matches = vector_store.query(q_vec, top_k=len(memories) or 1000, filters=scope_filters if scope_filters else None)
            vec_scores = {m.vector_id: m.score for m in matches}
        except Exception:
            pass

    # ---------- fuse and rank ----------
    results: list[MemorySearchResult] = []
    for item in memories:
        raw_kw, matched = kw_raw[item.id]
        kw_norm = _l2_norm(raw_kw, max_kw)
        vec_norm = max(0.0, min(1.0, vec_scores.get(item.id, 0.0)))

        if mode == "keyword":
            if raw_kw <= 0:
                continue
            final_score = raw_kw
            fused = raw_kw
            match_type = "exact" if query.lower() in item.content.lower() else "keyword"
            reasons = [f"Matched query terms: {', '.join(matched) or 'phrase'}."]
            matched_scopes: list[str] = []
        elif mode == "vector":
            if not vec_scores and embedder:
                # no vector store available, transparent degradation
                if raw_kw <= 0:
                    continue
                final_score = raw_kw
                fused = raw_kw
                match_type = "keyword_fallback"
                reasons = ["Vector search degraded to keyword (no vector store)."]
                matched_scopes = []
            else:
                if vec_norm <= 0 and raw_kw <= 0:
                    continue
                final_score = vec_norm
                fused = vec_norm
                match_type = "vector"
                reasons = [f"Vector similarity {vec_norm:.2f}."]
                matched_scopes = []
        else:  # hybrid
            age_days = max((now - item.created_at).days, 0)
            recency_boost = max(0.0, 0.25 - min(age_days, 30) / 120)
            importance_boost = max(item.importance - 5, 0) * 0.05
            type_boost = 0.15 if memory_type and item.memory_type == memory_type else 0.0
            matched_scopes = [
                name
                for name, value in (requested_scopes or {}).items()
                if value is not None and getattr(item, name) == value
            ]
            scope_boost = len(matched_scopes) * 0.1

            if embedder and vec_scores:
                fused = alpha * kw_norm + (1 - alpha) * vec_norm
            else:
                fused = kw_norm
                vec_norm = 0.0

            if fused <= 0 and raw_kw <= 0:
                continue

            final_score = fused + recency_boost + importance_boost + type_boost + scope_boost

            kw_terms = ", ".join(matched[:3]) if matched else "phrase"
            reasons = [
                f"Vector similarity {vec_norm:.2f} + keyword match ({kw_terms}) {kw_norm:.2f},"
                f" boosted by {', '.join(matched_scopes + (['importance'] if item.importance > 5 else []) + (['recency'] if recency_boost > 0 else []))  or 'none'}."
            ]
            match_type = "exact" if query.lower() in item.content.lower() else (
                "vector" if vec_norm > kw_norm else "keyword"
            )

        results.append(
            MemorySearchResult(
                item=item,
                score=round(final_score, 4),
                match_type=match_type,
                matched_terms=matched,
                ranking_reason=" ".join(reasons),
                keyword_score=round(kw_norm, 4),
                vector_score=round(vec_norm, 4),
                fused_score=round(fused if mode == "hybrid" else final_score, 4),
                embedder_name=embedder_name,
            )
        )

    return sorted(results, key=lambda r: r.score, reverse=True)[:limit]
