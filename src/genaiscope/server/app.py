"""FastAPI application factory for the GenAIScope REST API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.core.errors import ServerDependencyMissingError

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore


def _require_fastapi() -> Any:
    try:
        import fastapi

        return fastapi
    except ImportError as exc:
        raise ServerDependencyMissingError(
            'fastapi is not installed. Run: pip install "genaiscope[server]"'
        ) from exc


def create_app(store: BaseMemoryStore, auth_enabled: bool = False) -> Any:
    """Build and return a FastAPI application."""

    _require_fastapi()

    from fastapi import FastAPI

    from genaiscope.server.auth import make_auth_dependency
    from genaiscope.server.routes_health import add_health_routes
    from genaiscope.server.routes_memory import add_memory_routes
    from genaiscope.version import __version__

    app = FastAPI(
        title="GenAIScope Memory API",
        description="REST API for GenAIScope memory — compatible with any LLM client.",
        version=__version__,
    )

    auth_dep = make_auth_dependency(enabled=auth_enabled)

    add_health_routes(app, version=__version__)
    add_memory_routes(app, store=store, auth_dep=auth_dep)

    return app


def run_api_server(
    store: BaseMemoryStore,
    host: str = "127.0.0.1",
    port: int = 8000,
    auth_enabled: bool = False,
) -> None:
    """Start the uvicorn server."""

    try:
        import uvicorn  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ServerDependencyMissingError(
            'uvicorn is not installed. Run: pip install "genaiscope[server]"'
        ) from exc

    app = create_app(store, auth_enabled=auth_enabled)
    uvicorn.run(app, host=host, port=port)
