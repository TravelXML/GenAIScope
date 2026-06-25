"""ContextDoctor -- the v0.6.0 health-report engine for one LLM interaction."""

from __future__ import annotations

from typing import Any

from genaiscope.doctor.models import DiagnosisReport
from genaiscope.doctor.prompt_improver import (
    build_recommended_prompt,
    detect_entities,
    detect_intent,
    detect_missing_context,
    detect_prompt_issues,
    improvement_tips,
)
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


def _normalize_memory(memory: Any) -> dict[str, Any]:
    """Accept a MemorySearchResult, a ContextBuilder retrieved-memory dict, or
    a plain dict and return one consistent shape."""

    item = getattr(memory, "item", None)
    if item is not None:
        return {
            "id": item.id,
            "content": item.content,
            "memory_type": item.memory_type,
            "tags": item.tags,
            "score": getattr(memory, "score", 0.0),
        }
    if isinstance(memory, dict):
        return {
            "id": memory.get("id", ""),
            "content": memory.get("content", ""),
            "memory_type": memory.get("memory_type", "general"),
            "tags": memory.get("tags", []),
            "score": memory.get("score", 0.0),
        }
    return {"id": "", "content": str(memory), "memory_type": "general", "tags": [], "score": 0.0}


class ContextDoctor:
    """Diagnoses why an LLM interaction was weak and recommends a fix."""

    def diagnose(
        self,
        prompt: str,
        response: str | None = None,
        memories_used: list[Any] | None = None,
        provider: str | None = None,
        model: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        context_text: str | None = None,
    ) -> DiagnosisReport:
        """Build a full health report for one prompt/response interaction."""

        memories = [_normalize_memory(m) for m in (memories_used or [])]

        intent, recommended_model_type = detect_intent(prompt)
        missing = detect_missing_context(prompt, memories)
        entities = detect_entities(prompt, memories)
        issues = detect_prompt_issues(prompt, missing)
        recommended_prompt = build_recommended_prompt(prompt, memories, missing)
        tips = improvement_tips(missing)

        scores = {
            "prompt_clarity_score": prompt_clarity_score(prompt),
            "context_completeness_score": context_completeness_score(memories, missing_context=missing),
            "memory_match_score": memory_match_score(memories),
            "model_fit_score": model_fit_score(recommended_model_type, provider, model),
            "token_efficiency_score": token_efficiency_score(
                prompt=prompt, response=response, input_tokens=input_tokens, output_tokens=output_tokens
            ),
            "hallucination_risk_score": hallucination_risk_score(context_text, response),
            "answer_specificity_score": answer_specificity_score(response),
        }

        return DiagnosisReport(
            context_health_score=context_health_score(scores),
            missing_context=missing,
            detected_entities=entities,
            detected_intent=intent,
            prompt_issues=issues,
            recommended_prompt=recommended_prompt,
            recommended_model_type=recommended_model_type,
            improvement_tips=tips,
            **scores,
        )
