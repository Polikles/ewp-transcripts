"use strict";

const guiStages = [
  ["workspace", "Transcribe", "workspace-heading", "file-music"],
  ["correction", "Optional correction", "correction-heading", "list-ordered"],
  ["review", "Source review & export", "review-heading", "book-open"],
  ["translation", "Optional translation", "translation-heading", "languages"],
  ["semantic-review", "Translation review & export", "translation-review-heading", "download"],
  ["dictionary", "Dictionaries", "dictionary-heading", "book-open"],
  ["saved", "Saved work & cleanup", "workspace-state-heading", "settings-2"],
  ["settings", "Settings & About", "gui-settings-heading", "settings-2"],
];
let guiActiveStage = "workspace";
let guiActiveResult = "";
let guiActiveJobId = "";
let guiKnownJobs = [];
const guiPreferencesKey = "ewp-gui-preferences-v1";
let guiPreferences = {};
try { guiPreferences = JSON.parse(localStorage.getItem(guiPreferencesKey) || "{}"); } catch (_) { /* defaults */ }

function guiIcon(name) {
  const icon = document.createElement("img");
  icon.src = `/assets/brand/${name}.svg`;
  icon.alt = "";
  icon.width = 20;
  icon.height = 20;
  return icon;
}

function showGuiStage(stage, focus = false) {
  if (!guiStages.some(item => item[0] === stage)) return;
  guiActiveStage = stage;
  document.body.dataset.guiActiveStage = stage;
  lastWorkspaceStep = guiStages.find(item => item[0] === stage)[2];
  for (const [id, , heading] of guiStages) {
    const section = document.getElementById(heading)?.closest("section");
    if (section) section.hidden = id !== stage;
    const button = document.querySelector(`[data-gui-stage="${id}"]`);
    button?.setAttribute("aria-current", id === stage ? "step" : "false");
  }
  const heading = document.getElementById(guiStages.find(item => item[0] === stage)[2]);
  if (focus && heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); }
  document.dispatchEvent(new CustomEvent("ewp-stage", {detail: {stage}}));
  updateGuiContext();
}

function guiScrollTo(element, options) { revealGuiStage(element); element?.scrollIntoView(options); }

function revealGuiStage(element) {
  if (!document.getElementById("gui-stage-nav")) return;
  const section = element?.closest("section");
  const stage = guiStages.find(item => document.getElementById(item[2])?.closest("section") === section);
  if (stage) showGuiStage(stage[0]);
}

function updateGuiContext() {
  const context = document.getElementById("gui-active-context");
  if (!context) return;
  const source = guiActiveStage === "review" ? reviewDocument?.result_path
    : guiActiveStage === "semantic-review" ? translationReview?.result_path
    : guiActiveStage === "correction" ? correctionForm.elements.namedItem("result_path").value || guiActiveResult
    : guiActiveStage === "translation" ? translationForm.elements.namedItem("result_path").value || guiActiveResult : guiActiveResult;
  if (source) guiActiveResult = source;
  const job = guiKnownJobs.find(item => guiActiveResult ? item.result_path === guiActiveResult : item.job_id === guiActiveJobId);
  if (job) guiActiveJobId = job.job_id;
  const signature = JSON.stringify([guiActiveStage, guiActiveResult, guiActiveJobId, reviewDirty, translationReviewDirty,
    job?.workflow, reviewDocument?.job_id, translationReview?.revision_path,
    reviewDocument?.speaker_labels, guiSpeakerColors(), document.querySelector("#gui-export-palette")?.value,
    translationForm.elements.namedItem("target_language").value,
    stageQueueSelections.correction.size, stageQueueSelections.translation.size]);
  updateGuiRecordings();
  syncGuiRecordingSelection();
  if (context.dataset.signature === signature) { applyGuiSpeakerColors(); renderGuiTaskContext(job); return; }
  context.dataset.signature = signature;
  context.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = job?.planned_job_id || reviewDocument?.job_id || "No active recording";
  if (job?.planned_job_id || reviewDocument?.job_id) title.dataset.guiContent = "true";
  const stage = document.createElement("span");
  stage.textContent = guiStages.find(item => item[0] === guiActiveStage)[1];
  const path = document.createElement("span");
  path.className = "gui-path";
  const activePath = guiActiveResult || job?.input_path || "";
  path.textContent = activePath ? shortName(activePath) : "Choose a recording in a stage queue.";
  path.title = activePath;
  if (activePath) path.dataset.guiContent = "true";
  const saved = document.createElement("span");
  saved.textContent = reviewDirty || translationReviewDirty ? "Unsaved draft — navigation keeps it open" : "Draft changes saved or no draft open";
  context.append(title, stage, path, saved);
  const count = document.createElement("span");
  count.textContent = `Batch selection: ${stageQueueSelections.correction.size} correction · ${stageQueueSelections.translation.size} translation`;
  context.append(count);
  const compact = document.createElement("details"); compact.className = "gui-compact-context";
  const compactTitle = document.createElement("summary"); compactTitle.textContent = "Recording details";
  compact.append(compactTitle, guiTaskContextContent(job)); context.append(compact);
  const translationJob = guiKnownJobs.find(item => item.result_path === translationReview?.result_path);
  if (translationReview && translationJob?.workflow?.review?.path && translationReview.revision_path !== translationJob.workflow.review.path) {
    const stale = document.createElement('p'); stale.className='notice';
    stale.textContent='Translation uses an older or raw source. A newer verified source exists. Existing outputs are retained; reopen translation to use the new revision.';
    context.append(stale);
  }
  updateGuiRecordings();
  applyGuiSpeakerColors();
  renderGuiTaskContext(job);
}

