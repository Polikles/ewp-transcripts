/* Recoverable, navigable semantic-translation review controls. */

const translationReviewStorageKey = "ewp-active-translation-review-v1";
let translationReviewDirty = false;
let translationReviewSectionIndex = 0;
let translationReviewHistory = [];
let translationReviewHistoryIndex = -1;

function translationReviewTargets() {
  return (translationReview?.units || []).map(unit => ({
    unit_id: unit.unit_id,
    target_text: unit.target_text,
  }));
}

function translationReviewSnapshot() {
  return JSON.stringify(translationReviewTargets());
}

function resetTranslationReviewHistory() {
  translationReviewHistory = translationReview ? [translationReviewSnapshot()] : [];
  translationReviewHistoryIndex = translationReviewHistory.length - 1;
  updateTranslationReviewHistoryControls();
}

function recordTranslationReviewHistory() {
  const snapshot = translationReviewSnapshot();
  if (translationReviewHistory[translationReviewHistoryIndex] === snapshot) return;
  translationReviewHistory = translationReviewHistory.slice(0, translationReviewHistoryIndex + 1);
  translationReviewHistory.push(snapshot);
  if (translationReviewHistory.length > 100) translationReviewHistory.shift();
  translationReviewHistoryIndex = translationReviewHistory.length - 1;
  updateTranslationReviewHistoryControls();
}

function updateTranslationReviewHistoryControls() {
  const undo = document.querySelector("#undo-translation-review");
  const redo = document.querySelector("#redo-translation-review");
  if (undo) undo.disabled = translationReviewHistoryIndex <= 0;
  if (redo) {
    redo.disabled = translationReviewHistoryIndex < 0
      || translationReviewHistoryIndex >= translationReviewHistory.length - 1;
  }
}

function markTranslationReviewDirty() {
  translationReviewDirty = true;
  appliedTranslation = "";
  document.querySelector("#apply-translation-review").disabled = true;
  document.querySelector("#export-translation-review").disabled = true;
}

function restoreTranslationReviewHistory(direction) {
  const next = translationReviewHistoryIndex + direction;
  if (!translationReview || next < 0 || next >= translationReviewHistory.length) return;
  const targets = JSON.parse(translationReviewHistory[next]);
  const byId = new Map(targets.map(item => [item.unit_id, item.target_text]));
  translationReview = {
    ...translationReview,
    units: translationReview.units.map(unit => ({
      ...unit,
      target_text: byId.get(unit.unit_id) ?? unit.target_text,
    })),
  };
  translationReviewHistoryIndex = next;
  renderEnhancedTranslationReview(translationReview, {dirty: true, preserveHistory: true});
  document.querySelector("#translation-review-status").textContent = direction < 0
    ? "Undid the last current-editor change. Save before previewing."
    : "Redid the current-editor change. Save before previewing.";
}

function translationReviewContext() {
  return {
    review_path: translationReview?.review_path || "",
    result_path: translationReview?.result_path || translationCandidate?.result_path || "",
    revision_path: translationReview?.revision_path || translationCandidate?.revision_path || "",
    parent_translation_path: translationReview?.parent_translation_path
      || translationCandidate?.candidate_path || "",
  };
}

function persistTranslationReview() {
  if (!translationReview || !translationCandidate) return;
  localStorage.setItem(translationReviewStorageKey, JSON.stringify({
    ...translationReviewContext(),
    output_root: translationCandidate.output_root,
    applied_translation_path: appliedTranslation,
  }));
  updateTranslationReviewRestoreControl();
}

function updateTranslationReviewRestoreControl() {
  const restore = document.querySelector("#restore-translation-review");
  if (restore) restore.disabled = !localStorage.getItem(translationReviewStorageKey);
}

