"""CLI wiring tests for new v0.4.0 commands."""

from typer.testing import CliRunner

from genaiscope.cli.main import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.5.1" in result.output


def test_embed_test_local() -> None:
    result = runner.invoke(app, ["embed", "test", "hello world"])
    assert result.exit_code == 0
    assert "local_hash" in result.output
    assert "256" in result.output


def test_embed_test_help() -> None:
    result = runner.invoke(app, ["embed", "test", "--help"])
    assert result.exit_code == 0


def test_embed_reindex_help() -> None:
    result = runner.invoke(app, ["embed", "reindex", "--help"])
    assert result.exit_code == 0


def test_serve_mcp_help() -> None:
    result = runner.invoke(app, ["serve", "mcp", "--help"])
    assert result.exit_code == 0
    assert "transport" in result.output.lower() or "stdio" in result.output.lower()


def test_serve_mcp_help_shows_trace_flag() -> None:
    result = runner.invoke(app, ["serve", "mcp", "--help"])
    assert result.exit_code == 0
    assert "--trace" in result.output


def test_serve_api_help() -> None:
    result = runner.invoke(app, ["serve", "api", "--help"])
    assert result.exit_code == 0


def test_serve_api_help_shows_trace_flag() -> None:
    result = runner.invoke(app, ["serve", "api", "--help"])
    assert result.exit_code == 0
    assert "--trace" in result.output


def test_eval_memory_help() -> None:
    result = runner.invoke(app, ["eval", "memory", "--help"])
    assert result.exit_code == 0


def test_memory_search_with_mode_flag() -> None:
    result = runner.invoke(
        app,
        ["memory", "search", "test query", "--mode", "hybrid"],
    )
    assert result.exit_code == 0


def test_memory_search_vector_mode_degrades() -> None:
    """Vector mode with no embedder should degrade cleanly."""
    result = runner.invoke(
        app,
        ["memory", "search", "test query", "--mode", "vector"],
    )
    assert result.exit_code == 0
