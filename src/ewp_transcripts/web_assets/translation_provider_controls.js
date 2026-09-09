/* Local/cloud provider choice for non-final automated translations. */

const translationProviderLabel = document.createElement("label");
translationProviderLabel.htmlFor = "translation-provider";
translationProviderLabel.textContent = "Provider";
const translationProvider = document.createElement("select");
translationProvider.id = "translation-provider";
translationProvider.name = "provider";
translationProvider.innerHTML = '<option value="lm-studio">LM Studio (local)</option><option value="openrouter">OpenRouter (cloud)</option>';
translationProviderLabel.append(translationProvider);
document.querySelector('label[for="translation-target"]')?.after(translationProviderLabel);

const translationCloudOptions = document.createElement("div");
translationCloudOptions.id = "translation-openrouter-options";
translationCloudOptions.hidden = true;
translationCloudOptions.innerHTML = '<label for="translation-reasoning">Reasoning-token budget</label><input id="translation-reasoning" name="reasoning_max_tokens" type="number" min="0" value="0"><p class="field-hint">OpenRouter is a cloud API. Use the session-only key control; the key is never written to a project, workspace, browser storage, or translation artifact.</p><div class="actions"><button type="button" id="translation-set-openrouter-key">Set an OpenRouter API key</button></div>';
document.querySelector('label[for="translation-endpoint"]')?.after(translationCloudOptions);
document.querySelector("#translation-set-openrouter-key").addEventListener("click", () => {
  openRouterKeyButton.click();
});

const translationModelLabel = document.querySelector('label[for="translation-model"]');
const translationEndpointLabel = document.querySelector('label[for="translation-endpoint"]');
const translationRemoteLabel = document.querySelector("#translation-allow-remote").closest("label");
const translationDisclosure = document.querySelector('#translation-workflow input[name="confirmed"]').closest("label");

function updateTranslationProviderControls() {
  const cloud = translationProvider.value === "openrouter";
  translationModelLabel.firstChild.textContent = cloud ? "Exact OpenRouter model ID" : "Exact LM Studio model ID";
  translationEndpointLabel.firstChild.textContent = cloud ? "OpenRouter API endpoint" : "LM Studio API endpoint";
  translationRemoteLabel.hidden = cloud;
  translationCloudOptions.hidden = !cloud;
  if (cloud) {
    if (!translationForm.elements.namedItem("model").value.trim() || translationForm.elements.namedItem("model").value === "bielik-11b-v3.0-instruct") {
      translationForm.elements.namedItem("model").value = "google/gemini-2.5-flash";
    }
    translationForm.elements.namedItem("endpoint").value = "https://openrouter.ai/api/v1";
    translationForm.elements.namedItem("output_mode").value = "json-schema";
    translationDisclosure.lastChild.textContent = " I understand that OpenRouter is a separately operated cloud API: transcript text leaves this application, and EWP Transcriber cannot control how the provider logs, retains, uses, or forwards it. The translation remains non-final and requires semantic manual review.";
  } else {
    translationForm.elements.namedItem("endpoint").value = "http://127.0.0.1:1234/v1";
    translationForm.elements.namedItem("output_mode").value = "plain-text";
    translationDisclosure.lastChild.textContent = " I understand that transcript text is sent to a separately operated LM Studio API whose logging, retention, or forwarding EWP Transcriber cannot control. The translation remains non-final and requires semantic manual review.";
  }
}

translationProvider.addEventListener("change", updateTranslationProviderControls);
updateTranslationProviderControls();
workspaceFieldIds.push("translation-provider", "translation-reasoning");

translationForm.addEventListener("submit", async event => {
  event.preventDefault();
  event.stopImmediatePropagation();
  const submit = document.querySelector("#generate-translation");
  const form = new FormData(translationForm);
  const root = String(form.get("output_root") || "").replace(/[\\/]+$/, "");
  const reasoning = String(form.get("reasoning_max_tokens") || "");
  const request = {
    result_path: form.get("result_path"), source_revision_path: form.get("source_revision_path"),
    output_directory: `${root}/translation-candidates`, resume_directory: `${root}/translation-state`,
    target_language: form.get("target_language"), provider: form.get("provider"), model: form.get("model"),
    endpoint: form.get("endpoint"), allow_remote_endpoint: form.get("allow_remote_endpoint") === "on",
    allow_cloud: form.get("provider") === "openrouter", reasoning_max_tokens: reasoning === "" ? null : Number(reasoning),
    output_mode: form.get("output_mode"), dictionary_path: form.get("dictionary_path"),
    confirmed: form.get("confirmed") === "on",
  };
  const status = document.querySelector("#translation-status");
  const result = document.querySelector("#translation-result");
  const summary = document.querySelector("#translation-summary");
  translationCandidate = null;
  document.querySelector("#review-translation").disabled = true;
  submit.disabled = true;
  status.textContent = "Translation is running; do not close the server.";
  result.textContent = "";
  summary.replaceChildren();
  try {
    const payload = await queuePost("/api/v1/translations/generate", request);
    translationCandidate = {...payload, revision_path: String(form.get("source_revision_path") || ""), output_root: root};
    status.textContent = payload.source_verification === "manually_verified"
      ? "Non-final translation candidate generated; semantic manual review is required."
      : `WARNING: source is ${payload.source_verification}, not manually verified. The non-final translation requires semantic manual review.`;
    result.textContent = JSON.stringify(payload, null, 2);
    const table = document.createElement("table");
    table.className = "review-summary-table";
    const dictionary = payload.dictionary ? `${payload.dictionary.dictionary_id} · ${payload.dictionary.sha256}` : "None";
    const direction = `${payload.direction.source_language} → ${payload.direction.target_language}`;
    const rows = [["Final", "No — semantic review required"], ["Candidate", shortName(payload.candidate_path)], ["Direction", direction], ["Source", payload.source_verification], ["Provider", payload.provider], ["Model", payload.model], ["Dictionary", dictionary], ["Units", payload.statistics?.unit_count || 0], ["Warnings", payload.warnings?.length || 0]];
    const body = document.createElement("tbody");
    for (const [label, value] of rows) {
      const row = document.createElement("tr");
      const heading = document.createElement("th");
      heading.scope = "row";
      heading.textContent = label;
      const cell = document.createElement("td");
      cell.textContent = String(value);
      row.append(heading, cell);
      body.append(row);
    }
    table.append(body);
    summary.append(table);
    document.querySelector("#review-translation").disabled = false;
  } catch (error) {
    status.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
}, true);
