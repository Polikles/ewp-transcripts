"use strict";

function guiBatchRequests() {
  rememberGuiAudioLanguage();
  return guiAudioEpisodes().filter(episode => !episode.files.some(file => file.staged)).map(episode => {
    const request = {path:episode.paths[0], output_directory:workflowOutput.value.trim(), language:episode.files[0].language || "pl", speaker_count:episode.files[0].speaker_count ?? 2};
    if (episode.paths.length > 1) Object.assign(request, {group_paths:[...episode.paths], group_id:episode.name});
    return {episode, request};
  });
}
function appendBatchSettings(entries) {
  const table = document.createElement("table"); table.className = "queue-table plan-table";
  table.innerHTML = "<thead><tr><th>Source files</th><th>Recording language</th><th>Speakers</th></tr></thead>";
  const body = document.createElement("tbody");
  for (const {episode, request} of entries) {
    const row = document.createElement("tr");
    for (const value of [episode.files.map(file=>file.name).join(", "), `${request.language === "auto" ? "Auto-detect" : request.language} *`, `${request.speaker_count === "auto" ? "Auto-detect" : request.speaker_count} **`]) {
      const cell = document.createElement("td"); cell.textContent = value; row.append(cell);
    }
    body.append(row);
  }
  table.append(body);
  const summary = document.querySelector("#operation-summary"), notes = summary.querySelector(".summary-selection-notes");
  if (notes) notes.before(table); else summary.append(table);
}
async function runGuiBatch(kind, trigger) {
  if (guiBatchBusy) return;
  const entries = guiBatchRequests(), signature = JSON.stringify(entries.map(item=>item.request));
  const status = document.querySelector("#operation-status"), technical = document.querySelector("#operation-result");
  const form = document.querySelector("#workflow");
  if (!entries.length) return;
  guiBatchBusy = true;
  const locked = [...form.querySelectorAll('input, select, button[type="reset"], .path-browser-button')].map(element=>[element, element.disabled]);
  locked.forEach(([element])=>{ element.disabled = true; });
  renderGuiAudioChoices(); setGuiWorking(true, trigger);
  let succeeded = false;
  try {
    if (kind === "transcriptions") {
      if (!guiBatchPlan || guiBatchPlan.signature !== signature) throw new Error("GUI_DRY_RUN_REQUIRED: Run and review dry-run for this exact input, output, language, and speaker count before adding it to the queue.");
      if (!form.elements.confirmed.checked) throw new Error("GUI_CONFIRMATION_REQUIRED: Check 'I reviewed the plan' before adding jobs to the queue.");
      const plan = guiBatchPlan; guiBatchPlan = null;
      let added = 0, skipped = 0;
      // Each item retains the server's exact plan and hash validation. A failed item
      // stops staging; successful preceding items remain visible and are never duplicated.
      for (let index = 0; index < entries.length; index += 1) {
        const {episode, request} = entries[index];
        if (plan.results[index].jobs.every(job=>job.decision === "skip")) { skipped += 1; continue; }
        const job = await queuePost("/api/v1/transcriptions", {...request, confirmed:true}, {feedback:false});
        episode.files.forEach(file => {
          const durable = episode.files.length === 1 ? job.input_path : Object.keys(job.group_sources || {}).find(path=>shortName(path) === file.name);
          if (durable) file.path = durable;
          file.staged = true;
        });
        episode.paths = episode.files.map(file=>file.path);
        added += 1;
      }
      status.textContent = `Added to staged queue: ${added}. Already completed: ${skipped}.`;
      document.querySelector("#operation-summary").replaceChildren(); technical.textContent = "";
      await refreshJobs();
    } else {
      guiBatchPlan = null; form.elements.confirmed.checked = false;
      const results = [];
      for (const {episode, request} of entries) {
        status.textContent = `${kind === "inspect" ? "Inspecting" : "Planning"} ${results.length + 1} / ${entries.length}: ${episode.name}`;
        const operation = await queuePost(`/api/v1/${kind}`, request, {feedback:false});
        if (operation.status !== "completed") throw new Error(`${operation.error?.code || "GUI_RESPONSE_INVALID"}: ${operation.error?.message || "The local service returned no result."}`);
        results.push(operation.result);
      }
      if (JSON.stringify(guiBatchRequests().map(item=>item.request)) !== signature) throw new Error("GUI_BATCH_CHANGED: Selection or settings changed during planning. Inspect and plan the current list again.");
      const combined = {episodes:results.flatMap(item=>item.episodes || []), discovery:{files:results.flatMap(item=>item.discovery?.files || []), skipped:results.flatMap(item=>item.discovery?.skipped || [])}, jobs:results.flatMap(item=>item.jobs || []), inspection:{episodes:results.flatMap(item=>item.inspection?.episodes || [])}};
      const languages = [...new Set(entries.map(item=>item.request.language))].join(", ");
      const speakers = [...new Set(entries.map(item=>item.request.speaker_count))].join(", ");
      showSummary(kind, combined, {language:languages, speaker_count:speakers}); appendBatchSettings(entries);
      technical.textContent = JSON.stringify(results, null, 2);
      status.textContent = kind === "inspect" ? "Inspection completed" : "Dry-run completed";
      if (kind === "dry-run") {
        guiBatchPlan = {signature, results};
        document.querySelector('#workflow button[value="dry-run"]').classList.remove("next-required");
      }
    }
    succeeded = true;
  } catch (error) {
    if (!error.message.startsWith("GUI_CONFIRMATION_REQUIRED")) guiBatchPlan = null;
    status.textContent = error.message;
    if (error.message.startsWith("GUI_DRY_RUN_REQUIRED")) highlightDryRun();
    if (kind === "transcriptions") await refreshJobs();
  } finally {
    form.elements.confirmed.checked = false;
    locked.forEach(([element, disabled])=>{ element.disabled = disabled; });
    guiBatchBusy = false; renderGuiAudioChoices(); setGuiWorking(false, trigger, succeeded);
  }
}