function syncGuiRecordingSelection() {
  const result = guiActiveStage === "review" && reviewDocument?.result_path ? reviewDocument.result_path : guiActiveResult;
  for (const button of document.querySelectorAll("#gui-recordings .gui-recording")) {
    const active = result ? button.dataset.resultPath === result : button.dataset.jobId === guiActiveJobId;
    button.setAttribute("aria-pressed", String(active));
  }
  for (const item of document.querySelectorAll(".stage-queue-item[data-result-path]")) {
    const active = Boolean(result && item.dataset.resultPath === result);
    if (active) item.setAttribute("aria-current", "true"); else item.removeAttribute("aria-current");
  }
}

function updateGuiRecordings() {
  const list = document.getElementById("gui-recordings");
  if (!list) return;
  const signature = JSON.stringify([guiActiveResult, guiActiveJobId, guiKnownJobs.map(job => [job.job_id, job.workflow, job.status])]);
  if (list.dataset.signature === signature) return;
  list.dataset.signature = signature;
  list.replaceChildren();
  for (const job of guiKnownJobs) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "gui-recording"; button.dataset.status = job.status;
    button.dataset.jobId = job.job_id; button.dataset.resultPath = job.result_path || "";
    button.setAttribute("aria-pressed", String(guiActiveResult ? job.result_path === guiActiveResult : job.job_id === guiActiveJobId));
    const identity = document.createElement("strong");
    identity.textContent = job.planned_job_id;
    const status = document.createElement("span");
    const state = document.createElement("span"); state.textContent = queueJobStatusLabel(job);
    const next = document.createElement("span"); next.textContent = nextWorkflowLabel(nextWorkflowStage(job));
    status.append(state, " · ", next);
    button.title = job.result_path || job.input_path;
    button.append(identity, status);
    button.addEventListener("click", () => {
      guiActiveJobId = job.job_id;
      guiActiveResult = job.result_path || "";
      if (job.result_path) {
        const next = nextWorkflowStage(job);
        const stage = next === "original-export" ? "review" : ["translated-export", "finished"].includes(next) ? "semantic-review" : next;
        void openStageQueueItem(job, stage);
      } else { showGuiStage("workspace"); }
      updateGuiContext();
    });
    list.append(button);
  }
  if (!guiKnownJobs.length) list.textContent = "No recordings yet. Import audio or saved results.";
}

function saveGuiPreferences() {
  guiPreferences.locale = guiLocale;
  localStorage.setItem(guiPreferencesKey, JSON.stringify(guiPreferences));
  document.dispatchEvent(new Event("ewp-preferences-changed"));
}
function applyGuiTheme() {
  const preference = document.querySelector("#gui-theme").value;
  guiPreferences.theme = preference;
  document.documentElement.dataset.theme = preference === "system"
    ? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : preference;
  saveGuiPreferences();
}

