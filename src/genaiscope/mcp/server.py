"""MCP memory server — stdio and StreamableHTTP transports.

Requires: pip install "genaiscope[mcp]"

Usage:
    # stdio (local — Claude Desktop / Gemini CLI)
    python -m genaiscope serve mcp

    # HTTP (remote — Claude paid / ChatGPT / Gemini Enterprise)
    python -m genaiscope serve mcp --transport http --host 0.0.0.0 --port 8848
"""

from __future__ import annotations

from typing import Any

from genaiscope.core.errors import MCPDependencyMissingError
from genaiscope.mcp.tools import (
    tool_memory_add_prompt,
    tool_memory_context,
    tool_memory_list,
    tool_memory_remember,
    tool_memory_search,
    tool_memory_stats,
)


def _require_mcp() -> Any:
    try:
        import mcp
        return mcp
    except ImportError as exc:
        raise MCPDependencyMissingError(
            "mcp is not installed. Run: pip install \"genaiscope[mcp]\""
        ) from exc


def build_mcp_server(store: Any, server_name: str = "GenAIScope Memory") -> Any:
    """Build a FastMCP / MCP server object with GenAIScope tools registered."""
    _require_mcp()

    try:
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP(server_name)
        _register_fastmcp(mcp_server, store)
        return mcp_server
    except ImportError:
        pass

    # fallback: low-level MCP Server
    from mcp.server import Server
    from mcp.types import TextContent, Tool

    server = Server(server_name)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _tool_definitions()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        import json
        result = _dispatch(store, name, arguments)
        return [TextContent(type="text", text=json.dumps(result, default=str))]

    return server


def _register_fastmcp(mcp_server: Any, store: Any) -> None:
    """Register tools on a FastMCP instance."""

    @mcp_server.tool()
    def memory_remember(
        content: str,
        user_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
        memory_type: str = "general",
        importance: int = 5,
        ttl_days: int | None = None,
    ) -> dict:
        """Store a memory in GenAIScope."""
        return tool_memory_remember(
            store, content=content, user_id=user_id, project_id=project_id,
            workspace_id=workspace_id, memory_type=memory_type,
            importance=importance, ttl_days=ttl_days,
        )

    @mcp_server.tool()
    def memory_search(
        query: str,
        user_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 10,
        mode: str = "hybrid",
    ) -> dict:
        """Search memories by keyword, vector, or hybrid scoring."""
        kw: dict[str, Any] = {
            "user_id": user_id, "project_id": project_id, "workspace_id": workspace_id,
            "limit": limit, "mode": mode,
        }
        if memory_type:
            kw["memory_type"] = memory_type
        return tool_memory_search(store, query, **kw)

    @mcp_server.tool()
    def memory_context(
        query: str,
        user_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
        limit: int = 10,
        max_chars: int | None = None,
    ) -> dict:
        """Return a ready-to-inject context block for assistants."""
        return tool_memory_context(
            store, query,
            user_id=user_id, project_id=project_id, workspace_id=workspace_id,
            limit=limit, max_chars=max_chars,
        )

    @mcp_server.tool()
    def memory_add_prompt(
        prompt: str,
        user_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        """Store a prompt and return prompt quality score/comments."""
        return tool_memory_add_prompt(store, prompt, user_id=user_id, project_id=project_id)

    @mcp_server.tool()
    def memory_list(
        user_id: str | None = None,
        project_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 20,
    ) -> dict:
        """List recent memories."""
        kw: dict[str, Any] = {"user_id": user_id, "project_id": project_id, "limit": limit}
        if memory_type:
            kw["memory_type"] = memory_type
        return tool_memory_list(store, **kw)

    @mcp_server.tool()
    def memory_stats() -> dict:
        """Return aggregate memory statistics."""
        return tool_memory_stats(store)


def _tool_definitions() -> list[Any]:
    from mcp.types import Tool

    return [
        Tool(name="memory_remember", description="Store a memory.", inputSchema={"type": "object", "properties": {"content": {"type": "string"}, "user_id": {"type": "string"}, "project_id": {"type": "string"}, "memory_type": {"type": "string"}, "importance": {"type": "integer"}, "ttl_days": {"type": "integer"}}, "required": ["content"]}),
        Tool(name="memory_search", description="Search memories.", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "user_id": {"type": "string"}, "project_id": {"type": "string"}, "limit": {"type": "integer"}, "mode": {"type": "string"}}, "required": ["query"]}),
        Tool(name="memory_context", description="Return injectable context block.", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "user_id": {"type": "string"}, "project_id": {"type": "string"}, "limit": {"type": "integer"}, "max_chars": {"type": "integer"}}, "required": ["query"]}),
        Tool(name="memory_add_prompt", description="Store a prompt with quality analysis.", inputSchema={"type": "object", "properties": {"prompt": {"type": "string"}, "user_id": {"type": "string"}}, "required": ["prompt"]}),
        Tool(name="memory_list", description="List recent memories.", inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="memory_stats", description="Return memory statistics.", inputSchema={"type": "object", "properties": {}}),
    ]


def _dispatch(store: Any, name: str, args: dict) -> Any:
    dispatch = {
        "memory_remember": lambda: tool_memory_remember(store, **args),
        "memory_search": lambda: tool_memory_search(store, **args),
        "memory_context": lambda: tool_memory_context(store, **args),
        "memory_add_prompt": lambda: tool_memory_add_prompt(store, **args),
        "memory_list": lambda: tool_memory_list(store, **args),
        "memory_stats": lambda: tool_memory_stats(store),
    }
    fn = dispatch.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    return fn()


def run_stdio(store: Any) -> None:
    """Run MCP server over stdio transport."""
    import asyncio

    _require_mcp()
    server = build_mcp_server(store)

    try:
        # FastMCP path
        server.run(transport="stdio")
    except AttributeError:
        # low-level server path
        from mcp.server.stdio import stdio_server

        async def _run() -> None:
            async with stdio_server() as (read, write):
                await server.run(read, write, server.create_initialization_options())

        asyncio.run(_run())


def run_http(store: Any, host: str = "0.0.0.0", port: int = 8848) -> None:
    """Run MCP server over StreamableHTTP transport."""
    import asyncio

    _require_mcp()
    server = build_mcp_server(store)

    try:
        server.run(transport="streamable-http", host=host, port=port)
    except AttributeError:
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

        async def _run() -> None:
            manager = StreamableHTTPSessionManager(app=server, event_store=None, json_response=True)
            import uvicorn  # type: ignore[import-not-found]
            config = uvicorn.Config(manager.handle_request, host=host, port=port)
            srv = uvicorn.Server(config)
            await srv.serve()

        asyncio.run(_run())
