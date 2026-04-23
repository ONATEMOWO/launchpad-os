const DEFAULT_APP_BASE_URL = "http://127.0.0.1:5001";

function normalizeBaseUrl(value) {
  if (!value) {
    return DEFAULT_APP_BASE_URL;
  }
  return value.replace(/\/+$/, "");
}

async function loadSettings() {
  const result = await chrome.storage.sync.get({
    appBaseUrl: DEFAULT_APP_BASE_URL,
  });
  document.getElementById("appBaseUrl").value = normalizeBaseUrl(
    result.appBaseUrl
  );
}

async function saveSettings() {
  const input = document.getElementById("appBaseUrl");
  const status = document.getElementById("statusMessage");
  const appBaseUrl = normalizeBaseUrl(input.value.trim());

  await chrome.storage.sync.set({ appBaseUrl });
  status.textContent = "Saved.";
}

async function resetSettings() {
  const input = document.getElementById("appBaseUrl");
  const status = document.getElementById("statusMessage");

  await chrome.storage.sync.set({ appBaseUrl: DEFAULT_APP_BASE_URL });
  input.value = DEFAULT_APP_BASE_URL;
  status.textContent = "Reset to the default local URL.";
}

document.getElementById("saveButton").addEventListener("click", saveSettings);
document.getElementById("resetButton").addEventListener("click", resetSettings);

loadSettings();