function installGuiShell() {
  document.title = "EwP Transcripts";
  const header = document.querySelector("header");
  header.querySelector("h1").textContent = "EwP Transcripts";
  const logo = document.createElement("img");
  logo.src = "/assets/brand/logo.svg";
  logo.alt = "EwP";
  logo.className = "gui-logo";
  header.prepend(logo);
  const brandTitle = document.createElement("div");
  brandTitle.className = "gui-brand-title";
  brandTitle.append(header.querySelector("h1"), header.querySelector(".eyebrow"));
  logo.after(brandTitle);
  const main = document.querySelector("main");
  for (const id of workspaceFieldIds.filter(id => id.startsWith("gui-"))) {
    const input = document.createElement("input"); input.type = "hidden"; input.id = id; main.append(input);
  }
  const paths = document.createElement("details"); paths.className = "gui-source-paths";
  paths.innerHTML = "<summary>Source and output paths</summary>";
  const form = document.querySelector("#review-workflow");
  const reviewIdentity = document.querySelector("#review-identity").closest("p");
  while (form.firstElementChild && form.firstElementChild !== reviewIdentity) paths.append(form.firstElementChild);
  form.prepend(paths);
  const settings = document.createElement("section");
  settings.innerHTML = `<h2 id="gui-settings-heading">Settings & About</h2>
    <p>Local-first audio transcription. LLM correction and translation are optional. Source export never requires translation or dictionaries.</p>
    <p>Recommended for local ASR: a recent NVIDIA RTX with 12 GB VRAM or more, 32 GB RAM and an SSD. Tested reference: RTX 3090 with 24 GB VRAM. Smaller configurations may work, but have not been tested and are not guaranteed; cloud ASR is recommended.</p>
    <p>GPU architecture and runtime compatibility also matter. Cloud ASR and existing-result review do not require a local NVIDIA GPU. Windows AMD support is experimental.</p>
    <p>Provider readiness and disclosure consent remain in each optional stage. Local API endpoints are separately operated; the application cannot guarantee third-party logging, retention, forwarding or storage location.</p>
    <p>Audio is processed locally. Correction and translation send transcript text only after explicit scoped consent. Keys stay in server memory and are never saved in workspaces.</p>
    <p><a href="/help" target="_blank" rel="noreferrer">Open the complete local GUI instructions</a></p>
    <p><a href="/assets/brand/NOTICE.txt">Asset credits and notices</a> · <a href="/assets/brand/LICENSE-ASSETS.txt">Identity asset terms</a></p>
    <p class="gui-artwork-credit">Artwork: Cyryl. Creator URL is a placeholder (blogcyryla.pl); TODO replace when supplied.</p>`;
  main.append(settings);
  settings.append(document.querySelector("#dependency-panel"), document.querySelector("#temporary-workdirs"));
  settings.append(document.querySelector("footer"));
  const bar = document.createElement("div");
  bar.className = "gui-preferences";
  bar.innerHTML = `<label>Interface language<select id="gui-locale"><option value="en">English</option><option value="pl">Polski</option></select></label>
    <label>Appearance<select id="gui-theme"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>`;
  header.append(bar);
  document.querySelector("#gui-locale").value = ["pl","en"].includes(guiPreferences.locale)
    ? guiPreferences.locale : ((document.documentElement.dataset.systemLanguage || navigator.languages?.[0] || navigator.language || "en").toLowerCase().startsWith("pl") ? "pl" : "en");
  document.querySelector("#gui-theme").value = ["light", "dark"].includes(guiPreferences.theme) ? guiPreferences.theme : "system";
  guiLocale = document.querySelector("#gui-locale").value;
  document.querySelector("#gui-locale").addEventListener("change", event => { guiLocale = event.target.value; saveGuiPreferences(); translateGui(); });
  document.querySelector("#gui-theme").addEventListener("change", applyGuiTheme);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyGuiTheme);
  const navigation = document.createElement("aside");
  navigation.id = "gui-sidebar";
  const nav = document.createElement("nav");
  nav.id = "gui-stage-nav";
  nav.setAttribute("aria-label", "Workflow stages");
  const tools = document.createElement("nav"); tools.id = "gui-tool-nav";
  tools.setAttribute("aria-label", "Tools and settings");
  for (const [index, [id, title, , icon]] of guiStages.entries()) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.guiStage = id;
    if (index < 5) {
      const number = document.createElement("span"); number.className = "gui-stage-order";
      number.textContent = String(index + 1); button.append(number);
    }
    button.append(guiIcon(icon), document.createTextNode(title));
    button.addEventListener("click", () => showGuiStage(id, true));
    (index < 5 ? nav : tools).append(button);
  }
  const recordings = document.createElement("div");
  recordings.id = "gui-recordings";
  recordings.setAttribute("aria-label", "Recordings");
  const queueTitle = document.createElement("h2"); queueTitle.textContent = "Recording queue";
  const addAudio = document.createElement("button"); addAudio.type = "button";
  addAudio.id = "gui-add-audio"; addAudio.textContent = "Add files";
  addAudio.disabled = nativeMediaButton.disabled;
  new MutationObserver(() => { addAudio.disabled = nativeMediaButton.disabled; }).observe(nativeMediaButton, {attributes:true, attributeFilter:["disabled"]});
  addAudio.addEventListener("click", () => { if (nativeMediaButton.disabled) return; showGuiStage("workspace"); nativeMediaInput.click(); });
  navigation.append(document.querySelector("#compatibility"), queueTitle, addAudio, recordings, tools);
  main.prepend(nav);
  main.before(navigation);
  const context = document.createElement("div");
  context.id = "gui-active-context";
  context.setAttribute("role", "status");
  main.before(context);
  const taskContext = document.createElement("aside"); taskContext.id = "gui-task-context";
  taskContext.setAttribute("aria-label", "Task context"); main.after(taskContext);
  document.body.classList.add("gui-workbench");
  document.addEventListener("ewp-jobs", event => { guiKnownJobs = event.detail; updateGuiContext(); });
  for (const selector of ["#review-editor", "#translation-review-editor", "#review-status", "#translation-review-status"]) {
    new MutationObserver(updateGuiContext).observe(document.querySelector(selector), {childList: true, subtree: true});
  }
  document.addEventListener("input", event => {
    if (event.target.closest("#review-editor, #translation-review-editor, #review-speaker-labels")) updateGuiContext();
  });
  document.addEventListener("change", event => {
    if (event.target.matches('#gui-export-palette, #translation-workflow [name="target_language"]')) updateGuiContext();
  });
  applyGuiTheme();
  showGuiStage("workspace");
  startGuiTranslation();
}

