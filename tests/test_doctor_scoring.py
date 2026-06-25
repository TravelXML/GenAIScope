"""Tests for Context Doctor's rule-based scoring functions."""

from genaiscope.doctor.scoring import (
    answer_specificity_score,
    context_completeness_score,
    context_health_score,
    hallucination_risk_score,
    memory_match_score,
    model_fit_score,
    prompt_clarity_score,
    token_efficiency_score,
)


def test_prompt_clarity_score_penalizes_short_vague_prompts() -> None:
    weak = prompt_clarity_score("Write answer for this job.")
    strong = prompt_clarity_score(
        "Write a 200-word, senior-toned answer for a CTO interview about feature velocity, "
        "aimed at the hiring panel."
    )
    assert 0 <= weak <= 100
    assert 0 <= strong <= 100
    assert strong > weak


def test_context_completeness_score_uses_top_k_ratio() -> None:
    full = context_completeness_score([{"id": "1"}, {"id": "2"}], requested_top_k=2)
    half = context_completeness_score([{"id": "1"}], requested_top_k=2)
    assert full == 100
    assert half == 50


def test_context_completeness_score_penalizes_missing_context_without_top_k() -> None:
    none_missing = context_completeness_score([{"id": "1"}], missing_context=[])
    some_missing = context_completeness_score([{"id": "1"}], missing_context=["a", "b"])
    assert none_missing == 100
    assert some_missing < none_missing


def test_memory_match_score_averages_result_scores() -> None:
    assert memory_match_score([]) == 0
    assert memory_match_score([{"score": 1.0}, {"score": 0.5}]) == 75


def test_model_fit_score_neutral_without_provider_or_model() -> None:
    assert model_fit_score("writing", None, None) == 70


def test_token_efficiency_score_estimates_from_text_when_no_token_counts() -> None:
    score = token_efficiency_score(prompt="short prompt", response="a reasonably sized response here")
    assert 0 <= score <= 100


def test_hallucination_risk_score_neutral_without_context() -> None:
    assert hallucination_risk_score(None, "some response") == 30
    assert hallucination_risk_score("context", None) == 30


def test_hallucination_risk_score_uses_detector_when_both_present() -> None:
    score = hallucination_risk_score("GenAIScope is a Python toolkit.", "GenAIScope is a Java blockchain framework.")
    assert score > 0


def test_answer_specificity_score_penalizes_short_hedging_responses() -> None:
    hedging = answer_specificity_score("It depends. In general, many ways exist.")
    specific = answer_specificity_score(
        "Feature velocity at Acme grew 35% after we shipped the new CI pipeline in Q3, "
        "directly reducing customer churn."
    )
    assert specific > hedging


def test_context_health_score_is_weighted_composite() -> None:
    perfect = context_health_score({
        "prompt_clarity_score": 100,
        "context_completeness_score": 100,
        "memory_match_score": 100,
        "model_fit_score": 100,
        "token_efficiency_score": 100,
        "hallucination_risk_score": 0,
        "answer_specificity_score": 100,
    })
    assert perfect == 100

    worst = context_health_score({
        "prompt_clarity_score": 0,
        "context_completeness_score": 0,
        "memory_match_score": 0,
        "model_fit_score": 0,
        "token_efficiency_score": 0,
        "hallucination_risk_score": 100,
        "answer_specificity_score": 0,
    })
    assert worst == 0
