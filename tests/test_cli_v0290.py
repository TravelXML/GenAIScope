"""Tests for v0.2.90 CLI commands."""

from typer.testing import CliRunner

from genaiscope import __version__
from genaiscope.cli.main import app


def test_cli_memory_files_trace_dashboard(tmp_path):
    runner = CliRunner()
    db_path = tmp_path / "memory.db"
    sample = tmp_path / "README.md"
    sample.write_text("Installation with pip install genaiscope.", encoding="utf-8")

    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output

    result = runner.invoke(
        app,
        [
            "memory",
            "add",
            "User prefers concise answers",
            "--type",
            "preference",
            "--db-path",
            str(db_path),
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        app, ["memory", "add-prompt", "Summarize this properly.", "--db-path", str(db_path)]
    )
    assert result.exit_code == 0
    assert "Prompt Score" in result.output

    result = runner.invoke(app, ["memory", "search", "concise", "--db-path", str(db_path)])
    assert result.exit_code == 0
    assert "concise" in result.output

    result = runner.invoke(app, ["files", "add", str(sample), "--db-path", str(db_path)])
    assert result.exit_code == 0

    result = runner.invoke(app, ["trace", "stats", "--db-path", str(db_path)])
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "dashboard",
            "generate",
            "--output",
            str(tmp_path / "dashboard.html"),
            "--db-path",
            str(db_path),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "dashboard.html").exists()
