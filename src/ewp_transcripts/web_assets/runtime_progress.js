"use strict";

function renderRuntimeProgress(job) {
  const snapshot = job.runtime_progress;
  if (!snapshot) return document.createTextNode("");
  const host = document.createElement("div"); host.className = "gui-runtime-progress";
  const labels = {inspect:"Inspecting recording", plan:"Planning outputs", prepare_audio:"Preparing audio", transcribe:"Transcribing", align:"Aligning words", normalize:"Organizing transcript", diarize:"Identifying speakers", reconcile_speakers:"Assigning speakers", compose:"Combining tracks", publish:"Saving result", export:"Exporting files", cleanup:"Finishing cleanup"};
  if (job.status === "running") {
    const phase = document.createElement("span"); phase.textContent = labels[snapshot.phase] || "Working…";
    host.append(phase);
    if (snapshot.stream_count > 1 && ["prepare_audio", "transcribe", "align", "normalize"].includes(snapshot.phase)) {
      const track = document.createElement("span"); track.dataset.guiContent = "true";
      track.textContent = ` · ${snapshot.stream_index}/${snapshot.stream_count}`; host.append(track);
    }
    const line = document.createElement("div"); line.className = "gui-runtime-bar";
    const percent = document.createElement("span"); percent.dataset.guiContent = "true";
    percent.textContent = `~${snapshot.percent}%`;
    const bar = document.createElement("progress"); bar.max = 100; bar.value = snapshot.percent;
    bar.setAttribute("aria-label", "Approximate processing progress");
    bar.title = "Approximate phase progress; percentages within a phase use earlier timings from this machine.";
    line.append(bar, percent); host.append(line);
  }
  const clock = seconds => `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,"0")}`;
  const elapsed = document.createElement("div");
  const elapsedLabel = document.createElement("span"); elapsedLabel.textContent = "Elapsed";
  const time = document.createElement("span"); time.dataset.guiContent = "true"; time.textContent = ` ${clock(snapshot.elapsed_seconds)}`;
  elapsed.append(elapsedLabel,time); host.append(elapsed);
  if (job.status === "running") {
    const eta = document.createElement("div");
    if (snapshot.eta_seconds !== null) {
      const label = document.createElement("span"); label.textContent = "ETA";
      const range = document.createElement("span"); range.dataset.guiContent = "true";
      range.textContent = ` ~${clock(snapshot.eta_min_seconds)}–${clock(snapshot.eta_max_seconds)}`;
      eta.append(label, range);
    } else eta.textContent = snapshot.overdue ? "Taking longer than estimated" : "ETA: calibrating on this machine";
    host.append(eta);
  }
  return host;
}
