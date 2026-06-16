"""Optional auth for the MCP server.

Modes: none (default) | bearer (env GENAISCOPE_MCP_TOKEN)
"""

from __future__ import annotations

import os


def get_bearer_token() -> str | None:
    return os.environ.get("GENAISCOPE_MCP_TOKEN")


def check_bearer(provided_token: str | None, expected: str | None) -> bool:
    if not expected:
        return True
    return provided_token == expected
