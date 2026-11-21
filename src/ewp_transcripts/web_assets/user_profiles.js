"use strict";

function downloadGuiFile(filename, payload, type = "application/json") {
  const url = URL.createObjectURL(new Blob([payload], {type}));
  const link = document.createElement("a"); link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const userProfilePanel = document.createElement("div"); userProfilePanel.id = "gui-user-profile";
userProfilePanel.innerHTML = `<h3>User preferences</h3>
  <label class="confirmation"><input type="checkbox" id="gui-show-eta"> Show estimated remaining time (ETA)</label>
  <p class="field-hint">ETA is off by default. Estimates become available after 3 successful transcriptions with comparable language, models and track configuration on this computer. Timing history stays on this computer and is not transferred with a profile.</p>
  <h3>User profile</h3>
  <p class="field-hint">One JSON file contains preferences, current workflow settings, saved workspace manifests, custom palettes, project references and optionally dictionaries from the selected library and referenced workspaces. Media, transcripts, API keys, permissions and running jobs are excluded. Other workspace catalogs must be selected before saving. Referenced recordings and outputs must be transferred separately.</p>
  <label class="confirmation"><input type="checkbox" id="user-profile-dictionaries" checked> Include dictionaries in profile</label><label>Profile name<input id="user-profile-name" maxlength="100" value="My profile" autocomplete="off"></label>
  <div class="actions"><button type="button" id="user-profile-save">Save profile</button><button type="button" id="user-profile-load">Load saved profile</button><button type="button" id="user-profile-export">Export profile…</button><button type="button" id="user-profile-import">Import profile…</button><input type="file" id="user-profile-file" accept=".json,application/json" hidden></div>
  <p id="user-profile-status" role="status"></p>`;
document.querySelector("#dependency-panel").before(userProfilePanel);
const etaPreference = document.querySelector("#gui-show-eta");
etaPreference.checked = guiPreferences.showEta === true;
etaPreference.addEventListener("change", () => { guiPreferences.showEta = etaPreference.checked; saveGuiPreferences(); jobsSignature = ""; void refreshJobs(); });
const userProfileStatus = document.querySelector("#user-profile-status");
function collectGuiPreferences() {
  return {locale:guiLocale, theme:document.querySelector("#gui-theme").value, showEta:etaPreference.checked,
    playbackSpeed:Number(guiPreferences.playbackSpeed || 1), reviewLayout:localStorage.getItem("ewp-review-layout") || "one",
    translationLayout:localStorage.getItem("ewp-translation-review-layout") || "few", dictionaryDirectory:document.querySelector("#library-directory").value};
}
async function saveUserProfile(trigger) {
  return queuePost("/api/v1/profile/save", {name:document.querySelector("#user-profile-name").value,
    preferences:collectGuiPreferences(), fields:collectWorkspaceFields(), storage_directory:workspaceStorageDirectory(),
    dictionary_directory:document.querySelector("#library-directory").value, include_dictionaries:document.querySelector("#user-profile-dictionaries").checked}, {trigger});
}
async function applyUserProfile(payload) {
  const profile = payload.profile, preferences = profile.preferences;
  guiPreferences = {...preferences}; guiLocale = preferences.locale;
  document.querySelector("#gui-locale").value = guiLocale;
  document.querySelector("#gui-theme").value = preferences.theme; applyGuiTheme();
  etaPreference.checked = preferences.showEta; playbackAudio.playbackRate = preferences.playbackSpeed;
  localStorage.setItem("ewp-review-layout", preferences.reviewLayout);
  document.querySelector("#review-layout").value = preferences.reviewLayout; updateReviewSections();
  localStorage.setItem("ewp-translation-review-layout", preferences.translationLayout);
  document.querySelectorAll(".translation-review-layout").forEach(element=>{ element.value = preferences.translationLayout; element.dispatchEvent(new Event("change")); });
  document.querySelector("#library-directory").value = preferences.dictionaryDirectory;
  document.querySelector("#user-profile-name").value = profile.name;
  saveGuiPreferences(); translateGui();
  await refreshWorkspaces();
  if (typeof refreshProjectCatalog === "function") await refreshProjectCatalog();
  await loadGuiColorProfiles();
  document.querySelector("#library-refresh").click();
  jobsSignature = ""; await refreshJobs();
  userProfileStatus.textContent = "Profile loaded. Open Saved work & cleanup to select a restored workspace. Missing recordings or outputs must be restored before loading that workspace. The active queue and editor are unchanged.";
}
for (const action of ["save", "load", "export"]) {
  document.querySelector(`#user-profile-${action}`).addEventListener("click", async event => {
    const button = event.currentTarget; button.disabled = true;
    try {
      const payload = action === "load" ? await queuePost("/api/v1/profile/load", {}, {trigger:button}) : await saveUserProfile(button);
      if (action === "load") await applyUserProfile(payload);
      else if (action === "export") { downloadGuiFile("ewp-user-profile.json", JSON.stringify(payload.profile, null, 2) + "\n"); userProfileStatus.textContent = "Profile saved and exported as one JSON file."; }
      else userProfileStatus.textContent = "Profile saved on this computer.";
    } catch (error) { userProfileStatus.textContent = error.message; }
    finally { button.disabled = false; }
  });
}
document.querySelector("#user-profile-import").addEventListener("click", () => document.querySelector("#user-profile-file").click());
document.querySelector("#user-profile-file").addEventListener("change", async event => {
  const file = event.target.files?.[0]; event.target.value = ""; if (!file) return;
  try {
    if (file.size > 16 * 1024 * 1024) throw new Error("GUI_PROFILE_INVALID: User profile exceeds the 16 MiB limit");
    await applyUserProfile(await queuePost("/api/v1/profile/import", {profile:JSON.parse(await file.text())}, {trigger:document.querySelector("#user-profile-import")}));
  } catch (error) { userProfileStatus.textContent = error.message; }
});
// Display choices persist immediately in the browser; portable profile snapshots are explicit.
document.querySelector("#library-directory").value = guiPreferences.dictionaryDirectory || "dictionaries";
document.querySelector("#library-directory").addEventListener("change", event => { guiPreferences.dictionaryDirectory = event.target.value; saveGuiPreferences(); });
