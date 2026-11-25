"use strict";

const credentialStoreButtons = document.createElement("div");
credentialStoreButtons.className = "actions credential-store-primary";
for (const [action, label] of [
  ["save", "Save key"],
  ["use", "Use saved key"],
  ["remove", "Remove saved key"],
  ["clear-session", "Clear session key"],
]) {
  const button = document.createElement("button"); button.type = "button";
  button.id = `credential-${action}`; button.textContent = label;
  button.addEventListener("click", async () => {
    const input = document.querySelector("#openrouter-api-key");
    const status = document.querySelector("#openrouter-key-dialog-status");
    const apiKey = action === "save" ? input.value : "";
    input.value = ""; updateSessionKeyButton();keyCheckStatus.textContent="";button.disabled = true;
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
const credentialSecondary=document.createElement("div");credentialSecondary.className="credential-store-secondary";
credentialSecondary.append(document.querySelector("#credential-remove"),document.querySelector("#credential-clear-session"));
credentialStoreButtons.after(credentialSecondary);
document.querySelector("#credential-save").title="Save key in OS credential store";
document.querySelector("#credential-use").title="Use saved OpenRouter key";
const credentialFooter=document.createElement("div");credentialFooter.className="credential-dialog-footer";
credentialFooter.append(document.querySelector("#cancel-openrouter-key"));
document.querySelector("#openrouter-key-dialog-status").after(credentialFooter);

const credentialSettings = document.createElement("div");
credentialSettings.id = "gui-credentials";
credentialSettings.innerHTML = `<h3>OpenRouter API key</h3>
  <p class="field-hint">One key is shared by ASR, correction and translation. OS storage is optional. If no secure store is available, use a session-only key. After restarting, check the connection to load a saved key, or choose Use saved OpenRouter key.</p>`;
const credentialSettingsButton = document.createElement("button");
credentialSettingsButton.type = "button";
credentialSettingsButton.textContent = "Manage OpenRouter key";
credentialSettingsButton.addEventListener("click", () => openRouterKeyButton.click());
credentialSettings.append(credentialSettingsButton);
document.querySelector("#dependency-panel").before(credentialSettings);

document.querySelector("#close-openrouter-key-icon").addEventListener("click",closeOpenRouterKeyDialog);
document.addEventListener("keydown", event => {
  if (openRouterKeyDialog.hidden) return;
  if (event.key === "Escape") {
    event.preventDefault(); event.stopPropagation(); closeOpenRouterKeyDialog(); return;
  }
  if (event.key !== "Tab") return;
  const controls = [...openRouterKeyDialog.querySelectorAll("button:not(:disabled), input:not(:disabled), select:not(:disabled), a[href]")].filter(control => control.getClientRects().length);
  const first = controls[0], last = controls.at(-1);
  if (!first) return;
  if (!openRouterKeyDialog.contains(document.activeElement) || (!event.shiftKey && document.activeElement === last)) {
    event.preventDefault(); first.focus();
  } else if (event.shiftKey && document.activeElement === first) {
    event.preventDefault(); last.focus();
  }
}, true);
const keyCheckButton=document.querySelector("#check-openrouter-key");
const keyCheckGroup=document.createElement("div");keyCheckGroup.className="credential-key-check";keyCheckButton.before(keyCheckGroup);keyCheckGroup.append(keyCheckButton);
const keyCheckStatus=document.createElement("p");keyCheckStatus.id="openrouter-key-check-status";keyCheckStatus.setAttribute("role","status");keyCheckStatus.className="field-hint";keyCheckGroup.append(keyCheckStatus);
document.querySelector("#check-openrouter-key").addEventListener("click",async event=>{
  const button=event.currentTarget,input=document.querySelector("#openrouter-api-key"),status=keyCheckStatus;
  const key=input.value;input.value="";button.disabled=true;status.textContent="Checking OpenRouter key and connection…";
  try {
    const result=await queuePost("/api/v1/speech/check",key ? {api_key:key} : {},{trigger:button});
    showOpenRouterCheckResult(result,status);
  }catch(error){status.textContent=error.message;}
  finally{input.value="";button.disabled=false;}
});

openRouterKeyButton.addEventListener("click",()=>{keyCheckStatus.textContent="";});
document.querySelector("#openrouter-api-key").addEventListener("input",()=>{keyCheckStatus.textContent="";});

// Loading a stored key already activates the session; only entered text can set another key.
function updateSessionKeyButton() {
  document.querySelector("#save-openrouter-key").disabled=!document.querySelector("#openrouter-api-key").value.trim();
}
document.querySelector("#openrouter-api-key").addEventListener("input",updateSessionKeyButton);
openRouterKeyButton.addEventListener("click",updateSessionKeyButton);
new MutationObserver(updateSessionKeyButton).observe(document.querySelector("#openrouter-key-dialog-status"),{childList:true,subtree:true,characterData:true});
for(const button of credentialStoreButtons.querySelectorAll("button"))button.addEventListener("click",updateSessionKeyButton);
keyCheckButton.addEventListener("click",updateSessionKeyButton);
updateSessionKeyButton();

document.querySelector("#save-openrouter-key").addEventListener("click",updateSessionKeyButton);

function showOpenRouterCheckResult(result,status) {
  if(result.loaded_saved_key){openRouterKeyConfigured=true;updateOpenRouterKeyStatus();}
  status.textContent=result.loaded_saved_key
    ? "OpenRouter key and connection are ready. Saved key loaded. No audio was uploaded."
    : "OpenRouter key and connection are ready. No audio was uploaded.";
}
