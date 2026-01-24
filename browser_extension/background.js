const ENDPOINT = "http://127.0.0.1:8080/events";
const BROWSER_APP = "CHROME.EXE"; // Change to "WHALE.EXE" for Whale.
const SOURCE = "browser_extension";
const EVENT_TYPE = "browser.tab_active";
const URL_MODE = "full"; // "full" or "domain"
const MIN_INTERVAL_MS = 1500;

const lastSent = new Map();

function isHttpUrl(url) {
  return typeof url === "string" && (url.startsWith("http://") || url.startsWith("https://"));
}

function getDomain(url) {
  try {
    return new URL(url).hostname || "";
  } catch {
    return "";
  }
}

function normalizeUrl(url) {
  if (!isHttpUrl(url)) {
    return "";
  }
  if (URL_MODE === "domain") {
    return getDomain(url);
  }
  return url;
}

function shouldSend(tabId, signature) {
  const now = Date.now();
  const prev = lastSent.get(tabId);
  if (prev && prev.signature === signature && now - prev.ts < MIN_INTERVAL_MS) {
    return false;
  }
  lastSent.set(tabId, { signature, ts: now });
  return true;
}

function sendTab(tab) {
  if (!tab || !isHttpUrl(tab.url)) {
    return;
  }
  const domain = getDomain(tab.url);
  const urlValue = normalizeUrl(tab.url);
  const title = tab.title || "";

  const signature = `${urlValue}|${title}`;
  const tabId = tab.id ?? "unknown";
  if (!shouldSend(tabId, signature)) {
    return;
  }

  const event = {
    schema_version: "1.0",
    source: SOURCE,
    app: BROWSER_APP,
    event_type: EVENT_TYPE,
    resource: { type: "url", id: urlValue || domain || "unknown" },
    payload: {
      window_title: title,
      url: urlValue,
      domain: domain,
    },
  };

  fetch(ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  }).catch(() => {});
}

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  try {
    const tab = await chrome.tabs.get(tabId);
    sendTab(tab);
  } catch {
    // ignore
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (!tab.active) {
    return;
  }
  if (changeInfo.url || changeInfo.title || changeInfo.status === "complete") {
    sendTab(tab);
  }
});
