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

load();
