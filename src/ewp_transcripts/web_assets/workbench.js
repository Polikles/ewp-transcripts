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
  lastWorkspaceStep = guiStages.find(item => item[0] === stage)[2];
  for (const [id, , heading] of guiStages) {
    const section = document.getElementById(heading)?.closest("section");
    if (section) section.hidden = id !== stage;
    const button = document.querySelector(`[data-gui-stage="${id}"]`);
    button?.setAttribute("aria-current", id === stage ? "step" : "false");
  }
  const heading = document.getElementById(guiStages.find(item => item[0] === stage)[2]);
  if (focus && heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); }
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
  const job = guiKnownJobs.find(item => item.result_path === guiActiveResult);
  const signature = JSON.stringify([guiActiveStage, guiActiveResult, reviewDirty, translationReviewDirty,
    job?.workflow, reviewDocument?.job_id, translationReview?.revision_path,
    stageQueueSelections.correction.size, stageQueueSelections.translation.size]);
  updateGuiRecordings();
  if (context.dataset.signature === signature) { applyGuiSpeakerColors(); return; }
  context.dataset.signature = signature;
  context.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = job?.planned_job_id || reviewDocument?.job_id || "No active recording";
  const stage = document.createElement("span");
  stage.textContent = guiStages.find(item => item[0] === guiActiveStage)[1];
  const path = document.createElement("span");
  path.className = "gui-path";
  path.textContent = guiActiveResult ? shortName(guiActiveResult) : "Choose a recording in a stage queue.";
  path.title = guiActiveResult;
  const saved = document.createElement("span");
  saved.textContent = reviewDirty || translationReviewDirty ? "Unsaved draft — navigation keeps it open" : "Draft changes saved or no draft open";
  context.append(title, stage, path, saved);
  const count = document.createElement("span");
  count.textContent = `Batch selection: ${stageQueueSelections.correction.size} correction · ${stageQueueSelections.translation.size} translation`;
  context.append(count);
  const translationJob = guiKnownJobs.find(item => item.result_path === translationReview?.result_path);
  if (translationReview && translationJob?.workflow?.review?.path && translationReview.revision_path !== translationJob.workflow.review.path) {
    const stale = document.createElement('p'); stale.className='notice';
    stale.textContent='Translation uses an older or raw source. A newer verified source exists. Existing outputs are retained; reopen translation to use the new revision.';
    context.append(stale);
  }
  updateGuiRecordings();
  applyGuiSpeakerColors();
}

