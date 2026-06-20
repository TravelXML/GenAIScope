# GenAIScope v0.4.0 Release Notes

GenAIScope v0.4.0 is the Universal Memory Access release.

## Highlights

- Pluggable embedding providers: LocalHashEmbedder (zero-dependency), SentenceTransformerEmbedder, and OpenAIEmbedder
- SQLite-backed LocalVectorStore and optional RedisVectorStore for semantic retrieval
- Three memory search modes: keyword, vector, and fused hybrid (default)
- Injectable context helper via `memory.context()` with char budget control
- MCP memory server with stdio and StreamableHTTP transports for Claude Desktop, Gemini CLI, and enterprise hosts
- FastAPI REST API server with `/health`, `/v1/memory/*`, and `/v1/prompts` endpoints
- Provider adapters for OpenAI, Anthropic, and Gemini with automatic memory injection and turn persistence
- Memory retrieval eval harness with recall@k, precision@k, and MRR metrics
- Upgraded semantic cache with embedding cosine similarity and configurable threshold

## Known Limitations

- Consumer Gemini app has no custom MCP support; use the REST API or GeminiAdapter instead
- Qdrant and pgvector vector backends are planned for a future release
- Full RAG evaluation, agent tool safety, and org RBAC are planned for v0.5.0
