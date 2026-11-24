"use strict";

const workspaceRestoreDialog = document.createElement("dialog");
workspaceRestoreDialog.id = "gui-workspace-restore";
workspaceRestoreDialog.setAttribute("aria-labelledby", "gui-restore-title");
workspaceRestoreDialog.setAttribute("aria-busy", "true");
workspaceRestoreDialog.innerHTML = '<h2 id="gui-restore-title"><span>Loading</span> <span id="gui-restore-count" data-gui-content>0/0</span></h2><p class="gui-restore-message" role="status">Restoring saved queue and editors…</p><p class="field-hint">Wait until saved work is fully restored. Transcription does not start automatically.</p>';
workspaceRestoreDialog.addEventListener("cancel", event => event.preventDefault());
document.body.append(workspaceRestoreDialog);
let workspaceRestoreBusy = false;

async function loadSelectedWorkspace() {
  if (workspaceRestoreBusy) return;
  const selected = selectedWorkspaceReference();
  if (!selected) { workspaceStatus.textContent = "GUI_WORKSPACE_SELECTION_REQUIRED: Select a saved workspace first."; return; }
  if(typeof resetGuiCloudConsent==="function")resetGuiCloudConsent();
  workspaceRestoreBusy = true;
  workspaceStatus.textContent = "Restoring saved work…";
  const restoreId = crypto.randomUUID();
  let polling = false, timer = null;
  const count = document.getElementById("gui-restore-count");
  const button = document.getElementById("load-workspace");
  const update = (loaded, total) => { count.textContent = `${loaded}/${total}`; };
  const poll = async () => {
    if (!workspaceRestoreBusy || polling) return;
    polling = true;
    try {
      const status = await workspacePost("/api/v1/workspaces/restore-progress", {restore_id:restoreId}, {storageDirectory:selected.storageDirectory, feedback:false});
      if (workspaceRestoreBusy && status.total !== null) update(status.loaded, status.total);
    } catch (_) { /* The load request owns final error reporting. */ }
    finally { polling = false; }
  };
  try {
    if (reviewDocument && reviewDirty) await saveReviewDraft();
    if (translationReview && translationReviewDirty && !(await saveEnhancedTranslationReview())) return;
    update(0, selected.queueCount);
    workspaceRestoreDialog.showModal(); button.disabled = true;
    timer = setInterval(poll, 400);
    const payload = await workspacePost("/api/v1/workspaces/load", {workspace_id:selected.workspaceId, restore_id:restoreId}, {storageDirectory:selected.storageDirectory, feedback:false});
    const total = (payload.workspace.staged_jobs?.length || 0) + (payload.workspace.terminal_jobs?.length || 0);
    update(total, total);
    resetActiveReviewState(); clearActiveTranslationReview();
    selectedGuiAudio.length=0;activeGuiAudio=null;guiBatchPlan=null;renderGuiAudioChoices();
    await applyWorkspaceFields(payload.workspace.fields);
    await refreshJobs();
    await restorePendingGuiMedia(payload.workspace.pending_media);
    displayWorkspaceName(payload.workspace.name);clearWorkspaceNameError();showWorkspaceFile(payload.workspace_file);
    lastWorkspaceStep = payload.workspace.current_step || lastWorkspaceStep;
    activateWorkspace(payload.workspace, selected.storageDirectory);
    workspaceStatus.textContent = `Workspace loaded: ${payload.workspace.name}. Provider credentials and confirmations were not restored.`;
    const heading = document.getElementById(payload.workspace.current_step);
    guiScrollTo(heading, {behavior:"smooth"});
  } catch (error) { workspaceStatus.textContent = error.message; }
  finally {
    if (timer !== null) clearInterval(timer);
    workspaceRestoreBusy = false;
    if (workspaceRestoreDialog.open) workspaceRestoreDialog.close();
    updateWorkspaceSelectionControls();updateGuiQueueStart();
  }
}
