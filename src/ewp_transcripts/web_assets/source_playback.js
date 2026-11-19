"use strict";

const sourcePlaybackState = new Map();
let sourcePlaybackKey = "";
let sourcePlaybackRequest = 0;
let sourcePlaybackSeekRequest = 0;
let sourcePlaybackPromise = null;
const sourcePlayback = document.createElement("section");
sourcePlayback.id = "gui-source-playback"; sourcePlayback.hidden = true;
const playbackHeading = document.createElement("h2"); playbackHeading.textContent = "Recording audio";
const playbackSourceLabel = document.createElement("label"); playbackSourceLabel.textContent = "Audio source";
const playbackSource = document.createElement("select"); playbackSource.id = "gui-playback-source";
playbackSourceLabel.append(playbackSource);
const playbackAudio = document.createElement("audio"); playbackAudio.id = "gui-playback-audio";
playbackAudio.controls = true; playbackAudio.preload = "metadata";
playbackAudio.setAttribute("aria-label", "Recording audio");
const playbackRetry = document.createElement("button"); playbackRetry.type = "button";
playbackRetry.textContent = "Reload recording audio";
const playbackStatus = document.createElement("p"); playbackStatus.id = "gui-playback-status";
playbackStatus.className = "field-hint"; playbackStatus.setAttribute("role", "status");
sourcePlayback.append(playbackHeading, playbackSourceLabel, playbackAudio, playbackRetry, playbackStatus);
document.querySelector("#gui-recordings").after(sourcePlayback);

function rememberPlaybackPosition() {
  if (!sourcePlaybackKey || !playbackAudio.getAttribute("src")) return;
  sourcePlaybackState.set(sourcePlaybackKey, {source:playbackSource.value, time:Number.isFinite(playbackAudio.currentTime) ? playbackAudio.currentTime : 0});
}
playbackAudio.addEventListener("timeupdate", rememberPlaybackPosition);
playbackAudio.addEventListener("error", () => {
  if (playbackAudio.getAttribute("src")) playbackStatus.textContent = "Audio playback is unavailable. Restore the original recording and reload audio.";
});
async function prepareSourcePlayback() {
  const key = sourcePlaybackKey, source = playbackSource.value, request = ++sourcePlaybackRequest;
  if (!key || !source) return;
  playbackAudio.pause(); playbackAudio.removeAttribute("src"); playbackAudio.load();
  playbackStatus.textContent = "Preparing recording audio…";
  playbackRetry.disabled = true;
  setGuiWorking(true, playbackRetry);
  try {
    const payload = await postReview("playback", {result_path:key, source_id:source});
    if (request !== sourcePlaybackRequest || key !== sourcePlaybackKey || guiActiveStage !== "review") return;
    const saved = sourcePlaybackState.get(key);
    playbackAudio.src = payload.url;
    playbackAudio.addEventListener("loadedmetadata", () => {
      if (request === sourcePlaybackRequest && saved?.source === source) playbackAudio.currentTime = Math.min(saved.time, playbackAudio.duration || saved.time);
    }, {once:true});
    playbackAudio.load();
    playbackStatus.textContent = "Audio ready. Use Go to this fragment to listen while reviewing.";
  } catch (error) {
    if (request === sourcePlaybackRequest && key === sourcePlaybackKey) playbackStatus.textContent = error.message;
  } finally { if (request === sourcePlaybackRequest) playbackRetry.disabled = false; setGuiWorking(false, playbackRetry); }
}
function requestSourcePlayback() {
  sourcePlaybackPromise = prepareSourcePlayback();
  return sourcePlaybackPromise;
}
playbackRetry.addEventListener("click", () => { void requestSourcePlayback(); });
playbackSource.addEventListener("change", () => {
  sourcePlaybackState.set(sourcePlaybackKey, {source:playbackSource.value, time:0});
  void requestSourcePlayback();
});
function syncSourcePlayback() {
  const key = guiActiveStage === "review" ? reviewDocument?.result_path || "" : "";
  sourcePlayback.hidden = !key;
  if (key === sourcePlaybackKey) return;
  rememberPlaybackPosition();
  sourcePlaybackRequest += 1; playbackAudio.pause(); playbackAudio.removeAttribute("src"); playbackAudio.load();
  sourcePlaybackKey = key;
  playbackSource.replaceChildren();
  if (!key) return;
  const saved = sourcePlaybackState.get(key);
  for (const source of reviewDocument.playback_sources || []) {
    const option = document.createElement("option"); option.value = source.source_id;
    option.textContent = `${source.filename}${source.speaker_label ? ` · ${source.speaker_label}` : ""}${Number.isInteger(source.channel_selection) ? ` · ch ${source.channel_selection + 1}` : ""}`;
    option.dataset.guiContent = "true";
    playbackSource.append(option);
  }
  if ([...playbackSource.options].some(option=>option.value === saved?.source)) playbackSource.value = saved.source;
  playbackSourceLabel.hidden = playbackSource.options.length < 2;
  void requestSourcePlayback();
}
async function seekReviewBlock(button) {
  const key = reviewDocument?.result_path;
  if (!key) return;
  const seekRequest = ++sourcePlaybackSeekRequest;
  const {anchorIndex, blockIndex} = reviewBlockPosition(button);
  button.disabled = true; setGuiWorking(true, button);
  try {
    if (reviewDirty) await saveReviewDraft();
    if (reviewDocument?.result_path !== key || seekRequest !== sourcePlaybackSeekRequest) return;
    const position = await postReview("playback-position", {result_path:key, review_path:reviewDocument.review_path, review_sha256:reviewDocument.review_sha256, anchor_index:anchorIndex, block_index:blockIndex});
    syncSourcePlayback();
    await sourcePlaybackPromise;
    if (sourcePlaybackKey !== key || seekRequest !== sourcePlaybackSeekRequest || !playbackAudio.getAttribute("src")) return;
    const request = sourcePlaybackRequest;
    const seek = () => {
      if (sourcePlaybackKey !== key || request !== sourcePlaybackRequest || seekRequest !== sourcePlaybackSeekRequest || guiActiveStage !== "review") return;
      playbackAudio.currentTime = position.start_ms / 1000;
      playbackStatus.textContent = position.approximate ? "Playing from the nearest known source timestamp; edited text has no exact audio boundary." : "Playing from this fragment's source timestamp.";
      void playbackAudio.play().catch(() => { playbackStatus.textContent = "Press Play in the recording audio player."; });
    };
    if (playbackAudio.readyState >= 1) seek();
    else playbackAudio.addEventListener("loadedmetadata", seek, {once:true});
  } catch (error) { playbackStatus.textContent = error.message; }
  finally { button.disabled = false; setGuiWorking(false, button); }
}
function installReviewSeekButtons() {
  document.querySelectorAll("#review-editor .review-block").forEach(row => {
    if (row.querySelector(".review-seek")) return;
    const speaker = row.querySelector("label");
    const button = document.createElement("button"); button.type = "button";
    button.className = "review-seek"; button.textContent = "Go to this fragment";
    button.addEventListener("click", () => { void seekReviewBlock(button); });
    speaker.after(button);
  });
  syncSourcePlayback();
}
new MutationObserver(installReviewSeekButtons).observe(document.querySelector("#review-editor"), {childList:true, subtree:true});
document.addEventListener("ewp-stage", syncSourcePlayback);
installReviewSeekButtons();
