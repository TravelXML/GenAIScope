// Captures user/assistant turns from supported chat sites and forwards them
// to the background script, which calls the local GenAIScope REST API.
//
// These DOM selectors are unofficial and will break whenever a site changes
// its markup -- that's inherent to scraping a third-party web UI, not a bug
// here. If capture stops working, check whether the site's structure changed
// and update SITE_CONFIGS below.
(function () {
  const PROCESSED_ATTR = "data-genaiscope-captured";
  const DEBOUNCE_MS = 1200; // wait for streaming responses to finish before reading text

  const SITE_CONFIGS = [
    {
      match: (host) => host.includes("chatgpt.com") || host.includes("chat.openai.com"),
      turnSelector: "[data-message-author-role]",
      roleOf: (el) => el.getAttribute("data-message-author-role"),
      textOf: (el) => el.innerText.trim(),
    },
    {
      match: (host) => host.includes("claude.ai"),
      turnSelector: "[data-testid='user-message'], div.font-claude-message",
      roleOf: (el) => (el.matches("[data-testid='user-message']") ? "user" : "assistant"),
      textOf: (el) => el.innerText.trim(),
    },
    {
      match: (host) => host.includes("gemini.google.com"),
      turnSelector: "user-query, model-response",
      roleOf: (el) => (el.tagName.toLowerCase() === "user-query" ? "user" : "assistant"),
      textOf: (el) => el.innerText.trim(),
    },
  ];

  const config = SITE_CONFIGS.find((c) => c.match(location.hostname));
  if (!config) return;

  function captureNewTurns() {
    const turns = document.querySelectorAll(config.turnSelector);
    for (const el of turns) {
      if (el.getAttribute(PROCESSED_ATTR)) continue;
      const text = config.textOf(el);
      if (!text) continue;
      const role = config.roleOf(el);
      if (role !== "user" && role !== "assistant") continue;
      el.setAttribute(PROCESSED_ATTR, "1");
      chrome.runtime.sendMessage({
        type: "GENAISCOPE_CAPTURE",
        role,
        text,
        source: location.hostname,
      });
    }
  }

  let debounceTimer = null;
  const observer = new MutationObserver(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(captureNewTurns, DEBOUNCE_MS);
  });
  observer.observe(document.body, { childList: true, subtree: true });

  captureNewTurns();
})();