function updateTranslationReviewSections() {
  const units = [...document.querySelectorAll("#translation-review-editor .translation-unit")];
  const layout = document.querySelector(".translation-review-layout")?.value || "few";
  if (!units.length) return;
  const chunkSize = 5;
  const chunkCount = Math.ceil(units.length / chunkSize);
  translationReviewSectionIndex = Math.max(0, Math.min(translationReviewSectionIndex, chunkCount - 1));
  units.forEach((unit, index) => {
    unit.hidden = layout === "few"
      && Math.floor(index / chunkSize) !== translationReviewSectionIndex;
  });
  document.querySelectorAll(".translation-review-position").forEach(element => {
    const first = translationReviewSectionIndex * chunkSize + 1;
    const last = Math.min(first + chunkSize - 1, units.length);
    element.textContent = layout === "few"
      ? `Units ${first}–${last} of ${units.length}`
      : `${units.length} units`;
  });
  document.querySelectorAll(".previous-translation-review-unit").forEach(button => {
    button.disabled = layout !== "few" || translationReviewSectionIndex === 0;
  });
  document.querySelectorAll(".next-translation-review-unit").forEach(button => {
    button.disabled = layout !== "few" || translationReviewSectionIndex === chunkCount - 1;
  });
}

function resizeReviewTextarea(input) {
  input.style.height = "auto";
  input.style.height = `${Math.max(input.scrollHeight, 48)}px`;
}

function renderEnhancedTranslationReview(documentValue, options = {}) {
  const {dirty = false, preserveHistory = false} = options;
  const scrollTop = window.scrollY;
  translationReview = documentValue;
  translationReviewDirty = dirty;
  if (!preserveHistory) resetTranslationReviewHistory();
  const editor = document.querySelector("#translation-review-editor");
  editor.replaceChildren();
  documentValue.units.forEach((unit, index) => {
    const article = document.createElement("fieldset");
    article.className = "translation-unit";
    const legend = document.createElement("legend");
    legend.textContent = `Translation unit ${index + 1}`;
    const sourceLabel = document.createElement("p");
    sourceLabel.className = "translation-source-label";
    sourceLabel.textContent = "Source";
    const source = document.createElement("p");
    source.className = "translation-source";
    source.textContent = unit.source_text;
    const label = document.createElement("label");
    label.className = "translation-target-label";
    label.textContent = "Target translation";
    const input = document.createElement("textarea");
    input.dataset.unitId = unit.unit_id;
    input.value = unit.target_text;
    input.addEventListener("input", () => {
      unit.target_text = input.value;
      resizeReviewTextarea(input);
      markTranslationReviewDirty();
      recordTranslationReviewHistory();
    });
    label.append(input);
    article.append(legend, sourceLabel, source, label);
    editor.append(article);
    resizeReviewTextarea(input);
  });
  document.querySelector("#translation-review-navigation").hidden = false;
  document.querySelector("#translation-review-bottom-navigation").hidden = false;
  document.querySelector("#save-translation-review").disabled = false;
  document.querySelector("#preview-translation-review").disabled = false;
  document.querySelector("#translation-review-confirmed").checked = false;
  document.querySelector("#apply-translation-review").disabled = true;
  document.querySelector("#export-translation-review").disabled = !appliedTranslation;
  document.querySelector("#translation-review-status").textContent =
    `${documentValue.job_id} · ${documentValue.direction.source_language} → ${documentValue.direction.target_language} · source: ${documentValue.source_verification}`;
  document.querySelector("#translation-review-result").textContent = JSON.stringify(documentValue, null, 2);
  updateTranslationReviewSections();
  updateTranslationReviewHistoryControls();
  requestAnimationFrame(() => window.scrollTo(0, scrollTop));
}

async function openEnhancedTranslationReview() {
  if (!translationCandidate) return;
  const root = translationCandidate.output_root;
  try {
    const payload = await queuePost("/api/v1/translation-reviews/prepare", {
      ...translationReviewContext(),
      review_output_directory: `${root}/translation-reviews`,
    });
    translationReviewSectionIndex = 0;
    appliedTranslation = "";
    renderEnhancedTranslationReview(payload);
    persistTranslationReview();
    document.querySelector("#translation-review-heading").scrollIntoView({behavior: "smooth"});
  } catch (error) {
    document.querySelector("#translation-review-status").textContent = error.message;
  }
}

async function saveEnhancedTranslationReview() {
  if (!translationReview) return;
  try {
    const payload = await queuePost("/api/v1/translation-reviews/save", {
      ...translationReviewContext(),
      review_sha256: translationReview.review_sha256,
      targets: translationReviewTargets(),
    });
    renderEnhancedTranslationReview(payload);
    persistTranslationReview();
    document.querySelector("#translation-review-status").textContent =
      "Translation draft saved; preview is required again.";
  } catch (error) {
    document.querySelector("#translation-review-status").textContent = error.message;
  }
}

