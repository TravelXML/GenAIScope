# GenAIScope v0.7.0 Release Notes

GenAIScope v0.7.0 ships the entire v0.7.0 roadmap named in the v0.6.0 release notes: MCP tools
for Context Doctor, a multi-provider live LLM gateway, cross-encoder reranking, agent evaluation
workflows, LangChain/LlamaIndex integrations, Langfuse export, OpenTelemetry support, and a
browser extension.

## Highlights

- **MCP tools for Context Doctor** — `doctor_diagnose`, `analytics_usage_summary`,
  `analytics_prompt_patterns`, `report_generate`, alongside the v0.4.0 memory tools.
- **Multi-provider live LLM gateway** (`scope.gateway`, `genaiscope ask`) — auto-routes to a
  real OpenAI/Anthropic/Google call using `genaiscope.router.recommend()`'s candidate list, with
  fallback across providers and a Context Doctor health score attached to every call.
- **Cross-encoder reranking** — `rerank=True` on memory search reranks a larger hybrid-search
  candidate pool with `cross-encoder/ms-marco-MiniLM-L-6-v2` (reuses the existing
  `sentence-transformers` dependency, no new one).
- **Agent evaluation workflows** — `genaiscope.evals.run_agent_eval()` scores a multi-step agent
  trajectory's per-step pass/fail and latency. Library API only, no CLI command.
- **LangChain / LlamaIndex integrations** — `GenAIScopeChatMessageHistory` and `GenAIScopeMemory`,
  each implementing the real installed library's memory ABC.
- **Langfuse batch export** — `genaiscope export --format langfuse` writes a JSON file in
  Langfuse's documented ingestion-batch shape.
- **OpenTelemetry exporter hook** — `LocalTracer(exporters=[OTelExporter()])` maps every trace to
  a real OTel span using `gen_ai.*` semantic-convention attributes.
- **Browser extension** (`browser-extension/`) — captures prompts/replies from ChatGPT, Claude,
  and Gemini's web apps via the existing REST API, manual install only.

## Migration notes

**No breaking changes.** Every existing v0.6.x API, CLI command, and on-disk `.db` file keeps
working unchanged.

- `MemoryStore.search()` / `ContextBuilder.build()` gained an optional `rerank: bool = False`
  parameter — default behavior is identical to v0.6.x.
- `LocalTracer.__init__()` gained an optional `exporters` parameter — omitting it behaves exactly
  as before.
- New optional extras (`otel`, `langchain`, `llamaindex`) are additive; existing extras
  (`providers`, `embeddings`, `mcp`, `server`) are unchanged.
- No database/schema migrations: gateway traces, agent-eval task correlation, and LangChain/
  LlamaIndex message roles are all carried in the existing `metadata` JSON column.

## Known limitations

- The gateway only has a live adapter for `openai`/`anthropic`/`google` (alias `gemini`); other
  router-suggested providers (`groq`/`local`/`ollama`) are skipped during auto-routing.
- Browser extension DOM selectors are unofficial and will break whenever ChatGPT, Claude, or
  Gemini's web apps change their markup — inherent to scraping a third-party UI, not a defect.
- Langfuse export is a batch JSON file, not a live SDK push; pipe it through Langfuse's own
  ingestion endpoint or SDK to actually load it.
- LangChain/LlamaIndex integrations are verified against the versions installed at the time of
  this release (`langchain-core>=0.3.0`, `llama-index-core>=0.11.0`); both libraries' memory ABCs
  have changed across versions before.

## Roadmap: next

Nothing carried over from this release — the full documented v0.7.0 list shipped in one pass.
Future work: live (not just batch) Langfuse push, additional gateway providers, a Chrome Web
Store listing for the browser extension.
