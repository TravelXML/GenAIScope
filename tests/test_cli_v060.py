"""CLI wiring tests for the v0.6.0 Context Doctor commands."""

from pathlib import Path

from typer.testing import CliRunner

from genaiscope.cli.main import app

runner = CliRunner()


def test_init_creates_workspace(tmp_path: Path) -> None:
    db_path = tmp_path / "init.db"
    result = runner.invoke(app, ["init", "--db-path", str(db_path)])
    assert result.exit_code == 0
    assert db_path.exists()


def test_diagnose_command(tmp_path: Path) -> None:
    db_path = tmp_path / "diag.db"
    result = runner.invoke(app, ["diagnose", "--prompt", "Write answer for this job.", "--db-path", str(db_path)])
    assert result.exit_code == 0
    assert "Context Health Score" in result.output
    assert "Recommended prompt" in result.output


def test_analytics_command(tmp_path: Path) -> None:
    db_path = tmp_path / "analytics.db"
    result = runner.invoke(app, ["analytics", "--db-path", str(db_path)])
    assert result.exit_code == 0
    assert "Usage summary" in result.output


def test_report_command(tmp_path: Path) -> None:
    db_path = tmp_path / "report.db"
    out_path = tmp_path / "report.html"
    result = runner.invoke(app, ["report", "--db-path", str(db_path), "--out", str(out_path)])
    assert result.exit_code == 0
    assert out_path.exists()


def test_export_command(tmp_path: Path) -> None:
    db_path = tmp_path / "export.db"
    out_path = tmp_path / "export.json"
    runner.invoke(app, ["memory", "add", "hello world", "--db-path", str(db_path)])
    result = runner.invoke(app, ["export", "--db-path", str(db_path), "--out", str(out_path)])
    assert result.exit_code == 0
    assert out_path.exists()


def test_all_new_commands_have_help() -> None:
    for command in ("init", "diagnose", "analytics", "report", "export"):
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0
