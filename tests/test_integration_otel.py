"""OTel exporter tests -- fully offline via InMemorySpanExporter, no collector needed."""

from pathlib import Path

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from genaiscope.integrations.otel import OTelExporter
from genaiscope.tracing import LocalTracer


@pytest.fixture(scope="module")
def _otel_provider():
    # The OTel SDK only allows the global TracerProvider to be set once per
    # process, so this is module-scoped; each test clears the exporter instead.
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


@pytest.fixture
def in_memory_spans(_otel_provider):
    _otel_provider.clear()
    yield _otel_provider


def test_otel_exporter_emits_span_with_gen_ai_attributes(tmp_path: Path, in_memory_spans) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db", exporters=[OTelExporter()])

    tracer.log(
        name="chat", provider="openai", model="gpt-4o-mini",
        input_tokens=10, output_tokens=5, estimated_cost=0.001, status="success",
    )

    spans = in_memory_spans.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "chat"
    assert span.attributes["gen_ai.system"] == "openai"
    assert span.attributes["gen_ai.request.model"] == "gpt-4o-mini"
    assert span.attributes["gen_ai.usage.input_tokens"] == 10
    assert span.attributes["gen_ai.usage.output_tokens"] == 5
    assert span.status.status_code.name == "OK"
    tracer.close()


def test_otel_exporter_marks_error_status(tmp_path: Path, in_memory_spans) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db", exporters=[OTelExporter()])

    tracer.log(name="chat", status="error", error="boom")

    spans = in_memory_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code.name == "ERROR"
    tracer.close()


def test_tracer_log_survives_exporter_failure(tmp_path: Path) -> None:
    def _broken_exporter(_item):
        raise RuntimeError("exporter is down")

    tracer = LocalTracer(db_path=tmp_path / "t.db", exporters=[_broken_exporter])

    item = tracer.log(name="chat")

    assert item.id
    assert len(tracer.list()) == 1
    tracer.close()
