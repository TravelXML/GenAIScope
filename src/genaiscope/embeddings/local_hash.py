"""Zero-dependency deterministic hash-based embedder.

Tokens are hashed into a fixed-dimension vector and L2-normalized.
Always available — no network or ML runtime required.
"""

from __future__ import annotations

import hashlib
import math
import re

from genaiscope.embeddings.base import BaseEmbedder

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
_DEFAULT_DIMS = 256


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


class LocalHashEmbedder(BaseEmbedder):
    """Pure-Python deterministic embedder — no dependencies."""

    name = "local_hash"

    def __init__(self, dimensions: int = _DEFAULT_DIMS) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            tokens = [text.strip() or "empty"]
        vec = [0.0] * self.dimensions
        for token in tokens:
            h = int(hashlib.sha256(token.encode()).hexdigest(), 16)
            for i in range(4):
                idx = (h >> (i * 8)) % self.dimensions
                sign = 1.0 if (h >> (i * 8 + self.dimensions % 7)) & 1 else -1.0
                vec[idx] += sign
        return _l2_normalize(vec)
