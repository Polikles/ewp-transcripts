"use strict";

let automaticRecoveryReady = false;
let automaticRecoveryTimer = null;
const automaticRecoveryName = `Recovery ${new Date().toISOString().slice(0, 19).replaceAll(":", "-")} ${crypto.randomUUID().slice(0, 6)}`;

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
    workspaceAutosaveStatus.textContent = "Startup recovery paused because current work changed. Save or load a workspace to continue.";
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

async function saveAutomaticWorkspace(force = false) {
  if (!csrfToken || workspaceRestoreBusy || workspaceAutosaveBusy || guiBatchBusy || guiQueueStarting ||
      !workspaceAutosave.checked || workspaceAutosave.disabled || (!force && !automaticRecoveryReady)) return;
  const fingerprint = workspaceFingerprint();
  if (!force && fingerprint === lastWorkspaceFingerprint && !reviewDirty && !translationReviewDirty) return;
  workspaceAutosaveBusy = true;
  try {
    if (reviewDocument && reviewDirty) await saveReviewDraft();
    if (translationReview && translationReviewDirty && !(await saveEnhancedTranslationReview()))
      throw new Error("GUI_WORKSPACE_REVIEW_SAVE_FAILED: The open translation draft could not be saved.");
    const storage = activeWorkspaceStorageDirectory || workspaceStorageDirectory();
    const name = activeWorkspaceId ? workspaceName.value || automaticRecoveryName : automaticRecoveryName;
    const media = JSON.stringify(collectPendingGuiMedia());
    const payload = await workspacePost("/api/v1/workspaces/save", {
      workspace_id:activeWorkspaceId, name, current_step:lastWorkspaceStep,
      fields:collectWorkspaceFields(), pending_media:collectPendingGuiMedia(), autosave:true,
    }, {feedback:false, storageDirectory:storage});
    const saved = payload.workspace;
    if (media === JSON.stringify(collectPendingGuiMedia()) && saved.pending_media?.length)
      await restorePendingGuiMedia(saved.pending_media, {keepStaged:true});
    workspaceName.value = saved.name;
    activateWorkspace(saved, storage);
    lastWorkspaceFingerprint = fingerprint;
    showWorkspaceFile(payload.workspace_file);
    await refreshWorkspaces(activeWorkspaceKey, {feedback:false});
    workspaceAutosaveStatus.textContent = "Auto-save completed. No credential, confirmation, or editor text was stored.";
  } catch (error) {
    workspaceAutosaveStatus.textContent = `Auto-save could not save the tracked changes and will retry: ${error.message}`;
  } finally { workspaceAutosaveBusy = false; }
}

function scheduleAutomaticWorkspaceSave() {
  if (automaticRecoveryTimer !== null) clearTimeout(automaticRecoveryTimer);
  automaticRecoveryTimer = setTimeout(() => { void saveAutomaticWorkspace(); }, 750);
}
for (const event of ["input", "change", "ewp-stage"]) document.addEventListener(event, scheduleAutomaticWorkspaceSave);
document.addEventListener("visibilitychange", () => { if (document.hidden) void saveAutomaticWorkspace(); });
setInterval(() => { void saveAutomaticWorkspace(); }, 2000);
workspaceAutosave.addEventListener("change", () => {
  void workspacePost("/api/v1/workspaces/recovery", {enabled:workspaceAutosave.checked}, {feedback:false, storageDirectory:""});
});
window.addEventListener("beforeunload", event => {
  if (workspaceAutosaveBusy || workspaceAutosave.checked && workspaceFingerprint() !== lastWorkspaceFingerprint ||
      guiQueueJobs.some(job => ["queued", "running", "cancel_requested"].includes(job.status))) {
    event.preventDefault(); event.returnValue = "";
  }
});
