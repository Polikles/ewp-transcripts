"use strict";

function requireGuiVerification(input, status, message, code) {
  if (input.checked) return true;
  const label = input.closest("label");
  input.dataset.guiConfirmationMissing = "true";
  input.setAttribute("aria-invalid", "true"); label.classList.add("field-error");
  let feedback = label.nextElementSibling;
  if (!feedback?.classList.contains("gui-verification-feedback")) {
    feedback = document.createElement("p"); feedback.className = "gui-verification-feedback";
    feedback.id = `${status.id}-verification-feedback`; feedback.setAttribute("role", "alert");
    label.after(feedback);
  }
  feedback.hidden = false; feedback.textContent = message;
  const described = new Set((input.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
  described.add(feedback.id); input.setAttribute("aria-describedby", [...described].join(" "));
  status.textContent = `${code}: ${message}`;
  input.focus({preventScroll:true});
  return false;
}

function syncGuiStatusMotion() {
  for (const host of document.querySelectorAll('[role="status"]')) {
    const source = [...host.childNodes].map(node => guiNodeSources.get(node)?.source || node.textContent).join("").trim();
    const busy = host === guiWorking ? guiPendingRequests > 0 :
      /^(Working…|Status: connecting|Inspecting(?:…| \d)|Planning(?:…| \d)|Preparing recording audio…|Adding…|Generating (?:correction|translation)|Correction is running|Translation is running|Testing local dependencies…|Running .+…|Saving .+…|Loading .+…|Restoring saved queue and editors…|Refreshing .+…|Checking[ ;…]|Copying .+ into this local GUI session…|Reading audio streams…|Finding media by content…|Scanning saved results…|Inventorying|Auto-save detected tracked changes; validating)/.test(source);
    host.classList.toggle("gui-status-working", busy);
    host.setAttribute("aria-busy", String(busy));
  }
}

function createGuiLanguageChoice(label) {
  const choice = document.createElement("div"); choice.className = "gui-language-choice";
  if(label.parentNode)label.before(choice);choice.append(label);
  const details = document.createElement("details"); details.className = "gui-language-info";
  const summary = document.createElement("summary"); summary.textContent = "i";
  const message = "Choosing EN for Polish recordings has sometimes produced readable English text. This is not a guaranteed translation mode; the result still needs review and correction.";
  summary.title = message; summary.setAttribute("aria-label", "Language selection information");
  const info = document.createElement("p"); info.className = "field-hint"; info.textContent = message;
  details.append(summary, info); choice.append(details);
  return choice;
}
function installReviewFeedback() {
  const hint = [...document.querySelectorAll("#workflow .field-hint")].find(node=>node.textContent.includes("Windows"));
  if (hint) { hint.id = "gui-input-path-hint"; workflowInput.after(hint); }
  createGuiLanguageChoice(document.querySelector("#workflow-language").closest("label"));
  document.addEventListener("pointerdown", event => {
    document.querySelectorAll(".gui-language-info[open]").forEach(details=>{if(!details.contains(event.target))details.open=false;});
  });
  document.addEventListener("keydown", event => {
    const details=document.querySelector(".gui-language-info[open]");
    if (event.key === "Escape" && details) {
      details.open = false;
      details.querySelector("summary").focus({preventScroll:true});
    }
  });
  document.addEventListener("change",event=>{
    const input=event.target;
    if(!(input instanceof HTMLInputElement) || input.type!=="checkbox" || !input.checked || input.dataset.guiConfirmationMissing!=="true")return;
    input.dataset.guiConfirmationMissing="false";input.setAttribute("aria-invalid","false");
    const label=input.closest("label");label.classList.remove("field-error");
    const feedback=label.nextElementSibling;
    if(feedback?.classList.contains("gui-verification-feedback")) {
      feedback.hidden=true;feedback.textContent="";
      const status=document.getElementById(feedback.id.replace("-verification-feedback",""));
      if(status)status.textContent=input===reviewForm.elements.namedItem("verified") || input.id==="translation-review-confirmed"
        ? "Manual verification confirmed. Save and prepare for export when ready." : "Consent confirmed. Continue with the selected action.";
      const described=(input.getAttribute("aria-describedby") || "").split(/\s+/).filter(id=>id && id!==feedback.id);
      if(described.length)input.setAttribute("aria-describedby",described.join(" "));else input.removeAttribute("aria-describedby");
    }
  });
}
installReviewFeedback();
