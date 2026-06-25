"""Tests for the model-type router recommendation."""

from genaiscope.router import recommend


def test_recommend_coding_intent() -> None:
    rec = recommend("Refactor this Python function and explain bugs", cost_sensitive=True)
    assert rec.recommended_model_type == "coding"
    assert rec.cost_sensitivity == "high"
    assert "local" in rec.suggested_providers


def test_recommend_privacy_sensitive_routes_local_only() -> None:
    rec = recommend("Summarize this internal HR document", privacy_sensitive=True)
    assert rec.recommended_model_type == "privacy_sensitive_local"
    assert set(rec.suggested_providers) <= {"local", "ollama"}


def test_recommend_default_cost_sensitivity_is_medium() -> None:
    rec = recommend("Write a short poem about the sea")
    assert rec.cost_sensitivity == "medium"


def test_recommend_summarization_intent() -> None:
    rec = recommend("Summarize this 10-page report into a TL;DR")
    assert rec.recommended_model_type == "summarization"
