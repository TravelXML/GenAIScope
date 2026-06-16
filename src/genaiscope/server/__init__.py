"""FastAPI REST API server for GenAIScope memory."""

from genaiscope.server.app import create_app, run_api_server

__all__ = ["create_app", "run_api_server"]
