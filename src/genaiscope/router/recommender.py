"""Model-type recommendation. Offline classification only -- auto-routing to a
live provider call lives in `genaiscope.gateway` (v0.7.0), which calls
`recommend()` for its candidate provider list."""

from __future__ import annotations

from genaiscope.doctor.prompt_improver import detect_intent
from genaiscope.router.models import RouterRecommendation

_REASONS = {
    "coding": "The prompt requires code understanding, debugging, or refactoring.",
    "reasoning": "The prompt asks for analysis, comparison, or a multi-step decision.",
    "writing": "The prompt asks for original written content.",
    "summarization": "The prompt asks for condensing existing content.",
    "extraction": "The prompt asks for pulling structured information out of text.",
}

_PROVIDERS_BY_TYPE = {
    "coding": ["openai", "anthropic", "local"],
    "reasoning": ["openai", "anthropic"],
    "writing": ["openai", "anthropic", "google"],
    "summarization": ["google", "groq", "local"],
    "extraction": ["groq", "local", "openai"],
}


def recommend(
    prompt: str,
    privacy_sensitive: bool = False,
    cost_sensitive: bool = False,
) -> RouterRecommendation:
    """Recommend a model type (and candidate providers) for a prompt."""

    _, model_type = detect_intent(prompt)
    reason = _REASONS.get(model_type, "General-purpose writing/Q&A request.")

    if privacy_sensitive:
        model_type = "privacy_sensitive_local"
        reason = "Privacy-sensitive request -- routed to a local/self-hosted model only."
        providers = ["local", "ollama"]
    else:
        providers = list(_PROVIDERS_BY_TYPE.get(model_type, ["openai"]))
        if cost_sensitive:
            for cheap in ("local", "groq"):
                if cheap in providers:
                    providers.remove(cheap)
                    providers.insert(0, cheap)
            if "local" not in providers:
                providers.append("local")

    cost_sensitivity = "high" if cost_sensitive else "medium"

    return RouterRecommendation(
        recommended_model_type=model_type,
        reason=reason,
        suggested_providers=providers,
        cost_sensitivity=cost_sensitivity,
    )
