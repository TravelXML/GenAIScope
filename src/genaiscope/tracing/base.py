"""Shared trace backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from genaiscope.tracing.models import TraceItem, TraceStats


class BaseTraceStore(ABC):
    """Backend-neutral trace contract."""

    backend: str
    namespace: str

    @abstractmethod
    def log(self, name: str, **kwargs: Any) -> TraceItem: ...

    @abstractmethod
    def list(self, limit: int = 50, offset: int = 0) -> list[TraceItem]: ...

    @abstractmethod
    def get(self, trace_id: str) -> TraceItem | None: ...

    @abstractmethod
    def clear(self, confirm: bool = False) -> int: ...

    @abstractmethod
    def stats(self) -> TraceStats: ...

    @abstractmethod
    def close(self) -> None: ...
