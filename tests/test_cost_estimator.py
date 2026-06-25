"""Tests for CostEstimator and the provider/model pricing table."""

from genaiscope.cost import CostEstimator
from genaiscope.cost.pricing import lookup_price


def test_estimate_known_model() -> None:
    estimate = CostEstimator().estimate("openai", "gpt-4.1", 1000, 500)
    assert estimate.priced is True
    assert estimate.total_cost > 0
    assert estimate.total_cost == round(estimate.input_cost + estimate.output_cost, 10)


def test_estimate_unknown_model_returns_zero_and_unpriced() -> None:
    estimate = CostEstimator().estimate("openai", "nonexistent-model-xyz", 1000, 500)
    assert estimate.priced is False
    assert estimate.total_cost == 0.0


def test_local_and_ollama_are_free_by_default() -> None:
    for provider in ("local", "ollama"):
        estimate = CostEstimator().estimate(provider, "llama3", 1000, 500)
        assert estimate.priced is True
        assert estimate.total_cost == 0.0


def test_groq_has_real_pricing() -> None:
    estimate = CostEstimator().estimate("groq", "llama3-70b", 1000, 500)
    assert estimate.priced is True
    assert estimate.total_cost > 0


def test_lookup_price_prefers_longest_matching_alias() -> None:
    """A dated real model id should resolve to its specific alias, not a
    shorter, more generic one that happens to be a string prefix match too."""

    price = lookup_price("openai", "gpt-4o-mini-2024-07-18")
    assert price == lookup_price("openai", "gpt-4o-mini")
    assert price != lookup_price("openai", "gpt-4")
