"""Cross-encoder reranking for hybrid memory search results.

Reuses the `sentence-transformers` dependency already declared by the
`embeddings` extra (it ships both `SentenceTransformer` and `CrossEncoder`) --
no new optional dependency. Opt-in only: a model load + N inference calls per
query is too expensive to run by default on every `mode="hybrid"` search.

Requires: pip install "genaiscope[embeddings]"
"""

from __future__ import annotations

from genaiscope.core.errors import EmbeddingBackendError
from genaiscope.memory.models import MemorySearchResult

_DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_BLEND_WEIGHT = 0.5  # final = _BLEND_WEIGHT * fused_score + (1 - _BLEND_WEIGHT) * cross_encoder_score


class CrossEncoderReranker:
    """Reranks a candidate pool by jointly scoring (query, content) pairs,
    blended with each candidate's existing fused hybrid score."""

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise EmbeddingBackendError(
                'sentence-transformers is not installed. Run: pip install "genaiscope[embeddings]"'
            ) from exc
        self._model = CrossEncoder(model_name)

    def rerank(
        self, query: str, candidates: list[MemorySearchResult], top_k: int
    ) -> list[MemorySearchResult]:
        if not candidates:
            return []

        pairs = [(query, candidate.item.content) for candidate in candidates]
        raw_scores = [float(s) for s in self._model.predict(pairs)]
        lo, hi = min(raw_scores), max(raw_scores)
        spread = hi - lo

        reranked: list[MemorySearchResult] = []
        for candidate, raw in zip(candidates, raw_scores, strict=True):
            normalized = (raw - lo) / spread if spread > 0 else 0.5
            blended = _BLEND_WEIGHT * candidate.fused_score + (1 - _BLEND_WEIGHT) * normalized
            reranked.append(
                candidate.model_copy(update={"score": round(blended, 4), "ranking_reason": "cross_encoder_rerank"})
            )

        reranked.sort(key=lambda r: r.score, reverse=True)
        return reranked[:top_k]
