"""Tests for local tracing."""

from genaiscope.tracing import LocalTracer


def test_tracing_log_stats_and_context_manager(tmp_path):
    tracer = LocalTracer(db_path=tmp_path / "memory.db")
    item = tracer.log(
        name="demo",
        input_text="hello",
        output_text="hi",
        model="local",
        input_tokens=5,
        output_tokens=2,
        estimated_cost=0.0,
    )
    assert tracer.get(item.id) == item

    with tracer.trace(name="span", model="local") as span:
        span.log_input("hello")
        span.log_output("hi")
        span.log_tokens(input_tokens=1, output_tokens=1)

    stats = tracer.stats()
    assert stats.total_traces == 2
    assert stats.success_count == 2
    assert stats.total_input_tokens == 6
    tracer.close()
