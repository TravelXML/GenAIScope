"""CLI interface for GenAIScope."""

import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from genaiscope.analyzers import (
    CostAnalyzer,
    HallucinationDetector,
    PIIDetector,
    SafetyAnalyzer,
)
from genaiscope.cache import SemanticCache
from genaiscope.core.config import get_config
from genaiscope.core.logging import get_logger
from genaiscope.dashboard import generate_dashboard
from genaiscope.files import FileMemory
from genaiscope.inspect import Inspector
from genaiscope.memory import (
    MemoryStore,
    compact_memories,
    dedupe_memories,
    export_memories,
    find_duplicates,
    import_memories,
)
from genaiscope.tracing import LocalTracer

logger = get_logger(__name__)
console = Console()

app = typer.Typer(
    help="GenAIScope: Inspect, test, secure, optimize, and operationalize GenAI applications.",
    no_args_is_help=True,
)
memory_app = typer.Typer(help="Local memory commands.", no_args_is_help=True)
files_app = typer.Typer(help="Local file memory commands.", no_args_is_help=True)
trace_app = typer.Typer(help="Local trace commands.", no_args_is_help=True)
dashboard_app = typer.Typer(help="Local dashboard commands.", no_args_is_help=True)
cache_app = typer.Typer(help="Semantic cache commands.", no_args_is_help=True)
embed_app = typer.Typer(help="Embedding management commands.", no_args_is_help=True)
serve_app = typer.Typer(help="Server commands (MCP and REST API).", no_args_is_help=True)
eval_app = typer.Typer(help="Evaluation harness commands.", no_args_is_help=True)

app.add_typer(memory_app, name="memory")
app.add_typer(files_app, name="files")
app.add_typer(trace_app, name="trace")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(cache_app, name="cache")
app.add_typer(embed_app, name="embed")
app.add_typer(serve_app, name="serve")
app.add_typer(eval_app, name="eval")


def _parse_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def _truncate(value: str | None, length: int = 80) -> str:
    text = value or ""
    return text if len(text) <= length else text[: length - 3] + "..."


def _build_store(
    backend: str,
    redis_url: str,
    namespace: str,
    db_path: Path | None = None,
    embedder_name: str | None = None,
) -> object:
    """Build a memory store, optionally with an embedder attached."""
    embedder = None
    if embedder_name:
        try:
            from genaiscope.embeddings.factory import get_embedder
            embedder = get_embedder(embedder_name)
        except Exception as e:
            console.print(f"[yellow]Warning: embedder '{embedder_name}' not available: {e}[/yellow]")

    return MemoryStore(
        db_path=db_path,
        backend=backend,
        redis_url=redis_url,
        namespace=namespace,
        embedder=embedder,
    )


def _build_tracer(
    trace: bool,
    backend: str,
    redis_url: str,
    namespace: str,
    db_path: Path | None = None,
) -> LocalTracer | None:
    """Build a LocalTracer sharing the same backend/db_path as the memory store, or None if disabled."""
    if not trace:
        return None
    return LocalTracer(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)


# ──────────────────────────────────────────────────────────────────────────────
# Top-level commands
# ──────────────────────────────────────────────────────────────────────────────

@app.command()
def version() -> None:
    """Show version information."""
    from genaiscope import __version__

    console.print(f"GenAIScope version {__version__}")


