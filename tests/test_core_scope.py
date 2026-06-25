"""Tests for the GenAIScope v0.6.0 facade (core/scope.py)."""

from pathlib import Path

from genaiscope import GenAIScope


def test_genaiscope_importable_from_top_level_and_core() -> None:
    from genaiscope.core import GenAIScope as CoreGenAIScope

    assert CoreGenAIScope is GenAIScope


def test_memory_add_search_forget_list(tmp_path: Path) -> None:
    scope = GenAIScope(db_path=tmp_path / "scope.db")
    item = scope.memory.add(
        memory_type="profile_memory",
        content="Sapan is a CTO / VP Engineering leader with TravelTech experience.",
        title="User profile",
        tags=["profile", "cto"],
        confidence=0.95,
        importance_score=0.9,
    )
    assert item.memory_type == "profile_memory"
    assert item.metadata["title"] == "User profile"
    assert item.metadata["confidence"] == 0.95
    assert item.importance == 9  # 0.9 * 10

    results = scope.memory.search("CTO leader", top_k=5)
    assert len(results) >= 1

    listed = scope.memory.list(memory_type="profile_memory")
    assert len(listed) == 1

    assert scope.memory.forget(item.id) is True
    assert scope.memory.list(memory_type="profile_memory") == []
    scope.close()


def test_trace_context_manager_logs_and_diagnoses(tmp_path: Path) -> None:
    scope = GenAIScope(db_path=tmp_path / "scope.db")
    with scope.trace(provider="openai", model="gpt-4.1", category="cto_interview", tags=["traveltech"]) as trace:
        trace.log(prompt="Write answer for feature velocity.", response="Feature velocity matters.")

    traces = scope._tracer.list(limit=10)
    assert len(traces) == 1
    item = traces[0]
    assert item.metadata["category"] == "cto_interview"
    assert item.metadata["tags"] == ["traveltech"]
    assert "context_health_score" in item.metadata
    scope.close()


def test_log_interaction_direct(tmp_path: Path) -> None:
    scope = GenAIScope(db_path=tmp_path / "scope.db")
    item = scope.log_interaction(
        prompt="Explain feature velocity",
        response="Feature velocity means shipping value to customers faster.",
        provider="openai",
        model="gpt-4.1",
        input_tokens=120,
        output_tokens=240,
        latency_ms=1800,
        category="cto_learning",
        tags=["metrics", "cto"],
    )
    assert item.input_text == "Explain feature velocity"
    assert item.metadata["category"] == "cto_learning"
    assert "context_health_score" in item.metadata
    scope.close()


def test_scope_doctor_cost_router_analytics_report_accessible(tmp_path: Path) -> None:
    scope = GenAIScope(db_path=tmp_path / "scope.db")

    report = scope.doctor.diagnose(prompt="Write answer for this job.")
    assert 0 <= report.context_health_score <= 100

    cost = scope.cost.estimate(provider="openai", model="gpt-4.1", input_tokens=100, output_tokens=100)
    assert cost.total_cost >= 0

    rec = scope.router.recommend("Refactor this Python function")
    assert rec.recommended_model_type == "coding"

    summary = scope.analytics.usage_summary(days=7)
    assert summary.total_requests == 0

    out = scope.report.generate_html(tmp_path / "r.html")
    assert out.exists()
    scope.close()


def test_context_builder_accessible_from_scope(tmp_path: Path) -> None:
    scope = GenAIScope(db_path=tmp_path / "scope.db")
    scope.memory.add(memory_type="preference_memory", content="User prefers concise answers", tags=["style"])
    result = scope.context.build("concise answers", top_k=5)
    assert result.original_prompt == "concise answers"
    scope.close()
