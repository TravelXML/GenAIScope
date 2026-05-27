"""Heuristic prompt quality coach."""

from __future__ import annotations

import re

from genaiscope.memory.models import PromptQualityReport

VAGUE_WORDS = {
    "proper",
    "useful",
    "good",
    "better",
    "nice",
    "great",
    "excellent",
    "perfect",
    "detailed",
    "professional",
    "humanize",
    "optimize",
    "improve",
    "properly",
}


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def analyze_prompt_quality(prompt: str) -> PromptQualityReport:
    """Analyze a prompt and return coaching comments."""

    text = prompt.strip()
    lower = text.lower()
    words = re.findall(r"\b\w+\b", lower)
    score = 100
    issues: list[str] = []
    comments: list[str] = []
    suggestions: list[str] = []

    if len(words) < 6:
        score -= 20
        issues.append("too_short")
        comments.append("Prompt is very short and may not provide enough context.")
    if len(words) > 800:
        score -= 5
        issues.append("too_long")
        comments.append("Prompt is long enough that task boundaries may become hard to follow.")
    if not _has_any(lower, ("act as", "you are", "role", "persona", "expert")):
        score -= 10
        issues.append("missing_role")
        suggestions.append("Add a role or persona for the assistant.")
    if not _has_any(
        lower,
        (
            "summarize",
            "write",
            "classify",
            "extract",
            "compare",
            "analyze",
            "generate",
            "create",
            "rewrite",
            "list",
            "explain",
        ),
    ):
        score -= 15
        issues.append("missing_clear_task")
        suggestions.append("State the task with a concrete action verb.")
    if not _has_any(lower, ("format", "json", "table", "bullets", "markdown", "schema", "section")):
        score -= 15
        issues.append("missing_output_format")
        suggestions.append("Specify the expected output format.")
    if not _has_any(lower, ("must", "do not", "avoid", "limit", "constraint", "only", "under")):
        score -= 10
        issues.append("missing_constraints")
        suggestions.append("Add constraints such as length, style, exclusions, or allowed sources.")
    vague = sorted({word for word in words if word in VAGUE_WORDS})
    if vague:
        score -= 10
        issues.append("vague_wording")
        comments.append(f"Prompt uses vague words: {', '.join(vague)}.")
    if not _has_any(lower, ("success", "criteria", "rubric", "quality", "accepted when")):
        score -= 10
        issues.append("missing_success_criteria")
        suggestions.append("Add success criteria or a quick rubric.")
    if _has_any(
        lower, ("cite", "source", "reference", "evidence", "according to")
    ) is False and _has_any(lower, ("latest", "current", "today", "fact", "research")):
        score -= 5
        issues.append("missing_citation_instruction")
        suggestions.append("For factual answers, ask for sources or uncertainty handling.")
    if (
        _has_any(lower, ("json", "structured", "schema"))
        and "{" not in text
        and "schema" not in lower
    ):
        score -= 5
        issues.append("missing_schema_detail")
        suggestions.append("Provide a JSON schema or explicit fields for structured output.")
    if not _has_any(lower, ("safe", "privacy", "pii", "security", "harm", "policy")):
        score -= 5
        issues.append("missing_safety_boundaries")
    if not _has_any(lower, ("audience", "for developers", "for executives", "for users", "reader")):
        issues.append("missing_audience")
    if _has_any(lower, ("rewrite", "tone", "style")) and not _has_any(
        lower, ("friendly", "formal", "concise", "cto", "technical")
    ):
        issues.append("missing_tone")
        suggestions.append("Name the desired tone or style.")
    if re.search(r"\b(do not|don't)\b.+\b(must|always)\b", lower):
        score -= 20
        issues.append("possible_conflict")
        comments.append("Prompt may contain conflicting instructions.")

    if not comments and issues:
        comments.append(
            "Prompt can be improved by adding context, output format, constraints, and success criteria."
        )
    if not suggestions and issues:
        suggestions.append(
            "Add a role, clear task, output format, constraints, and success criteria."
        )

    score = max(0, min(100, score))
    risk_level = "low" if score >= 80 else "medium" if score >= 60 else "high"
    return PromptQualityReport(
        score=score,
        risk_level=risk_level,
        comments=comments,
        improvement_suggestions=suggestions,
        detected_issues=issues,
    )
