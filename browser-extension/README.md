# GenAIScope Capture (browser extension)

Captures your prompts and AI replies from ChatGPT, Claude, and Gemini's web apps into
your local GenAIScope memory store, via the existing REST API (`/v1/prompts` and
`/v1/memory/remember` -- no new backend endpoints).

It also has an **"Ask GenAIScope"** panel in the popup that routes a prompt through
GenAIScope's own live gateway (`POST /v1/gateway/ask`) instead of scraping a
provider's web UI. The server makes the real OpenAI/Anthropic/Google call with its
own API keys and logs exactly one trace with a cost estimate and Context Doctor
health score -- reliable, structured capture, since it's your own code calling a
documented SDK rather than reverse-engineering someone else's private web app.

## Known limitation

The DOM selectors in `content.js` are unofficial and **will break** whenever one of
these sites changes its markup. That's inherent to scraping a third-party web UI, not
a bug in this extension. If capture stops working for a site, inspect its current
message markup and update `SITE_CONFIGS` in `content.js`.

## Install (unpacked, no Chrome Web Store listing)

1. Start the GenAIScope REST API locally: `genaiscope serve api` (defaults to
   `http://127.0.0.1:8000`).
2. Open `chrome://extensions` in Chrome (or the equivalent in any Chromium-based
   browser).
3. Enable "Developer mode" (top-right toggle).
4. Click "Load unpacked" and select this `browser-extension/` directory.
5. Click the extension's toolbar icon to open the popup, confirm "Capture enabled" is
   checked, and that the API base URL matches your running `genaiscope serve api`
   instance (defaults to `http://127.0.0.1:8000`).
6. Visit chatgpt.com, claude.ai, or gemini.google.com and send a message.

## Verify it worked

```bash
genaiscope memory list
```

You should see your prompt and the assistant's reply as `conversation` memories
(prompts are also scored and stored via `/v1/prompts`).

## Using "Ask GenAIScope"

1. Install `genaiscope[providers]` and set at least one of `OPENAI_API_KEY`,
   `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` in the environment the server runs in.
2. Start the server with tracing on, so calls get a health score and cost logged:
   `genaiscope serve api --trace`.
3. Open the popup, type a prompt under "Ask GenAIScope", pick a provider (or leave
   "Auto"), and click **Ask**.
4. Check `genaiscope trace stats` / `genaiscope analytics` to see it logged.

If no provider key is configured, or all candidate providers fail, the popup shows
the error returned by the server (HTTP 502) instead of a reply.
