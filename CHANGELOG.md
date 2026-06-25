# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-06-25

Release theme: **Context Doctor** — memory + tracing + rule-based prompt/context health
diagnosis and improvement.

### Added

- **`GenAIScope` facade** (`genaiscope.core.scope`, exported from `genaiscope` and
  `genaiscope.core`): one shared local store behind `scope.memory`, `scope.context`,
  `scope.doctor`, `scope.cost`, `scope.analytics`, `scope.router`, and `scope.report`.
  `scope.trace(...)` (context manager) and `scope.log_interaction(...)` log prompt/response
  interactions with provider/model/category/tags/scope ids, automatically attaching a Context
  Doctor health score to the trace.
- **`ContextDoctor`** (`genaiscope.doctor`): rule-based `diagnose()` returning a
  `context_health_score` (0-100) plus seven sub-scores (prompt clarity, context completeness,
  memory match, model fit, token efficiency, hallucination risk, answer specificity),
  detected intent/entities, missing-context list, prompt issues, a recommended prompt rewrite,
  recommended model type, and improvement tips. No LLM call required.
- **`ContextBuilder`** (`genaiscope.context`): retrieves relevant memory and returns
  `retrieved_memories`, `context_text`, an `improved_prompt`, `token_estimate`,
  `memory_ids_used`, and a `context_quality_score`.
- **`CostEstimator`** (`genaiscope.cost`): provider-aware cost estimation (openai, anthropic,
  google, groq, ollama/local — local models are free unless priced explicitly), with a
  longest-alias-match pricing lookup so real dated model ids (e.g.
  `gpt-4o-mini-2024-07-18`) resolve correctly.
- **Model-type recommendation** (`genaiscope.router.recommend`): classifies a prompt into
  reasoning/coding/writing/summarization/extraction/local, with privacy- and cost-sensitive
  provider suggestions. No auto-routing yet, by design.
- **Usage analytics + prompt patterns** (`genaiscope.analytics`): `usage_summary()`
  (tokens/cost/latency over a time window) and `prompt_patterns()` (top categories/tags/entities,
  repeated weak patterns, best-performing prompt templates, per-category health/token/model
  breakdowns).
- **Context Doctor HTML report** (`genaiscope.report`), distinct from the existing
  `genaiscope dashboard`: health-score trend, weak/best prompt patterns, model/provider
  comparison, recent traces, memory usage.
- New memory-type constants (`genaiscope.memory.types`): `profile_memory`, `project_memory`,
  `preference_memory`, `conversation_memory`, `document_memory`, `entity_memory`,
  `decision_memory`, `learning_memory`, `prompt_pattern_memory` — conventions, not an enforced
  enum; existing/custom memory types keep working unchanged.
- New CLI commands: `genaiscope init`, `genaiscope diagnose --prompt "..."`,
  `genaiscope analytics`, `genaiscope report --out FILE`, and a top-level
  `genaiscope export --format json --out FILE` alias for `memory export`.
- New examples `examples/01_basic_trace.py` through `examples/07_cto_copilot_example.py`
  (the last is a full memory → context → trace → diagnosis → HTML report walkthrough).

### Notes on design

- No new database columns or migrations: `title`/`confidence`/`entities` (memory) and
  `category`/`tags`/`session_id`/`rating`/diagnosis results (traces) are stored in the existing
  `metadata` JSON column on `MemoryItem`/`TraceItem`. Existing `.db` files keep working
  unchanged; analytics/pattern modules group these in Python rather than via SQL `GROUP BY`,
  which is the intentional trade-off at the local/single-developer scale this layer targets.
- Reuses the existing embeddings/vector-search stack for memory retrieval (no new vector DB
  dependency) and the existing `HallucinationDetector`/`CostAnalyzer` for two of the doctor's
  sub-scores, rather than duplicating that logic.
