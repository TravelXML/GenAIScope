const DEFAULT_API_BASE = "http://127.0.0.1:8000";

async function load() {
  const stored = await chrome.storage.local.get(["apiBase", "enabled"]);
  document.getElementById("apiBase").value = stored.apiBase || DEFAULT_API_BASE;
  document.getElementById("enabled").checked = stored.enabled !== false;
}

document.getElementById("save").addEventListener("click", async () => {
  const apiBase = document.getElementById("apiBase").value.trim() || DEFAULT_API_BASE;
  const enabled = document.getElementById("enabled").checked;
  await chrome.storage.local.set({ apiBase, enabled });

  const status = document.getElementById("status");
  status.textContent = "Saved.";
  setTimeout(() => {
    status.textContent = "";
  }, 1500);
});

// "Ask GenAIScope" -- routes the prompt through the server's own live gateway
// (POST /v1/gateway/ask) instead of scraping a provider's web UI. The server
// makes the real OpenAI/Anthropic/Google call with its own API keys and logs
// exactly one trace with a cost estimate and Context Doctor health score.
document.getElementById("ask").addEventListener("click", async () => {
  const askButton = document.getElementById("ask");
  const askStatus = document.getElementById("askStatus");
  const askResult = document.getElementById("askResult");
  const askResultText = document.getElementById("askResultText");
  const askResultMeta = document.getElementById("askResultMeta");

  const prompt = document.getElementById("prompt").value.trim();
  if (!prompt) {
    askStatus.textContent = "Enter a prompt first.";
    return;
  }

  const provider = document.getElementById("provider").value;
  const stored = await chrome.storage.local.get(["apiBase"]);
  const apiBase = stored.apiBase || DEFAULT_API_BASE;

  askButton.disabled = true;
  askStatus.textContent = "Asking...";
  askResult.classList.remove("visible", "error");

  try {
    const resp = await fetch(`${apiBase}/v1/gateway/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, provider }),
    });
    const data = await resp.json();

    if (!resp.ok) {
      throw new Error(data.detail || `Request failed (${resp.status})`);
    }

    askResultText.textContent = data.text;
    const meta = [
      `<span class="badge">${data.provider}${data.model ? " / " + data.model : ""}</span>`,
      `<span class="badge">$${Number(data.estimated_cost || 0).toFixed(6)}</span>`,
    ];
    if (data.context_health_score !== null && data.context_health_score !== undefined) {
      meta.push(`<span class="badge">Health ${data.context_health_score}/100</span>`);
    }
    askResultMeta.innerHTML = meta.join("");
    askResult.classList.add("visible");
    askStatus.textContent = "";
  } catch (err) {
    askResultText.textContent = String(err.message || err);
    askResultMeta.innerHTML = "";
    askResult.classList.add("visible", "error");
    askStatus.textContent = "";
  } finally {
    askButton.disabled = false;
  }
});

load();
