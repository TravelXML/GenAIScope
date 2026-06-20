# GenAIScope v0.5.0 Release Notes

GenAIScope v0.5.0 is the Memory Compaction + Automatic Observability release.

## Highlights

- **Semantic memory compaction**: clusters near-duplicate memories by embedding cosine
  similarity — catching paraphrases that text-based dedupe misses — and merges each cluster
  deterministically (`keep_best`) or via an LLM-assisted `summarizer` (OpenAI/Anthropic/Gemini),
  reporting tokens/$ saved per future context injection
- `genaiscope memory compact` CLI command and `genaiscope.memory.compact_memories()` API
- `BaseVectorStore.get_vector()` on `LocalVectorStore`/`RedisVectorStore` to fetch a stored
  embedding without re-embedding
- Public `genaiscope.evals.memory_eval.compute_metrics` for recall@k/precision@k/MRR, reused by
  the new compaction regression tests to prove compaction never reduces retrieval recall
- **Automatic observability**: `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`,
  `genaiscope serve mcp`, and `genaiscope serve api` now accept an optional tracer
  (`tracer=...` / CLI `--trace`) and automatically log latency, real token usage, estimated
  cost, and success/error status for every call — no manual instrumentation needed. The
  existing local dashboard and `genaiscope trace list/show/stats` immediately surface this data
  once enabled. Off by default; zero behavior change for existing callers.

## Known Limitations

- Trace cost shows `$0.00` for most real provider model strings — `CostAnalyzer`'s pricing
  table matches short aliases (`"gpt-4"`, `"claude-3-sonnet"`, `"gemini-pro"`), not real model
  identifiers like `"gpt-4o-mini-2024-07-18"`. A model-name normalizer is a natural fast-follow.
- Qdrant and pgvector vector backends are still planned for a future release.
- Full RAG evaluation, agent tool safety, and org RBAC — originally floated for v0.5.0 — are now
  planned for v0.6.0.
