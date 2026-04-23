const DEFAULT_APP_BASE_URL = "http://127.0.0.1:5001";

function normalizeBaseUrl(value) {
  if (!value) {
    return DEFAULT_APP_BASE_URL;
  }
  return value.replace(/\/+$/, "");
}

async function getAppBaseUrl() {
  const stored = await chrome.storage.sync.get({
    appBaseUrl: DEFAULT_APP_BASE_URL,
  });
  return normalizeBaseUrl(stored.appBaseUrl);
}

async function getSelectedText(tabId) {
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        const selection = window.getSelection();
        return selection ? selection.toString() : "";
      },
    });
    return result && result.result ? result.result : "";
  } catch (error) {
    return "";
  }
}

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !tab.id) {
    return;
  }

  const selectedText = await getSelectedText(tab.id);
  const appBaseUrl = await getAppBaseUrl();
  const params = new URLSearchParams({
    source: "clipper",
    title: tab.title || "",
    url: tab.url || "",
    selected_text: selectedText,
  });

  chrome.tabs.create({
    url: `${appBaseUrl}/opportunities/capture/?${params.toString()}`,
  });
});
