/* Readable transcript-review editor sizing and local navigation controls. */

function resizeTranscriptReviewTextarea(textarea) {
  if (!textarea.getClientRects().length) return;
  textarea.style.height = "auto";
  const border = textarea.offsetHeight - textarea.clientHeight;
  textarea.style.height = `${Math.max(textarea.scrollHeight + border, 56)}px`;
}

function resizeTranscriptReviewTextareas() {
  document.querySelectorAll("#review-editor textarea, #translation-review-editor textarea").forEach(resizeTranscriptReviewTextarea);
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
new MutationObserver(() => {
  window.requestAnimationFrame(resizeTranscriptReviewTextareas);
}).observe(document.querySelector("#review-editor"), {
  attributes: true,
  attributeFilter: ["hidden"],
  subtree: true,
});
new MutationObserver(syncBottomReviewNavigation).observe(document.querySelector("#review-navigation"), {
  attributes: true,
  childList: true,
  subtree: true,
});
resizeTranscriptReviewTextareas();
syncBottomReviewNavigation();

let reviewResizeScheduled = false;
function scheduleTranscriptReviewResize() {
  if (reviewResizeScheduled) return;
  reviewResizeScheduled = true;
  requestAnimationFrame(() => {
    reviewResizeScheduled = false;
    resizeTranscriptReviewTextareas();
  });
}
const reviewSizeObserver = new ResizeObserver(scheduleTranscriptReviewResize);
reviewSizeObserver.observe(document.querySelector("#review-editor"));
reviewSizeObserver.observe(document.querySelector("#translation-review-editor"));
window.addEventListener("resize", scheduleTranscriptReviewResize);
document.addEventListener("ewp-stage", scheduleTranscriptReviewResize);
document.fonts.ready.then(scheduleTranscriptReviewResize);

const reviewSectionGuidance = document.createElement("p");
reviewSectionGuidance.className = "field-hint";
reviewSectionGuidance.textContent = "Sections make correction easier. Check speaker assignments carefully. Splitting a speaker block here does not determine subtitle line breaks.";
document.querySelector("#review-navigation").after(reviewSectionGuidance);
const reviewSentenceWarning = document.createElement("p");
reviewSentenceWarning.id = "review-sentence-warning"; reviewSentenceWarning.className = "review-sentence-warning";
reviewSentenceWarning.setAttribute("role", "note"); reviewSentenceWarning.hidden = true;
reviewSentenceWarning.textContent = "ASR sentence boundaries appear incomplete. Text may be divided incorrectly; pay extra attention to punctuation and speaker assignments during correction.";
reviewSectionGuidance.after(reviewSentenceWarning);
const reviewSpeakerContinuityWarning = document.createElement("p");
reviewSpeakerContinuityWarning.id = "review-speaker-continuity-warning";
reviewSpeakerContinuityWarning.className = "review-sentence-warning";
reviewSpeakerContinuityWarning.setAttribute("role", "note");
reviewSpeakerContinuityWarning.hidden = true;
reviewSpeakerContinuityWarning.textContent = "Some cloud chunks could not be matched to earlier speakers. Check and correct speaker assignments across sections.";
reviewSentenceWarning.after(reviewSpeakerContinuityWarning);
function syncReviewSentenceWarning() {
  reviewSpeakerContinuityWarning.hidden = !reviewDocument?.speaker_continuity_warning;
  reviewSectionGuidance.hidden = !reviewDocument;
  reviewSentenceWarning.hidden = !reviewDocument?.sentence_boundary_warning;
}
new MutationObserver(syncReviewSentenceWarning).observe(document.querySelector("#review-editor"), {childList:true});
document.addEventListener("ewp-review-metadata", syncReviewSentenceWarning);
syncReviewSentenceWarning();
