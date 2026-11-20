"use strict";

const runtimeClocks = new Map();
function runtimeClock(seconds) { return `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,"0")}`; }
setInterval(() => {
  for (const [id, clock] of runtimeClocks) {
    if (!clock.element.isConnected) { runtimeClocks.delete(id); continue; }
    const next = clock.base + Math.min(3, Math.floor((performance.now() - clock.received) / 1000));
    if (next > clock.shown) { clock.shown = next; clock.element.textContent = ` ${runtimeClock(clock.shown)}`; }
  }
}, 250);
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
  const clock = runtimeClock;
  const elapsed = document.createElement("div"); elapsed.className = "gui-runtime-elapsed";
  const elapsedLabel = document.createElement("span"); elapsedLabel.textContent = "Elapsed";
  const time = document.createElement("span"); time.dataset.guiContent = "true"; time.textContent = ` ${clock(snapshot.elapsed_seconds)}`;
  elapsed.append(elapsedLabel,time); host.append(elapsed);
  if (job.status === "running") {
    const shown = Math.max(snapshot.elapsed_seconds, runtimeClocks.get(job.job_id)?.shown || 0);
    runtimeClocks.set(job.job_id, {element:time, base:snapshot.elapsed_seconds, received:performance.now(), shown});
    time.textContent = ` ${clock(shown)}`;
  } else runtimeClocks.delete(job.job_id);
  if (job.status === "running" && guiPreferences.showEta === true) {
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
