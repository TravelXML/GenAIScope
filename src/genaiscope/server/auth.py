"""Optional bearer auth for the REST API server."""

from __future__ import annotations

import os
from typing import Any


def make_auth_dependency(enabled: bool = False) -> Any:
    """Return a FastAPI dependency for optional bearer auth."""

    try:
        from fastapi import HTTPException, Security
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    except ImportError as exc:
        from genaiscope.core.errors import ServerDependencyMissingError

        raise ServerDependencyMissingError(
            'fastapi is not installed. Run: pip install "genaiscope[server]"'
        ) from exc

    if not enabled:
        async def no_auth() -> None:
            return None

        return no_auth

    _bearer = HTTPBearer(auto_error=False)
    expected_token = os.environ.get("GENAISCOPE_API_TOKEN", "")

    async def bearer_auth(
        credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    ) -> None:
        if not credentials or credentials.credentials != expected_token:
            raise HTTPException(status_code=401, detail="Unauthorized")

    return bearer_auth