@app.command()
def config_show() -> None:
    """Show current configuration."""
    config = get_config()

    table = Table(title="GenAIScope Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in config.to_dict().items():
        table.add_row(key, str(value))

    console.print(table)


@app.command()
def inspect_prompt(prompt: str, output_format: str = "text") -> None:
    """Inspect a prompt for quality and safety."""
    try:
        inspector = Inspector()
        report = inspector.inspect_prompt(prompt)

        if output_format == "json":
            console.print_json(report.model_dump_json())
        else:
            console.print(report.summary())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e


@app.command()
def detect_pii(text: str, redact: bool = False) -> None:
    """Detect PII in text."""
    detector = PIIDetector()
    detections = detector.detect(text)

    if detections:
        console.print("[yellow]Potential PII detected:[/yellow]")
        for pii_type, matches in detections.items():
            console.print(f"  {pii_type}: {matches}")

        if redact:
            redacted = detector.redact(text)
            console.print(f"\n[green]Redacted text:[/green]\n{redacted}")
    else:
        console.print("[green]No PII detected[/green]")


@app.command()
def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> None:
    """Estimate API costs."""
    analyzer = CostAnalyzer()
    costs = analyzer.estimate_cost(model, input_tokens, output_tokens)

    table = Table(title=f"Cost Estimate for {model}")
    table.add_column("Metric", style="cyan")
    table.add_column("Cost (USD)", style="magenta")

    for key, value in costs.items():
        table.add_row(key.replace("_", " ").title(), f"${value:.4f}")

    console.print(table)


@app.command()
def analyze_text(
    text: str,
    analyze_pii: bool = False,
    analyze_hallucination: bool = False,
    context: str | None = None,
) -> None:
    """Analyze text for various issues."""
    console.print("[bold]Text Analysis Report[/bold]\n")

    safety_analyzer = SafetyAnalyzer()
    safety_issues = safety_analyzer.analyze(text)

    if safety_issues:
        console.print("[yellow]Safety Issues:[/yellow]")
        for issue_type, matches in safety_issues.items():
            console.print(f"  {issue_type}: Found {len(matches)} occurrence(s)")

    if analyze_pii:
        pii_detector = PIIDetector()
        pii_detections = pii_detector.detect(text)

        if pii_detections:
            console.print("\n[yellow]PII Detections:[/yellow]")
            for pii_type, matches in pii_detections.items():
                console.print(f"  {pii_type}: {len(matches)} occurrence(s)")

    if analyze_hallucination and context:
        hallucination_detector = HallucinationDetector()
        hallucination_results = hallucination_detector.detect(context, text)

        console.print("\n[yellow]Hallucination Analysis:[/yellow]")
        console.print(f"  Hallucination Risk: {hallucination_results['hallucination_risk']:.2f}")
        console.print(f"  Contains Uncertainty: {hallucination_results['contains_uncertainty']}")
        console.print(
            f"  Unsupported Statements: {hallucination_results['unsupported_statements']}"
        )


@app.command()
def validate_output(
    output: str,
    format: str = typer.Option("json", "--format", "-f", help="Expected output format"),
) -> None:
    """Validate structured output."""
    from genaiscope.analyzers import StructuredOutputValidator

    validator = StructuredOutputValidator()

    if format.lower() == "json":
        result = validator.validate_json(output)
    elif format.lower() == "xml":
        result = validator.validate_xml(output)
    elif format.lower() == "csv":
        result = validator.validate_csv(output)
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
        raise typer.Exit(code=1)

    if result["valid"]:
        console.print(f"[green]✓ Valid {format.upper()} output[/green]")
    else:
        console.print(f"[red]✗ Invalid {format.upper()} output[/red]")
        if "error" in result:
            console.print(f"  Error: {result['error']}")


# ──────────────────────────────────────────────────────────────────────────────
# Memory commands
# ──────────────────────────────────────────────────────────────────────────────

@memory_app.command("add")
def memory_add(
    content: str,
    memory_type: str = typer.Option("general", "--type", help="Memory type."),
    user_id: str | None = typer.Option(None, "--user-id", help="User scope."),
    workspace_id: str | None = typer.Option(None, "--workspace-id"),
    project_id: str | None = typer.Option(None, "--project-id"),
    agent_id: str | None = typer.Option(None, "--agent-id"),
    session_id: str | None = typer.Option(None, "--session-id"),
    importance: int = typer.Option(5, "--importance"),
    ttl_days: int | None = typer.Option(None, "--ttl-days"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags."),
    db_path: Path | None = typer.Option(None, "--db-path", help="SQLite DB path."),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
    embedder: str | None = typer.Option(None, "--embedder", help="Embedder backend."),
) -> None:
    """Add a local memory."""

    memory = _build_store(backend, redis_url, namespace, db_path, embedder)
    item = memory.add(content, memory_type=memory_type, user_id=user_id, workspace_id=workspace_id, project_id=project_id, agent_id=agent_id, session_id=session_id, importance=importance, ttl_days=ttl_days, tags=_parse_tags(tags))
    console.print(
        Panel.fit(f"Memory ID: {item.id}\nType: {item.memory_type}", title="Memory added")
    )
    memory.close()


@memory_app.command("add-prompt")
def memory_add_prompt(
    prompt: str,
    user_id: str | None = typer.Option(None, "--user-id", help="User scope."),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags."),
    db_path: Path | None = typer.Option(None, "--db-path", help="SQLite DB path."),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Add a prompt memory and show quality coaching."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    item = memory.add_prompt(prompt, user_id=user_id, tags=_parse_tags(tags))
    console.print(
        Panel.fit(
            f"Memory ID: {item.id}\nPrompt Score: {item.prompt_score}\nRisk Level: {item.prompt_risk_level}",
            title="Prompt stored",
        )
    )
    for comment in item.prompt_comments:
        console.print(f"[yellow]Comment:[/yellow] {comment}")
    for suggestion in item.prompt_suggestions:
        console.print(f"[green]Suggestion:[/green] {suggestion}")
    memory.close()


@memory_app.command("search")
def memory_search(
    query: str,
    limit: int = typer.Option(10, "--limit", "-l"),
    mode: str = typer.Option("hybrid", "--mode", help="Search mode: keyword|vector|hybrid"),
    user_id: str | None = typer.Option(None, "--user-id"),
    workspace_id: str | None = typer.Option(None, "--workspace-id"),
    project_id: str | None = typer.Option(None, "--project-id"),
    memory_type: str | None = typer.Option(None, "--type"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
    embedder: str | None = typer.Option(None, "--embedder", help="Embedder: local|sentence-transformers|openai"),
) -> None:
    """Search local memories."""

    memory = _build_store(backend, redis_url, namespace, db_path, embedder)
    results = memory.search(query, user_id=user_id, workspace_id=workspace_id, project_id=project_id, memory_type=memory_type, limit=limit, mode=mode)
    table = Table(title=f"Memory Search Results [mode={mode}]")
    table.add_column("Score")
    table.add_column("Type")
    table.add_column("Content")
    table.add_column("Vec")
    table.add_column("KW")
    for result in results:
        table.add_row(
            f"{result.score:.2f}",
            result.item.memory_type,
            _truncate(result.item.content),
            f"{result.vector_score:.2f}",
            f"{result.keyword_score:.2f}",
        )
    console.print(table)
    memory.close()


@memory_app.command("list")
def memory_list(
    limit: int = typer.Option(20, "--limit", "-l"),
    user_id: str | None = typer.Option(None, "--user-id"),
    project_id: str | None = typer.Option(None, "--project-id"),
    workspace_id: str | None = typer.Option(None, "--workspace-id"),
    include_expired: bool = typer.Option(False, "--include-expired"),
    memory_type: str | None = typer.Option(None, "--type"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """List local memories."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    table = Table(title="Memories")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Content")
    table.add_column("Created")
    for item in memory.list(user_id=user_id, project_id=project_id, workspace_id=workspace_id, memory_type=memory_type, include_expired=include_expired, limit=limit):
        table.add_row(
            item.id, item.memory_type, _truncate(item.content), item.created_at.isoformat()
        )
    console.print(table)
    memory.close()


@memory_app.command("show")
def memory_show(memory_id: str, db_path: Path | None = typer.Option(None, "--db-path")) -> None:
    """Show one memory."""

    memory = MemoryStore(db_path=db_path)
    item = memory.get(memory_id)
    if item is None:
        console.print("[red]Memory not found[/red]")
        raise typer.Exit(code=1)
    console.print_json(item.model_dump_json())
    memory.close()


@memory_app.command("delete")
def memory_delete(memory_id: str, db_path: Path | None = typer.Option(None, "--db-path")) -> None:
    """Delete one memory."""

    memory = MemoryStore(db_path=db_path)
    deleted = memory.delete(memory_id)
    console.print("[green]Deleted[/green]" if deleted else "[yellow]Memory not found[/yellow]")
    memory.close()


@memory_app.command("stats")
def memory_stats(
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Show memory statistics."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    console.print_json(memory.stats().model_dump_json())
    memory.close()


@memory_app.command("clear")
def memory_clear(
    yes: bool = typer.Option(False, "--yes", help="Confirm clearing all memories."),
    db_path: Path | None = typer.Option(None, "--db-path"),
) -> None:
    """Clear all memories."""

    memory = MemoryStore(db_path=db_path)
    count = memory.clear(confirm=yes)
    console.print(f"[green]Cleared {count} memories[/green]")
    memory.close()


@memory_app.command("cleanup-expired")
def memory_cleanup_expired(
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Delete expired memories."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    console.print(f"[green]Cleaned {memory.cleanup_expired()} expired memories[/green]")
    memory.close()


@memory_app.command("duplicates")
def memory_duplicates(
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Show duplicate memory groups."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    groups = find_duplicates(memory)
    console.print_json(data={"duplicate_groups": [[item.id for item in group] for group in groups]})
    memory.close()


@memory_app.command("dedupe")
def memory_dedupe(
    apply: bool = typer.Option(False, "--apply"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    strategy: str = typer.Option("keep_newest", "--strategy"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Preview or apply duplicate cleanup."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    console.print_json(data=dedupe_memories(memory, strategy=strategy, dry_run=dry_run or not apply))
    memory.close()


def _resolve_summarizer(summarizer: str, summarizer_model: str | None):
    """Build a real LLM summarizer for --summarizer openai|anthropic|gemini."""

    from genaiscope.adapters.summarizers import (
        anthropic_summarizer,
        gemini_summarizer,
        openai_summarizer,
    )

    factories = {"openai": openai_summarizer, "anthropic": anthropic_summarizer, "gemini": gemini_summarizer}
    if summarizer not in factories:
        raise ValueError(f"Unknown summarizer: {summarizer}. Use 'none', 'openai', 'anthropic', or 'gemini'.")
    kwargs = {"model": summarizer_model} if summarizer_model else {}
    return factories[summarizer](**kwargs)


@memory_app.command("compact")
def memory_compact(
    apply: bool = typer.Option(False, "--apply", help="Apply compaction (default is dry-run)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Force dry-run even if --apply is passed."),
    strategy: str = typer.Option("synthesize", "--strategy", help="synthesize|keep_best"),
    threshold: float = typer.Option(0.92, "--threshold", help="Cosine similarity threshold for clustering."),
    summarizer: str = typer.Option("none", "--summarizer", help="none|openai|anthropic|gemini"),
    summarizer_model: str | None = typer.Option(None, "--summarizer-model", help="Model name for the chosen summarizer SDK."),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
    embedder: str | None = typer.Option(None, "--embedder", help="Embedder: local|sentence-transformers|openai"),
    user_id: str | None = typer.Option(None, "--user-id"),
    project_id: str | None = typer.Option(None, "--project-id"),
) -> None:
    """Preview or apply semantic memory compaction (merges paraphrased duplicates, not just exact-text ones)."""

    memory = _build_store(backend, redis_url, namespace, db_path, embedder)
    try:
        summarizer_fn = _resolve_summarizer(summarizer, summarizer_model) if summarizer != "none" else None
        report = compact_memories(
            memory,
            strategy=strategy,
            summarizer=summarizer_fn,
            threshold=threshold,
            dry_run=dry_run or not apply,
            user_id=user_id,
            project_id=project_id,
        )
        console.print_json(data=report.model_dump())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e
    finally:
        memory.close()


@memory_app.command("export")
def memory_export(
    output: Path,
    format: str = typer.Option("json", "--format"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Export memories for backup or migration."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    console.print(f"[green]Exported {export_memories(memory, output, format=format)} memories[/green]")
    memory.close()


@memory_app.command("import")
def memory_import(
    input: Path,
    merge_strategy: str = typer.Option("skip_existing", "--merge-strategy"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Import memories from JSON or JSONL."""

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    console.print(f"[green]Imported {import_memories(memory, input, merge_strategy=merge_strategy)} memories[/green]")
    memory.close()


# ──────────────────────────────────────────────────────────────────────────────
# File memory commands
# ──────────────────────────────────────────────────────────────────────────────

@files_app.command("add")
def files_add(
    path: Path,
    recursive: bool = typer.Option(False, "--recursive", "-r"),
    tags: str | None = typer.Option(None, "--tags"),
    user_id: str | None = typer.Option(None, "--user-id"),
    db_path: Path | None = typer.Option(None, "--db-path"),
) -> None:
    """Add a file or folder to file memory."""

    files = FileMemory(db_path=db_path)
    items = (
        files.add_folder(path, recursive=recursive, tags=_parse_tags(tags), user_id=user_id)
        if path.is_dir()
        else files.add_file(path, tags=_parse_tags(tags), user_id=user_id)
    )
    console.print(f"[green]Indexed {len(items)} chunks[/green]")


@files_app.command("search")
def files_search(
    query: str,
    limit: int = typer.Option(10, "--limit", "-l"),
    user_id: str | None = typer.Option(None, "--user-id"),
    db_path: Path | None = typer.Option(None, "--db-path"),
) -> None:
    """Search indexed file memory."""

    files = FileMemory(db_path=db_path)
    table = Table(title="File Search Results")
    table.add_column("Score")
    table.add_column("File")
    table.add_column("Content")
    for result in files.search(query, limit=limit, user_id=user_id):
        table.add_row(
            f"{result.score:.2f}",
            str(result.item.metadata.get("file_name", "")),
            _truncate(result.item.content),
        )
    console.print(table)


@files_app.command("list")
def files_list(db_path: Path | None = typer.Option(None, "--db-path")) -> None:
    """List indexed files."""

    files = FileMemory(db_path=db_path)
    table = Table(title="Indexed Files")
    table.add_column("File")
    table.add_column("Type")
    table.add_column("Chunks")
    table.add_column("Path")
    for item in files.list_files():
        table.add_row(
            str(item.get("file_name")),
            str(item.get("file_type")),
            str(item.get("total_chunks")),
            str(item.get("file_path")),
        )
    console.print(table)


@files_app.command("stats")
def files_stats(db_path: Path | None = typer.Option(None, "--db-path")) -> None:
    """Show file memory stats."""

    files = FileMemory(db_path=db_path)
    console.print_json(data=files.stats())


# ──────────────────────────────────────────────────────────────────────────────
# Trace commands
# ──────────────────────────────────────────────────────────────────────────────

@trace_app.command("list")
def trace_list(
    limit: int = typer.Option(20, "--limit", "-l"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
) -> None:
    """List local traces."""

    tracer = LocalTracer(db_path=db_path, backend=backend, redis_url=redis_url)
    table = Table(title="Traces")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Cost")
    for trace in tracer.list(limit=limit):
        table.add_row(trace.id, trace.name, trace.status, f"${trace.estimated_cost:.6f}")
    console.print(table)
    tracer.close()


@trace_app.command("show")
def trace_show(trace_id: str, db_path: Path | None = typer.Option(None, "--db-path")) -> None:
    """Show one trace."""

    tracer = LocalTracer(db_path=db_path)
    trace = tracer.get(trace_id)
    if trace is None:
        console.print("[red]Trace not found[/red]")
        raise typer.Exit(code=1)
    console.print_json(trace.model_dump_json())
    tracer.close()


@trace_app.command("stats")
def trace_stats(db_path: Path | None = typer.Option(None, "--db-path"), backend: str = typer.Option("sqlite", "--backend"), redis_url: str = typer.Option("redis://localhost:6379", "--redis-url")) -> None:
    """Show trace stats."""

    tracer = LocalTracer(db_path=db_path, backend=backend, redis_url=redis_url)
    console.print_json(tracer.stats().model_dump_json())
    tracer.close()


@trace_app.command("clear")
def trace_clear(
    yes: bool = typer.Option(False, "--yes", help="Confirm clearing all traces."),
    db_path: Path | None = typer.Option(None, "--db-path"),
) -> None:
    """Clear local traces."""

    tracer = LocalTracer(db_path=db_path)
    count = tracer.clear(confirm=yes)
    console.print(f"[green]Cleared {count} traces[/green]")
    tracer.close()


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard commands
# ──────────────────────────────────────────────────────────────────────────────

@dashboard_app.command("generate")
def dashboard_generate(
    output: Path | None = typer.Option(None, "--output", "-o"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Generate the static local dashboard."""

    path = generate_dashboard(output_path=output, db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    console.print(f"Dashboard generated: {path}")


@dashboard_app.command("open")
def dashboard_open(
    output: Path | None = typer.Option(None, "--output", "-o"),
    db_path: Path | None = typer.Option(None, "--db-path"),
) -> None:
    """Generate and open the static local dashboard."""

    path = generate_dashboard(output_path=output, db_path=db_path)
    webbrowser.open(path.resolve().as_uri())
    console.print(f"Dashboard opened: {path}")


# ──────────────────────────────────────────────────────────────────────────────
# Cache commands
# ──────────────────────────────────────────────────────────────────────────────

@cache_app.command("stats")
def cache_stats(db_path: Path | None = typer.Option(None, "--db-path")) -> None:
    """Show semantic cache statistics."""

    console.print_json(SemanticCache(db_path=db_path).stats().model_dump_json())


@cache_app.command("clear")
def cache_clear(yes: bool = typer.Option(False, "--yes"), db_path: Path | None = typer.Option(None, "--db-path")) -> None:
    """Clear semantic cache entries."""

    console.print(f"[green]Cleared {SemanticCache(db_path=db_path).clear(confirm=yes)} cache entries[/green]")


# ──────────────────────────────────────────────────────────────────────────────
# Embed commands (v0.4.0)
# ──────────────────────────────────────────────────────────────────────────────

@embed_app.command("test")
def embed_test(
    text: str,
    embedder: str = typer.Option("local", "--embedder", "-e", help="Embedder backend."),
) -> None:
    """Test an embedder — show vector dimensions and first few values."""

    try:
        from genaiscope.embeddings.factory import get_embedder

        emb = get_embedder(embedder)
        vec = emb.embed(text)
        table = Table(title=f"Embedding [{emb.name}]")
        table.add_column("Property")
        table.add_column("Value")
        table.add_row("Backend", emb.name)
        table.add_row("Dimensions", str(emb.dimensions))
        table.add_row("First 8 values", str([round(v, 4) for v in vec[:8]]))
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e


@embed_app.command("reindex")
def embed_reindex(
    embedder: str = typer.Option("local", "--embedder", "-e", help="Embedder backend."),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Recompute and store embeddings for all memories."""

    try:
        from genaiscope.embeddings.factory import get_embedder

        emb = get_embedder(embedder)
        memory = MemoryStore(
            db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace, embedder=emb
        )
        count = memory.reindex_embeddings() if hasattr(memory, "reindex_embeddings") else 0
        console.print(f"[green]Reindexed {count} memories with embedder '{emb.name}'[/green]")
        memory.close()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e


# ──────────────────────────────────────────────────────────────────────────────
# Serve commands (v0.4.0)
# ──────────────────────────────────────────────────────────────────────────────

@serve_app.command("mcp")
def serve_mcp(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio|http"),
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8848, "--port"),
    auth: str = typer.Option("none", "--auth", help="Auth mode: none|bearer"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
    embedder: str | None = typer.Option(None, "--embedder"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    trace: bool = typer.Option(False, "--trace", help="Enable local tracing for tool calls."),
) -> None:
    """Run the GenAIScope MCP memory server."""

    try:
        from genaiscope.mcp.server import run_http, run_stdio
    except Exception as e:
        console.print(f"[red]MCP server error: {e}[/red]")
        raise typer.Exit(code=1) from e

    store = _build_store(backend, redis_url, namespace, db_path, embedder)
    tracer = _build_tracer(trace, backend, redis_url, namespace, db_path)
    console.print(f"[bold green]GenAIScope MCP server starting ({transport})[/bold green]")

    if transport == "stdio":
        run_stdio(store, tracer=tracer)
    else:
        console.print(f"Listening on {host}:{port}")
        run_http(store, host=host, port=port, tracer=tracer)


@serve_app.command("api")
def serve_api(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    auth: str = typer.Option("none", "--auth", help="Auth mode: none|bearer"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
    embedder: str | None = typer.Option(None, "--embedder"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    trace: bool = typer.Option(False, "--trace", help="Enable local tracing for API requests."),
) -> None:
    """Run the GenAIScope REST API server."""

    try:
        from genaiscope.server.app import run_api_server
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")
        raise typer.Exit(code=1) from e

    store = _build_store(backend, redis_url, namespace, db_path, embedder)
    tracer = _build_tracer(trace, backend, redis_url, namespace, db_path)
    auth_enabled = auth == "bearer"
    console.print(f"[bold green]GenAIScope REST API starting on {host}:{port}[/bold green]")
    run_api_server(store, host=host, port=port, auth_enabled=auth_enabled, tracer=tracer)


# ──────────────────────────────────────────────────────────────────────────────
# Eval commands (v0.4.0)
# ──────────────────────────────────────────────────────────────────────────────

@eval_app.command("memory")
def eval_memory(
    mode: str | None = typer.Option(None, "--mode", help="Run only this mode: keyword|vector|hybrid"),
    embedder: str = typer.Option("local", "--embedder", "-e"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    dataset: Path | None = typer.Option(None, "--dataset", "-d", help="Custom eval dataset JSON."),
) -> None:
    """Run the memory retrieval eval harness."""

    from genaiscope.evals.memory_eval import load_eval_dataset, run_eval

    ds = None
    if dataset:
        try:
            ds = load_eval_dataset(dataset)
        except Exception as e:
            console.print(f"[red]Failed to load dataset: {e}[/red]")
            raise typer.Exit(code=1) from e

    modes = [mode] if mode else ["keyword", "hybrid"]
    with console.status("Running memory eval..."):
        report = run_eval(dataset=ds, modes=modes, embedder_name=embedder, top_k=top_k)

    table = Table(title=f"Memory Retrieval Eval (top-{top_k}, dataset_size={report.dataset_size})")
    table.add_column("Mode")
    table.add_column("Embedder")
    table.add_column("Recall@k")
    table.add_column("Precision@k")
    table.add_column("MRR")
    for r in report.results:
        table.add_row(
            r.mode, r.embedder,
            f"{r.recall_at_k:.3f}", f"{r.precision_at_k:.3f}", f"{r.mrr:.3f}",
        )
    console.print(table)


# ──────────────────────────────────────────────────────────────────────────────
# Context Doctor commands (v0.6.0)
# ──────────────────────────────────────────────────────────────────────────────

@app.command()
def init(
    db_path: Path | None = typer.Option(None, "--db-path"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Initialize a local GenAIScope workspace."""

    from genaiscope.memory.utils import default_db_path

    target = db_path or default_db_path()
    memory = MemoryStore(db_path=target, namespace=namespace)
    tracer = LocalTracer(db_path=target, namespace=namespace)
    memory.close()
    tracer.close()
    console.print(
        Panel.fit(
            f"Workspace ready at {target}\n\n"
            "Next steps:\n"
            '  genaiscope memory add "..." --type profile_memory\n'
            '  genaiscope diagnose --prompt "..."\n'
            "  genaiscope report --out genaiscope_report.html",
            title="GenAIScope initialized",
        )
    )


@app.command()
def diagnose(
    prompt: str = typer.Option(..., "--prompt", help="The prompt to diagnose."),
    response: str | None = typer.Option(None, "--response", help="Optional response to evaluate."),
    provider: str | None = typer.Option(None, "--provider"),
    model: str | None = typer.Option(None, "--model"),
    top_k: int = typer.Option(5, "--top-k"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
    embedder: str | None = typer.Option(None, "--embedder"),
) -> None:
    """Diagnose a prompt: missing context, health score, and a recommended rewrite."""

    from genaiscope.context import ContextBuilder
    from genaiscope.doctor import ContextDoctor

    memory = _build_store(backend, redis_url, namespace, db_path, embedder)
    ctx = ContextBuilder(memory).build(prompt, top_k=top_k)
    report = ContextDoctor().diagnose(
        prompt=prompt,
        response=response,
        memories_used=ctx.retrieved_memories,
        provider=provider,
        model=model,
    )
    memory.close()

    console.print(Panel.fit(f"Context Health Score: {report.context_health_score}/100", title="Context Doctor"))

    table = Table(title="Sub-scores")
    table.add_column("Metric")
    table.add_column("Score")
    for field in (
        "prompt_clarity_score",
        "context_completeness_score",
        "memory_match_score",
        "model_fit_score",
        "token_efficiency_score",
        "hallucination_risk_score",
        "answer_specificity_score",
    ):
        table.add_row(field, str(getattr(report, field)))
    console.print(table)

    console.print(f"[bold]Detected intent:[/bold] {report.detected_intent}")
    console.print(f"[bold]Recommended model type:[/bold] {report.recommended_model_type}")
    if report.missing_context:
        console.print("[yellow]Missing context:[/yellow] " + ", ".join(report.missing_context))
    if report.prompt_issues:
        console.print("[red]Prompt issues:[/red] " + ", ".join(report.prompt_issues))
    console.print(f"\n[bold green]Recommended prompt:[/bold green]\n{report.recommended_prompt}")
    if report.improvement_tips:
        console.print("\n[bold]Improvement tips:[/bold]")
        for tip in report.improvement_tips:
            console.print(f"  - {tip}")


@app.command()
def analytics(
    days: int = typer.Option(7, "--days", help="Usage summary window."),
    pattern_days: int = typer.Option(30, "--pattern-days", help="Prompt pattern window."),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Show token/cost/latency usage and prompt-pattern analytics."""

    from genaiscope.analytics import prompt_patterns, usage_summary

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    tracer = LocalTracer(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)

    usage = usage_summary(tracer, days=days)
    table = Table(title=f"Usage summary (last {days} days)")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Total requests", str(usage.total_requests))
    table.add_row("Total tokens", str(usage.total_tokens))
    table.add_row("Estimated cost", f"${usage.total_estimated_cost:.6f}")
    table.add_row("Average latency (ms)", str(usage.average_latency_ms or "N/A"))
    console.print(table)

    patterns = prompt_patterns(memory, tracer, days=pattern_days)
    console.print(f"\n[bold]Top categories:[/bold] {', '.join(patterns.top_topics) or 'none yet'}")
    if patterns.repeated_weak_patterns:
        console.print("[yellow]Repeated weak patterns:[/yellow]")
        for item in patterns.repeated_weak_patterns:
            console.print(f"  - {item}")
    if patterns.best_prompt_templates:
        console.print("[green]Best prompt templates:[/green]")
        for item in patterns.best_prompt_templates:
            console.print(f"  - {item}")

    memory.close()
    tracer.close()


@app.command()
def report(
    out: Path = typer.Option(Path("genaiscope_report.html"), "--out"),
    days: int = typer.Option(30, "--days"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Generate the Context Doctor HTML report (distinct from `dashboard generate`)."""

    from genaiscope.report import generate_html

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    tracer = LocalTracer(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    generated = generate_html(out, memory=memory, tracer=tracer, days=days)
    memory.close()
    tracer.close()
    console.print(f"[green]Report generated at {generated}[/green]")


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="The prompt to send to a live LLM provider."),
    provider: str = typer.Option("auto", "--provider", "-p", help="auto|openai|anthropic|google"),
    model: str | None = typer.Option(None, "--model"),
    cost_sensitive: bool = typer.Option(False, "--cost-sensitive"),
    privacy_sensitive: bool = typer.Option(False, "--privacy-sensitive"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Call a live LLM provider (auto-routed by default) and log the interaction
    with an attached Context Doctor health score. Requires the providers extra
    and the relevant *_API_KEY environment variable."""

    from genaiscope.gateway import GatewayClient

    memory = _build_store(backend, redis_url, namespace, db_path, None)
    tracer = LocalTracer(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    try:
        result = GatewayClient(memory, tracer).complete(
            prompt, provider=provider, model=model,
            cost_sensitive=cost_sensitive, privacy_sensitive=privacy_sensitive,
        )
    except Exception as e:
        console.print(f"[red]Gateway error: {e}[/red]")
        raise typer.Exit(code=1) from e
    finally:
        memory.close()
        tracer.close()

    console.print(Panel.fit(result.text, title=f"{result.provider} / {result.model}"))
    console.print(
        f"[bold]Context Health Score:[/bold] {result.context_health_score}/100  "
        f"[bold]Tokens:[/bold] {result.input_tokens}/{result.output_tokens}  "
        f"[bold]Est. cost:[/bold] ${result.estimated_cost:.6f}"
    )


@app.command()
def export(
    out: Path = typer.Option(Path("genaiscope_export.json"), "--out"),
    format: str = typer.Option("json", "--format", help="json|jsonl|langfuse"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    backend: str = typer.Option("sqlite", "--backend"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis-url"),
    namespace: str = typer.Option("genaiscope", "--namespace"),
) -> None:
    """Export memories (json/jsonl, alias for `memory export`) or traces as a
    Langfuse batch-ingestion file (`--format langfuse`)."""

    if format == "langfuse":
        from genaiscope.export import export_langfuse

        tracer = LocalTracer(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
        path = export_langfuse(tracer, out)
        tracer.close()
        console.print(f"[green]Exported traces to {path} (Langfuse batch-ingestion format)[/green]")
        return

    memory = MemoryStore(db_path=db_path, backend=backend, redis_url=redis_url, namespace=namespace)
    count = export_memories(memory, out, format=format)
    memory.close()
    console.print(f"[green]Exported {count} memories to {out}[/green]")


if __name__ == "__main__":
    app()
