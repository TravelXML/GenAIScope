"""Tests for analytics.usage_summary()."""

from __future__ import annotations

import datetime
from pathlib import Path

from genaiscope.analytics import usage_summary
from genaiscope.tracing import LocalTracer


def test_usage_summary_empty_store(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    summary = usage_summary(tracer, days=7)
    assert summary.total_requests == 0
    assert summary.total_tokens == 0
    tracer.close()


def test_usage_summary_aggregates_tokens_cost_and_latency(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    tracer.log(
        name="call-1", model="gpt-4.1", provider="openai",
        input_tokens=100, output_tokens=200, estimated_cost=0.01, latency_ms=500,
        metadata={"category": "cto_interview"},
    )
    tracer.log(
        name="call-2", model="gpt-4.1", provider="openai",
        input_tokens=50, output_tokens=50, estimated_cost=0.005, latency_ms=300,
        metadata={"category": "cto_interview"},
    )

    summary = usage_summary(tracer, days=7)
    assert summary.total_requests == 2
    assert summary.total_input_tokens == 150
    assert summary.total_output_tokens == 250
    assert summary.total_tokens == 400
    assert round(summary.total_estimated_cost, 6) == 0.015
    assert summary.average_latency_ms == 400
    assert summary.cost_by_provider["openai"] > 0
    assert summary.cost_by_model["gpt-4.1"] > 0
    assert summary.tokens_by_category["cto_interview"] == 400
    tracer.close()


def test_usage_summary_excludes_traces_outside_window(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    tracer.log(name="old-call", input_tokens=10, output_tokens=10)

    # Push the trace's created_at into the past by editing the row directly --
    # there's no public "backdate" API, and there shouldn't be one.
    old_date = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30)).isoformat()
    tracer.store.connection.execute("UPDATE traces SET created_at = ?", (old_date,))
    tracer.store.connection.commit()

    summary = usage_summary(tracer, days=7)
    assert summary.total_requests == 0
    tracer.close()
