"""Local tracing interface."""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from genaiscope.tracing.factory import create_trace_store
from genaiscope.tracing.models import TraceItem, TraceStats


class TraceSpan:
    """Context manager span used by LocalTracer."""

    def __init__(
        self, tracer: LocalTracer, name: str, model: str | None = None, provider: str | None = None
    ):
        self.tracer = tracer
        self.name = name
        self.model = model
        self.provider = provider
        self.input_text: str | None = None
        self.output_text: str | None = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.estimated_cost = 0.0
        self.metadata: dict[str, Any] = {}
        self.start = 0.0
        self.item: TraceItem | None = None

    def __enter__(self) -> TraceSpan:
        self.start = time.perf_counter()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, _tb: object
    ) -> None:
        latency_ms = (time.perf_counter() - self.start) * 1000
        self.item = self.tracer.log(
            name=self.name,
            input_text=self.input_text,
            output_text=self.output_text,
            model=self.model,
            provider=self.provider,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            estimated_cost=self.estimated_cost,
            latency_ms=latency_ms,
            status="error" if exc else "success",
            error=str(exc) if exc else None,
            metadata=self.metadata,
        )

    def log_input(self, text: str) -> None:
        self.input_text = text

    def log_output(self, text: str) -> None:
        self.output_text = text

    def log_tokens(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def log_cost(self, estimated_cost: float) -> None:
        self.estimated_cost = estimated_cost


class LocalTracer:
    """Lightweight local trace logger."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        backend: str = "sqlite",
        redis_url: str = "redis://localhost:6379",
        namespace: str = "genaiscope",
        exporters: list[Callable[[TraceItem], None]] | None = None,
    ):
        self.store = create_trace_store(backend=backend, db_path=db_path, redis_url=redis_url, namespace=namespace)
        self.exporters = list(exporters or [])

    def log(self, *args: Any, **kwargs: Any) -> TraceItem:
        """Log one trace, then fan it out to any registered exporters. An
        exporter failure is swallowed -- exporting is a side effect and must
        never break local tracing."""

        item = self.store.log(*args, **kwargs)
        for exporter in self.exporters:
            # exporter failures must never break tracing
            with contextlib.suppress(Exception):
                exporter(item)
        return item

    def trace(self, name: str, model: str | None = None, provider: str | None = None) -> TraceSpan:
        """Create a context manager tracing span."""

        return TraceSpan(self, name=name, model=model, provider=provider)

    def list(self, limit: int = 50, offset: int = 0) -> list[TraceItem]:
        return self.store.list(limit=limit, offset=offset)

    def get(self, trace_id: str) -> TraceItem | None:
        return self.store.get(trace_id)

    def stats(self) -> TraceStats:
        return self.store.stats()

    def clear(self, confirm: bool = False) -> int:
        return self.store.clear(confirm=confirm)

    def close(self) -> None:
        self.store.close()
