"""Health check routes."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def add_health_routes(app: Any, version: str) -> None:
    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": version})
