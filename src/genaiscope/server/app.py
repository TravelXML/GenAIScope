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


def create_app(store: BaseMemoryStore, auth_enabled: bool = False, tracer: Any = None) -> Any:
    """Build and return a FastAPI application."""

    _require_fastapi()

    from fastapi import FastAPI, Request

    from genaiscope.server.auth import make_auth_dependency
    from genaiscope.server.routes_health import add_health_routes
    from genaiscope.server.routes_memory import add_memory_routes
    from genaiscope.version import __version__

    app = FastAPI(
        title="GenAIScope Memory API",
        description="REST API for GenAIScope memory — compatible with any LLM client.",
        version=__version__,
    )

    if tracer is not None:

        @app.middleware("http")
        async def _trace_requests(request: Request, call_next: Any) -> Any:
            import time

            start = time.perf_counter()
            response = None
            try:
                response = await call_next(request)
                return response
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                status_code = response.status_code if response is not None else 500
                tracer.log(
                    name=request.url.path,
                    provider="rest",
                    latency_ms=latency_ms,
                    status="success" if status_code < 400 else "error",
                    metadata={"method": request.method, "status_code": status_code},
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
    tracer: Any = None,
) -> None:
    """Start the uvicorn server."""

    try:
        import uvicorn  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ServerDependencyMissingError(
            'uvicorn is not installed. Run: pip install "genaiscope[server]"'
        ) from exc

    app = create_app(store, auth_enabled=auth_enabled, tracer=tracer)
    uvicorn.run(app, host=host, port=port)
