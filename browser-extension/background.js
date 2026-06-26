// Receives GENAISCOPE_CAPTURE messages from content.js and calls the local
// GenAIScope REST API. Runs in the extension's background service worker --
// not the page's content-script context -- so it isn't subject to the
// target page's CORS policy as long as host_permissions covers the API host.
const DEFAULT_API_BASE = "http://127.0.0.1:8000";

async function getSettings() {
  const stored = await chrome.storage.local.get(["apiBase", "enabled"]);
  return {
    apiBase: stored.apiBase || DEFAULT_API_BASE,
    enabled: stored.enabled !== false, // default on
  };
}

async function handleCapture(message) {
  const { apiBase, enabled } = await getSettings();
  if (!enabled) return;

  if (message.role === "user") {
    await fetch(`${apiBase}/v1/prompts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: message.text }),
    });
  } else if (message.role === "assistant") {
    await fetch(`${apiBase}/v1/memory/remember`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: message.text,
        memory_type: "conversation",
        tags: ["browser-capture", message.source],
      }),
    });
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type !== "GENAISCOPE_CAPTURE") return;
  handleCapture(message).catch((err) => console.error("GenAIScope capture failed:", err));
});
