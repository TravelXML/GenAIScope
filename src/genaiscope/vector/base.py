"""Abstract vector store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from genaiscope.vector.models import VectorMatch, VectorRecord


class BaseVectorStore(ABC):
    """Backend-neutral vector store contract."""

    @abstractmethod
    def upsert(self, vector_id: str, vector: list[float], metadata: dict) -> None: ...

    def upsert_batch(self, items: list[VectorRecord]) -> None:
        for item in items:
            self.upsert(item.vector_id, item.vector, item.metadata)

    @abstractmethod
    def query(
        self,
        vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[VectorMatch]: ...

    @abstractmethod
    def delete(self, vector_id: str) -> bool: ...

    @abstractmethod
    def count(self) -> int: ...
