# REST API

`genaiscope serve api` starts a FastAPI server exposing the local memory store, tracer, and
(as of v0.8.0) the live LLM gateway over HTTP — the same backend the browser extension and any
non-Python client use. Requires the `server` extra: `pip install "genaiscope[server]"`.

```bash
genaiscope serve api --host 127.0.0.1 --port 8000 --trace
```

| Option | Default | Purpose |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8000` | Bind port |
| `--auth` | `none` | `none` or `bearer` — see [Authentication](#authentication) |
| `--backend` | `sqlite` | `sqlite` or `redis` |
| `--redis-url` | `redis://localhost:6379` | Used when `--backend redis` |
| `--namespace` | `genaiscope` | Redis key namespace |
| `--embedder` | *(none)* | Embedder name for semantic search |
| `--db-path` | *(default location)* | SQLite file path |
| `--trace` | `False` | Log every request as a trace, and enable gateway-call health scoring |

## Authentication

`--auth none` (default) requires no credentials — fine for local-only use. `--auth bearer`
requires every request to send `Authorization: Bearer <token>`, where `<token>` must match the
`GENAISCOPE_API_TOKEN` environment variable set on the server. `/health` is never gated.

```bash
export GENAISCOPE_API_TOKEN=secret123
genaiscope serve api --auth bearer
curl -H "Authorization: Bearer secret123" http://127.0.0.1:8000/v1/memory/stats
```

## Health

```
GET /health
```

Returns `{"status": "ok", "version": "0.8.0"}`. Never requires auth.

## Memory routes

| Route | Body / Query | Returns |
|---|---|---|
| `POST /v1/memory/remember` | `content`, `memory_type`, `user_id`, `project_id`, `workspace_id`, `agent_id`, `session_id`, `tags`, `importance`, `ttl_days`, `metadata` | `{id, memory_type, content}` |
| `POST /v1/memory/search` | `query`, `limit`, `mode`, `user_id`, `project_id`, `workspace_id`, `memory_type` | `{results: [...]}` — hybrid keyword/vector search |
| `POST /v1/memory/context` | `query`, `user_id`, `project_id`, `workspace_id`, `limit`, `max_chars`, `mode` | Retrieved-memory context block, ready to prepend to a prompt |
| `GET /v1/memory/{id}` | — | One memory item, or 404 |
| `GET /v1/memory` | `user_id`, `project_id`, `workspace_id`, `memory_type`, `limit` | `{memories: [...]}` |
| `DELETE /v1/memory/{id}` | — | `{deleted: true, id}`, or 404 |
| `GET /v1/memory/stats` | — | Aggregate memory counts by type/source/user/project/workspace |
| `POST /v1/prompts` | `prompt`, `user_id`, `project_id` | Stores the prompt and returns its quality score, risk level, comments, and suggestions |

```bash
curl -X POST http://127.0.0.1:8000/v1/memory/remember \
  -H "Content-Type: application/json" \
  -d '{"content": "User prefers concise CTO-level answers.", "memory_type": "preference"}'
```

## Gateway route (v0.8.0)

```
POST /v1/gateway/ask
```

Routes a prompt through the same multi-provider live gateway as `scope.gateway.complete()` /
`genaiscope ask` — auto-selects a provider via `genaiscope.router.recommend()`, falls back
across candidates on failure, and (when the server was started with `--trace`) logs exactly one
trace with a cost estimate and Context Doctor health score attached. This is what the browser
extension's **"Ask GenAIScope"** popup panel calls.

Requires `pip install "genaiscope[providers]"` and at least one of `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` set in the server's environment.

**Request body:**

| Field | Type | Default | Notes |
|---|---|---|---|
| `prompt` | `str` | *(required)* | |
| `provider` | `str` | `"auto"` | `"auto"`, `"openai"`, `"anthropic"`, `"google"` (alias `"gemini"`) |
| `model` | `str \| null` | `null` | Overrides the provider's default model |
| `user_id`, `project_id` | `str \| null` | `null` | Attributed to the trace/memory if set |
| `privacy_sensitive`, `cost_sensitive` | `bool` | `false` | Passed to the router when `provider="auto"` |

**Response (200):**

```json
{
  "text": "...",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "input_tokens": 42,
  "output_tokens": 18,
  "estimated_cost": 0.0009,
  "context_health_score": 78,
  "attempted_providers": ["openai"]
}
```

**Error (502):** returned when every candidate provider fails (or none are configured/installed)
— `{"detail": "All candidate providers failed: [...]. Last error: ..."}`.

```bash
curl -X POST http://127.0.0.1:8000/v1/gateway/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Refactor this function and explain the bug", "provider": "auto"}'
```

### Known limitations

- Only `openai`/`anthropic`/`google` have a live adapter; other router-suggested providers
  (`groq`/`local`/`ollama`) are skipped during `provider="auto"` routing.
- The route calls the provider SDK synchronously inside an `async def` handler, matching the
  rest of this API's existing pattern — a slow/hanging call blocks that worker's event loop for
  other requests. Fine for local, single-user use; a high-concurrency deployment would need a
  thread-pool offload.
- Without `--trace`, the call still happens and still returns a response, but nothing gets
  logged — there's no trace to attach a health score's *history* to (the score is still returned
  in the response either way).

## Request tracing middleware

When `--trace` is set, every request (not just the gateway route) is logged as a trace with
`provider="rest"`, `name=<path>`, latency, and `metadata.status_code`. See it with
`genaiscope trace stats` or `genaiscope analytics`.

## See also

- [CLI Reference](cli.md) for the equivalent `genaiscope ask` / `genaiscope serve` commands.
- [Context Doctor](context-doctor.md) for what `context_health_score` measures.
- `browser-extension/README.md` for the extension that calls this API from a browser.