- `genaiscope report` (Context Doctor) and `genaiscope dashboard` (memory/file/trace overview)
  remain two distinct, separately generated HTML artifacts.

## [0.5.1] - 2026-06-25

### Fixed

- **REST API route registration crash.** `genaiscope.server.routes_health` and
  `routes_memory` combined `from __future__ import annotations` with imports made
  *inside* the `add_*_routes()` functions, so FastAPI/Pydantic could not resolve
  those names as forward references at route-registration time, raising
  `PydanticUndefinedAnnotation` from `create_app()` against current FastAPI/Pydantic
  releases. This also broke `tests/test_server_api.py` (5/7 failing). Fixed by moving
  the affected imports to module level in both files.
- **REST API/MCP server SQLite thread-affinity crash.** `SQLiteMemoryStore` and the
  SQLite-backed `LocalTracer` opened their shared connection with the sqlite3 default
  `check_same_thread=True`, which raised `sqlite3.ProgrammingError` the first time a
  request was served from a different thread than the one that created the store —
  surfaced once the route-registration bug above was fixed, and present since the
  REST API/MCP server shipped in v0.4.0. Fixed by opening both connections with
  `check_same_thread=False` (access remains effectively serialized for GenAIScope's
  single-store-per-server usage pattern).

## [0.5.0] - 2026-06-20

Release theme: **Memory Compaction + Automatic Observability**

### Added

- **Semantic memory compaction** (`genaiscope.memory.compaction`): clusters near-duplicate
  memories by embedding cosine similarity (catching paraphrases that text-based dedupe misses)
  and merges each cluster into one memory, either deterministically (`keep_best`) or via an
  LLM-assisted `summarizer` callable. Reports tokens/$ saved per future context injection.
- `genaiscope memory compact` CLI command (`--apply/--dry-run`, `--strategy`, `--threshold`,
  `--summarizer none|openai|anthropic|gemini`).
- `genaiscope.adapters.openai_summarizer` / `anthropic_summarizer` / `gemini_summarizer` — thin
  provider-agnostic factories producing a merge-callable for compaction's synthesis strategy.
- `BaseVectorStore.get_vector(vector_id)` (with `LocalVectorStore`/`RedisVectorStore`
  implementations) to fetch an already-stored embedding without re-embedding.
- `genaiscope.evals.memory_eval.compute_metrics` made public so callers (including the new
  compaction regression tests) can compute recall@k/precision@k/MRR directly.
- **Automatic observability**: `OpenAIAdapter`/`AnthropicAdapter`/`GeminiAdapter`,
  `genaiscope serve mcp`, and `genaiscope serve api` now accept an optional `tracer` (CLI:
  `--trace`) and automatically record latency, real token usage, estimated cost, and
  success/error status for every call into GenAIScope's existing local tracing store — no
  manual instrumentation required. Defaults to off; zero behavior change when not configured.

### Known limitations

- Trace cost is `$0.00` for most real provider model strings, since `CostAnalyzer`'s pricing
  table only matches short aliases (`"gpt-4"`, `"claude-3-sonnet"`, `"gemini-pro"`), not real
  model identifiers (e.g. `"gpt-4o-mini-2024-07-18"`). Latency/tokens/status are unaffected.

## [0.4.0] - 2026-06-16

Release theme: **Universal Memory Access** — Embeddings + Vector Search + MCP Memory Server + REST API + Provider Adapters

### Added

