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
    const row = window.document.createElement("div");
    row.className = "review-speaker-label-row";
    const label = window.document.createElement("label");
    label.textContent = `${speakerId} display name`;
    const input = window.document.createElement("input");
    input.type = "text";
    input.value = document.speaker_labels?.[speakerId] || speakerId;
    input.dataset.speakerId = speakerId;
    input.autocomplete = "off";
    label.append(input);
    row.append(label);
    if (!document.canonical_speakers?.includes(speakerId)) {
      const remove = window.document.createElement("button");
      remove.type = "button";
      remove.className = "review-remove-speaker";
      remove.textContent = `Remove ${speakerId}`;
      remove.title = "Remove this unused revision-only speaker from the current draft.";
      remove.addEventListener("click", async () => {
        if (!reviewDocument) return;
        const inUse = reviewDocument.anchors.some(anchor =>
          anchor.blocks.some(block => block.speaker_id === speakerId),
        );
        if (inUse) {
          setReviewStatus(
            `GUI_REVIEW_SPEAKER_IN_USE: Reassign or merge every ${speakerId} block before removing it.`,
          );
          return;
        }
        try {
          const savedBeforeRemove = reviewDirty;
          if (savedBeforeRemove) await saveReviewDraft();
          reviewDocument.speakers = reviewDocument.speakers.filter(id => id !== speakerId);
          delete reviewDocument.speaker_labels[speakerId];
          markReviewDirty();
          renderReview(reviewDocument, true);
          setReviewStatus(
            savedBeforeRemove
              ? `Draft saved before removing ${speakerId}. Save again when the current review is ready.`
              : `${speakerId} removed from this revision-only speaker list. Save the draft when ready.`,
          );
        } catch (error) {
          setReviewStatus(error.message);
        }
      });
      row.append(remove);
    }
    container.append(row);
  }
  const add = window.document.createElement("button");
  add.type = "button";
  add.className = "review-add-speaker";
  add.textContent = "Add revision-only speaker";
  add.title = "Add a speaker available only in this editable review and its descendant revision.";
  add.addEventListener("click", async () => {
    if (!reviewDocument) return;
    try {
      const savedBeforeAdd = reviewDirty;
      if (savedBeforeAdd) await saveReviewDraft();
      const speakerId = nextRevisionSpeakerId(reviewDocument.speakers);
      const number = Number(speakerId.slice("speaker_".length));
      reviewDocument.speakers = [...reviewDocument.speakers, speakerId];
      reviewDocument.speaker_labels[speakerId] = `Speaker ${number}`;
      markReviewDirty();
      renderReview(reviewDocument, true);
      setReviewStatus(
        savedBeforeAdd
          ? `Draft saved before adding ${speakerId}. Rename it if needed, assign it to isolated text, then save again.`
          : `${speakerId} added for this revision only. Rename it if needed, then assign it to isolated text and save the draft.`,
      );
    } catch (error) {
      setReviewStatus(error.message);
    }
  });
  container.append(add);
  panel.hidden = document.speakers.length === 0;
}
