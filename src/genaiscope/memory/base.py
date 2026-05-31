"""Shared interface for memory backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from genaiscope.memory.models import MemoryItem, MemorySearchResult, MemoryStats


class BaseMemoryStore(ABC):
    """Backend-neutral memory store contract."""

    backend: str
    namespace: str

    @abstractmethod
    def add(self, content: str, **kwargs: Any) -> MemoryItem: ...

    def remember(self, content: str, **kwargs: Any) -> MemoryItem:
        """Store a memory using the conversational API alias."""

        return self.add(content, **kwargs)

    def add_prompt(self, prompt: str, **kwargs: Any) -> MemoryItem:
        """Store a prompt memory with quality analysis."""

        return self.add(prompt, memory_type="prompt", **kwargs)

    @abstractmethod
    def search(self, query: str, **kwargs: Any) -> list[MemorySearchResult]: ...

    @abstractmethod
    def get(self, memory_id: str, **kwargs: Any) -> MemoryItem | None: ...

    @abstractmethod
    def list(self, **kwargs: Any) -> list[MemoryItem]: ...

    @abstractmethod
    def delete(self, memory_id: str) -> bool: ...

    @abstractmethod
    def clear(self, confirm: bool = False, **kwargs: Any) -> int: ...

    @abstractmethod
    def stats(self) -> MemoryStats: ...

    @abstractmethod
    def cleanup_expired(self) -> int: ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> BaseMemoryStore:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
