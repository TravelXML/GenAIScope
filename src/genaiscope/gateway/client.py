"""Multi-provider live LLM gateway — auto-routes a prompt to a real provider call.

Ties together two pieces that already existed but were never connected:
`genaiscope.router.recommend()` (offline provider/model-type suggestion) and
`genaiscope.adapters.{OpenAIAdapter,AnthropicAdapter,GeminiAdapter}` (live SDK
calls with memory injection). One real call is logged as exactly one trace,
with a Context Doctor health score attached.

Requires: pip install "genaiscope[providers]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from genaiscope.core.errors import GatewayError
from genaiscope.gateway.models import GatewayResponse
from genaiscope.router import recommend

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore
    from genaiscope.tracing import LocalTracer

_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-6",
    "google": "gemini-1.5-flash",
}


def _call_openai(
    store: BaseMemoryStore, prompt: str, model: str | None, user_id: str | None, project_id: str | None
) -> tuple[str, str, int, int]:
    from genaiscope.adapters import OpenAIAdapter

    adapter = OpenAIAdapter(store, user_id=user_id, project_id=project_id, store_assistant_turns=False)
    resp_model = model or _DEFAULT_MODELS["openai"]
    response = adapter.chat([{"role": "user", "content": prompt}], model=resp_model)
    reply = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    return reply, getattr(response, "model", None) or resp_model, input_tokens or 0, output_tokens or 0


def _call_anthropic(
    store: BaseMemoryStore, prompt: str, model: str | None, user_id: str | None, project_id: str | None
) -> tuple[str, str, int, int]:
    from genaiscope.adapters import AnthropicAdapter

    adapter = AnthropicAdapter(store, user_id=user_id, project_id=project_id, store_assistant_turns=False)
    resp_model = model or _DEFAULT_MODELS["anthropic"]
    response = adapter.chat([{"role": "user", "content": prompt}], model=resp_model)
    reply = response.content[0].text if response.content else ""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
    return reply, getattr(response, "model", None) or resp_model, input_tokens or 0, output_tokens or 0


def _call_google(
    store: BaseMemoryStore, prompt: str, model: str | None, user_id: str | None, project_id: str | None
) -> tuple[str, str, int, int]:
    from genaiscope.adapters import GeminiAdapter

    resp_model = model or _DEFAULT_MODELS["google"]
    adapter = GeminiAdapter(
        store, model=resp_model, user_id=user_id, project_id=project_id, store_assistant_turns=False
    )
    response = adapter.chat([{"role": "user", "content": prompt}])
    reply = response.text if hasattr(response, "text") else ""
    usage = getattr(response, "usage_metadata", None)
    input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
    output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
    return reply, resp_model, input_tokens or 0, output_tokens or 0


_CALLERS = {"openai": _call_openai, "anthropic": _call_anthropic, "google": _call_google}


class GatewayClient:
    """`scope.gateway.complete(...)` -- auto-routes to a live provider call."""

    def __init__(self, store: BaseMemoryStore, tracer: LocalTracer | None = None) -> None:
        self._store = store
        self._tracer = tracer

    def complete(
        self,
        prompt: str,
        provider: str = "auto",
        model: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        privacy_sensitive: bool = False,
        cost_sensitive: bool = False,
    ) -> GatewayResponse:
        """Call a live LLM provider for `prompt`, logging exactly one trace with an
        attached Context Doctor health score. `provider="auto"` asks
        `genaiscope.router.recommend()` for candidates and tries them in order,
        falling back on failure; only `openai`/`anthropic`/`google` (alias
        `gemini`) have a live adapter today -- other router suggestions
        (`groq`/`local`/`ollama`) are skipped."""

        provider = "google" if provider == "gemini" else provider

        if provider == "auto":
            rec = recommend(prompt, privacy_sensitive=privacy_sensitive, cost_sensitive=cost_sensitive)
            candidates = [p for p in rec.suggested_providers if p in _CALLERS]
            if not candidates:
                candidates = ["openai"]
        else:
            candidates = [provider]

        attempted: list[str] = []
        last_error: Exception | None = None

        for candidate in candidates:
            caller = _CALLERS.get(candidate)
            if caller is None:
                continue
            attempted.append(candidate)
            try:
                reply, resp_model, input_tokens, output_tokens = caller(
                    self._store, prompt, model, user_id, project_id
                )
                break
            except Exception as exc:  # any candidate failure falls through to the next
                last_error = exc
        else:
            raise GatewayError(
                f"All candidate providers failed: {attempted}. Last error: {last_error}"
            )

        return self._finish(prompt, reply, candidate, resp_model, input_tokens, output_tokens, attempted)

    def _finish(
        self,
        prompt: str,
        reply: str,
        provider_used: str,
        resp_model: str,
        input_tokens: int,
        output_tokens: int,
        attempted: list[str],
    ) -> GatewayResponse:
        from genaiscope.cost import CostEstimator
        from genaiscope.doctor import ContextDoctor

        cost = CostEstimator().estimate(provider_used, resp_model, input_tokens, output_tokens)
        diagnosis = ContextDoctor().diagnose(
            prompt=prompt,
            response=reply,
            provider=provider_used,
            model=resp_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        if self._tracer is not None:
            self._tracer.log(
                name="gateway.complete",
                input_text=prompt,
                output_text=reply,
                model=resp_model,
                provider=provider_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost.total_cost,
                status="success",
                metadata={
                    "category": "gateway",
                    "attempted_providers": attempted,
                    "context_health_score": diagnosis.context_health_score,
                    "missing_context": diagnosis.missing_context,
                },
            )

        return GatewayResponse(
            text=reply,
            provider=provider_used,
            model=resp_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost.total_cost,
            context_health_score=diagnosis.context_health_score,
            attempted_providers=attempted,
        )
