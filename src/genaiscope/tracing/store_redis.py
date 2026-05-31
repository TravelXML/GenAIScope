"""Optional Redis trace store."""

from __future__ import annotations

import uuid
from typing import Any

from genaiscope.memory.namespaces import normalize_namespace
from genaiscope.memory.store_redis import _redis_client
from genaiscope.memory.utils import utc_now
from genaiscope.tracing.base import BaseTraceStore
from genaiscope.tracing.models import TraceItem, TraceStats


class RedisTraceStore(BaseTraceStore):
    """Redis-backed trace storage."""

    backend = "redis"

    def __init__(self, redis_url: str = "redis://localhost:6379", namespace: str = "genaiscope", **_kwargs: Any):
        self.namespace = normalize_namespace(namespace)
        self.client = _redis_client(redis_url)

    def _key(self, trace_id: str) -> str:
        return f"{self.namespace}:trace:{trace_id}"

    def _indexes(self, trace: TraceItem) -> list[str]:
        keys = [f"{self.namespace}:traces", f"{self.namespace}:trace_status:{trace.status}"]
        if trace.model:
            keys.append(f"{self.namespace}:trace_model:{trace.model}")
        if trace.provider:
            keys.append(f"{self.namespace}:trace_provider:{trace.provider}")
        return keys

    def log(self, name: str, **kwargs: Any) -> TraceItem:
        now = utc_now()
        trace = TraceItem(id=str(uuid.uuid4()), name=name, created_at=now, updated_at=now, **kwargs)
        pipe = self.client.pipeline()
        pipe.set(self._key(trace.id), trace.model_dump_json())
        for index in self._indexes(trace):
            pipe.sadd(index, trace.id)
        pipe.execute()
        return trace

    def get(self, trace_id: str) -> TraceItem | None:
        value = self.client.get(self._key(trace_id))
        return TraceItem.model_validate_json(value) if value else None

    def list(self, limit: int = 50, offset: int = 0) -> list[TraceItem]:
        ids = self.client.smembers(f"{self.namespace}:traces")
        traces = [trace for trace_id in ids if (trace := self.get(trace_id))]
        traces.sort(key=lambda trace: trace.created_at, reverse=True)
        return traces[offset : offset + limit]

    def clear(self, confirm: bool = False) -> int:
        if not confirm:
            raise ValueError("clear requires confirm=True")
        traces = self.list(limit=100000)
        pipe = self.client.pipeline()
        for trace in traces:
            pipe.delete(self._key(trace.id))
            for index in self._indexes(trace):
                pipe.srem(index, trace.id)
        pipe.execute()
        return len(traces)

    def stats(self) -> TraceStats:
        traces = self.list(limit=100000)
        latencies = [trace.latency_ms for trace in traces if trace.latency_ms is not None]
        def counts(field: str) -> dict[str, int]:
            result: dict[str, int] = {}
            for trace in traces:
                value = getattr(trace, field)
                if value:
                    result[value] = result.get(value, 0) + 1
            return result
        return TraceStats(
            total_traces=len(traces), success_count=len([trace for trace in traces if trace.status == "success"]),
            error_count=len([trace for trace in traces if trace.status != "success"]),
            total_estimated_cost=round(sum(trace.estimated_cost for trace in traces), 6),
            average_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else None,
            total_input_tokens=sum(trace.input_tokens for trace in traces),
            total_output_tokens=sum(trace.output_tokens for trace in traces),
            traces_by_model=counts("model"), traces_by_provider=counts("provider"),
        )

    def close(self) -> None:
        self.client.close()
