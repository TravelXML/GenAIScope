"""OpenTelemetry exporter -- maps a TraceItem to a real OTel span using the
`gen_ai.*` semantic-convention attribute names, not invented ones.

`TraceItem` (genaiscope.tracing.models) already carries everything a span
needs, so this is a pure mapping layer; no new trace data is collected.

Requires: pip install "genaiscope[otel]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.core.errors import OTelDependencyMissingError

if TYPE_CHECKING:
    from genaiscope.tracing.models import TraceItem


class OTelExporter:
    """Callable exporter: `LocalTracer(exporters=[OTelExporter()])`. Emits one
    OTel span per `TraceItem` through whatever global `TracerProvider` the
    host application has configured -- this class never configures one
    itself, it only calls `opentelemetry.trace.get_tracer(...)`."""

    def __init__(self, tracer_name: str = "genaiscope") -> None:
        try:
            from opentelemetry import trace
        except ImportError as exc:
            raise OTelDependencyMissingError(
                'opentelemetry-sdk is not installed. Run: pip install "genaiscope[otel]"'
            ) from exc
        self._tracer = trace.get_tracer(tracer_name)

    def __call__(self, item: TraceItem) -> None:
        from opentelemetry.trace import Status, StatusCode

        start_ns = int(item.created_at.timestamp() * 1_000_000_000)
        end_ns = int(item.updated_at.timestamp() * 1_000_000_000)
        if end_ns < start_ns:
            end_ns = start_ns

        attributes: dict[str, Any] = {"genaiscope.trace_id": item.id}
        if item.provider:
            attributes["gen_ai.system"] = item.provider
        if item.model:
            attributes["gen_ai.request.model"] = item.model
        attributes["gen_ai.usage.input_tokens"] = item.input_tokens
        attributes["gen_ai.usage.output_tokens"] = item.output_tokens
        attributes["genaiscope.estimated_cost"] = item.estimated_cost

        span = self._tracer.start_span(name=item.name, start_time=start_ns, attributes=attributes)
        if item.status == "error":
            span.set_status(Status(StatusCode.ERROR, item.error or ""))
        else:
            span.set_status(Status(StatusCode.OK))
        span.end(end_time=end_ns)
