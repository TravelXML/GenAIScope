# GenAIScope v0.8.0 Release Notes

GenAIScope v0.8.0 exposes the v0.7.0 live gateway over REST so the browser extension (and any
other HTTP client) can use it, ships a browsable sample dashboard, and fixes several issues an
end-to-end Colab test pass surfaced in v0.7.0.

## Highlights

- **`POST /v1/gateway/ask` REST route** — the same auto-routing, provider fallback, and
  Context Doctor health score as `scope.gateway`/`genaiscope ask`, now reachable over HTTP from
  `genaiscope serve api`. A `GatewayError` (all candidate providers failed) comes back as an
  HTTP 502 with the underlying message.
- **"Ask GenAIScope" browser extension panel** — a prompt box, provider selector, and result
  panel (reply, provider/model, cost, health score) in the extension popup, wired to the new
  REST route. Every call is captured completely and reliably because it's your own gateway
  making a documented SDK call, not DOM-scraping a chat site's private, ever-changing markup.
  Additive: the existing ChatGPT/Claude/Gemini capture (`content.js`/`background.js`) is
  unchanged.
- **Sample dashboard** (`examples/dashboard_sample/dashboard.html`) — committed and browsable
  without running anything, generated from a small demo dataset via
  `populate_demo_data.py`. Linked from `docs/dashboard.md`.
- **v0.7.0 Colab test notebook hardened** — `genaiscope_complete_colab_test_v0_7_0.ipynb` gained
  cells covering every v0.7.0 feature and a local-repo test mode
  (`INSTALL_SOURCE = "local"`, no git clone needed).

## Fixes that came out of the Colab test pass

- CLI tests no longer break under environments that force `FORCE_COLOR`/`CLICOLOR_FORCE`
  (Jupyter's ipykernel does this for every subprocess) — `tests/conftest.py` strips those env
  vars before any Typer app is imported.
- `genaiscope.__version__` (`src/genaiscope/__init__.py`) now imports from
  `genaiscope.version` instead of duplicating the literal, so a version bump can't update one
  copy and silently miss the other.
- Running the Colab notebook against a real local working copy no longer mutates
  repo-tracked files (`.genaiscope/memory.db`): the CLI smoke-test cell now runs with an
  isolated `cwd`, and the install cell `chdir`s off the repo directory afterward, matching how
  a real Colab session behaves (it never `cd`s into the cloned repo either).

## Migration notes

**No breaking changes.** Every existing v0.7.x API, CLI command, REST route, and on-disk `.db`
file keeps working unchanged.

- The new `/v1/gateway/ask` route is additive; no existing route's request/response shape
  changed.
- No database/schema migrations.

## Known limitations

- `/v1/gateway/ask` inherits the same provider coverage as `scope.gateway`: only
  `openai`/`anthropic`/`google` (alias `gemini`) have a live adapter.
- The route calls provider SDKs synchronously inside an `async def` FastAPI handler (matching
  the rest of the REST API's existing pattern) — a slow/hanging provider call blocks that
  worker's event loop for other requests. Acceptable for the local-first, single-user use case
  this API targets; would need a thread-pool offload for high-concurrency deployments.
- The browser extension's "Ask GenAIScope" panel requires the server to be started with its
  own provider API key(s) in the environment and `--trace` for the health score/cost to be
  logged — it does not prompt for or store keys itself.

## Roadmap: next

- Clean up/redesign the generated dashboard's visual presentation (raised as feedback on the
  v0.7.0 dashboard: cards/tables read as dense and utilitarian rather than an at-a-glance
  health-check view).
- Broaden the browser extension's DOM-capture site coverage and resilience alongside the new
  gateway panel.
