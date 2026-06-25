"""Tests for analytics.prompt_patterns()."""

from pathlib import Path

from genaiscope.analytics import prompt_patterns
from genaiscope.memory import MemoryStore
from genaiscope.tracing import LocalTracer


def test_prompt_patterns_empty_store(tmp_path: Path) -> None:
    memory = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    patterns = prompt_patterns(memory, tracer, days=30)
    assert patterns.top_topics == []
    assert patterns.repeated_weak_patterns == []
    memory.close()
    tracer.close()


def test_prompt_patterns_surfaces_categories_tags_and_entities(tmp_path: Path) -> None:
    memory = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "t.db")

    for _ in range(3):
        tracer.log(
            name="interview",
            model="gpt-4.1",
            input_tokens=10,
            output_tokens=20,
            metadata={
                "category": "cto_interview",
                "tags": ["traveltech"],
                "context_health_score": 40,
                "missing_context": ["Target audience"],
                "detected_entities": ["TravelTech"],
            },
        )

    patterns = prompt_patterns(memory, tracer, days=30)
    assert "cto_interview" in patterns.top_topics
    assert "traveltech" in patterns.most_used_tags
    assert "TravelTech" in patterns.most_used_entities
    assert patterns.average_health_score_by_category["cto_interview"] == 40
    assert any("missing" in p.lower() for p in patterns.repeated_weak_patterns)
    memory.close()
    tracer.close()


def test_prompt_patterns_flags_low_average_health_score(tmp_path: Path) -> None:
    memory = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "t.db")

    tracer.log(name="weak", metadata={"category": "weak_category", "context_health_score": 20})
    tracer.log(name="strong", metadata={"category": "strong_category", "context_health_score": 90})

    patterns = prompt_patterns(memory, tracer, days=30)
    assert any("weak_category" in p for p in patterns.repeated_weak_patterns)
    assert "strong_category" not in " ".join(patterns.repeated_weak_patterns)
    memory.close()
    tracer.close()
