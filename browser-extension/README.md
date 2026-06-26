# GenAIScope Capture (browser extension)

Captures your prompts and AI replies from ChatGPT, Claude, and Gemini's web apps into
your local GenAIScope memory store, via the existing REST API (`/v1/prompts` and
`/v1/memory/remember` -- no new backend endpoints).

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