function updateGuiRecordings() {
  const list = document.getElementById("gui-recordings");
  if (!list) return;
  const signature = JSON.stringify([guiActiveResult, guiKnownJobs.map(job => [job.job_id, job.workflow, job.status])]);
  if (list.dataset.signature === signature) return;
  list.dataset.signature = signature;
  list.replaceChildren();
  for (const job of guiKnownJobs) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "gui-recording";
    button.setAttribute("aria-pressed", String(job.result_path === guiActiveResult));
    const identity = document.createElement("strong");
    identity.textContent = job.planned_job_id;
    const status = document.createElement("span");
    status.textContent = `${job.status} · ${nextWorkflowLabel(nextWorkflowStage(job))}`;
    button.title = job.result_path || job.input_path;
    button.append(identity, status);
    button.addEventListener("click", () => {
      guiActiveResult = job.result_path || "";
      if (job.result_path && ["correction", "review", "translation", "semantic-review"].includes(guiActiveStage)) {
        void openStageQueueItem(job, guiActiveStage);
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
  const main = document.querySelector("main");
  for (const id of workspaceFieldIds.filter(id => id.startsWith("gui-"))) {
    const input = document.createElement("input"); input.type = "hidden"; input.id = id; main.append(input);
  }
  const paths = document.createElement("details"); paths.className = "gui-source-paths";
  paths.innerHTML = "<summary>Source and output paths</summary>";
  const form = document.querySelector("#review-workflow");
  while (form.firstElementChild && !form.firstElementChild.contains(document.querySelector("#prepare-review"))) paths.append(form.firstElementChild);
  form.prepend(paths);
  const settings = document.createElement("section");
  settings.innerHTML = `<h2 id="gui-settings-heading">Settings & About</h2>
    <p>Local-first audio transcription. LLM correction and translation are optional. Source export never requires translation or dictionaries.</p>
    <p>Provider readiness and disclosure consent remain in each optional stage. Local API endpoints are separately operated; the application cannot guarantee third-party logging, retention, forwarding or storage location.</p>
    <p>Audio is processed locally. Correction and translation send transcript text only after explicit scoped consent. Keys stay in server memory and are never saved in workspaces.</p>
    <p><a href="/help" target="_blank" rel="noreferrer">Open the complete local GUI instructions</a></p>
    <p><a href="/assets/brand/NOTICE.txt">Asset credits and notices</a> · <a href="/assets/brand/LICENSE-ASSETS.txt">Identity asset terms</a></p>
    <p>Artwork: Cyryl. Creator URL is an unverified placeholder (blogcyryla.pl); TODO replace when supplied.</p>`;
  main.append(settings);
  settings.append(document.querySelector("footer"));
  const bar = document.createElement("div");
  bar.className = "gui-preferences";
  bar.innerHTML = `<label>Interface language<select id="gui-locale"><option value="en">English</option><option value="pl">Polski</option></select></label>
    <label>Appearance<select id="gui-theme"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>`;
  header.append(bar);
  document.querySelector("#gui-locale").value = guiPreferences.locale === "pl" ? "pl" : "en";
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
  for (const [id, title, , icon] of guiStages) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.guiStage = id;
    button.append(guiIcon(icon), document.createTextNode(title));
    button.addEventListener("click", () => showGuiStage(id, true));
    nav.append(button);
  }
  const recordings = document.createElement("div");
  recordings.id = "gui-recordings";
  recordings.setAttribute("aria-label", "Recordings");
  navigation.append(nav, recordings);
  main.before(navigation);
  const context = document.createElement("div");
  context.id = "gui-active-context";
  context.setAttribute("role", "status");
  main.before(context);
  document.body.classList.add("gui-workbench");
  document.addEventListener("ewp-jobs", event => { guiKnownJobs = event.detail; updateGuiContext(); });
  for (const selector of ["#review-editor", "#translation-review-editor", "#review-status", "#translation-review-status"]) {
    new MutationObserver(updateGuiContext).observe(document.querySelector(selector), {childList: true, subtree: true});
  }
  document.addEventListener("input", event => {
    if (event.target.closest("#review-editor, #translation-review-editor")) updateGuiContext();
  });
  applyGuiTheme();
  showGuiStage("workspace");
  startGuiTranslation();
}

// Colors are display/export preferences, never transcript text or speaker identity.
const guiBrandPalette = ["#F5F7FA", "#00AEEF", "#F2C55B", "#BF734D", "#8CFFB3", "#64D8D0"];
function guiPaletteKey() { return `ewp-colors-v1:${reviewDocument?.result_path || ""}`; }
function guiSpeakerColors() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(guiPaletteKey()) || "{}"); } catch (_) { /* defaults */ }
  const colors = {...(reviewDocument?.configured_speaker_colors || {}), ...saved};
  for (const id of reviewDocument?.speakers || []) {
    if (!/^#[0-9a-f]{6}$/i.test(colors[id] || "")) {
      const number = Number(id.match(/\d+$/)?.[0] || 1);
      colors[id] = guiBrandPalette[(number - 1) % guiBrandPalette.length];
    }
  }
  return Object.fromEntries((reviewDocument?.speakers || []).map(id => [id, colors[id]]));
}
function applyGuiSpeakerColors() {
  if (!reviewDocument) return;
  const colors = guiSpeakerColors();
  document.querySelectorAll("#review-editor .review-block").forEach(row => {
    row.style.borderInlineStart = `6px solid ${colors[row.querySelector("select")?.value] || guiBrandPalette[0]}`;
  });
  document.querySelectorAll("#review-speaker-labels .review-speaker-label-row").forEach(row => {
    const id = row.querySelector("input[data-speaker-id]")?.dataset.speakerId;
    if (!id || row.querySelector("input[type=color]")) return;
    const label = document.createElement("label");
    label.textContent = "Speaker color";
    const input = document.createElement("input");
    input.type = "color";
    input.value = colors[id];
    input.setAttribute("aria-label", `Speaker color ${id}`);
    input.addEventListener("input", () => {
      const updated = guiSpeakerColors(); updated[id] = input.value;
      localStorage.setItem(guiPaletteKey(), JSON.stringify(updated));
      document.querySelector("#gui-export-palette").value = "brand";
      applyGuiSpeakerColors();
    });
    label.append(input); row.append(label);
  });
}
function installGuiPaletteControls() {
  const panel = document.createElement("div");
  panel.id = "gui-palette";
  panel.innerHTML = `<label>YTT color profile<select id="gui-export-palette"><option value="configured">Configured production palette</option><option value="brand">Brand preview palette</option></select></label>
    <p>Existing custom colors are retained. Brand colors require a new YouTube check; existing exports are never recolored.</p>
    <button type="button" id="gui-adopt-brand">Adopt brand palette for this recording</button>
    <button type="button" id="gui-production-palette">Use configured production palette</button>`;
  document.querySelector("#review-speaker-names").after(panel);
  document.querySelector("#gui-adopt-brand").addEventListener("click", () => {
    if (!reviewDocument || !window.confirm("Replace this recording's custom colors with the brand palette? Existing exports will stay unchanged.")) return;
    const colors = Object.fromEntries(reviewDocument.speakers.map(id => [id, guiBrandPalette[(Number(id.match(/\d+$/)?.[0] || 1) - 1) % 6]]));
    localStorage.setItem(guiPaletteKey(), JSON.stringify(colors));
    document.querySelector("#gui-export-palette").value = "brand";
    renderReviewSpeakerLabels(reviewDocument); applyGuiSpeakerColors();
  });
  document.querySelector("#gui-production-palette").addEventListener("click", () => { document.querySelector("#gui-export-palette").value = "configured"; });
}
function guiExportPreferences() {
  return {speaker_colors: document.querySelector("#gui-export-palette")?.value === "brand" ? guiSpeakerColors() : null};
}

