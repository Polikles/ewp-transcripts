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
      /^(Working…|Status: connecting|Inspecting(?:…| \d)|Planning…|Adding…|Generating (?:correction|translation)|Correction is running|Translation is running|Testing local dependencies…|Running .+…|Saving .+…|Loading .+…|Refreshing .+…|Checking[ ;…]|Copying .+ into this local GUI session…|Inventorying|Auto-save detected tracked changes; validating)/.test(source);
    host.classList.toggle("gui-status-working", busy);
    host.setAttribute("aria-busy", String(busy));
  }
}

function installReviewFeedback() {
  const hint = [...document.querySelectorAll("#workflow .field-hint")].find(node=>node.textContent.includes("Windows"));
  if (hint) { hint.id = "gui-input-path-hint"; workflowInput.after(hint); }
  const language = document.querySelector("#workflow-language");
  const label = language.closest("label");
  const choice = document.createElement("div"); choice.className = "gui-language-choice";
  label.before(choice); choice.append(label);
  const details = document.createElement("details"); details.className = "gui-language-info";
  const summary = document.createElement("summary"); summary.textContent = "i";
  const message = "Choosing EN for Polish recordings has sometimes produced readable English text. This is not a guaranteed translation mode; the result still needs review and correction.";
  summary.title = message; summary.setAttribute("aria-label", "Language selection information");
  const info = document.createElement("p"); info.className = "field-hint"; info.textContent = message;
  details.append(summary, info); choice.append(details);
  for (const input of [reviewForm.elements.namedItem("verified"), document.querySelector("#translation-review-confirmed")]) {
    input.addEventListener("change", () => {
      if (!input.checked || input.dataset.guiConfirmationMissing !== "true") return;
      input.dataset.guiConfirmationMissing = "false";
      input.setAttribute("aria-invalid", "false");
      const row = input.closest("label"); row.classList.remove("field-error");
      const feedback = row.nextElementSibling;
      if (feedback?.classList.contains("gui-verification-feedback")) {
        feedback.hidden = true; feedback.textContent = "";
        const status = document.getElementById(feedback.id.replace("-verification-feedback", ""));
        if (status) status.textContent = "Manual verification confirmed. Save and prepare for export when ready.";
        const described = (input.getAttribute("aria-describedby") || "").split(/\s+/).filter(id=>id && id !== feedback.id);
        if (described.length) input.setAttribute("aria-describedby", described.join(" "));
        else input.removeAttribute("aria-describedby");
      }
    });
  }
}
installReviewFeedback();
