"use strict";

let automaticRecoveryReady = false;
let automaticRecoveryTimer = null;
let automaticRecoveryDatecode = new Date().toISOString().slice(0, 19).replaceAll(":", "-");
function defaultWorkspaceName() {
  return `${document.documentElement.lang === "pl" ? "zadanie" : "task"} ${automaticRecoveryDatecode}`;
}
function displayWorkspaceName(name) {
  const automatic = /^(task|zadanie) (\d{4}-.*)$/.exec(name);
  if (automatic) { automaticRecoveryDatecode = automatic[2]; workspaceName.value = ""; updateDefaultWorkspaceName(); }
  else workspaceName.value = name;
}
function updateDefaultWorkspaceName() { const name = defaultWorkspaceName(); if (workspaceName.placeholder !== name) workspaceName.placeholder = name; }
updateDefaultWorkspaceName();
new MutationObserver(updateDefaultWorkspaceName).observe(document.documentElement, {attributes:true, attributeFilter:["lang"]});

async function initializeAutomaticRecovery() {
  if (automaticRecoveryReady || workspaceRestoreBusy) return;
  const initial = workspaceFingerprint();
  const payload = await workspacePost("/api/v1/workspaces/recovery", {}, {feedback:false, storageDirectory:""});
  let reference = payload.reference;
  const choices = [...workspaceList.options].filter(option => option.dataset.workspaceId);
  if (!reference && !clearedWorkspaceAtStartup) {
    const latest = choices.sort((a, b) => String(b.dataset.savedAt).localeCompare(String(a.dataset.savedAt)))[0];
    if (latest) reference = {workspace_id:latest.dataset.workspaceId, storage_directory:latest.dataset.storageDirectory || ""};
  }
  if (workspaceFingerprint() !== initial || reviewDirty || translationReviewDirty || selectedGuiAudio.length) {
    // New input takes precedence over recovery, but must still be auto-saved.
    automaticRecoveryReady = true;
    workspaceAutosave.checked = true;
    workspaceAutosave.disabled = false;
    await saveAutomaticWorkspace(true);
    return;
  }
  if (reference) {
    const key = workspaceKey(reference.workspace_id, reference.storage_directory);
    const option = choices.find(item => item.value === key);
    if (!option || option.dataset.available !== "true") {
      workspaceAutosaveStatus.textContent = "The last work state is unavailable. Its recovery file was preserved; restore missing paths or load another workspace.";
      return;
    }
    workspaceList.value = key;
    updateWorkspaceSelectionControls();
    await loadSelectedWorkspace();
    if (activeWorkspaceKey !== key) return;
  }
  automaticRecoveryReady = true;
  workspaceAutosave.checked = true;
  workspaceAutosave.disabled = false;
  if (!activeWorkspaceId) await saveAutomaticWorkspace(true);
  workspaceAutosaveStatus.textContent = "Auto-save active. Changes are saved within a few seconds.";
}

async function saveAutomaticWorkspace(force = false, closing = false) {
  if (!csrfToken || workspaceRestoreBusy || workspaceAutosaveBusy || guiBatchBusy || guiQueueStarting ||
      (!closing && (!workspaceAutosave.checked || workspaceAutosave.disabled)) || (!force && !automaticRecoveryReady)) return false;
  const fingerprint = workspaceFingerprint();
  if (!force && fingerprint === lastWorkspaceFingerprint && !reviewDirty && !translationReviewDirty) return true;
  workspaceAutosaveBusy = true;
  let saveSucceeded = false;
  try {
    if (reviewDocument && reviewDirty) await saveReviewDraft();
    if (translationReview && translationReviewDirty && !(await saveEnhancedTranslationReview()))
      throw new Error("GUI_WORKSPACE_REVIEW_SAVE_FAILED: The open translation draft could not be saved.");
    const storage = activeWorkspaceStorageDirectory || workspaceStorageDirectory();
    const name = workspaceName.value.trim() || defaultWorkspaceName();
    const media = collectPendingGuiMedia();
    const payload = await workspacePost("/api/v1/workspaces/save", {
      workspace_id:activeWorkspaceId, name, current_step:lastWorkspaceStep,
      fields:collectWorkspaceFields(), pending_media:media, autosave:workspaceAutosave.checked,
    }, {feedback:false, storageDirectory:storage});
    const saved = payload.workspace;
    const unchanged = fingerprint === workspaceFingerprint();
    adoptSavedGuiMedia(saved.pending_media || [], media);
    if (unchanged) displayWorkspaceName(saved.name);
    activateWorkspace(saved, storage);
    lastWorkspaceFingerprint = unchanged ? workspaceFingerprint() : fingerprint;
    showWorkspaceFile(payload.workspace_file);
    await refreshWorkspaces(activeWorkspaceKey, {feedback:false});
    workspaceAutosaveStatus.textContent = "Auto-save completed. No credential, confirmation, or editor text was stored.";
    saveSucceeded = true;
  } catch (error) {
    workspaceAutosaveStatus.textContent = `Auto-save could not save the tracked changes and will retry: ${error.message}`;
  } finally {
    workspaceAutosaveBusy = false;
    if (saveSucceeded && automaticRecoveryReady && workspaceAutosave.checked && workspaceFingerprint() !== lastWorkspaceFingerprint)
      scheduleAutomaticWorkspaceSave();
  }
  return saveSucceeded;
}

function scheduleAutomaticWorkspaceSave() {
  if (automaticRecoveryTimer !== null) clearTimeout(automaticRecoveryTimer);
  automaticRecoveryTimer = setTimeout(() => { void saveAutomaticWorkspace(); }, 500);
}
for (const event of ["input", "change", "ewp-stage"]) document.addEventListener(event, scheduleAutomaticWorkspaceSave);
document.addEventListener("ewp-workspace-changed", () => { void saveAutomaticWorkspace(); });
document.addEventListener("visibilitychange", () => { if (document.hidden) void saveAutomaticWorkspace(); });
setInterval(() => { void saveAutomaticWorkspace(); }, 15000);
workspaceAutosave.addEventListener("change", () => {
  void workspacePost("/api/v1/workspaces/recovery", {enabled:workspaceAutosave.checked}, {feedback:false, storageDirectory:""});
});
window.addEventListener("beforeunload", event => {
  if (workspaceAutosaveBusy || workspaceAutosave.checked && workspaceFingerprint() !== lastWorkspaceFingerprint ||
      guiQueueJobs.some(job => ["queued", "running", "cancel_requested"].includes(job.status))) {
    event.preventDefault(); event.returnValue = "";
  }
});
