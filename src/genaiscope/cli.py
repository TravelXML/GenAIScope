"""CLI interface for GenAIScope."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from genaiscope.inspect import Inspector
from genaiscope.core.config import get_config
from genaiscope.core.logging import get_logger
from genaiscope.analyzers import (
    CostAnalyzer,
    PIIDetector,
    HallucinationDetector,
    SafetyAnalyzer,
)

logger = get_logger(__name__)
console = Console()

app = typer.Typer(
    help="GenAIScope: Inspect, test, secure, optimize, and operationalize GenAI applications.",
    no_args_is_help=True,
)


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
        raise typer.Exit(code=1)


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
def estimate_cost(
    model: str, input_tokens: int, output_tokens: int
) -> None:
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
    context: Optional[str] = None,
) -> None:
    """Analyze text for various issues."""
    console.print("[bold]Text Analysis Report[/bold]\n")

    # Safety analysis
    safety_analyzer = SafetyAnalyzer()
    safety_issues = safety_analyzer.analyze(text)

    if safety_issues:
        console.print("[yellow]Safety Issues:[/yellow]")
        for issue_type, matches in safety_issues.items():
            console.print(f"  {issue_type}: Found {len(matches)} occurrence(s)")

    # PII analysis
    if analyze_pii:
        pii_detector = PIIDetector()
        pii_detections = pii_detector.detect(text)
        
        if pii_detections:
            console.print("\n[yellow]PII Detections:[/yellow]")
            for pii_type, matches in pii_detections.items():
                console.print(f"  {pii_type}: {len(matches)} occurrence(s)")

    # Hallucination analysis
    if analyze_hallucination and context:
        hallucination_detector = HallucinationDetector()
        hallucination_results = hallucination_detector.detect(context, text)
        
        console.print("\n[yellow]Hallucination Analysis:[/yellow]")
        console.print(f"  Hallucination Risk: {hallucination_results['hallucination_risk']:.2f}")
        console.print(f"  Contains Uncertainty: {hallucination_results['contains_uncertainty']}")
        console.print(f"  Unsupported Statements: {hallucination_results['unsupported_statements']}")


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


if __name__ == "__main__":
    app()
