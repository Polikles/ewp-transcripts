"use strict";

const projectPanel = document.createElement("details");
projectPanel.id = "gui-projects";
projectPanel.innerHTML = `<summary>Projects and locations</summary>
  <p class="field-hint">Recent projects and named directories are references. Removing an entry never deletes recordings or results. Imported paths are checked on this computer.</p>
  <label>Project name (optional)<input id="project-name" maxlength="100"></label>
  <button type="button" id="project-remember">Remember current project</button>
  <div id="project-recent"></div>
  <h3>Named locations</h3>
  <label>Location name<input id="location-name" maxlength="80"></label>
  <label>Location type<select id="location-kind"><option value="input">Input directory</option><option value="output">Output directory</option></select></label>
  <label>Directory path<input id="location-path" autocomplete="off"></label>
  <button type="button" id="location-save">Save location</button><div id="location-list"></div>
  <h3>Find saved canonical results</h3>
  <p class="field-hint">Scan only the chosen directory, up to 500 entries. Select results to add to review queues; no transcription starts.</p>
  <label>Canonical result directory<input id="project-scan-path" autocomplete="off"></label>
  <div class="actions"><button type="button" id="project-scan">Find saved results</button>
    <button type="button" id="project-scan-add" disabled>Add selected results to queues</button></div>
  <div id="project-scan-results"></div><p id="project-status" role="status"></p>`;