installGuiPaletteControls();
installGuiShell();

async function splitReviewAtCursor(button) {
  const {row, anchorIndex, blockIndex} = reviewBlockPosition(button);
  const input = row?.querySelector("textarea");
  if (!reviewDocument || !input) return;
  const at = input.selectionStart;
  const value = input.value;
  if (at !== input.selectionEnd || at <= 0 || at >= value.length ||
      (!/\s/.test(value[at - 1]) && !/\s/.test(value[at]))) {
    setReviewStatus("GUI_REVIEW_CURSOR_BOUNDARY: Place the cursor between complete words inside a block. Use Separate selected text for a selection.");
    input.focus(); return;
  }
  const left = value.slice(0, at).trim(), right = value.slice(at).trim();
  if (!left || !right) { setReviewStatus("GUI_REVIEW_CURSOR_BOUNDARY: Both sides must contain text."); return; }
  try {
    if (reviewDirty) await saveReviewDraft();
    const anchor = reviewDocument.anchors[anchorIndex];
    const speaker = anchor.blocks[blockIndex].speaker_id;
    anchor.blocks.splice(blockIndex, 1, {speaker_id:speaker, text:left}, {speaker_id:speaker, text:right});
    markReviewDirty(); renderReview(reviewDocument, true);
    reviewSectionIndex = anchorIndex; updateReviewSections();
    setReviewStatus("Cursor split created two editable blocks. Save and Preview to validate real word alignment before Apply.");
  } catch (error) { setReviewStatus(error.message); }
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
    button.addEventListener("pointerdown", event => event.preventDefault());
    button.addEventListener("click", () => splitReviewAtCursor(button));
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
    'gui-speaker-colors': reviewDocument ? JSON.stringify(guiSpeakerColors()) : '',
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
  document.querySelector('#gui-export-palette').value = get('gui-palette-profile') === 'brand' ? 'brand' : 'configured';
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

const manualTranslation = document.createElement('button'); manualTranslation.type='button';
manualTranslation.id='gui-manual-translation'; manualTranslation.textContent='Open manual translation';
manualTranslation.addEventListener('click', () => {
  const result=translationForm.elements.namedItem('result_path').value || guiActiveResult;
  const job=guiKnownJobs.find(item=>item.result_path===result);
  if (!result) { document.querySelector('#translation-status').textContent='Choose a recording first.'; return; }
  void openEnhancedTranslationReview({result_path:result,
    revision_path:translationForm.elements.namedItem('source_revision_path').value || job?.workflow?.review?.path || '',
    candidate_path:'', output_root:translationForm.elements.namedItem('output_root').value || job?.output_directory || workflowOutput.value,
    target_language:translationForm.elements.namedItem('target_language').value});
});
const directionActions=document.createElement('div'); directionActions.className='actions';
for(const [source,target] of [['pl','en'],['en','pl']]) {
  const button=document.createElement('button'); button.type='button'; button.textContent=`${source.toUpperCase()} → ${target.toUpperCase()}`;
  button.addEventListener('click',()=>{
    const result=translationForm.elements.namedItem('result_path').value || guiActiveResult;
    const job=guiKnownJobs.find(item=>item.result_path===result);
    if(job && job.language!==source) { document.querySelector('#translation-status').textContent='Choose a recording whose source language matches this direction.'; return; }
    translationForm.elements.namedItem('target_language').value=target;
  }); directionActions.append(button);
}
directionActions.append(manualTranslation); translationForm.before(directionActions);
