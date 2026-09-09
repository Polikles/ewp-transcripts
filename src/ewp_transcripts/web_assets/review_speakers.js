"use strict";

function reviewSpeakerNamesPanel() {
  const existing = window.document.querySelector("#review-speaker-names");
  if (existing instanceof HTMLDetailsElement) return existing;

  const panel = window.document.createElement("details");
  panel.id = existing.id;
  panel.hidden = existing.hidden;
  const summary = window.document.createElement("summary");
  summary.textContent = "Speaker names for this revision";
  const hint = existing.querySelector(".field-hint");
  const labels = existing.querySelector("#review-speaker-labels");
  panel.append(summary);
  if (hint) panel.append(hint);
  if (labels) panel.append(labels);
  existing.replaceWith(panel);
  return panel;
}

function nextRevisionSpeakerId(speakers) {
  const highest = speakers.reduce((current, speakerId) => {
    const match = /^speaker_(\d{3,})$/.exec(speakerId);
    return match ? Math.max(current, Number(match[1])) : current;
  }, 0);
  return `speaker_${String(highest + 1).padStart(3, "0")}`;
}

function renderReviewSpeakerLabels(document) {
  const panel = reviewSpeakerNamesPanel();
  const container = window.document.querySelector("#review-speaker-labels");
  container.replaceChildren();
  for (const speakerId of document.speakers) {
    const label = window.document.createElement("label");
    label.textContent = `${speakerId} display name`;
    const input = window.document.createElement("input");
    input.type = "text";
    input.value = document.speaker_labels?.[speakerId] || speakerId;
    input.dataset.speakerId = speakerId;
    input.autocomplete = "off";
    label.append(input);
    container.append(label);
  }
  const add = window.document.createElement("button");
  add.type = "button";
  add.className = "review-add-speaker";
  add.textContent = "Add revision-only speaker";
  add.title = "Add a speaker available only in this editable review and its descendant revision.";
  add.addEventListener("click", () => {
    if (!reviewDocument) return;
    const speakerId = nextRevisionSpeakerId(reviewDocument.speakers);
    const number = Number(speakerId.slice("speaker_".length));
    reviewDocument.speakers = [...reviewDocument.speakers, speakerId];
    reviewDocument.speaker_labels[speakerId] = `Speaker ${number}`;
    markReviewDirty();
    renderReview(reviewDocument, true);
    setReviewStatus(
      `${speakerId} added for this revision only. Rename it if needed, then assign it to isolated text and save the draft.`,
    );
  });
  container.append(add);
  panel.hidden = document.speakers.length === 0;
}
