"use strict";

const reviewHistoryLimit = 100;
let reviewHistory = [];
let reviewHistoryIndex = -1;
let reviewHistoryRecordingScheduled = false;
let reviewHistoryRestoring = false;

function arrangeReviewControls() {
  const prepare = document.querySelector("#prepare-review");
  const preview = document.querySelector("#preview-review");
  const save = document.querySelector("#save-review");
  const restore = document.querySelector("#restore-review");
  const clear = document.querySelector("#clear-review");
  if (!prepare || !preview || !save || !restore || !clear) return;

  const originalActions = prepare.parentElement;
  const layout = document.createElement("div");
  layout.className = "review-control-groups";
  const preparation = document.createElement("section");
  preparation.className = "review-control-group";
  preparation.innerHTML = "<h3>Prepare and validate</h3>";
  const editing = document.createElement("section");
  editing.className = "review-control-group";
  editing.innerHTML = "<h3>Draft and history</h3>";
  const prepareLine = document.createElement("div");
  prepareLine.className = "review-control-line";
  prepareLine.append(prepare);
  const previewLine = document.createElement("div");
  previewLine.className = "review-control-line";
  previewLine.append(preview);
  preparation.append(prepareLine, previewLine);
  const saveLine = document.createElement("div");
  saveLine.className = "review-control-line";
  saveLine.append(save, restore);
  const clearLine = document.createElement("div");
  clearLine.className = "review-control-line";
  clearLine.append(clear);
  const historyLine = document.createElement("div");
  historyLine.className = "review-control-line";
  const undo = document.createElement("button");
  undo.type = "button";
  undo.id = "undo-review";
  undo.textContent = "Undo";
  undo.title = "Undo the last current-editor change. This does not change saved files.";
  const redo = document.createElement("button");
  redo.type = "button";
  redo.id = "redo-review";
  redo.textContent = "Redo";
  redo.title = "Redo a current-editor change. This does not change saved files.";
  historyLine.append(undo, redo);
  editing.append(saveLine, clearLine, historyLine);
  layout.append(preparation, editing);
  originalActions.replaceWith(layout);
  undo.addEventListener("click", () => restoreReviewHistory(-1));
  redo.addEventListener("click", () => restoreReviewHistory(1));
}

function reviewHistorySnapshot() {
  if (!reviewDocument) return "";
  return JSON.stringify({
    anchors: reviewDocument.anchors,
    speakers: reviewDocument.speakers,
    speaker_labels: reviewDocument.speaker_labels,
  });
}

function updateReviewHistoryControls() {
  const undo = document.querySelector("#undo-review");
  const redo = document.querySelector("#redo-review");
  if (undo) undo.disabled = reviewHistoryIndex <= 0;
  if (redo) redo.disabled = reviewHistoryIndex < 0 || reviewHistoryIndex >= reviewHistory.length - 1;
}

function resetReviewHistory() {
  const snapshot = reviewHistorySnapshot();
  reviewHistory = snapshot ? [snapshot] : [];
  reviewHistoryIndex = snapshot ? 0 : -1;
  updateReviewHistoryControls();
}

function recordReviewHistory() {
  if (!reviewDocument || reviewHistoryRestoring) return;
  const snapshot = reviewHistorySnapshot();
  if (!snapshot || reviewHistory[reviewHistoryIndex] === snapshot) return;
  reviewHistory = reviewHistory.slice(0, reviewHistoryIndex + 1);
  reviewHistory.push(snapshot);
  if (reviewHistory.length > reviewHistoryLimit) reviewHistory.shift();
  reviewHistoryIndex = reviewHistory.length - 1;
  updateReviewHistoryControls();
}

function scheduleReviewHistoryRecord() {
  if (reviewHistoryRecordingScheduled || reviewHistoryRestoring) return;
  reviewHistoryRecordingScheduled = true;
  queueMicrotask(() => {
    reviewHistoryRecordingScheduled = false;
    recordReviewHistory();
  });
}

