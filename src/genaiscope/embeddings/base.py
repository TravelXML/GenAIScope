"""Base interface for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Backend-neutral embedding contract."""

    name: str
    dimensions: int

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text string into a float vector."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts; default impl calls embed() per item."""
        return [self.embed(t) for t in texts]
