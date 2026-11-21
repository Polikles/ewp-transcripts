"use strict";

const credentialStoreButtons = document.createElement("div");
credentialStoreButtons.className = "actions";
for (const [action, label] of [
  ["save", "Save key in OS credential store"],
  ["use", "Use saved OpenRouter key"],
  ["remove", "Remove saved OpenRouter key"],
  ["clear-session", "Clear session key"],
]) {
  const button = document.createElement("button"); button.type = "button";
  button.id = `credential-${action}`; button.textContent = label;
  button.addEventListener("click", async () => {
    const input = document.querySelector("#openrouter-api-key");
    const status = document.querySelector("#openrouter-key-dialog-status");
    const apiKey = action === "save" ? input.value : "";
    input.value = ""; button.disabled = true;
    try {
      const payload = await queuePost("/api/v1/credentials/openrouter", {action, api_key:apiKey});
      openRouterKeyConfigured = payload.configured === true; updateOpenRouterKeyStatus();
      status.textContent = action === "save" ? "Key saved in the OS credential store and active for this session."
        : action === "use" ? "Saved OpenRouter key is active for this session."
        : payload.environment_configured ? "Stored/session key cleared. The server environment still supplies a key."
        : "OpenRouter key removed from the selected storage.";
    } catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; }
  });
  credentialStoreButtons.append(button);
}
document.querySelector("#openrouter-key-dialog-status").before(credentialStoreButtons);
const credentialSettings = document.createElement("div");
credentialSettings.id = "gui-credentials";
credentialSettings.innerHTML = `<h3>OpenRouter API key</h3>
  <p class="field-hint">One key is shared by ASR, correction and translation. OS storage is optional. If no secure store is available, use a session-only key. After restarting, choose Use saved OpenRouter key.</p>`;
const credentialSettingsButton = document.createElement("button");
credentialSettingsButton.type = "button";
credentialSettingsButton.textContent = "Manage OpenRouter key";
credentialSettingsButton.addEventListener("click", () => openRouterKeyButton.click());
credentialSettings.append(credentialSettingsButton);
document.querySelector("#dependency-panel").before(credentialSettings);