function restoreReviewHistory(direction) {
  const target = reviewHistoryIndex + direction;
  if (!reviewDocument || target < 0 || target >= reviewHistory.length) return;
  reviewHistoryRestoring = true;
  try {
    const snapshot = JSON.parse(reviewHistory[target]);
    reviewDocument = {
      ...reviewDocument,
      anchors: snapshot.anchors,
      speakers: snapshot.speakers,
      speaker_labels: snapshot.speaker_labels,
    };
    reviewHistoryIndex = target;
    renderReview(reviewDocument, true);
    setReviewStatus(
      direction < 0
        ? "Undo applied to the current draft. Save and preview again before applying."
        : "Redo applied to the current draft. Save and preview again before applying.",
    );
  } finally {
    reviewHistoryRestoring = false;
    updateReviewHistoryControls();
  }
}

async function separateSelectedReviewText(button) {
  const {row, anchorIndex, blockIndex} = reviewBlockPosition(button);
  const text = row?.querySelector("textarea");
  const anchor = reviewDocument?.anchors?.[anchorIndex];
  const block = anchor?.blocks?.[blockIndex];
  if (!text || !anchor || !block) {
    setReviewStatus("GUI_REVIEW_STRUCTURE_INVALID: The selected review block is no longer available.");
    return;
  }
  let start = text.selectionStart;
  let end = text.selectionEnd;
  const value = text.value;
  while (start < end && /\s/.test(value.charAt(start))) start += 1;
  while (end > start && /\s/.test(value.charAt(end - 1))) end -= 1;
  const startsWithTerminalPunctuation = ".!?".includes(value.charAt(start)) && /\s/.test(value.charAt(start + 1));
  const startsAtBoundary = start === 0 || /\s/.test(value.charAt(start - 1)) || startsWithTerminalPunctuation;
  const endsAtBoundary = end === value.length || /\s/.test(value.charAt(end));
  let before = value.slice(0, start).trim();
  let selected = value.slice(start, end);
  const after = value.slice(end).trim();
  if (startsWithTerminalPunctuation && before) {
    before = `${before}${selected.charAt(0)}`;
    selected = selected.slice(1).trimStart();
  }
  if (!selected || !startsAtBoundary || !endsAtBoundary) {
    setReviewStatus("GUI_REVIEW_SELECTION_REQUIRED: Select one or more complete words or a sentence before separating it.");
    text.focus();
    return;
  }
  const replacement = [];
  if (before) replacement.push({speaker_id: block.speaker_id, text: before});
  replacement.push({speaker_id: block.speaker_id, text: selected});
  if (after) replacement.push({speaker_id: block.speaker_id, text: after});
  const selectedIndex = blockIndex + (before ? 1 : 0);
  try {
    const savedBeforeSeparate = reviewDirty;
    if (savedBeforeSeparate) await saveReviewDraft();
    const currentAnchor = reviewDocument?.anchors?.[anchorIndex];
    if (!currentAnchor?.blocks?.[blockIndex]) {
      throw new Error("GUI_REVIEW_STRUCTURE_INVALID: The selected review block changed before separation.");
    }
    currentAnchor.blocks.splice(blockIndex, 1, ...replacement);
    markReviewDirty();
    renderReview(reviewDocument, true);
    reviewSectionIndex = anchorIndex;
    updateReviewSections();
    [...document.querySelectorAll(".review-anchor")][anchorIndex]
      ?.querySelectorAll("select")[selectedIndex]
      ?.focus();
    setReviewStatus(
      savedBeforeSeparate
        ? "Draft saved before separation. Selected text isolated; choose its speaker, then save again."
        : "Selected text isolated. Choose its speaker, then save the draft.",
    );
  } catch (error) {
    setReviewStatus(error.message);
  }
}

arrangeReviewControls();
new MutationObserver(() => {
  if (!reviewDocument) return;
  if (reviewHistoryIndex < 0) resetReviewHistory();
  else scheduleReviewHistoryRecord();
}).observe(document.querySelector("#review-editor"), {childList: true});
document.querySelector("#review-editor").addEventListener("input", scheduleReviewHistoryRecord);
document.querySelector("#review-editor").addEventListener("change", scheduleReviewHistoryRecord);
document
  .querySelector("#review-speaker-labels")
  .addEventListener("input", scheduleReviewHistoryRecord);
document
  .querySelector("#review-speaker-labels")
  .addEventListener("click", scheduleReviewHistoryRecord);
document.querySelector("#clear-review").addEventListener("click", () => {
  if (!reviewDocument) resetReviewHistory();
});
