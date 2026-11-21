"use strict";

for(const [id,kind] of [
  ["input-path","directory"], ["review-result-path","file"], ["correction-result-path","file"],
  ["translation-result-path","file"], ["translation-revision-path","file"],
  ["review-project-path","directory"], ["review-output-path","directory"],
  ["revision-output-path","directory"], ["export-output-path","directory"],
  ["correction-dictionary","file"], ["translation-dictionary","file"], ["dictionary-previous","file"],
  ["library-directory","directory"], ["dictionary-output-root","directory"],
  ["workspace-directory","directory"], ["location-path","directory"], ["project-scan-path","directory"],
]) {
  const input=document.getElementById(id); if(!input) continue;
  const button=document.createElement("button"); button.type="button"; button.className="path-browser-button";
  button.dataset.pickerFor=id;
  button.textContent=kind==="directory" ? "Choose directory…" : "Choose file…";
  button.addEventListener("click",async()=>{
    button.disabled=true;
    try {
      const payload=await queuePost("/api/v1/select-path",{kind},{trigger:button});
      if(payload.path) { input.value=payload.path; input.dispatchEvent(new Event("input",{bubbles:true})); input.dispatchEvent(new Event("change",{bubbles:true})); }
    } catch(error) {
      let status=button.nextElementSibling;
      if(!status?.classList.contains("picker-feedback")) {status=document.createElement("p");status.className="picker-feedback";status.setAttribute("role","status");button.after(status);}
      status.textContent=error.message; input.focus({preventScroll:true});
    } finally {button.disabled=false;}
  });
  (id==="input-path" ? document.querySelector("#gui-input-path-hint") || input : input).after(button);
}