async function restoreEnhancedTranslationReview() {
  const stored = localStorage.getItem(translationReviewStorageKey);
  if (!stored) return;
  if (translationReviewDirty && !window.confirm("Discard the current unsaved translation edits and restore the saved draft?")) {
    return;
  }
  try {
    const context = JSON.parse(stored);
    const payload = await queuePost("/api/v1/translation-reviews/load", context);
    translationCandidate = {
      result_path: context.result_path,
      revision_path: context.revision_path || "",
      candidate_path: context.parent_translation_path,
      output_root: context.output_root,
    };
    appliedTranslation = context.applied_translation_path || "";
    translationReviewSectionIndex = 0;
    renderEnhancedTranslationReview(payload);
    if (appliedTranslation) document.querySelector("#export-translation-review").disabled = false;
    document.querySelector("#translation-review-status").textContent = appliedTranslation
      ? "Saved applied translation review restored from disk."
      : "Saved translation draft restored from disk; preview is required again.";
  } catch (error) {
    document.querySelector("#translation-review-status").textContent =
      `GUI_TRANSLATION_REVIEW_RESTORE_FAILED: ${error.message}`;
  }
}

async function previewEnhancedTranslationReview() {
  if (!translationReview) return;
  if (translationReviewDirty) {
    document.querySelector("#translation-review-status").textContent =
      "GUI_TRANSLATION_REVIEW_SAVE_REQUIRED: Save the current draft before preview.";
    return;
  }
  try {
    const payload = await queuePost("/api/v1/translation-reviews/preview", translationReviewContext());
    document.querySelector("#translation-review-result").textContent = JSON.stringify(payload, null, 2);
    const summary = document.querySelector("#translation-review-summary");
    const table = document.createElement("table");
    table.className = "review-summary-table";
    const rows = [
      ["Validation", "Passed"],
      ["Publication", "None — preview only"],
      ["Units", payload.statistics.unit_count],
      ["Source tokens", payload.statistics.source_tokens],
      ["Target tokens", payload.statistics.target_tokens],
      ["Warnings", payload.warnings.length],
    ];
    const body = document.createElement("tbody");
    for (const [label, value] of rows) {
      const row = document.createElement("tr");
      const heading = document.createElement("th");
      heading.scope = "row";
      heading.textContent = label;
      const cell = document.createElement("td");
      cell.textContent = String(value);
      row.append(heading, cell);
      body.append(row);
    }
    table.append(body);
    summary.replaceChildren(table);
    document.querySelector("#translation-review-status").textContent =
      "Preview passed: exact source lineage, complete target text, and immutable unit ownership validated. No translation was published.";
    document.querySelector("#apply-translation-review").disabled = false;
  } catch (error) {
    document.querySelector("#translation-review-status").textContent = error.message;
  }
}

async function applyEnhancedTranslationReview() {
  if (!translationReview) return;
  try {
    const root = translationCandidate.output_root;
    const payload = await queuePost("/api/v1/translation-reviews/apply", {
      ...translationReviewContext(),
      translation_output_directory: `${root}/accepted-translations`,
      confirmed: document.querySelector("#translation-review-confirmed").checked,
    });
    appliedTranslation = payload.translation_path;
    persistTranslationReview();
    document.querySelector("#translation-review-result").textContent = JSON.stringify(payload, null, 2);
    document.querySelector("#translation-review-status").textContent = "Verified manual translation applied.";
    document.querySelector("#export-translation-review").disabled = false;
    document.querySelector("#apply-translation-review").disabled = true;
  } catch (error) {
    document.querySelector("#translation-review-status").textContent = error.message;
    await reportWorkflowError(translationReview?.result_path || translationCandidate?.result_path, "translation", error);
  }
}

