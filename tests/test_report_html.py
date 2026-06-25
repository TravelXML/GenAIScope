"""Tests for the Context Doctor HTML report (distinct from genaiscope.dashboard)."""

from pathlib import Path

from genaiscope.memory import MemoryStore
from genaiscope.report import generate_html
from genaiscope.tracing import LocalTracer


def test_generate_html_creates_report_with_seeded_data(tmp_path: Path) -> None:
    memory = MemoryStore(db_path=tmp_path / "m.db")
    memory.add("Sapan is a CTO / VP Engineering leader", memory_type="profile_memory")
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    tracer.log(
        name="interview", model="gpt-4.1", input_tokens=10, output_tokens=20, estimated_cost=0.001,
        metadata={"category": "cto_interview", "context_health_score": 70},
    )

    output_path = tmp_path / "report.html"
    generated = generate_html(output_path, memory=memory, tracer=tracer, days=30)

    assert generated == output_path
    html_text = output_path.read_text(encoding="utf-8")
    assert "GenAIScope Context Doctor Report" in html_text
    assert "cto_interview" in html_text
    memory.close()
    tracer.close()


def test_generate_html_handles_empty_store(tmp_path: Path) -> None:
    memory = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "t.db")

    output_path = tmp_path / "empty_report.html"
    generated = generate_html(output_path, memory=memory, tracer=tracer)

    assert generated.exists()
    assert "No traces yet" in generated.read_text(encoding="utf-8")
    memory.close()
    tracer.close()


def test_report_generator_facade(tmp_path: Path) -> None:
    from genaiscope.report import ReportGenerator

    memory = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    generator = ReportGenerator(memory, tracer)

    output_path = tmp_path / "facade_report.html"
    generated = generator.generate_html(output_path)
    assert generated.exists()
    memory.close()
    tracer.close()
