# Context Doctor (v0.6.0)

Context Doctor is GenAIScope's memory + tracing + prompt diagnosis layer. It helps you
understand why an LLM answer was weak, what context was missing, what memory was used, what
token/cost/latency happened, and how to rewrite the prompt for a better result — entirely with
local, rule-based heuristics (no extra LLM call).

## The `GenAIScope` facade

```python
from genaiscope import GenAIScope

scope = GenAIScope(storage="sqlite", db_path="genaiscope.db")
```

`GenAIScope` shares one local memory store and tracer behind several sub-objects:

| Attribute | Purpose |
|---|---|
| `scope.memory` | Add/search/forget/list memory (wraps `MemoryStore`) |
| `scope.context` | `ContextBuilder` — retrieve memory and build an improved prompt |
| `scope.doctor` | `ContextDoctor` — diagnose a prompt/response interaction |
| `scope.cost` | `CostEstimator` — provider-aware cost estimation |
| `scope.router` | Model-type recommendation |
| `scope.analytics` | Usage summaries and prompt-pattern analysis |
| `scope.report` | Generate the Context Doctor HTML report |

## Logging interactions

```python
with scope.trace(provider="openai", model="gpt-4.1", category="cto_interview", tags=["traveltech"]) as trace:
    response = llm_call(prompt)
    trace.log(prompt=prompt, response=response)

# or, without a context manager:
scope.log_interaction(
    prompt="Explain feature velocity",
    response="Feature velocity means shipping value to customers faster.",
    provider="openai", model="gpt-4.1",
    input_tokens=120, output_tokens=240, latency_ms=1800,
    category="cto_learning", tags=["metrics", "cto"],
)
```

Both automatically run `ContextDoctor.diagnose()` on the prompt/response and store the
resulting `context_health_score`, `missing_context`, `detected_intent`, and `detected_entities`
into the trace's `metadata` — this is what powers `scope.analytics.prompt_patterns()` later.

## Memory types

`MemoryItem.memory_type` is (and remains) a free string. `genaiscope.memory.types` provides
typo-safe constants for the conventional v0.6.0 types: `PROFILE_MEMORY`, `PROJECT_MEMORY`,
`PREFERENCE_MEMORY`, `CONVERSATION_MEMORY`, `DOCUMENT_MEMORY`, `ENTITY_MEMORY`,
`DECISION_MEMORY`, `LEARNING_MEMORY`, `PROMPT_PATTERN_MEMORY`.

```python
scope.memory.add(
    memory_type="profile_memory",
    title="User profile",
    content="Sapan is a CTO / VP Engineering leader with TravelTech experience.",
    tags=["profile", "cto", "traveltech"],
    confidence=0.95,
    importance_score=0.9,   # 0-1 float, mapped onto the existing 1-10 `importance` field
)
```

`title`, `entities`, and `confidence` are stored in the existing `metadata` dict (no schema
change) and are accessible via `item.metadata["title"]`, etc.

## Building improved context

```python
context = scope.context.build(
    user_prompt="Write answer for CTO interview question about feature velocity",
    top_k=5,
    include_profile=True,
    include_projects=True,
    include_preferences=True,
)

context.original_prompt       # the input prompt, unchanged
context.retrieved_memories    # list[dict]: id, content, memory_type, tags, score
context.context_text          # ready-to-inject "- [type] content" block
context.improved_prompt       # rewritten prompt incorporating retrieved memory
context.token_estimate        # chars/4 estimate of context_text + improved_prompt
context.memory_ids_used       # ids of memories actually included
context.context_quality_score # 0-100 retrieval-completeness score (top_k fill ratio)
```

## Diagnosing an interaction

```python
report = scope.doctor.diagnose(
    prompt="Write answer for this job",
    response=response,
    memories_used=results,   # MemorySearchResult list, ContextBuilder dicts, or plain dicts
    provider="openai",
    model="gpt-4.1",
)
```

`report` (a `DiagnosisReport`) contains:

- `context_health_score` — weighted composite (0-100) of the seven sub-scores below
- `prompt_clarity_score`, `context_completeness_score`, `memory_match_score`,
  `model_fit_score`, `token_efficiency_score`, `hallucination_risk_score`,
  `answer_specificity_score`
- `missing_context` — e.g. `["Target audience", "Desired answer length or format", ...]`
- `detected_entities`, `detected_intent`, `prompt_issues`
- `recommended_prompt`, `recommended_model_type`, `improvement_tips`

Note: `missing_context` for `diagnose()` flags personal memory (profile/project) that *exists*
but wasn't referenced in the prompt or response — a deliberate diagnostic signal. This is
different from `ContextBuilder.build()`, where every memory in `retrieved_memories` has, by
definition, already been incorporated, so the same check is disabled there.

## CLI

```bash
genaiscope init
genaiscope diagnose --prompt "Write answer for feature velocity."
genaiscope analytics --days 7
genaiscope report --out genaiscope_report.html
```

## Design notes

- All new fields live in the existing `metadata` JSON column on `MemoryItem`/`TraceItem` — no
  database migration, existing `.db` files keep working unchanged.
- Scoring is rule-based (regex/heuristics), not an LLM call, by design — see
  `genaiscope.doctor.scoring` and `genaiscope.doctor.prompt_improver`.
- Memory retrieval reuses the existing `genaiscope.embeddings` / `genaiscope.vector` stack;
  configure an embedder for semantic (not just keyword) matching:

```python
from genaiscope.embeddings import LocalHashEmbedder
from genaiscope.vector import LocalVectorStore

scope = GenAIScope(
    db_path="genaiscope.db",
    embedder=LocalHashEmbedder(),
    vector_store=LocalVectorStore(db_path="genaiscope_vectors.db"),
)
```
