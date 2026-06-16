"""MCP server import tests — skips gracefully without mcp extra."""

import pytest


def test_mcp_server_import_without_mcp() -> None:
    """Importing server module itself never crashes."""
    from genaiscope.mcp import server as mcp_server_module

    assert mcp_server_module is not None


def test_run_stdio_raises_without_mcp(tmp_path) -> None:
    """run_stdio should raise MCPDependencyMissingError when mcp not installed."""
    try:
        import mcp  # noqa: F401

        pytest.skip("mcp is installed — skip missing-dep test")
    except ImportError:
        pass

    from genaiscope.core.errors import MCPDependencyMissingError
    from genaiscope.memory.factory import MemoryStore
    from genaiscope.mcp.server import run_stdio

    store = MemoryStore(db_path=tmp_path / "m.db")
    with pytest.raises(MCPDependencyMissingError):
        run_stdio(store)
    store.close()