function guiTaskContextContent(job) {
  const content = document.createElement("div"), values = document.createElement("dl");
  const source = job?.language || (reviewDocument?.result_path === guiActiveResult ? reviewDocument.language : "—");
  const target = translationReview?.result_path === guiActiveResult ? translationReview.direction.target_language
    : translationForm.elements.namedItem("result_path").value === guiActiveResult && guiActiveResult
      ? translationForm.elements.namedItem("target_language").value : "—";
  for (const [name, value] of [["Recording language", source], ["Translation target", target], ["Audio processing", job?.speech?.provider === "openrouter" ? "OpenRouter cloud ASR" : document.documentElement.dataset.localAccelerator === "amd" ? "AMD ROCm (experimental) · CPU alignment/diarization" : "Local · WhisperX"]]) {
    const term = document.createElement("dt"), description = document.createElement("dd");
    term.textContent = name; description.textContent = value; values.append(term, description);
  }
  content.append(values);
  if (reviewDocument?.result_path === guiActiveResult) {
    const title = document.createElement("h3"); title.textContent = "Speaker names and colors"; content.append(title);
    const colors = guiSpeakerColors();
    for (const id of reviewDocument.speakers) {
      const row = document.createElement("p"); row.className = "gui-context-speaker";
      const marker = document.createElement("span"); marker.className = "gui-speaker-marker";
      marker.style.backgroundColor = colors[id]; marker.setAttribute("aria-hidden", "true");
      row.append(marker, document.createTextNode(reviewDocument.speaker_labels?.[id] || id));
      row.title = id; row.dataset.speakerId = id; content.append(row);
    }
  }
  const draft = document.createElement("p"); draft.className = "gui-context-draft";
  draft.textContent = reviewDirty || translationReviewDirty ? "Unsaved draft — navigation keeps it open" : "Draft changes saved or no draft open";
  content.append(draft); return content;
}

function renderGuiTaskContext(job) {
  const panel = document.querySelector("#gui-task-context");
  if (!panel) return;
  const heading = document.createElement("h2"); heading.textContent = "Task context";
  panel.replaceChildren(heading, guiTaskContextContent(job));
}

