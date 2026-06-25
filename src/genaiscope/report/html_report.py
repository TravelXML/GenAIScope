"""Context Doctor HTML report -- distinct from the existing memory/file/trace
dashboard (genaiscope.dashboard). Reuses its small HTML helpers instead of
re-implementing card/table markup.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from genaiscope import __version__
from genaiscope.analytics.patterns import prompt_patterns
from genaiscope.analytics.usage import usage_summary
from genaiscope.dashboard.html import _card, _dict_rows, _escape
from genaiscope.memory.utils import iso_now

if TYPE_CHECKING:
    from genaiscope.memory import BaseMemoryStore
    from genaiscope.tracing import LocalTracer


def _default_output_path() -> Path:
    return Path(".genaiscope") / "reports" / "genaiscope_report.html"


def generate_html(
    output_path: str | Path | None = None,
    memory: BaseMemoryStore | None = None,
    tracer: LocalTracer | None = None,
    days: int = 30,
) -> Path:
    """Build the Context Doctor HTML report (health trend, patterns, model
    comparison, recent traces, memory usage)."""

    output = Path(output_path) if output_path else _default_output_path()
    output.parent.mkdir(parents=True, exist_ok=True)

    usage = usage_summary(tracer, days=days) if tracer else None
    patterns = prompt_patterns(memory, tracer, days=days) if tracer else None
    memory_stats = memory.stats() if memory else None
    traces = tracer.list(limit=50) if tracer else []

    health_rows = (
        "".join(
            "<tr>"
            f"<td>{_escape(t.created_at.isoformat())}</td>"
            f"<td>{_escape(t.metadata.get('category', t.name))}</td>"
            f"<td>{_escape(t.metadata.get('context_health_score', 'n/a'))}</td>"
            f"<td>{_escape(t.model)}</td>"
            "</tr>"
            for t in traces
        )
        or "<tr><td colspan='4'>No traces yet</td></tr>"
    )

    weak_items = "".join(f"<li>{_escape(item)}</li>" for item in (patterns.repeated_weak_patterns if patterns else []))
    best_items = "".join(f"<li>{_escape(item)}</li>" for item in (patterns.best_prompt_templates if patterns else []))

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GenAIScope Context Doctor Report</title>
  <style>
    body {{ margin:0; font-family: Inter, Arial, sans-serif; color:#17202a; background:#f7f9fb; }}
    header {{ background:#102033; color:white; padding:28px 36px; }}
    main {{ max-width:1180px; margin:0 auto; padding:28px; }}
    h1, h2 {{ margin:0 0 12px; }}
    section {{ margin:28px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; }}
    .card {{ background:white; border:1px solid #dde5ee; border-radius:8px; padding:16px; }}
    .card span {{ display:block; color:#52616f; font-size:13px; }}
    .card strong {{ display:block; margin-top:8px; font-size:24px; }}
    table {{ width:100%; border-collapse:collapse; background:white; border:1px solid #dde5ee; }}
    th, td {{ text-align:left; padding:10px; border-bottom:1px solid #e8eef5; vertical-align:top; }}
    th {{ background:#edf3f8; }}
    ul {{ background:white; border:1px solid #dde5ee; border-radius:8px; padding:18px 28px; }}
    .muted {{ color:#d9e5f2; }}
  </style>
</head>
<body>
  <header>
    <h1>GenAIScope Context Doctor Report</h1>
    <div class="muted">Version {_escape(__version__)} &middot; Generated {_escape(iso_now())} &middot; Window: last {days} days</div>
  </header>
  <main>
    <section>
      <h2>Overview</h2>
      <div class="grid">
        {_card("Total prompts", usage.total_requests if usage else 0)}
        {_card("Total tokens", usage.total_tokens if usage else 0)}
        {_card("Estimated cost", f"${(usage.total_estimated_cost if usage else 0):.6f}")}
        {_card("Average latency (ms)", usage.average_latency_ms if usage and usage.average_latency_ms else "N/A")}
        {_card("Total memories", memory_stats.total_memories if memory_stats else 0)}
      </div>
    </section>
    <section>
      <h2>Context Health Trend (recent traces)</h2>
      <table><tr><th>When</th><th>Category</th><th>Health score</th><th>Model</th></tr>{health_rows}</table>
    </section>
    <section>
      <h2>Top Categories</h2>
      <table><tr><th>Category</th><th>Count</th></tr>{_dict_rows(dict.fromkeys(patterns.top_topics if patterns else [], 1))}</table>
    </section>
    <section>
      <h2>Weak Prompt Patterns</h2>
      <ul>{weak_items or "<li>No weak patterns detected yet</li>"}</ul>
    </section>
    <section>
      <h2>Best Prompt Templates</h2>
      <ul>{best_items or "<li>Not enough data yet</li>"}</ul>
    </section>
    <section>
      <h2>Model / Provider Comparison</h2>
      <table><tr><th>Provider</th><th>Cost</th></tr>{_dict_rows(usage.cost_by_provider if usage else {})}</table>
      <table><tr><th>Model</th><th>Cost</th></tr>{_dict_rows(usage.cost_by_model if usage else {})}</table>
    </section>
  </main>
</body>
</html>
"""
    output.write_text(html_text, encoding="utf-8")
    return output


class ReportGenerator:
    """`scope.report.generate_html(...)` facade."""

    def __init__(self, memory: BaseMemoryStore, tracer: LocalTracer) -> None:
        self._memory = memory
        self._tracer = tracer

    def generate_html(self, output_path: str | Path | None = None, days: int = 30) -> Path:
        return generate_html(output_path, memory=self._memory, tracer=self._tracer, days=days)
