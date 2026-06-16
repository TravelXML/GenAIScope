# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
