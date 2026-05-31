"""Tests for the v0.3.0 memory backend release."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path

import pytest
from typer.testing import CliRunner

from genaiscope.cache import SemanticCache
from genaiscope.cli.main import app
from genaiscope.core.errors import InvalidBackendError, RedisDependencyMissingError
from genaiscope.dashboard import generate_dashboard
from genaiscope.memory import (
    MemoryStore,
    SQLiteMemoryStore,
    dedupe_memories,
    export_memories,
    find_duplicates,
    import_memories,
)


def test_default_factory_scopes_ttl_and_cleanup(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "memory.db")
    assert isinstance(store, SQLiteMemoryStore)
    store.add("Project decision", user_id="u1", project_id="p1", workspace_id="w1")
    store.add("Other project", user_id="u1", project_id="p2")
    expired = store.add("short lived", ttl_seconds=1)
    store.connection.execute(
        "UPDATE memories SET expires_at = '2000-01-01T00:00:00+00:00' WHERE id = ?",
        (expired.id,),
    )
    store.connection.commit()
    assert len(store.list(project_id="p1")) == 1
    assert store.get(expired.id) is None
    assert store.stats().expired_memories == 1
    assert store.cleanup_expired() == 1


def test_invalid_backend() -> None:
    with pytest.raises(InvalidBackendError):
        MemoryStore(backend="unknown")


def test_dedupe_export_import_and_cache(tmp_path: Path) -> None:
    source = MemoryStore(db_path=tmp_path / "source.db")
    source.add("User prefers concise answers", user_id="sapan", project_id="memovo")
    source.add(" user prefers   concise answers ", user_id="sapan", project_id="memovo")
    assert len(find_duplicates(source)) == 1
    assert dedupe_memories(source, dry_run=True)["duplicates_removed"] == 1
    assert dedupe_memories(source, dry_run=False)["duplicates_removed"] == 1

    cache = SemanticCache(memory_store=source)
    cache.set("summarize refund policy", "Refunds are available.", user_id="sapan")
    assert cache.get("summarize refund policy", user_id="sapan").response == "Refunds are available."

    output = tmp_path / "memories.json"
    assert export_memories(source, output) == 2
    target = MemoryStore(db_path=tmp_path / "target.db")
    assert import_memories(target, output) == 2
    assert target.stats().total_memories == 2


def test_dashboard_backend_metadata(tmp_path: Path) -> None:
    output = generate_dashboard(output_path=tmp_path / "dashboard.html", db_path=tmp_path / "memory.db")
    html = output.read_text(encoding="utf-8")
    assert "Backend" in html
    assert "Namespace" in html
    assert "Semantic cache entries" in html


def test_redis_dependency_error_when_redis_is_not_installed() -> None:
    if find_spec("redis"):
        pytest.skip("redis-py is installed")
    with pytest.raises(RedisDependencyMissingError, match=r'pip install "genaiscope\[redis\]"'):
        MemoryStore(backend="redis")


def test_v030_cli_memory_workflow(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "memory.db"
    export_path = tmp_path / "memories.json"
    result = runner.invoke(
        app,
        [
            "memory", "add", "User prefers concise answers", "--user-id", "sapan",
            "--project-id", "memovo", "--importance", "8", "--db-path", str(db_path),
        ],
    )
    assert result.exit_code == 0
    assert runner.invoke(
        app, ["memory", "search", "concise answers", "--project-id", "memovo", "--db-path", str(db_path)]
    ).exit_code == 0
    assert runner.invoke(
        app, ["memory", "export", str(export_path), "--db-path", str(db_path)]
    ).exit_code == 0
    assert export_path.exists()
