"""Provider/model pricing table for CostEstimator.

Extends genaiscope.analyzers.CostAnalyzer's pricing dict with provider-keyed
entries (including groq and ollama/local, which are zero-cost unless
configured) plus a simple prefix-match fallback so real model identifiers
like "gpt-4o-mini-2024-07-18" still resolve to a price.
"""

from __future__ import annotations

# Per-1K-token USD pricing, keyed by provider -> model alias -> {"input", "output"}.
PRICING: dict[str, dict[str, dict[str, float]]] = {
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4.1": {"input": 0.002, "output": 0.008},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    },
    "google": {
        "gemini-pro": {"input": 0.0005, "output": 0.0015},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    },
    "groq": {
        "llama3-70b": {"input": 0.00059, "output": 0.00079},
        "llama3-8b": {"input": 0.00005, "output": 0.00008},
        "mixtral-8x7b": {"input": 0.00024, "output": 0.00024},
    },
    "ollama": {},  # local models are free unless a price is explicitly configured
    "local": {},
}


def lookup_price(provider: str, model: str) -> dict[str, float] | None:
    """Find a price entry for (provider, model), trying exact match first,
    then a prefix match against known aliases (handles real, dated model
    identifiers)."""

    provider_table = PRICING.get(provider.lower(), {})
    if model in provider_table:
        return provider_table[model]

    model_lower = model.lower()
    matches = [(alias, price) for alias, price in provider_table.items() if model_lower.startswith(alias.lower())]
    if matches:
        # Longest alias wins so "gpt-4o-mini-..." matches "gpt-4o-mini" rather
        # than the more generic "gpt-4".
        return max(matches, key=lambda pair: len(pair[0]))[1]

    if provider.lower() in ("ollama", "local"):
        return {"input": 0.0, "output": 0.0}

    return None