// Colors are display/export preferences, never transcript text or speaker identity.
const guiExamplePalette = ["#FFE8A3", "#FF8FA3", "#A8DADC", "#CDB4DB", "#F4A261", "#B8DE6F"];
const guiBrandPalette = ["#F5F7FA", "#00AEEF", "#F2C55B", "#BF734D", "#8CFFB3", "#64D8D0"];
function guiPaletteKey() { return `ewp-colors-v1:${reviewDocument?.result_path || ""}`; }
function guiSavedSpeakerColors() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(guiPaletteKey()) || "{}"); } catch (_) { /* defaults */ }
  return saved && !Array.isArray(saved) && typeof saved === "object" ? saved : {};
}
let guiPreviewColors = null;
let guiPreviewResult = "";
let guiColorProfiles = [];
function guiAppliedSpeakerColors() {
  const colors = guiSavedSpeakerColors();
  const profile = guiColorProfiles.find(item => guiProfileValue(item) === (guiPreferences.defaultPalette || "configured"));
  const defaults = profile?.colors?.length ? profile.colors : guiExamplePalette;
  return Object.fromEntries((reviewDocument?.speakers || []).map(id => {
    const n = Number(id.match(/\d+$/)?.[0] || 1) - 1;
    return [id, /^#[0-9a-f]{6}$/i.test(colors[id] || "") ? colors[id] : defaults[n % defaults.length]];
  }));
}
function guiSpeakerColors() {
  return guiPreviewResult === reviewDocument?.result_path && guiPreviewColors
    ? Object.fromEntries((reviewDocument?.speakers || []).map(id => [id, guiPreviewColors[id] || guiAppliedSpeakerColors()[id]])) : guiAppliedSpeakerColors();
}
function applyGuiSpeakerColors() {
  if (!reviewDocument) return;
  const colors = guiSpeakerColors();
  document.querySelectorAll("#review-editor .review-block").forEach(row => {
    row.style.borderInlineStart = `6px solid ${colors[row.querySelector("select")?.value] || guiBrandPalette[0]}`;
  });
  document.querySelectorAll("#review-speaker-labels .review-speaker-label-row").forEach(row => {
    const id = row.querySelector("input[data-speaker-id]")?.dataset.speakerId;
    if (!id) return;
    const existing = row.querySelector("input[type=color]");
    if (existing) { existing.value = colors[id]; return; }
    const label = document.createElement("label"); label.textContent = "Speaker color"; label.className = "gui-speaker-color";
    const input = document.createElement("input"); input.type = "color"; input.value = colors[id];
    input.setAttribute("aria-label", `Speaker color ${id}`);
    input.addEventListener("input", () => {
      guiPreviewColors = {...guiSpeakerColors(), [id]:input.value}; guiPreviewResult = reviewDocument.result_path;
      document.querySelector("#gui-palette-status").textContent = "Preview only. Apply to use these colors for this recording's next export.";
      applyGuiSpeakerColors(); updateGuiContext();
    }); label.append(input); row.append(label);
  });
}
function guiProfileValue(profile) {
  return profile.id || (["Example default", "Configured production"].includes(profile.name) ? "configured" : ["EwP brand", "EwP Brand®"].includes(profile.name) ? "brand" : profile.name);
}
function renderGuiProfileSwatches() {
  const host = document.querySelector("#gui-profile-swatches"); if (!host) return;
  const profile = guiColorProfiles.find(item => guiProfileValue(item) === document.querySelector("#gui-export-palette").value);
  host.replaceChildren();
  for (const color of profile?.colors || []) {
    const marker = document.createElement("span"); marker.className = "gui-profile-swatch";
    marker.style.backgroundColor = color; marker.title = color; marker.setAttribute("aria-label", color); host.append(marker);
  }
}
function renderGuiColorProfiles(payload, selected = "") {
  guiColorProfiles = payload.profiles;
  const select = document.querySelector("#gui-export-palette");
  const value = selected || select.value || guiPreferences.defaultPalette || "configured";
  select.replaceChildren();
  for (const profile of guiColorProfiles) {
    const option = document.createElement("option"); option.value = guiProfileValue(profile);
    option.textContent = profile.name; select.append(option);
  }
  select.value = value;
  if (!select.value) select.value = "configured";
  renderGuiProfileSwatches();
  document.dispatchEvent(new Event("ewp-palettes-loaded"));
}
async function loadGuiColorProfiles() {
  try { renderGuiColorProfiles(await queuePost("/api/v1/dictionaries/profiles", {}, {feedback:false})); }
  catch (error) { document.querySelector("#gui-palette-status").textContent = error.message; }
}
function previewGuiColorProfile() {
  renderGuiProfileSwatches();
  if (!reviewDocument) return;
  const profile = guiColorProfiles.find(item => guiProfileValue(item) === document.querySelector("#gui-export-palette").value);
  if (!profile) return;
  guiPreviewColors = Object.fromEntries(reviewDocument.speakers.map(id => {
    const n = Number(id.match(/\d+$/)?.[0] || 1) - 1;
    return [id, profile.colors[n % profile.colors.length]];
  }));
  guiPreviewResult = reviewDocument.result_path;
  document.querySelector("#gui-palette-status").textContent = "Preview only. Apply to use these colors for this recording's next export.";
  applyGuiSpeakerColors(); updateGuiContext();
}
function installGuiPaletteControls() {
  const panel = document.createElement("div"); panel.id = "gui-palette";
  panel.innerHTML = `<label>YTT color profile<select id="gui-export-palette"></select></label>
    <div id="gui-profile-swatches" aria-label="Preset colors"></div>
    <div class="actions"><button type="button" id="gui-preview-palette">Preview</button><button type="button" id="gui-apply-palette">Apply</button><button type="button" id="gui-save-palette">Save</button></div>
    <label>Custom profile name<input id="gui-palette-name" maxlength="80" autocomplete="off"></label>
    <p id="gui-palette-status" class="field-hint" role="status">Preview a profile or edit speaker colors, then Apply for this recording. Save keeps a named profile for other recordings.</p>`;
  document.querySelector("#review-speaker-labels").before(panel);
  document.querySelector("#gui-export-palette").addEventListener("change", previewGuiColorProfile);
  document.querySelector("#gui-preview-palette").addEventListener("click", previewGuiColorProfile);
  document.querySelector("#gui-apply-palette").addEventListener("click", () => {
    if (!reviewDocument) return;
    localStorage.setItem(guiPaletteKey(), JSON.stringify(guiSpeakerColors()));
    guiPreviewColors = null; guiPreviewResult = "";
    document.querySelector("#gui-palette-status").textContent = "Colors applied to this recording's next export. Existing exports stay unchanged.";
    applyGuiSpeakerColors(); updateGuiContext();
  });
  document.querySelector("#gui-save-palette").addEventListener("click", async () => {
    if (!reviewDocument) return;
    const button = document.querySelector("#gui-save-palette"); button.disabled = true;
    document.querySelector("#gui-palette-status").textContent = "Saving custom profile…";
    try {
      const name = document.querySelector("#gui-palette-name").value.trim();
      const colors = guiSpeakerColors();
      // Preserve numeric speaker slots, including gaps introduced by revision-only speakers.
      const count = Math.max(...reviewDocument.speakers.map(id => Number(id.match(/\d+$/)?.[0] || 1)));
      const palette = Array.from({length:count}, (_, index) => colors[`speaker_${String(index + 1).padStart(3,"0")}`] || guiBrandPalette[index % guiBrandPalette.length]);
      const payload = await queuePost("/api/v1/dictionaries/profile-save", {name, colors:palette});
      renderGuiColorProfiles(payload, name);
      document.querySelector("#gui-palette-status").textContent = "Custom profile saved. Apply to use it for this recording's next export.";
    } catch (error) { document.querySelector("#gui-palette-status").textContent = error.message; } finally { button.disabled = false; }
  });
  // Session initialization is asynchronous; wait for the session token, without a second session.
  document.addEventListener("ewp-session-ready", () => { void loadGuiColorProfiles(); });
}
function guiExportPreferences() {
  const colors = guiAppliedSpeakerColors();
  const configured = reviewDocument?.configured_speaker_colors || {};
  const same = Object.entries(colors).every(([id, color]) => configured[id]?.toUpperCase() === color.toUpperCase());
  return {speaker_colors:Object.keys(guiSavedSpeakerColors()).length || !same ? colors : null};
}

installGuiPaletteControls();
installGuiShell();

const guiReviewCarets = new WeakMap();
let guiCursorSplitPending = false;
function rememberReviewCaret(event) {
  const input = event?.target instanceof HTMLTextAreaElement ? event.target : document.activeElement;
  if (!(input instanceof HTMLTextAreaElement) || !input.closest("#review-editor")) return;
  guiReviewCarets.set(input, {start: input.selectionStart, end: input.selectionEnd, value: input.value});
}
for (const kind of ["input", "select", "keyup", "pointerup", "focusout"]) {
  document.querySelector("#review-editor").addEventListener(kind, rememberReviewCaret, true);
}
document.addEventListener("selectionchange", rememberReviewCaret);

function showReviewCursorMessage(row, message) {
  let feedback = row.querySelector(".review-cursor-status");
  if (!feedback) {
    feedback = document.createElement("p"); feedback.className = "review-cursor-status";
    feedback.setAttribute("role", "status"); row.append(feedback);
  }
  feedback.textContent = message;
  setReviewStatus(message);
}

async function splitReviewAtCursor(button, captured = null) {
  const {row, anchorIndex, blockIndex} = reviewBlockPosition(button);
  const input = row?.querySelector("textarea");
  if (!reviewDocument || !input || guiCursorSplitPending) return;
  const caret = captured || guiReviewCarets.get(input) || {start:input.selectionStart, end:input.selectionEnd, value:input.value};
  const at = caret.start;
  const value = input.value;
  if (caret.value !== value || at !== caret.end || at <= 0 || at >= value.length ||
      (!/\s/.test(value[at - 1]) && !/\s/.test(value[at]))) {
    showReviewCursorMessage(row, "GUI_REVIEW_CURSOR_BOUNDARY: Place the cursor between complete words inside a block. Use Separate selected text for a selection.");
    input.focus({preventScroll:true}); return;
  }
  const left = value.slice(0, at).trim(), right = value.slice(at).trim();
  if (!left || !right) { showReviewCursorMessage(row, "GUI_REVIEW_CURSOR_BOUNDARY: Both sides must contain text."); return; }
  const reviewPath = reviewDocument.review_path;
  guiCursorSplitPending = true; button.disabled = true;
  try {
    if (reviewDirty) await saveReviewDraft();
    const anchor = reviewDocument.anchors[anchorIndex];
    if (reviewDocument.review_path !== reviewPath || !anchor?.blocks[blockIndex]) throw new Error("GUI_REVIEW_STRUCTURE_INVALID: The selected block changed before splitting.");
    const speaker = anchor.blocks[blockIndex].speaker_id;
    anchor.blocks.splice(blockIndex, 1, {speaker_id:speaker, text:left}, {speaker_id:speaker, text:right});
    markReviewDirty(); renderReview(reviewDocument, true);
    reviewSectionIndex = anchorIndex; updateReviewSections();
    const rightInput = document.querySelectorAll("#review-editor .review-anchor")[anchorIndex]?.querySelectorAll("textarea")[blockIndex + 1];
    rightInput?.focus({preventScroll:true}); rightInput?.setSelectionRange(0, 0);
    setReviewStatus("Cursor split created two editable blocks. Save and Preview to validate real word alignment before Apply.");
  } catch (error) { showReviewCursorMessage(row, error.message); }
  finally { guiCursorSplitPending = false; button.disabled = false; }
}
function addCursorSplitControls() {
  document.querySelectorAll('#review-editor .review-anchor').forEach((group, index) => {
    const anchor=reviewDocument?.anchors[index], legend=group.querySelector('legend');
    if(!anchor || !legend || legend.querySelector('.review-time')) return;
    const time=document.createElement('span'); time.className='review-time';
    const format=ms=>`${Math.floor(ms/60000)}:${String(Math.floor(ms/1000)%60).padStart(2,'0')}.${String(ms%1000).padStart(3,'0')}`;
    time.textContent=Number.isInteger(anchor.start_ms)&&Number.isInteger(anchor.end_ms)
      ? ` · ${format(anchor.start_ms)} – ${format(anchor.end_ms)}` : ' · Timing unavailable';
    legend.append(time);
  });
  document.querySelectorAll("#review-editor .review-block-controls").forEach(controls => {
    if (controls.querySelector(".review-cursor-split")) return;
    const button = document.createElement("button"); button.type = "button";
    button.className = "review-cursor-split"; button.textContent = "Split at cursor";
    button.title = "Place the cursor between complete words, then split. Select text to use Separate selected text instead.";
    let captured = null;
    button.addEventListener("pointerdown", event => {
      if (event.button !== 0) return;
      event.preventDefault();
      const input = controls.closest(".review-block")?.querySelector("textarea");
      captured = input ? {start:input.selectionStart, end:input.selectionEnd, value:input.value} : null;
    });
    button.addEventListener("click", () => { void splitReviewAtCursor(button, captured); captured = null; });
    controls.prepend(button);
  });
}
new MutationObserver(addCursorSplitControls).observe(document.querySelector("#review-editor"), {childList:true, subtree:true});

function checkpointGuiWorkspaceFields() {
  const context = translationReviewContext();
  const values = {
    'gui-translation-review-path': context.review_path,
    'gui-translation-result-path': context.result_path,
    'gui-translation-revision-path': context.revision_path,
    'gui-translation-parent-path': context.parent_translation_path,
    'gui-translation-target': context.target_language,
    'gui-translation-applied-path': appliedTranslation || '',
    'gui-speaker-colors': reviewDocument ? JSON.stringify(guiSavedSpeakerColors()) : '',
    'gui-palette-profile': document.querySelector('#gui-export-palette')?.value || 'configured',
  };
  for (const [id, value] of Object.entries(values)) { const input=document.getElementById(id); if(input) input.value=value || ''; }
}
async function restoreGuiWorkspaceFields() {
  const get = id => document.getElementById(id)?.value || '';
  const colors = get('gui-speaker-colors');
  if (reviewDocument && colors) {
    try {
      const parsed = JSON.parse(colors);
      if (!Array.isArray(parsed) && parsed && Object.entries(parsed).every(([id,c]) => /^speaker_\d{3,}$/.test(id) && /^#[a-f0-9]{6}$/i.test(c))) {
        localStorage.setItem(guiPaletteKey(), colors);
        renderReviewSpeakerLabels(reviewDocument); applyGuiSpeakerColors();
      }
    } catch (_) { /* ignore malformed display preferences */ }
  }
  guiPreviewColors = null; guiPreviewResult = '';
  document.querySelector('#gui-export-palette').value = get('gui-palette-profile') || 'configured';
  applyGuiSpeakerColors();
  if (get('gui-translation-review-path') && get('gui-translation-result-path')) {
    const context = {review_path:get('gui-translation-review-path'), result_path:get('gui-translation-result-path'),
      revision_path:get('gui-translation-revision-path'), parent_translation_path:get('gui-translation-parent-path'), target_language:get('gui-translation-target')};
    try {
      const loaded = await queuePost('/api/v1/translation-reviews/load', context);
      translationCandidate = {...context, candidate_path:context.parent_translation_path, output_root:parentPath(parentPath(context.review_path))};
      renderEnhancedTranslationReview(loaded);
      appliedTranslation = get("gui-translation-applied-path");
      document.querySelector("#export-translation-review").disabled = !appliedTranslation;
      persistTranslationReview();
    } catch (error) { document.querySelector('#translation-review-status').textContent = error.message; }
  }
  guiActiveResult = reviewDocument?.result_path || translationReview?.result_path || '';
  updateGuiContext();
}

const directionActions = document.createElement("div"); directionActions.className = "actions"; directionActions.id = "gui-translation-directions";
const directionStatus = document.createElement("p"); directionStatus.id = "gui-direction-status"; directionStatus.className = "field-hint"; directionStatus.setAttribute("role", "status");
const directionWarning = document.createElement("p"); directionWarning.id = "gui-direction-warning";
directionWarning.setAttribute("role", "status"); directionWarning.hidden = true;
const acceptDirection = document.createElement("button"); acceptDirection.type = "button"; acceptDirection.textContent = "Accept direction change"; acceptDirection.hidden = true;
let guiPendingDirection = null;
let guiDirectionResult = "";
function translationSourceJob() {
  const result = translationForm.elements.namedItem("result_path").value || guiActiveResult;
  return guiKnownJobs.find(item => item.result_path === result);
}
function setGuiTranslationDirection(target) {
  translationForm.elements.namedItem("target_language").value = target;
  translationForm.elements.namedItem("target_language").dispatchEvent(new Event("change", {bubbles:true}));
  directionWarning.hidden = true; acceptDirection.hidden = true; guiPendingDirection = null;
  refreshGuiTranslationDirection();
}
function refreshGuiTranslationDirection() {
  const job = translationSourceJob();
  if (job && guiDirectionResult !== job.result_path) {
    guiDirectionResult = job.result_path;
    translationForm.elements.namedItem("target_language").value = job.language === "en" ? "pl" : "en";
    directionWarning.hidden = true; acceptDirection.hidden = true; guiPendingDirection = null;
  }
  const target = translationForm.elements.namedItem("target_language").value;
  for (const button of directionActions.querySelectorAll("button[data-target]")) button.setAttribute("aria-pressed", String(button.dataset.target === target));
  const mismatch = job && job.language === target;
  const generate = document.querySelector("#generate-translation");
  generate.dataset.directionMismatch = String(Boolean(mismatch));
  const path=String(translationForm.elements.namedItem("result_path").value || "");
  const batch=stageQueueJobs.some(item=>stageQueueSelections.translation.has(item.job_id) && stageQueueItemIsActionable(item,"translation"));
  const completed=job?.result_path===path && job.workflow?.assisted_translation?.state==="complete";
  generate.disabled = Boolean(mismatch) || generate.dataset.generationBusy==="true" || generate.getAttribute("aria-busy")==="true"
    || (!batch && (!path || generate.dataset.generatedFor===path || (completed && generate.dataset.allowRegenerationFor!==path)));

  directionStatus.textContent = mismatch
    ? "This direction needs a recording in the other source language. Choose a matching recording before generating."
    : `Current direction: ${target === "en" ? "PL → EN" : "EN → PL"}.`;
  const inputs = document.querySelector("#gui-translation-inputs");
  if (inputs && job && translationForm.elements.namedItem("result_path").value === job.result_path && inputs.dataset.result !== job.result_path) { inputs.open = false; inputs.dataset.result = job.result_path; }
}
for (const [source, target] of [["pl","en"], ["en","pl"]]) {
  const button = document.createElement("button"); button.type = "button"; button.dataset.target = target;
  button.textContent = `${source.toUpperCase()} → ${target.toUpperCase()}`;
  button.addEventListener("click", () => {
    if (translationForm.elements.namedItem("target_language").value === target) return;
    guiPendingDirection = target;
    directionWarning.textContent = "Changing direction requires a matching source-language recording. Existing translations stay unchanged. Accept this change to continue.";
    directionWarning.hidden = false; acceptDirection.hidden = false;
  }); directionActions.append(button);
}
acceptDirection.addEventListener("click", () => { if (guiPendingDirection) setGuiTranslationDirection(guiPendingDirection); });
translationForm.before(directionActions, directionStatus, directionWarning, acceptDirection);
translationForm.elements.namedItem("target_language").addEventListener("change", refreshGuiTranslationDirection);
document.addEventListener("ewp-stage", refreshGuiTranslationDirection);
