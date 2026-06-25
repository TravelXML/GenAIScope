"""GenAIScope -- the v0.6.0 facade tying memory, tracing, context, doctor,
cost, analytics, router, and report together around one shared local store.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from genaiscope.doctor import ContextDoctor
from genaiscope.memory import MemoryItem, MemorySearchResult, MemoryStore
from genaiscope.memory.base import BaseMemoryStore
from genaiscope.tracing import LocalTracer
from genaiscope.tracing.models import TraceItem
from genaiscope.tracing.tracer import TraceSpan


def _importance_from_score(importance_score: float | None, importance: int) -> int:
    if importance_score is None:
        return importance
    return max(1, min(10, round(importance_score * 10)))


def _diagnosis_metadata(
    doctor: ContextDoctor | None,
    prompt: str | None,
    response: str | None,
    provider: str | None,
    model: str | None,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, Any]:
    """Run ContextDoctor and shape its result for trace metadata. Never raises
    -- diagnosis is a side note, not allowed to break tracing/logging."""

    if not prompt or doctor is None:
        return {}
    try:
        report = doctor.diagnose(
            prompt=prompt,
            response=response,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        return {
            "context_health_score": report.context_health_score,
            "missing_context": report.missing_context,
            "detected_intent": report.detected_intent,
            "detected_entities": report.detected_entities,
        }
    except Exception:
        return {}


class _ScopeMemory:
    """`scope.memory` -- thin convenience layer over MemoryStore.

    New spec fields (`title`, `entities`, `confidence`) are stored inside the
    existing MemoryItem.metadata dict rather than as new columns (see
    v0.6.0 plan decision #4) -- no schema migration needed, fully backward
    compatible with existing .db files.
    """

    def __init__(self, store: BaseMemoryStore) -> None:
        self._store = store

    def add(
        self,
        memory_type: str,
        content: str,
        title: str | None = None,
        entities: list[str] | None = None,
        confidence: float | None = None,
        importance_score: float | None = None,
        importance: int = 5,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> MemoryItem:
        meta = dict(metadata or {})
        if title is not None:
            meta["title"] = title
        if entities is not None:
            meta["entities"] = entities
        if confidence is not None:
            meta["confidence"] = confidence

        return self._store.add(
            content,
            memory_type=memory_type,
            tags=tags,
            metadata=meta,
            importance=_importance_from_score(importance_score, importance),
            **kwargs,
        )

    def search(self, query: str, top_k: int = 5, **filters: Any) -> list[MemorySearchResult]:
        return self._store.search(query, limit=top_k, **filters)

    def forget(self, memory_id: str) -> bool:
        return self._store.delete(memory_id)

    def list(self, memory_type: str | None = None, **filters: Any) -> list[MemoryItem]:
        return self._store.list(memory_type=memory_type, **filters)


class _ScopeRouter:
    """`scope.router` -- thin wrapper so usage matches `scope.router.recommend(...)`."""

    def recommend(self, prompt: str, privacy_sensitive: bool = False, cost_sensitive: bool = False) -> Any:
        from genaiscope.router import recommend

        return recommend(prompt, privacy_sensitive=privacy_sensitive, cost_sensitive=cost_sensitive)


class _GenAIScopeTraceSpan(TraceSpan):
    """`with scope.trace(...) as trace:` span -- adds category/tags/scope ids
    and an optional automatic Context Doctor health score on exit."""

    def __init__(
        self,
        tracer: LocalTracer,
        doctor: ContextDoctor | None,
        name: str,
        model: str | None = None,
        provider: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        super().__init__(tracer, name=name, model=model, provider=provider)
        self._doctor = doctor
        self.metadata = {
            "category": category,
            "tags": list(tags or []),
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
        }

    def log(self, prompt: str | None = None, response: str | None = None, rating: float | None = None) -> None:
        if prompt is not None:
            self.log_input(prompt)
        if response is not None:
            self.log_output(response)
        if rating is not None:
            self.metadata["rating"] = rating

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object) -> None:
        self.metadata.update(
            _diagnosis_metadata(
                self._doctor, self.input_text, self.output_text, self.provider, self.model,
                self.input_tokens, self.output_tokens,
            )
        )
        super().__exit__(exc_type, exc, tb)


class GenAIScope:
    """The v0.6.0 entry point: one shared local store behind
    memory/context/doctor/cost/analytics/router/report."""

    def __init__(
        self,
        storage: str = "sqlite",
        db_path: str | Path | None = None,
        namespace: str = "genaiscope",
        redis_url: str = "redis://localhost:6379",
        embedder: Any = None,
        vector_store: Any = None,
    ) -> None:
        self._store = MemoryStore(
            backend=storage,
            db_path=db_path,
            namespace=namespace,
            redis_url=redis_url,
            embedder=embedder,
            vector_store=vector_store,
        )
        self._tracer = LocalTracer(backend=storage, db_path=db_path, namespace=namespace, redis_url=redis_url)
        self._doctor = ContextDoctor()

        self.memory = _ScopeMemory(self._store)

    @property
    def context(self) -> Any:
        from genaiscope.context import ContextBuilder

        return ContextBuilder(self._store)

    @property
    def doctor(self) -> ContextDoctor:
        return self._doctor

    @property
    def cost(self) -> Any:
        from genaiscope.cost import CostEstimator

        return CostEstimator()

    @property
    def router(self) -> _ScopeRouter:
        return _ScopeRouter()

    @property
    def analytics(self) -> Any:
        from genaiscope.analytics import AnalyticsEngine

        return AnalyticsEngine(self._store, self._tracer)

    @property
    def report(self) -> Any:
        from genaiscope.report import ReportGenerator

        return ReportGenerator(self._store, self._tracer)

    def trace(
        self,
        provider: str | None = None,
        model: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        session_id: str | None = None,
        name: str | None = None,
    ) -> _GenAIScopeTraceSpan:
        """Context manager: `with scope.trace(...) as trace: trace.log(...)`."""

        return _GenAIScopeTraceSpan(
            self._tracer,
            self._doctor,
            name=name or category or "interaction",
            model=model,
            provider=provider,
            category=category,
            tags=tags,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
        )

    def log_interaction(
        self,
        prompt: str,
        response: str,
        provider: str | None = None,
        model: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        session_id: str | None = None,
        rating: float | None = None,
    ) -> TraceItem:
        """Direct one-shot logging (no context manager)."""

        metadata: dict[str, Any] = {
            "category": category,
            "tags": list(tags or []),
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
        }
        if rating is not None:
            metadata["rating"] = rating
        metadata.update(
            _diagnosis_metadata(self._doctor, prompt, response, provider, model, input_tokens, output_tokens)
        )

        return self._tracer.log(
            name=category or "interaction",
            input_text=prompt,
            output_text=response,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            metadata=metadata,
        )

    def close(self) -> None:
        self._store.close()
        self._tracer.close()
