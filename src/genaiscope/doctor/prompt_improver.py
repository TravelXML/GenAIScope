"""Rule-based intent detection, missing-context detection, and prompt rewriting.

Shared by ContextBuilder (improved_prompt), ContextDoctor (recommended_prompt /
recommended_model_type), and the model router (recommend) so all three surfaces
agree on what a prompt is "about." No LLM call -- pure heuristics, per the
v0.6.0 design goal of rule-based diagnosis in the MVP.
"""

from __future__ import annotations

from typing import Any

from genaiscope.memory.search import tokenize

# (intent, model_type, keywords) -- order matters, first match wins.
_INTENT_TABLE: list[tuple[str, str, tuple[str, ...]]] = [
    ("job_application_answer", "writing", ("job", "interview", "application", "hiring", "recruiter", "candidate")),
    ("coding_question", "coding", ("refactor", "bug", "function", "code", "python", "javascript", "stack trace", "exception", "compile")),
    ("summarization_request", "summarization", ("summarize", "summary", "tl;dr", "condense", "shorten")),
    ("extraction_request", "extraction", ("extract", "parse", "pull out", "list all", "find all")),
    ("reasoning_request", "reasoning", ("why", "analyze", "compare", "trade-off", "tradeoff", "evaluate", "decide", "architecture")),
    ("explanation_request", "writing", ("explain", "what is", "define", "describe")),
    ("writing_request", "writing", ("write", "draft", "compose", "answer")),
]

_DEFAULT_INTENT = "general_request"
_DEFAULT_MODEL_TYPE = "writing"

_AUDIENCE_HINTS = ("for the", "to the", "audience", "interviewer", "recruiter", "ceo", "cto", "manager", "team", "reader", "customer")
_FORMAT_HINTS = ("words", "characters", "sentences", "paragraph", "bullet", "format", "json", "concise", "brief", "short", "long", "length")
_TONE_HINTS = ("tone", "formal", "casual", "professional", "friendly", "senior", "playful")
_BUSINESS_HINTS = ("business", "customer", "revenue", "impact", "outcome", "roi", "roadmap")


def detect_intent(prompt: str) -> tuple[str, str]:
    """Return (detected_intent, recommended_model_type) for a prompt."""

    lowered = prompt.lower()
    for intent, model_type, keywords in _INTENT_TABLE:
        if any(keyword in lowered for keyword in keywords):
            return intent, model_type
    return _DEFAULT_INTENT, _DEFAULT_MODEL_TYPE


def detect_entities(prompt: str, memories: list[dict[str, Any]] | None = None) -> list[str]:
    """Surface capitalized/multi-word tokens from the prompt plus any memory tags
    that overlap with the prompt -- a lightweight entity proxy with no NLP
    dependency."""

    entities: list[str] = []
    words = prompt.split()
    for index, word in enumerate(words):
        if index == 0:
            continue  # sentence-initial capitalization isn't a reliable entity signal
        cleaned = word.strip(".,!?:;\"'()")
        if len(cleaned) > 2 and cleaned[0].isupper() and cleaned.lower() not in entities:
            entities.append(cleaned)

    prompt_tokens = set(tokenize(prompt))
    for memory in memories or []:
        for tag in memory.get("tags", []):
            if tag.lower() in prompt_tokens and tag not in entities:
                entities.append(tag)
    return entities


