/* Readable transcript-review editor sizing and local navigation controls. */

function resizeTranscriptReviewTextarea(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.max(textarea.scrollHeight, 96)}px`;
}

function resizeTranscriptReviewTextareas() {
  document.querySelectorAll("#review-editor textarea").forEach(resizeTranscriptReviewTextarea);
}

function addBottomReviewNavigation() {
  const editor = document.querySelector("#review-editor");
  const bottom = document.createElement("div");
  bottom.id = "review-bottom-navigation";
  bottom.className = "review-bottom-navigation actions";
  bottom.hidden = true;
  const previous = document.createElement("button");
  previous.type = "button";
  previous.textContent = "Previous section";
  const position = document.createElement("span");
  position.id = "review-bottom-position";
  const next = document.createElement("button");
  next.type = "button";
  next.textContent = "Next section";
  previous.addEventListener("click", () => {
    reviewSectionIndex -= 1;
    updateReviewSections();
  });
  next.addEventListener("click", () => {
    reviewSectionIndex += 1;
    updateReviewSections();
  });
  bottom.append(previous, position, next);
  editor.after(bottom);
  return {bottom, previous, position, next};
}

const bottomReviewNavigation = addBottomReviewNavigation();

function syncBottomReviewNavigation() {
  const primary = document.querySelector("#review-navigation");
  const previous = document.querySelector("#previous-review-section");
  const next = document.querySelector("#next-review-section");
  const position = document.querySelector("#review-position");
  bottomReviewNavigation.bottom.hidden = primary.hidden;
  bottomReviewNavigation.previous.disabled = previous.disabled;
  bottomReviewNavigation.next.disabled = next.disabled;
  bottomReviewNavigation.position.textContent = position.textContent;
}

document.querySelector("#review-editor").addEventListener("input", event => {
  if (event.target instanceof HTMLTextAreaElement) resizeTranscriptReviewTextarea(event.target);
});
new MutationObserver(() => {
  resizeTranscriptReviewTextareas();
  syncBottomReviewNavigation();
}).observe(document.querySelector("#review-editor"), {childList: true, subtree: true});
new MutationObserver(syncBottomReviewNavigation).observe(document.querySelector("#review-navigation"), {
  attributes: true,
  childList: true,
  subtree: true,
});
resizeTranscriptReviewTextareas();
syncBottomReviewNavigation();
