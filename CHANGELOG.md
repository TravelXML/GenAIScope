# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-07-01

Release theme: a REST-exposed live gateway for the browser extension, a browsable dashboard
sample, and a v0.7.0 end-to-end Colab smoke-test pass with fixes for what it found.

### Added

- **`POST /v1/gateway/ask` REST route** (`genaiscope.server.routes_gateway`): exposes the
  v0.7.0 multi-provider live gateway (`GatewayClient.complete()` — same auto-routing,
  fallback, and Context Doctor health score as `scope.gateway`/`genaiscope ask`) over HTTP, so
  any HTTP client can use it, not just Python callers. Returns the provider's `GatewayError`
  as an HTTP 502 with the underlying message.
- **"Ask GenAIScope" browser extension panel** (`browser-extension/popup.html`,
  `popup.js`): a prompt box, provider selector, and result panel wired to the new REST route.
  Lets the extension capture *complete, structured* interactions by calling GenAIScope's own
  gateway with your own API keys, instead of only scraping a chat site's rendered DOM. Additive
  — the existing ChatGPT/Claude/Gemini DOM-capture (`content.js`/`background.js`) is unchanged.
- **Sample dashboard** (`examples/dashboard_sample/`): a committed, browsable
  `dashboard.html` generated from a small demo dataset (memories, a prompt, a file, and traces
  across OpenAI/Anthropic/Google), plus `populate_demo_data.py` to regenerate it. Linked from
  `docs/dashboard.md`.

### Fixed

- **CLI test fragility under forced-color environments** (`tests/conftest.py`): Jupyter's
  ipykernel (and some CI runners) set `FORCE_COLOR`/`CLICOLOR_FORCE` on every subprocess, which
  made Typer's Rich-based `--help`/`version` output embed ANSI escape codes and broke 4 CLI
  tests' plain substring assertions (e.g. `"0.7.0" in result.output`). A session-level
  `conftest.py` now strips those env vars before any test module (and its Typer app) loads.
  Found by an end-to-end run of the v0.7.0 Colab test notebook under a real Jupyter kernel.
- **Duplicated `__version__`** (`src/genaiscope/__init__.py`): was hardcoded separately from
  `genaiscope.version.__version__` instead of importing it, so a version bump could silently
  update one and not the other. `__init__.py` now imports from `genaiscope.version` directly.
- **`genaiscope_complete_colab_test_v0_7_0.ipynb`**: added an `INSTALL_SOURCE = "local"` option
  (test the working copy directly, no git clone) and cells covering every v0.7.0 feature (MCP
  tools, gateway, reranking, agent eval, LangChain/LlamaIndex, Langfuse export, OpenTelemetry,
  browser extension). Fixed two side effects the local-mode run exposed: the CLI smoke-test cell
  now runs with `cwd=WORKDIR` and the install cell now `chdir`s off the repo directory, so
  running the notebook against a real working copy no longer mutates repo-tracked files
  (`.genaiscope/memory.db`) that default-constructed `MemoryStore()`/`LocalTracer()` calls write to.

### Notes on design

- No database/schema migrations: the new REST route reuses the existing `GatewayClient`/tracer
  wiring `genaiscope serve api` already builds; nothing new is stored.

## [0.7.0] - 2026-06-26

Release theme: full v0.7.0 roadmap — MCP tools for Context Doctor, a multi-provider live LLM
gateway, cross-encoder reranking, agent evaluation workflows, LangChain/LlamaIndex integrations,
Langfuse export, OpenTelemetry support, and a browser extension.

### Added

- **MCP tools for Context Doctor** (`genaiscope.mcp.tools`, `genaiscope.mcp.server`):
  `doctor_diagnose`, `analytics_usage_summary`, `analytics_prompt_patterns`, `report_generate`,
  alongside the 6 memory tools shipped in v0.4.0. The 3 trace-dependent tools return a plain
  `{"error": ...}` dict (not an exception) if the MCP server was started without `--trace`.
- **Multi-provider live LLM gateway** (`genaiscope.gateway`, `scope.gateway`, `genaiscope ask`):
  connects `genaiscope.router.recommend()` (offline provider/model-type suggestion) to the
  existing `OpenAIAdapter`/`AnthropicAdapter`/`GeminiAdapter` live SDK calls. `provider="auto"`
  tries `recommend()`'s candidate providers in order, falling back on failure, and raises a new
  `GatewayError` if none succeed. Each call is logged as exactly one trace with an automatically
  attached Context Doctor health score — the first time a real LLM response gets diagnosed
  end-to-end. Only `openai`/`anthropic`/`google` (alias `gemini`) have a live adapter; other
  router suggestions (`groq`/`local`/`ollama`) are skipped.
- **Cross-encoder reranking** (`genaiscope.memory.rerank.CrossEncoderReranker`): opt-in
  `rerank=True` on `MemoryStore.search()` / `ContextBuilder.build()` / the MCP `memory_search`
  tool runs hybrid search over a larger candidate pool, then reranks with
  `cross-encoder/ms-marco-MiniLM-L-6-v2`, blended with each candidate's existing fused score.
  Reuses the `sentence-transformers` dependency already declared by the `embeddings` extra — no
  new dependency.
- **Agent evaluation workflows** (`genaiscope.evals.run_agent_eval`, `AgentTrajectory`,
  `AgentStep`): runs a multi-step agent trajectory against a user-provided callable, scoring
  per-step pass/fail and latency. Library API only (no CLI command — `agent_fn` is a Python
  callable, not something a CLI flag can express). If a `LocalTracer` is given, each step is
  logged with a shared `metadata["task_id"]` for trajectory correlation — no schema change.
- **LangChain integration** (`genaiscope.integrations.langchain.GenAIScopeChatMessageHistory`):
  implements `langchain_core.chat_history.BaseChatMessageHistory` backed by a GenAIScope
  `MemoryStore`, verified against the installed `langchain-core` ABC.
- **LlamaIndex integration** (`genaiscope.integrations.llamaindex.GenAIScopeMemory`): implements
  `llama_index.core.memory.types.BaseMemory`, verified against the installed
  `llama-index-core` ABC.
- **Langfuse batch export** (`genaiscope.export.export_langfuse`, `genaiscope export --format
  langfuse`): writes a JSON file matching Langfuse's documented `POST /api/public/ingestion`
  batch-event shape (`trace-create` + `generation-create` events) — no network call, no
  `langfuse` package dependency.
- **OpenTelemetry exporter hook** (`genaiscope.integrations.otel.OTelExporter`,
  `LocalTracer(exporters=[...])`): maps each logged `TraceItem` to a real OTel span using the
  `gen_ai.*` semantic-convention attribute names, through whatever global `TracerProvider` the
  host application has configured. An exporter failure never breaks local tracing.
- **Browser extension** (`browser-extension/`, manual install): captures prompts/replies from
  ChatGPT, Claude, and Gemini's web apps via the existing `/v1/prompts` and `/v1/memory/remember`
  REST endpoints — no new backend routes. DOM selectors are unofficial and will need updating
  whenever a site's markup changes.
- New optional extras: `otel`, `langchain`, `llamaindex` (added to `all`).

### Notes on design

- No database/schema migrations: gateway traces, agent-eval task correlation, and LangChain/
  LlamaIndex message roles are all carried in the existing `metadata` JSON column, the same
  convention v0.6.0 established for `title`/`entities`/`confidence`/category/tags/session_id.
- The gateway reuses the existing tracer that `serve_mcp`/`serve_api` already build from the same
  backend/db_path/namespace as the memory store, rather than opening a second connection.

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
