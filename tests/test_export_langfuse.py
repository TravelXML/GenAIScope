"""Tests for the Langfuse batch-export shape -- pure mapping, no network/SDK needed."""

import json
from pathlib import Path

from genaiscope.export import export_langfuse
from genaiscope.tracing import LocalTracer


def test_export_langfuse_writes_trace_and_generation_events(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    tracer.log(
        name="chat", input_text="hi", output_text="hello",
        provider="openai", model="gpt-4o-mini",
        input_tokens=10, output_tokens=5, estimated_cost=0.001, status="success",
    )

    out = tmp_path / "langfuse_export.json"
    path = export_langfuse(tracer, out)

    assert path == out
    data = json.loads(out.read_text())
    assert "batch" in data
    types = [event["type"] for event in data["batch"]]
    assert types == ["trace-create", "generation-create"]

    trace_event, gen_event = data["batch"]
    assert trace_event["body"]["input"] == "hi"
    assert trace_event["body"]["output"] == "hello"
    assert gen_event["body"]["model"] == "gpt-4o-mini"
    assert gen_event["body"]["usage"]["promptTokens"] == 10
    assert gen_event["body"]["usage"]["completionTokens"] == 5
    assert gen_event["body"]["level"] == "DEFAULT"
    tracer.close()


def test_export_langfuse_marks_error_level(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    tracer.log(name="chat", provider="openai", model="gpt-4o-mini", status="error", error="boom")

    out = tmp_path / "out.json"
    export_langfuse(tracer, out)
    data = json.loads(out.read_text())

    gen_event = next(e for e in data["batch"] if e["type"] == "generation-create")
    assert gen_event["body"]["level"] == "ERROR"
    assert gen_event["body"]["statusMessage"] == "boom"
    tracer.close()


def test_export_langfuse_skips_generation_event_without_model_or_provider(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    tracer.log(name="memory_search", input_text="query")

    out = tmp_path / "out.json"
    export_langfuse(tracer, out)
    data = json.loads(out.read_text())

    assert [e["type"] for e in data["batch"]] == ["trace-create"]
    tracer.close()
