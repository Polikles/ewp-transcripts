"use strict";

// This bridge exposes only save/readiness results; the native management secret never enters JS.
if (window.chrome?.webview) {
  const editableFingerprint = fingerprint => {
    const value = JSON.parse(fingerprint || "{}");
    delete value.queue; // Live queue metrics are checkpointed by the backend on shutdown.
    return JSON.stringify(value);
  };
  const appearance = () => ({
    theme: document.documentElement.dataset.theme === "dark" ? "dark" : "light",
    themePreference: ["light","dark"].includes(guiPreferences.theme) ? guiPreferences.theme : "system",
    titleBarMode: ["system","application","custom"].includes(guiPreferences.titleBarMode) ? guiPreferences.titleBarMode : "system",
    titleBarColor: /^#[a-f0-9]{6}$/i.test(guiPreferences.titleBarColor || "") ? guiPreferences.titleBarColor : "#24485c",
    locale: document.documentElement.lang === "pl" ? "pl" : "en",
  });
  const sendAppearance = () => window.chrome.webview.postMessage({type:"appearance",...appearance()});
  document.addEventListener("ewp-preferences-changed",sendAppearance);
  sendAppearance();
  const desktopStatus = () => ({
    ...appearance(),
    ready: automaticRecoveryReady && !workspaceRestoreBusy,
    busy: guiBatchBusy || guiQueueStarting || workspaceRestoreBusy || guiMediaImportBusy || guiResultImportBusy ||
      guiQueueJobs.some(job => ["queued", "running", "cancel_requested"].includes(job.status)) ||
      Boolean(document.querySelector('[data-generation-busy="true"], button[aria-busy="true"]')),
    dirty: reviewDirty || translationReviewDirty || workspaceFingerprint() !== lastWorkspaceFingerprint,
    pending_count: collectPendingGuiMedia().length,
  });
  window.chrome.webview.addEventListener("message", async event => {
    const message = event.data;
    if (!message || !["status", "prepare-close"].includes(message.type) ||
        typeof message.id !== "string" || message.id.length > 100) return;
    let ok = true;
    if (message.type === "prepare-close") {
      const deadline = Date.now() + 30000;
      while ((!automaticRecoveryReady || workspaceRestoreBusy || workspaceAutosaveBusy || guiBatchBusy || guiQueueStarting || guiMediaImportBusy || guiResultImportBusy) && Date.now() < deadline)
        await new Promise(resolve => setTimeout(resolve, 100));
      ok = automaticRecoveryReady && !workspaceRestoreBusy && !workspaceAutosaveBusy && !guiBatchBusy && !guiQueueStarting && !guiMediaImportBusy && !guiResultImportBusy;
      if (ok) {
        ok = false;
        for (let attempt = 0; attempt < 3; attempt += 1) {
          if ((await saveAutomaticWorkspace(true, true)) !== true) break;
          if (!reviewDirty && !translationReviewDirty &&
              editableFingerprint(workspaceFingerprint()) === editableFingerprint(lastWorkspaceFingerprint)) {
            ok = true;
            break;
          }
        }
      }
    }
    window.chrome.webview.postMessage({type:"lifecycle-result", id:message.id, ok, ...desktopStatus()});
  });
}
