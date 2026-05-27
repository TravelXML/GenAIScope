"""Tests for dashboard generation."""

from genaiscope.dashboard import generate_dashboard
from genaiscope.memory import MemoryStore
from genaiscope.tracing import LocalTracer


def test_dashboard_generation_contains_core_sections(tmp_path):
    db_path = tmp_path / "memory.db"
    memory = MemoryStore(db_path=db_path)
    memory.add_prompt("Summarize this properly.")
    memory.close()
    tracer = LocalTracer(db_path=db_path)
    tracer.log(name="demo", model="local", estimated_cost=0.01)
    tracer.close()

    output = generate_dashboard(output_path=tmp_path / "dashboard.html", db_path=db_path)
    html = output.read_text(encoding="utf-8")
    assert "GenAIScope Dashboard" in html
    assert "Memory Statistics" in html
    assert "Prompt Quality Comments" in html
    assert "Trace Statistics" in html
    assert "Cost Insights" in html
    assert "Recommendations" in html
