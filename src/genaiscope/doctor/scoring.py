"""Rule-based 0-100 scoring functions for Context Doctor.

No LLM call -- every score is a deterministic heuristic over the prompt,
response, and retrieved memories. Reuses genaiscope.analyzers.HallucinationDetector
for the unsupported-claim signal instead of reimplementing it.
"""

from __future__ import annotations

from typing import Any

from genaiscope.analyzers import HallucinationDetector
from genaiscope.doctor.prompt_improver import detect_missing_context
from genaiscope.memory.search import tokenize


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, round(value)))


def prompt_clarity_score(prompt: str) -> int:
    """Penalize vague, very short, or under-specified prompts."""

    words = prompt.strip().split()
    score = 100.0

    if len(words) < 4:
        score -= 40
    elif len(words) < 8:
        score -= 20

    missing = detect_missing_context(prompt)
    score -= 10 * len(missing)

    if prompt.strip() and prompt.strip()[-1] not in ".?!":
        score -= 5

    return _clamp(score)


def context_completeness_score(
    memories_used: list[dict[str, Any]] | None,
    missing_context: list[str] | None = None,
    requested_top_k: int | None = None,
) -> int:
    """How complete the retrieved context is.

    When `requested_top_k` is known (ContextBuilder), score the fill ratio.
    Otherwise (ContextDoctor, which only sees the final memories_used) fall
    back to penalizing by the number of detected missing-context items.
    """

    count = len(memories_used or [])
    score = (count / requested_top_k) * 100 if requested_top_k else (100.0 if count else 60.0)
    if missing_context:
        score -= 12 * len(missing_context)
    return _clamp(score)


def memory_match_score(memories_used: list[dict[str, Any]] | None) -> int:
    """Average retrieval score of the memories actually used, scaled to 0-100."""

    memories = memories_used or []
    if not memories:
        return 0
    scores = [float(m.get("score", 0.0)) for m in memories]
    return _clamp((sum(scores) / len(scores)) * 100)


def model_fit_score(detected_model_type: str, provider: str | None, model: str | None) -> int:
    """Light heuristic: flag an obvious provider/model vs. intent mismatch."""

    if not provider and not model:
        return 70  # neutral -- nothing to evaluate against

    name = f"{provider or ''} {model or ''}".lower()
    if detected_model_type == "coding" and any(k in name for k in ("instruct-mini", "nano")):
        return 55
    if detected_model_type == "reasoning" and "mini" in name:
        return 65
    return 85


def token_efficiency_score(
    prompt: str | None = None,
    response: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> int:
    """Flag responses that look disproportionately long/short for the ask.

    Accepts real token counts when known (from a traced LLM call), and falls
    back to a chars/4 estimate from the prompt/response text otherwise (e.g.
    inside ContextDoctor.diagnose(), which doesn't require token counts).
    """

    if not input_tokens and prompt:
        input_tokens = max(1, len(prompt) // 4)
    if not output_tokens and response:
        output_tokens = max(1, len(response) // 4)

    if input_tokens <= 0 and output_tokens <= 0:
        return 70  # neutral -- no usage data supplied

    prompt_words = len(prompt.split()) if prompt else 0
    if prompt_words and output_tokens > 0:
        ratio = output_tokens / max(1, prompt_words)
        if ratio > 80:
            return 50
        if ratio > 40:
            return 70
    return 90


def hallucination_risk_score(context: str | None, response: str | None) -> int:
    """0-100, higher = riskier. Delegates to HallucinationDetector when both
    context and response are available; neutral default otherwise."""

    if not context or not response:
        return 30  # neutral-low default: nothing to ground against, can't tell
    result = HallucinationDetector().detect(context, response)
    return _clamp(result["hallucination_risk"] * 100)


def answer_specificity_score(response: str | None) -> int:
    """Penalize short, hedging, or filler-heavy responses."""

    if not response:
        return 0

    words = response.strip().split()
    score = 100.0
    if len(words) < 15:
        score -= 30

    hedges = ("it depends", "in general", "various factors", "many ways", "it varies")
    lowered = response.lower()
    score -= 10 * sum(1 for h in hedges if h in lowered)

    tokens = tokenize(response)
    has_specifics = any(t.isdigit() for t in tokens) or any(w[0].isupper() for w in words if len(w) > 2)
    if not has_specifics:
        score -= 15

    return _clamp(score)


# context_health_score weights -- must sum to 1.0
_WEIGHTS = {
    "prompt_clarity_score": 0.20,
    "context_completeness_score": 0.15,
    "memory_match_score": 0.15,
    "model_fit_score": 0.10,
    "token_efficiency_score": 0.10,
    "hallucination_risk_score": 0.15,  # inverted -- lower risk is healthier
    "answer_specificity_score": 0.15,
}


def context_health_score(scores: dict[str, int]) -> int:
    """Weighted composite of every sub-score. hallucination_risk_score is
    inverted (100 - risk) since a *low* risk is healthy."""

    total = 0.0
    for key, weight in _WEIGHTS.items():
        value = scores.get(key, 0)
        if key == "hallucination_risk_score":
            value = 100 - value
        total += weight * value
    return _clamp(total)
