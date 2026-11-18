"use strict";

let guiWorkflowGuides = null;
const guiWorkflowTargets = {};

function workflowStepLabel(stage, number) {
  const step = guiWorkflowGuides[stage].steps[number - 1];
  const label = `${number}. ${step.title.en}`;
  guiPolish.set(label, `${number}. ${step.title.pl}`);
  return label;
}

function markWorkflowStep(stage, number, target, {rename = false} = {}) {
  if (!target) return;
  const id = `gui-${stage}-step-${number}`;
  const label = workflowStepLabel(stage, number);
  if (rename) {
    const count = target.querySelector(".stage-queue-summary");
    target.textContent = label;
    if (count) target.append(count);
    target.id = id;
  } else {
    const heading = document.createElement("h3");
    heading.id = id; heading.className = "gui-workflow-step"; heading.textContent = label;
    const host = target.closest(".feedback-anchor") || target;
    host.before(heading);
  }
  (guiWorkflowTargets[stage] ||= {})[number] = id;
}

function installOptionalDictionaryDetails(selector) {
  const input = document.querySelector(selector), picker = input.previousElementSibling;
  const label = document.querySelector(`label[for="${input.id}"]`);
  const hint = input.nextElementSibling;
  const details = document.createElement("details"); details.className = "gui-optional-dictionary";
  const summary = document.createElement("summary"); summary.textContent = label.textContent;
  label.before(details); details.append(summary, picker, label, input);
  if (hint?.classList.contains("field-hint")) details.append(hint);
}

function numberWorkflowSections() {
  for (const stage of ["correction", "review", "translation", "semantic-review"]) {
    const heading = document.querySelector(`#stage-queue-${stage}-heading`);
    // Keep queue count labels and the existing aria-labelledby identity intact.
    const id = heading.id;
    markWorkflowStep(stage, 1, heading, {rename:true});
    heading.id = id;
    guiWorkflowTargets[stage][1] = id;
  }
  const form = document.querySelector("#workflow");
  markWorkflowStep("workspace", 1, form);
  const inspectActions = form.querySelector(".actions");
  markWorkflowStep("workspace", 2, inspectActions);
  const confirmation = form.querySelector('input[name="confirmed"]').closest("label");
  const planActions = document.createElement("div"); planActions.className = "actions";
  planActions.append(form.querySelector('button[value="dry-run"]'));
  confirmation.before(planActions);
  markWorkflowStep("workspace", 3, planActions);
  markWorkflowStep("workspace", 4, document.querySelector("#queue-scroll-hint").previousElementSibling, {rename:true});

  markWorkflowStep("review", 2, document.querySelector("#review-speaker-names summary, #review-speaker-names legend"), {rename:true});
  markWorkflowStep("review", 3, document.querySelector("#review-navigation"));
  markWorkflowStep("review", 4, document.querySelector(".review-control-groups"));
  markWorkflowStep("review", 5, document.querySelector('#review-workflow .formats legend'), {rename:true});

  markWorkflowStep("correction", 2, correctionForm);
  markWorkflowStep("correction", 3, document.querySelector("#generate-correction"));
  markWorkflowStep("correction", 4, document.querySelector("#correction-status").closest(".status-panel"));

  const direction = document.querySelector("#gui-translation-directions");
  markWorkflowStep("translation", 2, direction);
  markWorkflowStep("translation", 3, translationForm);
  document.querySelector("#stage-queue-translation").after(skipTranslation.closest(".feedback-anchor") || skipTranslation);
  installOptionalDictionaryDetails("#correction-dictionary");
  installOptionalDictionaryDetails("#translation-dictionary");
  const translationInputs = document.createElement("details"); translationInputs.id = "gui-translation-inputs";
  translationInputs.open = !translationForm.elements.namedItem("result_path").value;
  translationInputs.innerHTML = "<summary>Source and target details</summary>";
  const end = document.querySelector("#translation-target");
  for (const node of [...translationForm.children]) {
    translationInputs.append(node);
    if (node === end) break;
  }
  translationForm.prepend(translationInputs);
  refreshGuiTranslationDirection();
  const clearTranslation = document.querySelector("#clear-translation-review");
  const clearLine = document.createElement("div"); clearLine.className = "translation-clear-line";
  const clearHost = clearTranslation.closest(".feedback-anchor") || clearTranslation;
  document.querySelector("#save-translation-review").closest(".actions").after(clearLine);
  clearLine.append(clearHost);
  document.querySelector("#apply-translation-review").title = "Preview the saved draft, then confirm that you verified meaning and speaker attribution before applying an immutable translation.";
  document.querySelector("#export-translation-review").title = "Apply the verified translation first. Audit checks its source lineage before generating the selected subtitle formats.";
  markWorkflowStep("translation", 4, document.querySelector("#translation-status").closest(".status-panel"));
  markWorkflowStep("semantic-review", 2, document.querySelector("#translation-review-editor"));
  markWorkflowStep("semantic-review", 3, document.querySelector("#save-translation-review").closest(".actions"));
  markWorkflowStep("semantic-review", 4, document.querySelector("#translation-review-confirmed").closest("label"));
  markWorkflowStep("semantic-review", 5, document.querySelector('input[name="translation-format"]').closest("fieldset").querySelector("legend"), {rename:true});

  for (let number = 1; number <= 4; number++) {
    const heading = document.querySelector(`#gui-dictionary-step-${number}`);
    markWorkflowStep("dictionary", number, heading, {rename:true});
  }
  markWorkflowStep("saved", 1, document.querySelector('label[for="workspace-directory"]'));
  markWorkflowStep("saved", 2, document.querySelector('label[for="workspace-name"]'));
  markWorkflowStep("saved", 3, document.querySelector('label[for="workspace-list"]'));
  markWorkflowStep("saved", 4, document.querySelector("#managed-sources summary"), {rename:true});
  document.querySelector("#dependency-repair").before(document.querySelector("#doctor-status"), document.querySelector("#doctor-details"));
  markWorkflowStep("settings", 1, document.querySelector("#dependency-panel h3"), {rename:true});
  markWorkflowStep("settings", 2, document.querySelector("#doctor-status"));
  markWorkflowStep("settings", 3, document.querySelector("#dependency-repair"));
  markWorkflowStep("settings", 4, document.querySelector("footer"));
}