async function exportEnhancedTranslationReview() {
  if (!translationReview || !appliedTranslation) return;
  try {
    const root = translationCandidate.output_root;
    const formats = [...document.querySelectorAll('input[name="translation-format"]:checked')]
      .map(item => item.value);
    const payload = await queuePost("/api/v1/translation-reviews/audit-export", {
      ...translationReviewContext(),
      translation_path: appliedTranslation,
      audit_output_directory: `${root}/translation-audits`,
      export_output_directory: `${root}/translation-exports`,
      formats,
    });
    document.querySelector("#translation-review-result").textContent = JSON.stringify(payload, null, 2);
    document.querySelector("#translation-review-status").textContent =
      "Verified translation audited and exported.";
    await enableProceedNextOutput();
  } catch (error) {
    document.querySelector("#translation-review-status").textContent = error.message;
    await reportWorkflowError(translationReview?.result_path || translationCandidate?.result_path, "translated_export", error);
  }
}

function replaceTranslationReviewButton(selector, handler) {
  const original = document.querySelector(selector);
  const button = original.cloneNode(true);
  original.replaceWith(button);
  button.addEventListener("click", handler);
  return button;
}

function addTranslationReviewNavigation() {
  const heading = document.querySelector("#translation-review-heading");
  const navigation = document.createElement("div");
  navigation.id = "translation-review-navigation";
  navigation.className = "translation-review-navigation";
  navigation.hidden = true;
  navigation.innerHTML = '<label>Display <select class="translation-review-layout"><option value="few">Five units at a time</option><option value="all">All units</option></select></label><div class="actions"><button type="button" class="previous-translation-review-unit">Previous units</button><span class="translation-review-position"></span><button type="button" class="next-translation-review-unit">Next units</button></div>';
  heading.after(navigation);
  const bottom = navigation.cloneNode(true);
  bottom.id = "translation-review-bottom-navigation";
  bottom.hidden = true;
  document.querySelector("#translation-review-editor").after(bottom);
  document.querySelectorAll(".previous-translation-review-unit").forEach(button => {
    button.addEventListener("click", () => {
      translationReviewSectionIndex -= 1;
      updateTranslationReviewSections();
    });
  });
  document.querySelectorAll(".next-translation-review-unit").forEach(button => {
    button.addEventListener("click", () => {
      translationReviewSectionIndex += 1;
      updateTranslationReviewSections();
    });
  });
  document.querySelectorAll(".translation-review-layout").forEach(select => {
    select.addEventListener("change", event => {
      const value = event.currentTarget.value;
      document.querySelectorAll(".translation-review-layout").forEach(other => {
        other.value = value;
      });
      localStorage.setItem("ewp-translation-review-layout", value);
      updateTranslationReviewSections();
    });
  });
  const storedLayout = localStorage.getItem("ewp-translation-review-layout");
  const savedLayout = storedLayout === "all" ? "all" : "few";
  document.querySelectorAll(".translation-review-layout").forEach(select => {
    select.value = savedLayout;
  });
}

function addTranslationReviewRecoveryControls() {
  const controls = document.querySelector("#save-translation-review").parentElement;
  const restore = document.createElement("button");
  restore.type = "button";
  restore.id = "restore-translation-review";
  restore.textContent = "Restore saved draft";
  controls.insertBefore(restore, document.querySelector("#save-translation-review").nextSibling);
  const undo = document.createElement("button");
  undo.type = "button";
  undo.id = "undo-translation-review";
  undo.textContent = "Undo";
  const redo = document.createElement("button");
  redo.type = "button";
  redo.id = "redo-translation-review";
  redo.textContent = "Redo";
  controls.append(undo, redo);
  restore.addEventListener("click", restoreEnhancedTranslationReview);
  undo.addEventListener("click", () => restoreTranslationReviewHistory(-1));
  redo.addEventListener("click", () => restoreTranslationReviewHistory(1));
  updateTranslationReviewRestoreControl();
}

addTranslationReviewNavigation();
addTranslationReviewRecoveryControls();
replaceTranslationReviewButton("#review-translation", openEnhancedTranslationReview);
replaceTranslationReviewButton("#save-translation-review", saveEnhancedTranslationReview);
replaceTranslationReviewButton("#preview-translation-review", previewEnhancedTranslationReview);
replaceTranslationReviewButton("#apply-translation-review", applyEnhancedTranslationReview);
replaceTranslationReviewButton("#export-translation-review", exportEnhancedTranslationReview);