workspaceSection.append(projectPanel);
const projectStatus = document.querySelector("#project-status");
let scannedProjectResults = [];
function setProjectField(id, value) {
  if (id === "input-path") { selectedGuiAudio.length = 0; activeGuiAudio = null; guiBatchPlan = []; renderGuiAudioChoices(); }
  const element = document.getElementById(id);
  element.value = value; element.dispatchEvent(new Event("input", {bubbles:true}));
  element.dispatchEvent(new Event("change", {bubbles:true}));
}
function projectAction(label, action) {
  const button = document.createElement("button"); button.type = "button"; button.textContent = label;
  button.addEventListener("click", async () => {
    button.disabled = true;
    try { await action(); } catch (error) { projectStatus.textContent = error.message; }
    finally { button.disabled = false; }
  });
  return button;
}
async function refreshProjectCatalog() {
  if (!csrfToken) return;
  const payload = await queuePost("/api/v1/projects/list", {}, {quiet:true});
  const recent = document.querySelector("#project-recent"); recent.replaceChildren();
  for (const item of payload.recent) {
    const row = document.createElement("div"); row.className = "library-item";
    const text = document.createElement("span"); text.textContent = `${item.name} · ${shortName(item.result_path) || item.output_root}`;
    row.append(text);
    const open = projectAction("Open project", async () => {
      await preserveActiveReviewBeforeSwitch();
      setProjectField("output-path", item.output_root);
      document.querySelector("#project-name").value = item.name;
      if (item.result_path) {
        await openManualReviewForResult(item.result_path, item.output_root);
        showGuiStage("review");
      } else showGuiStage("workspace");
    });
    open.disabled = !item.available;
    row.append(open, projectAction("Remove from list", async () => {
      await queuePost("/api/v1/projects/forget", {id:item.id}); await refreshProjectCatalog();
    }));
    if (!item.available) { const hint=document.createElement("small"); hint.textContent="Paths unavailable"; row.append(hint); }
    recent.append(row);
  }
  const locations = document.querySelector("#location-list"); locations.replaceChildren();
  for (const item of payload.locations) {
    const row = document.createElement("div"); row.className = "library-item";
    const text = document.createElement("span"); text.textContent = `${item.name} · ${item.path}`;
    row.append(text, projectAction("Use location", async () => {
      if (item.kind === "output") await preserveActiveReviewBeforeSwitch();
      setProjectField(item.kind === "input" ? "input-path" : "output-path", item.path);
      showGuiStage("workspace");
    }), projectAction("Remove from list", async () => {
      await queuePost("/api/v1/projects/location", {...item, remove:true}); await refreshProjectCatalog();
    }));
    locations.append(row);
  }
}
async function rememberCurrentProject() {
  await queuePost("/api/v1/projects/remember", {
    output_root:workflowOutput.value, result_path:reviewDocument?.result_path || "",
    name:document.querySelector("#project-name").value,
  });
  await refreshProjectCatalog();
}
document.querySelector("#project-remember").addEventListener("click", async () => {
  try { await rememberCurrentProject(); projectStatus.textContent="Project reference saved."; }
  catch (error) { projectStatus.textContent=error.message; }
});
document.querySelector("#location-save").addEventListener("click", async () => {
  try {
    await queuePost("/api/v1/projects/location", {name:document.querySelector("#location-name").value,
      kind:document.querySelector("#location-kind").value, path:document.querySelector("#location-path").value});
    await refreshProjectCatalog(); projectStatus.textContent="Location saved.";
  } catch (error) { projectStatus.textContent=error.message; }
});
document.querySelector("#project-scan").addEventListener("click", async event => {
  const button=event.currentTarget; button.disabled=true; projectStatus.textContent="Scanning saved results…";
  scannedProjectResults=[]; document.querySelector("#project-scan-add").disabled=true;
  const host=document.querySelector("#project-scan-results"); host.replaceChildren();
  try {
    const payload=await queuePost("/api/v1/projects/scan", {directory:document.querySelector("#project-scan-path").value}, {trigger:button});
    scannedProjectResults=payload.items;
    for (const [index,item] of payload.items.entries()) {
      const label=document.createElement("label"); label.className="confirmation";
      const check=document.createElement("input"); check.type="checkbox"; check.value=String(index);
      check.addEventListener("change",()=>{document.querySelector("#project-scan-add").disabled=!host.querySelector("input:checked");});
      label.append(check, ` ${item.job_id} · ${shortName(item.path)} · ${item.language}`); host.append(label);
    }
    const label=document.createElement("span"); label.textContent="Canonical results found:";
    projectStatus.replaceChildren(label, ` ${payload.items.length}`);
    if (payload.truncated) { const note=document.createElement("span"); note.textContent="Scan limit reached; choose a smaller directory."; projectStatus.append(" · ",note); }
  } catch (error) { projectStatus.textContent=error.message; }
  finally { button.disabled=false; }
});
document.querySelector("#project-scan-path").addEventListener("input",()=>{
  scannedProjectResults=[]; document.querySelector("#project-scan-add").disabled=true;
  document.querySelector("#project-scan-results").replaceChildren();
});
document.querySelector("#project-scan-add").addEventListener("click", async event => {
  const button=event.currentTarget; button.disabled=true;
  try {
    const items=[...document.querySelectorAll("#project-scan-results input:checked")].map(input=>scannedProjectResults[Number(input.value)]);
    await queuePost("/api/v1/projects/import-results", {items, output_root:workflowOutput.value}, {trigger:button});
    await refreshJobs(); projectStatus.textContent="Selected results added to review queues.";
  } catch(error) { projectStatus.textContent=error.message; }
  finally { button.disabled=false; }
});
const rememberSessionBeforeProjects = rememberReviewSession;
rememberReviewSession = async function(...args) {
  const payload = await rememberSessionBeforeProjects(...args);
  if (reviewDocument && reviewValue("project_output_directory")) {
    try {
      await queuePost("/api/v1/projects/remember", {output_root:reviewValue("project_output_directory"), result_path:reviewDocument.result_path});
      await refreshProjectCatalog();
    } catch(error) { projectStatus.textContent=error.message; }
  }
  return payload;
};
if (csrfToken) void refreshProjectCatalog().catch(error=>{projectStatus.textContent=error.message;});
else document.addEventListener("ewp-session-ready",()=>{void refreshProjectCatalog().catch(error=>{projectStatus.textContent=error.message;});},{once:true});
