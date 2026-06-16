"""Shared interface for memory backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from genaiscope.memory.context import ContextResult
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

    def context(
        self,
        query: str,
        user_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
        limit: int = 10,
        mode: str = "hybrid",
        max_chars: int | None = None,
        **kwargs: Any,
    ) -> ContextResult:
        """Return a ready-to-inject context block. Override in subclasses for richer impl."""
        results = self.search(
            query, limit=limit, mode=mode,
            user_id=user_id, project_id=project_id, workspace_id=workspace_id, **kwargs
        )
        lines: list[str] = []
        selected: list[dict] = []
        char_count = 0
        for result in results:
            line = f"- [{result.item.memory_type}] {result.item.content}"
            if max_chars and char_count + len(line) > max_chars:
                break
            lines.append(line)
            char_count += len(line)
            selected.append({"id": result.item.id, "content": result.item.content, "score": result.score})
        return ContextResult(
            query=query, memories=selected, text="\n".join(lines),
            char_count=char_count, memory_count=len(selected), mode=mode,
        )

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
