"use strict";

function installGuiDictionaryLibrary() {
  const section = document.querySelector("#dictionary-heading").closest("section");
  const legacy = document.createElement("details"); legacy.id = "dictionary-corpus-proposal";
  legacy.innerHTML = "<summary>Build a proposal from reviewed recordings (optional)</summary>";
  const nodes = [...section.children].slice(2); legacy.append(...nodes); section.append(legacy);
  const panel = document.createElement("div"); panel.id = "gui-dictionary-library";
  panel.innerHTML = `
    <h3 id="gui-dictionary-step-1">1. Choose dictionary library</h3>
    <label>Dictionary catalog directory<input id="library-directory" value="dictionaries" autocomplete="off"></label>
    <div class="actions"><button type="button" id="library-refresh">Refresh dictionary list</button><button type="button" id="library-new">New dictionary</button><button type="button" id="library-import">Add dictionary file…</button><input id="library-file" type="file" accept=".json,application/json" hidden></div>
    <label class="confirmation"><input id="library-show-hidden" type="checkbox"> Show removed dictionaries</label>
    <div id="library-items"></div>
    <h3 id="gui-dictionary-step-2">2. View and compare versions</h3>
    <label>Dictionary<select id="library-select"><option value="">Choose a dictionary</option></select></label>
    <label>Compare with<select id="library-compare"><option value="">No comparison</option></select></label>
    <div class="actions"><button type="button" id="library-open">View / edit</button><button type="button" id="library-diff">Compare versions</button></div>
    <div id="library-comparison"></div>
    <h3 id="gui-dictionary-step-3">3. Edit a new version</h3>
    <label>Dictionary kind<select id="library-kind"><option value="correction">Polish correction</option><option value="translation">Translation</option></select></label>
    <label>Project ID<input id="library-project" autocomplete="off" placeholder="my-podcast"></label>
    <label>New dictionary ID<input id="library-id" autocomplete="off" placeholder="my-podcast-pl-v3"></label>
    <label>Recording scope<input id="library-scope" value="*" placeholder="* or comma-separated recording IDs"></label>
    <div id="library-direction"><label>Source language<select id="library-source"><option value="pl">Polish</option><option value="en">English</option></select></label><label>Target language<select id="library-target"><option value="en">English</option><option value="pl">Polish</option></select></label></div>
    <div id="library-entries"></div>
    <div class="actions"><button type="button" id="library-add-entry">Add entry</button><button type="button" id="library-example">Use example</button></div>
    <details id="library-advanced"><summary>Full dictionary document (JSON)</summary><textarea id="library-json" rows="8" spellcheck="false"></textarea><button type="button" id="library-use-json">Load JSON into editor</button></details>
    <h3 id="gui-dictionary-step-4">4. Save new dictionary version</h3>
    <p class="field-hint">Use a new ID when editing an existing dictionary. Previous files remain available to earlier runs. Remove hides an entry from this library; it does not delete its file.</p>
    <button type="button" id="library-save" class="primary">Save new dictionary version</button>
    <p id="library-status" role="status">Choose a dictionary or create a new one.</p>`;
  legacy.before(panel);
  let catalog = [], loaded = null, draft = null;
  const get = id => document.getElementById(`library-${id}`);
  function status(text) { get("status").textContent = text; }
  function kindChanged() { get("direction").hidden = get("kind").value !== "translation"; }
  function entryRow(entry = {}) {
    const row = document.createElement("div"); row.className = "library-entry";
    const source = document.createElement("input"); source.value = entry.source || ""; source.placeholder = "Source term"; source.setAttribute("aria-label", "Source term");
    const target = document.createElement("input"); target.value = entry.target || ""; target.placeholder = "Preferred term"; target.setAttribute("aria-label", "Preferred term");
    const decision = document.createElement("select"); decision.setAttribute("aria-label", "Entry decision"); decision.innerHTML = '<option value="approved">Approved</option><option value="rejected">Rejected</option>'; decision.value = entry.status || "approved";
    decision.hidden = get("kind").value !== "correction";
    const remove = document.createElement("button"); remove.type = "button"; remove.textContent = "Remove entry"; remove.addEventListener("click", () => row.remove());
    row.append(source, target, decision, remove); get("entries").append(row);
  }
  function nextDictionaryId(id) {
    const match = /^(.*-v)(\d+)$/.exec(id);
    const prefix = match ? match[1] : `${id}-v`;
    let number = match ? Number(match[2]) + 1 : 2;
    while (catalog.some(item => item.dictionary_id === `${prefix}${number}`)) number += 1;
    return `${prefix}${number}`;
  }
  function fill(document, identity = null, {suggest = true} = {}) {
    draft = structuredClone(document); loaded = identity;
    get("kind").value = document.source_language ? "translation" : "correction";
    get("kind").disabled = Boolean(identity);
    get("project").value = document.project_id || "";
    get("id").value = identity && suggest ? nextDictionaryId(document.dictionary_id) : document.dictionary_id || "";
    get("scope").value = (document.job_ids || ["*"]).join(", ");
    get("source").value = document.source_language || "pl"; get("target").value = document.target_language || "en";
    get("entries").replaceChildren(); (document.entries || [{}]).forEach(entryRow);
    get("json").value = JSON.stringify(document, null, 2); kindChanged();
  }
  function currentDocument() {
    const translation = get("kind").value === "translation";
    const result = {
      dictionary_version: translation ? "1.0" : "1.1", dictionary_id:get("id").value.trim(),
      project_id:get("project").value.trim(), job_ids:get("scope").value.split(",").map(item=>item.trim()).filter(Boolean),
      entries:[...get("entries").children].map(row => {
        const inputs = row.querySelectorAll("input");
        const entry = {source:inputs[0].value.trim(), target:inputs[1].value.trim()};
        if (!translation) entry.status = row.querySelector("select").value; return entry;
      }),
    };
    if (translation) { result.source_language = get("source").value; result.target_language = get("target").value; }
    else { result.language = "pl"; result.proposal_sha256 = draft?.proposal_sha256 || "0".repeat(64); result.manual_conventions = draft?.manual_conventions || []; }
    return result;
  }
  async function refresh() {
    const previous = get("select").value;
    const payload = await queuePost("/api/v1/dictionaries/catalog", {catalog_directory:get("directory").value, include_hidden:get("show-hidden").checked});
    catalog = payload.items;
    for (const name of ["select", "compare"]) {
      get(name).replaceChildren(new Option(name === "select" ? "Choose a dictionary" : "No comparison", ""));
      for (const item of catalog) get(name).append(new Option(`${item.dictionary_id} · ${item.kind}${item.hidden ? " (removed)" : ""}`, item.path));
    }
    get("select").value = previous;
    get("items").replaceChildren();
    for (const item of catalog) {
      const row = document.createElement("div"); row.className = "library-item";
      const label = document.createElement("span"); label.textContent = `${item.dictionary_id} · ${item.kind}`; label.title = item.path;
      const view = document.createElement("button"); view.type = "button"; view.textContent = "View / edit";
      view.addEventListener("click", () => { get("select").value = item.path; get("open").click(); });
      const hide = document.createElement("button"); hide.type = "button"; hide.textContent = item.hidden ? "Restore to list" : "Remove from list";
      hide.addEventListener("click", async () => {
        try { await queuePost("/api/v1/dictionaries/visibility", {path:item.path, sha256:item.sha256, visible:item.hidden}); await refresh(); status("Dictionary list updated. Published files are unchanged."); }
        catch (error) { status(error.message); }
      }); row.append(label, view, hide); get("items").append(row);
    }
    status(`${catalog.length} dictionaries in this view.`);
    document.dispatchEvent(new Event("ewp-library-changed"));
  }
  get("refresh").addEventListener("click", () => { void refresh().catch(error=>status(error.message)); });
  get("show-hidden").addEventListener("change", () => get("refresh").click());
  get("open").addEventListener("click", async () => {
    try { const payload = await queuePost("/api/v1/dictionaries/view", {path:get("select").value}); fill(payload.document, payload); status("Dictionary loaded. Save with a new ID to create an edited version."); }
    catch (error) { status(error.message); }
  });
  get("diff").addEventListener("click", async () => {
    try {
      const [left, right] = await Promise.all([get("select").value, get("compare").value].map(path => queuePost("/api/v1/dictionaries/view", {path})));
      const changes = document.createElement("table"); changes.className = "queue-table library-comparison";
      const head = changes.createTHead().insertRow();
      for (const label of ["Term / field", left.document.dictionary_id, right.document.dictionary_id]) { const cell = document.createElement("th"); cell.textContent = label; head.append(cell); }
      const maps = [left, right].map(item => new Map([
        ...["project_id", "language", "source_language", "target_language", "job_ids"].map(key => [`@${key}`, JSON.stringify(item.document[key] ?? "—")]),
        ...item.document.entries.map(entry => [entry.source, `${entry.target} (${entry.status || "approved"})`]),
        ...(item.document.manual_conventions || []).map(entry => [`Convention: ${entry.source}`, `${entry.target} — ${entry.rationale}`]),
      ]));
      const body = changes.createTBody(); let count = 0;
      for (const key of new Set([...maps[0].keys(), ...maps[1].keys()])) {
        if (maps[0].get(key) === maps[1].get(key)) continue;
        count += 1; const row = body.insertRow();
        for (const value of [key, maps[0].get(key) || "—", maps[1].get(key) || "—"]) row.insertCell().textContent = value;
      }
      get("comparison").replaceChildren(changes); status(`${count} differences. Neither dictionary was changed.`);
    } catch (error) { status(error.message); }
  });
  get("new").addEventListener("click", () => { fill({}); status("New dictionary. Enter project, version ID, scope and at least one entry."); });
  get("kind").addEventListener("change", () => { kindChanged(); get("entries").querySelectorAll("select").forEach(select=>{ select.hidden = get("kind").value !== "correction"; }); });
  get("add-entry").addEventListener("click", () => entryRow());
  get("example").addEventListener("click", () => {
    fill({dictionary_id:"example-pl-v1", project_id:"example", job_ids:["*"], entries:[{source:"example misspelling", target:"preferred spelling", status:"approved"}]});
    status("Example loaded. Replace the example project and terms before saving.");
  });
  get("advanced").addEventListener("toggle", () => { if (get("advanced").open) get("json").value = JSON.stringify(currentDocument(), null, 2); });
  get("use-json").addEventListener("click", () => {
    try { fill(JSON.parse(get("json").value), loaded, {suggest:false}); status("JSON loaded into editor. Review before saving a new version."); }
    catch (error) { status(error.message); }
  });
  get("import").addEventListener("click", () => get("file").click());
  get("file").addEventListener("change", async () => {
    const file = get("file").files?.[0]; get("file").value = ""; if (!file) return;
    try { fill(JSON.parse(await file.text())); status("Dictionary file loaded. Review its entries and Save new dictionary version to add it to this catalog."); }
    catch (error) { status(error.message); }
  });
  get("save").addEventListener("click", async () => {
    get("save").disabled = true; status("Saving new dictionary version…");
    try {
      const payload = await queuePost("/api/v1/dictionaries/edition", {document:currentDocument(), directory:get("directory").value, previous_path:loaded?.path || "", previous_sha256:loaded?.sha256 || ""});
      await refresh(); get("select").value = payload.path; fill(payload.document, payload);
      status("New dictionary version saved. Previous versions and past runs are unchanged.");
    } catch (error) { status(error.message); } finally { get("save").disabled = false; }
  });
  fill({});
}
installGuiDictionaryLibrary();
