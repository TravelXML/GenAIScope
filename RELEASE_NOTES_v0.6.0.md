# GenAIScope v0.6.0 Release Notes

GenAIScope v0.6.0 is the **Context Doctor** release: a lightweight memory, tracing, and
prompt diagnosis layer for LLM and Agent applications. It captures prompts, responses, token
usage, model behavior, memory usage, and context gaps, and recommends better prompts for
higher-quality AI outputs — all locally, with rule-based heuristics, no extra LLM call and no
API keys required.

## Highlights

- **`GenAIScope` facade** — one shared local store behind `scope.memory`, `scope.context`,
  `scope.doctor`, `scope.cost`, `scope.router`, `scope.analytics`, and `scope.report`.
  `scope.trace(...)` / `scope.log_interaction(...)` log interactions and automatically attach a
  Context Doctor health score.
- **`ContextDoctor.diagnose()`** — a `context_health_score` (0-100) plus seven sub-scores,
  missing-context detection, detected intent/entities, prompt issues, a recommended prompt
  rewrite, recommended model type, and improvement tips.
- **`ContextBuilder.build()`** — retrieves relevant memory and returns an injectable context
  block plus an improved prompt.
- **`CostEstimator`** — provider-aware cost estimation for OpenAI, Anthropic, Google, Groq, and
  local/Ollama models (free unless priced).
- **Model-type recommendation** (`genaiscope.router.recommend`) — reasoning/coding/writing/
  summarization/extraction/local, with privacy- and cost-sensitive provider suggestions.
- **Usage analytics + prompt patterns** (`genaiscope.analytics`) — token/cost/latency summaries
  and repeated weak/best prompt pattern detection.
- **Context Doctor HTML report** (`genaiscope.report`) — distinct from the existing
  `genaiscope dashboard`.
- New CLI: `genaiscope init`, `diagnose`, `analytics`, `report`, and a top-level `export` alias.
- New examples `01_basic_trace.py` through `07_cto_copilot_example.py`.

## Migration notes

**No breaking changes.** Every existing v0.5.x API, CLI command, and on-disk `.db` file keeps
working unchanged.

- New memory fields (`title`, `entities`, `confidence`) and trace fields (`category`, `tags`,
  `session_id`, `rating`, diagnosis results) are stored inside the existing `metadata` JSON
  column on `MemoryItem`/`TraceItem` — no database migration is needed, and no new tables or
  columns were added.
- `memory_type` remains a free string; the new `profile_memory`/`project_memory`/... constants
  in `genaiscope.memory.types` are typo-safety conventions, not an enforced enum. Existing
  custom memory types are unaffected.
- `genaiscope report` (new, Context Doctor) and `genaiscope dashboard` (existing, memory/file/
  trace overview) are two separate commands producing two separate HTML files — neither
  replaces the other.
- If you were relying on `genaiscope.analyzers.CostAnalyzer`'s short-alias-only pricing table,
  it is unchanged; `genaiscope.cost.CostEstimator` is new and additive, with a richer
  provider-keyed table and longest-alias-match resolution for real model ids.

## Known limitations

- Diagnosis scoring is rule-based (regex/heuristics), not model-graded — it will occasionally
  misclassify intent or flag a borderline item as missing. This is by design for v0.6.0 (no
  extra LLM call required); see the v0.7.0 roadmap below for richer evaluation.
- Analytics/pattern aggregation happens in Python over recent traces, not via SQL `GROUP BY` —
  fine at local/single-developer scale, not intended for high-volume production analytics.
- `CostEstimator`'s pricing table is illustrative and will drift from real provider pricing
  over time; treat estimates as directional, not billing-accurate.

## Roadmap: v0.7.0

- MCP server support for Context Doctor tools (memory MCP already shipped in v0.4.0)
- Browser extension capture
- Multi-provider live LLM gateway
- Advanced semantic memory
- Agent evaluation workflows
- LangChain / LlamaIndex integration
- Langfuse export
- OpenTelemetry support
