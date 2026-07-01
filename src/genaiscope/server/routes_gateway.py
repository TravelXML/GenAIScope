"""Live LLM gateway REST route.

Lets any HTTP client -- including the browser extension -- route a prompt
through GenAIScope's own multi-provider gateway (real OpenAI/Anthropic/Google
call via `genaiscope[providers]`) instead of scraping a provider's web UI.
Every call is captured as exactly one trace with an attached Context Doctor
health score and cost estimate, the same as `scope.gateway.complete()`.
"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse

from genaiscope.core.errors import GatewayError
from genaiscope.gateway import GatewayClient
from genaiscope.server.schemas import GatewayAskRequest


def add_gateway_routes(app: Any, store: Any, tracer: Any, auth_dep: Any) -> None:
    client = GatewayClient(store, tracer=tracer)

    @app.post("/v1/gateway/ask")
    async def ask(req: GatewayAskRequest, _: Any = Depends(auth_dep)) -> JSONResponse:
        try:
            result = client.complete(
                req.prompt,
                provider=req.provider,
                model=req.model,
                user_id=req.user_id,
                project_id=req.project_id,
                privacy_sensitive=req.privacy_sensitive,
                cost_sensitive=req.cost_sensitive,
            )
        except GatewayError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return JSONResponse(result.model_dump())