function renderWorkflowInstructions() {
  const guide = guiWorkflowGuides?.[guiActiveStage];
  const panel = document.querySelector("#gui-stage-instructions");
  if (!guide || !panel) return;
  panel.replaceChildren();
  const title = document.createElement("p"); title.className = "gui-guide-title";
  const label = document.createElement("strong"); label.textContent = "Quick steps";
  const full = document.createElement("a"); full.href = `/help/${guide.slug}`;
  full.textContent = "Full instructions (English)";
  full.target = "_blank"; full.rel = "noopener noreferrer";
  title.append(label, full);
  const list = document.createElement("ol");
  guide.steps.forEach((step, index) => {
    const item = document.createElement("li"), link = document.createElement("a");
    const id = guiWorkflowTargets[guiActiveStage]?.[index + 1];
    link.textContent = step.title.en; link.title = step.text.en;
    link.href = id ? `#${id}` : `/help/${guide.slug}`;
    link.addEventListener("click", event => {
      const target = id && document.getElementById(id);
      if (!target) return;
      event.preventDefault();
      const details = target.closest("details"); if (details) details.open = true;
      target.scrollIntoView({behavior:"smooth", block:"start"});
    });
    item.append(link); list.append(item);
  });
  panel.append(title, list);
  translateGui();
}

async function installWorkflowGuidance() {
  const panel = document.createElement("aside"); panel.id = "gui-stage-instructions";
  panel.setAttribute("aria-label", "Stage instructions");
  const main = document.querySelector("main"), stages = document.querySelector("#gui-stage-nav");
  if (stages.parentElement === main) stages.after(panel); else main.prepend(panel);
  const stickySizes = new ResizeObserver(() => {
    document.documentElement.style.setProperty("--gui-context-height", `${Math.ceil(document.querySelector("#gui-active-context").getBoundingClientRect().height)}px`);
    document.documentElement.style.setProperty("--gui-nav-height", `${Math.ceil(stages.getBoundingClientRect().height)}px`);
  });
  stickySizes.observe(document.querySelector("#gui-active-context")); stickySizes.observe(stages);
  try {
    guiWorkflowGuides = await loadJson("/api/v1/guides");
    for (const [stage, guide] of Object.entries(guiWorkflowGuides)) {
      guiPolish.set(guide.title.en, guide.title.pl);
      const heading = document.getElementById(guiStages.find(item => item[0] === stage)[2]);
      heading.textContent = guide.title.en;
      for (const step of guide.steps) {
        guiPolish.set(step.title.en, step.title.pl); guiPolish.set(step.text.en, step.text.pl);
      }
    }
    numberWorkflowSections();
    renderWorkflowInstructions();
    document.addEventListener("ewp-stage", renderWorkflowInstructions);
  } catch (_) {
    const link = document.createElement("a"); link.href = "/help";
    link.textContent = "Open the complete local GUI instructions"; panel.append(link);
  }
}

void installWorkflowGuidance();