def detect_missing_context(
    prompt: str,
    memories: list[dict[str, Any]] | None = None,
    check_memory_references: bool = True,
) -> list[str]:
    """Heuristically list what context the prompt is missing.

    `check_memory_references` flags profile/project memories whose tags the
    prompt text never mentions -- a useful signal in ContextDoctor.diagnose(),
    where it surfaces personal context that *exists* but isn't being drawn on.
    ContextBuilder.build() passes False: by construction, everything in its
    `memories` list has already been retrieved and folded into context_text,
    so flagging it as "missing" there would be self-contradictory.
    """

    lowered = prompt.lower()
    memories = memories or []
    missing: list[str] = []

    if not any(hint in lowered for hint in _AUDIENCE_HINTS):
        missing.append("Target audience")
    if not any(hint in lowered for hint in _FORMAT_HINTS):
        missing.append("Desired answer length or format")
    if not any(hint in lowered for hint in _TONE_HINTS):
        missing.append("Tone preference")

    intent, _ = detect_intent(prompt)
    if intent == "job_application_answer":
        if "company" not in lowered and not any(m.get("memory_type") == "project_memory" for m in memories):
            missing.append("Target company")
        if "description" not in lowered and "role" not in lowered:
            missing.append("Job description")

    if not any(hint in lowered for hint in _BUSINESS_HINTS):
        missing.append("Business context (impact, outcomes)")

    if check_memory_references:
        prompt_tokens = set(tokenize(prompt))
        for memory in memories:
            if memory.get("memory_type") not in ("profile_memory", "project_memory"):
                continue
            tags = [t for t in memory.get("tags", []) if t.lower() not in prompt_tokens]
            if tags:
                label = tags[0].replace("_", " ").title()
                missing.append(f"{label} example")

    # de-dupe, keep order
    seen: set[str] = set()
    deduped = []
    for item in missing:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def build_recommended_prompt(
    prompt: str,
    memories: list[dict[str, Any]] | None = None,
    missing: list[str] | None = None,
) -> str:
    """Compose a rewritten prompt from the user's request plus retrieved memory."""

    memories = memories or []
    missing = missing if missing is not None else detect_missing_context(prompt, memories)

    profile_bits = [
        m["content"] for m in memories if m.get("memory_type") == "profile_memory" and m.get("content")
    ]
    project_bits = [
        m["content"] for m in memories if m.get("memory_type") == "project_memory" and m.get("content")
    ]

    lead = ""
    if profile_bits:
        lead = f"Using your background ({profile_bits[0].rstrip('.')}"
        if project_bits:
            lead += f"; {project_bits[0].rstrip('.')}"
        lead += "), "

    core = prompt.strip().rstrip(".")
    if core and core[0].isupper() and lead:
        core = core[0].lower() + core[1:]

    sentence = f"{lead}{core}."

    qualifiers = []
    if "Desired answer length or format" in missing:
        qualifiers.append("Keep it concise and well-structured")
    if "Tone preference" in missing:
        qualifiers.append("use a senior, professional tone")
    if "Business context (impact, outcomes)" in missing:
        qualifiers.append("connect it to business impact and outcomes")
    if "Target audience" in missing:
        qualifiers.append("write for the intended audience explicitly")

    if qualifiers:
        sentence += " " + ". ".join(q.capitalize() for q in qualifiers) + "."

    return sentence


def detect_prompt_issues(prompt: str, missing: list[str]) -> list[str]:
    """Human-readable issues with the prompt itself (distinct from missing
    background context)."""

    issues: list[str] = []
    words = prompt.strip().split()
    if len(words) < 6:
        issues.append("Prompt is too vague")
    if "Target audience" in missing:
        issues.append("No target audience provided")
    if "Desired answer length or format" in missing:
        issues.append("No output format or length specified")
    if "Tone preference" in missing:
        issues.append("No tone specified")
    return issues


def improvement_tips(missing: list[str]) -> list[str]:
    """Turn missing-context items into actionable tips."""

    tip_map = {
        "Target audience": "Add who the answer is for",
        "Desired answer length or format": "Mention desired length or output format",
        "Tone preference": "Specify tone (e.g. senior, casual, formal)",
        "Target company": "Add the company name",
        "Job description": "Add the job description",
        "Business context (impact, outcomes)": "Connect the answer to business impact",
    }
    tips = [tip_map.get(item, f"Add {item.lower()}") for item in missing]
    return tips
