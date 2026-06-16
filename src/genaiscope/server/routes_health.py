"""Health check routes."""

from __future__ import annotations

from typing import Any


def add_health_routes(app: Any, version: str) -> None:
    from fastapi.responses import JSONResponse

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": version})
