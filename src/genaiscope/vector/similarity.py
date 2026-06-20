"""Shared vector similarity math."""

from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors. Uses numpy when available."""
    try:
        import numpy as np  # type: ignore[import-not-found]

        return float(np.dot(a, b))
    except ImportError:
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)
