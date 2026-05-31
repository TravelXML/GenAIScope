"""Static local HTML dashboard."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from genaiscope import __version__
from genaiscope.dashboard.recommendations import generate_recommendations
from genaiscope.files import FileMemory
from genaiscope.memory import MemoryStore
from genaiscope.memory.dedupe import find_duplicates
from genaiscope.memory.utils import default_db_path, iso_now
from genaiscope.tracing import LocalTracer


def _escape(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _default_output_path() -> Path:
    return Path(".genaiscope") / "reports" / "dashboard.html"


def _card(label: str, value: Any) -> str:
    return f"<div class='card'><span>{_escape(label)}</span><strong>{_escape(value)}</strong></div>"


def _dict_rows(data: dict[str, Any]) -> str:
    if not data:
        return "<tr><td colspan='2'>No data yet</td></tr>"
    return "".join(
        f"<tr><td>{_escape(key)}</td><td>{_escape(value)}</td></tr>" for key, value in data.items()
    )


def generate_dashboard(
    output_path: str | Path | None = None,
    db_path: str | Path | None = None,
    backend: str = "sqlite",
    redis_url: str = "redis://localhost:6379",
    namespace: str = "genaiscope",
) -> Path:
    """Generate a self-contained local HTML dashboard."""

    output = Path(output_path) if output_path else _default_output_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    db = Path(db_path) if db_path else default_db_path()
    memory = MemoryStore(backend=backend, db_path=db, redis_url=redis_url, namespace=namespace)
    tracer = LocalTracer(backend=backend, db_path=db, redis_url=redis_url, namespace=namespace)
    files = FileMemory(memory_store=memory)

    memory_stats = memory.stats()
    memories = memory.list(limit=1000)
    prompt_memories = [item for item in memories if item.memory_type == "prompt"]
    trace_stats = tracer.stats()
    traces = tracer.list(limit=1000)
    file_stats = files.stats()
    recommendations = generate_recommendations(memory_stats, memories, trace_stats, traces)
    duplicate_count = sum(len(group) - 1 for group in find_duplicates(memory))
    cache_count = len([item for item in memories if item.memory_type == "cache"])

    prompt_rows = (
        "".join(
            "<tr>"
            f"<td>{_escape(item.content[:160])}</td>"
            f"<td>{_escape(item.prompt_score)}</td>"
            f"<td>{_escape(item.prompt_risk_level)}</td>"
            f"<td>{_escape('; '.join(item.prompt_comments))}</td>"
            f"<td>{_escape('; '.join(item.prompt_suggestions))}</td>"
            f"<td>{_escape(', '.join(item.tags))}</td>"
            f"<td>{_escape(item.created_at.isoformat())}</td>"
            "</tr>"
            for item in prompt_memories
        )
        or "<tr><td colspan='7'>No prompt memories yet</td></tr>"
    )

    file_rows = (
        "".join(
            "<tr>"
            f"<td>{_escape(file.get('file_name'))}</td>"
            f"<td>{_escape(file.get('file_type'))}</td>"
            f"<td>{_escape(file.get('total_chunks'))}</td>"
            f"<td>{_escape(file.get('file_path'))}</td>"
            "</tr>"
            for file in files.list_files()
        )
        or "<tr><td colspan='4'>No indexed files yet</td></tr>"
    )

    trace_rows = (
        "".join(
            "<tr>"
            f"<td>{_escape(trace.name)}</td>"
            f"<td>{_escape(trace.model)}</td>"
            f"<td>{_escape(trace.status)}</td>"
            f"<td>{_escape(trace.latency_ms)}</td>"
            f"<td>${trace.estimated_cost:.6f}</td>"
            f"<td>{_escape(trace.created_at.isoformat())}</td>"
            "</tr>"
            for trace in traces[:50]
        )
        or "<tr><td colspan='6'>No traces yet</td></tr>"
    )

    rec_items = "".join(f"<li>{_escape(item)}</li>" for item in recommendations)
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GenAIScope Dashboard</title>
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
    <h1>GenAIScope Dashboard</h1>
    <div class="muted">Version {_escape(__version__)} · Generated {_escape(iso_now())}</div>
  </header>
  <main>
    <section>
      <h2>Overview</h2>
      <div class="grid">
        {_card("Total memories", memory_stats.total_memories)}
        {_card("Backend", memory.backend)}
        {_card("Namespace", memory.namespace)}
        {_card("Total documents", memory_stats.total_documents)}
        {_card("Total prompts", memory_stats.total_prompts)}
        {_card("Total traces", trace_stats.total_traces)}
        {_card("Estimated total cost", f"${trace_stats.total_estimated_cost:.6f}")}
        {_card("Average prompt score", memory_stats.average_prompt_score or "N/A")}
        {_card("Expired memories", memory_stats.expired_memories)}
        {_card("Duplicate memories", duplicate_count)}
        {_card("Semantic cache entries", cache_count)}
      </div>
    </section>
    <section>
      <h2>Memory Statistics</h2>
      <table><tr><th>Type</th><th>Count</th></tr>{_dict_rows(memory_stats.memories_by_type)}</table>
      <table><tr><th>Source</th><th>Count</th></tr>{_dict_rows(memory_stats.memories_by_source)}</table>
      <table><tr><th>User</th><th>Count</th></tr>{_dict_rows(memory_stats.memories_by_user)}</table>
      <table><tr><th>Project</th><th>Count</th></tr>{_dict_rows(memory_stats.memories_by_project)}</table>
      <table><tr><th>Workspace</th><th>Count</th></tr>{_dict_rows(memory_stats.memories_by_workspace)}</table>
    </section>
    <section>
      <h2>Prompt Quality Comments</h2>
      <table><tr><th>Prompt</th><th>Score</th><th>Risk</th><th>Comments</th><th>Suggestions</th><th>Tags</th><th>Created</th></tr>{prompt_rows}</table>
    </section>
    <section>
      <h2>File Memory</h2>
      <div class="grid">{_card("Indexed files", file_stats["total_files"])}{_card("Total chunks", file_stats["total_chunks"])}</div>
      <table><tr><th>File</th><th>Type</th><th>Chunks</th><th>Path</th></tr>{file_rows}</table>
    </section>
    <section>
      <h2>Trace Statistics</h2>
      <div class="grid">
        {_card("Success", trace_stats.success_count)}
        {_card("Errors", trace_stats.error_count)}
        {_card("Average latency", trace_stats.average_latency_ms or "N/A")}
        {_card("Input tokens", trace_stats.total_input_tokens)}
        {_card("Output tokens", trace_stats.total_output_tokens)}
      </div>
      <table><tr><th>Name</th><th>Model</th><th>Status</th><th>Latency ms</th><th>Cost</th><th>Created</th></tr>{trace_rows}</table>
    </section>
    <section>
      <h2>Cost Insights</h2>
      <table><tr><th>Metric</th><th>Value</th></tr><tr><td>Total estimated cost</td><td>${trace_stats.total_estimated_cost:.6f}</td></tr><tr><td>Models</td><td>{_escape(trace_stats.traces_by_model)}</td></tr></table>
    </section>
    <section>
      <h2>Recommendations</h2>
      <ul>{rec_items}</ul>
    </section>
  </main>
</body>
</html>
"""
    output.write_text(html_text, encoding="utf-8")
    memory.close()
    tracer.close()
    return output