- **Pluggable embedding providers** (`genaiscope.embeddings`): local hash (zero-dependency default), sentence-transformers, and OpenAI backends
- **Vector store abstraction** (`genaiscope.vector`): LocalVectorStore (SQLite-backed cosine search) and RedisVectorStore (optional)
- **Real semantic and fused hybrid memory search**: `mode="keyword"` | `mode="vector"` | `mode="hybrid"` (default)
- **`memory.context()`** injectable-context helper — returns a ready-to-inject text block with char/token budget control
- **`MemorySearchResult`** extended with `vector_score`, `keyword_score`, `fused_score`, `embedder_name` fields
- **Semantic cache upgraded** to embedding cosine similarity with configurable threshold (deterministic fallback retained)
- **MCP memory server** (`genaiscope.mcp`): stdio and StreamableHTTP transports, optional bearer auth; tools: `memory_remember`, `memory_search`, `memory_context`, `memory_add_prompt`, `memory_list`, `memory_stats`
- **REST API server** (`genaiscope.server`): FastAPI app with `/health`, `/v1/memory/*`, `/v1/prompts` endpoints; optional bearer auth
- **Provider adapters** (`genaiscope.adapters`): `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter` with automatic memory context injection and turn persistence
- **Memory retrieval eval harness** (`genaiscope.evals`): recall@k, precision@k, MRR per mode; built-in sample dataset; `run_eval()`
- **New error classes**: `EmbeddingBackendError`, `VectorBackendError`, `MCPDependencyMissingError`, `ServerDependencyMissingError`, `ProviderDependencyMissingError`, `AdapterError`
- **New CLI commands**: `genaiscope embed test`, `genaiscope embed reindex`, `genaiscope serve mcp`, `genaiscope serve api`, `genaiscope eval memory`
- **New optional extras**: `genaiscope[embeddings]`, `genaiscope[mcp]`, `genaiscope[server]`, `genaiscope[providers]`

### Changed

- Default search mode is now fused hybrid when an embedder is configured (degrades transparently to keyword otherwise)
- `memory search` CLI command now shows `Vec` and `KW` score columns and accepts `--mode` and `--embedder` flags

### Known limitations

- Consumer Gemini app has no custom MCP support; use the REST API / GeminiAdapter instead
- Full RAG evaluation, agent tool safety, and org RBAC are planned for v0.5.0
- Qdrant / pgvector vector backends planned for a future release

## [0.3.0] - 2026-05-31

### Added

- Pluggable SQLite and optional Redis memory backends
- User, project, workspace, agent, and session scoped memory
- TTL expiry and cleanup, deterministic hybrid search, dedupe, and export/import
- Redis trace store support and lightweight semantic cache foundation
- Backend-aware dashboard statistics and Memovo-ready memory APIs

### Known limitations

- Redis vector search with real embeddings is planned for v0.4.0
- MCP server is planned for v0.5.0
- Qdrant and pgvector support are planned for later releases

## [0.2.91] - 2026-05-27

### Fixed

- Completed PyPI README footer links for contribution guidelines, license, documentation, issues, and discussions.

## [0.2.90] - 2026-05-27

### Added

- SQLite-backed local memory store
- Local memory search
- Prompt quality coach with comments and suggestions
- File memory for TXT, MD, JSON, and CSV
- Local trace logging
- Static HTML dashboard
- CLI command groups for memory, files, trace, and dashboard
- Tests, examples, docs, and release notes for local-first workflows

### Changed

- Version updated to 0.2.90
- README expanded with memory, file, tracing, and dashboard examples

## [0.1.0] - 2024-05-24

### Added

- Initial release of GenAIScope
- Core inspection module for prompts, RAG, and outputs
- Analyzers for cost estimation, PII detection, hallucination detection, and safety analysis
- Structured output validators for JSON, XML, and CSV
- Scoring engine with pluggable scorers
- CLI interface with Rich terminal output
- Configuration management via environment variables
- Comprehensive test suite
- Full type hints and Pydantic models
- Support for OpenAI, Anthropic, and Google providers
- Local provider for testing

### Features

- One-line useful APIs for beginners
- Deep inspection APIs for advanced teams
- CLI-first developer experience
- Clear reports for CTOs and clients
- No vendor lock-in
- Local-first by default
- Async-first where useful
- Production-ready code quality

[0.1.0]: https://github.com/genaiscope/genaiscope/releases/tag/v0.1.0
