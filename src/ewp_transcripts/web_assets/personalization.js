"use strict";

const personalizationButton = document.createElement("button");
personalizationButton.id = "gui-personalization"; personalizationButton.type = "button";
personalizationButton.textContent = "Personalization";
personalizationButton.setAttribute("aria-haspopup", "dialog");
userProfilePanel.querySelectorAll("h3")[1].after(personalizationButton);
const personalization = document.createElement("dialog");
personalization.id = "gui-personalization-dialog";
personalization.setAttribute("aria-labelledby", "gui-personalization-title");
personalization.innerHTML = `<h2 id="gui-personalization-title">Personalization</h2>
  <p class="field-hint">Changes are saved immediately on this device and included when you save a user profile.</p>
  <div class="gui-personalization-grid">
    <label>Appearance<select id="gui-personal-theme"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
    <label>Interface language<select id="gui-personal-locale"><option value="pl">Polski</option><option value="en">English</option></select></label>
    <label>Default color palette<select id="gui-personal-palette"></select></label>
    <label>Playback speed<select id="gui-personal-speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="0.75">0.75×</option><option value="1">1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="1.75">1.75×</option><option value="2">2×</option><option value="2.5">2.5×</option><option value="3">3×</option><option value="4">4×</option></select></label>
    <label>Source review display<select id="gui-personal-review"><option value="one">One section at a time</option><option value="all">All sections</option></select></label>
    <label>Translation review display<select id="gui-personal-translation"><option value="few">A few units at a time</option><option value="all">All units</option></select></label>
  </div>
  <p class="field-hint">The default palette is used for recordings without saved speaker colors. Applied recording colors stay unchanged.</p>
  <fieldset id="gui-personal-native" hidden><legend>Window title bar</legend><div class="gui-personalization-grid">
    <label>Title bar appearance<select id="gui-titlebar-mode"><option value="system">System theme</option><option value="application">Match application theme</option><option value="custom">Custom color</option></select></label>
    <label>Title bar color<input id="gui-titlebar-color" type="color" value="#24485c"></label>
  </div></fieldset>
  <label class="gui-preference"><input id="gui-personal-eta" type="checkbox"> Show estimated remaining time (ETA)</label>
  <div class="actions"><button type="button" id="gui-personal-close">Close</button></div>`;
document.body.append(personalization);
document.querySelector("#gui-personal-native").hidden = !window.chrome?.webview;
const personal = name => document.getElementById(`gui-personal-${name}`);
let personalizationPaletteSignature = "";
function syncPersonalization() {
  personal("theme").value = document.querySelector("#gui-theme").value;
  personal("locale").value = guiLocale;
  const profiles = guiColorProfiles.length ? guiColorProfiles : [{id:"configured",name:"Configured production"},{id:"brand",name:"EwP Brand®"}];
  const signature = JSON.stringify(profiles.map(item=>[guiProfileValue(item),item.name]));
  if (signature !== personalizationPaletteSignature) {
    personal("palette").replaceChildren();
    for (const profile of profiles) { const option=document.createElement("option"); option.value=guiProfileValue(profile); option.textContent=profile.name; personal("palette").append(option); }
    personalizationPaletteSignature = signature;
  }
  personal("palette").value = guiPreferences.defaultPalette || "configured";
  if (!personal("palette").value) personal("palette").value = "configured";
  const speed=String(guiPreferences.playbackSpeed || 1);
  if (![...personal("speed").options].some(option=>option.value===speed)) personal("speed").add(new Option(`${speed}×`,speed));
  personal("speed").value = speed;
  personal("review").value = localStorage.getItem("ewp-review-layout") || "one";
  personal("translation").value = localStorage.getItem("ewp-translation-review-layout") || "few";
  personal("eta").checked = etaPreference.checked;
  document.querySelector("#gui-titlebar-mode").value = ["system","application","custom"].includes(guiPreferences.titleBarMode) ? guiPreferences.titleBarMode : "system";
  document.querySelector("#gui-titlebar-color").value = /^#[a-f0-9]{6}$/i.test(guiPreferences.titleBarColor || "") ? guiPreferences.titleBarColor : "#24485c";
  document.querySelector("#gui-titlebar-color").disabled = document.querySelector("#gui-titlebar-mode").value !== "custom";
}
personalizationButton.addEventListener("click", () => { syncPersonalization(); personalization.showModal(); });
personal("close").addEventListener("click", () => personalization.close());
personalization.addEventListener("click", event => { if (event.target === personalization) personalization.close(); });
for (const name of ["theme","locale"]) personal(name).addEventListener("change", () => {
  const target=document.querySelector(`#gui-${name}`); target.value=personal(name).value; target.dispatchEvent(new Event("change"));
});
personal("palette").addEventListener("change", () => {
  guiPreferences.defaultPalette=personal("palette").value; saveGuiPreferences();
  if (!reviewDocument || !Object.keys(guiSavedSpeakerColors()).length) { document.querySelector("#gui-export-palette").value=guiPreferences.defaultPalette; renderGuiProfileSwatches(); }
  applyGuiSpeakerColors(); updateGuiContext();
});
personal("speed").addEventListener("change", () => { guiPreferences.playbackSpeed=Number(personal("speed").value); playbackAudio.playbackRate=guiPreferences.playbackSpeed; saveGuiPreferences(); });
personal("review").addEventListener("change", () => { document.querySelector("#review-layout").value=personal("review").value; localStorage.setItem("ewp-review-layout",personal("review").value); updateReviewSections(); saveGuiPreferences(); });
personal("translation").addEventListener("change", () => {
  localStorage.setItem("ewp-translation-review-layout",personal("translation").value);
  document.querySelectorAll(".translation-review-layout").forEach(element=>{ element.value=personal("translation").value; element.dispatchEvent(new Event("change")); }); saveGuiPreferences();
});
personal("eta").addEventListener("change", () => { etaPreference.checked=personal("eta").checked; etaPreference.dispatchEvent(new Event("change")); });
for (const id of ["gui-titlebar-mode","gui-titlebar-color"]) document.getElementById(id).addEventListener("input", () => {
  guiPreferences.titleBarMode=document.querySelector("#gui-titlebar-mode").value;
  guiPreferences.titleBarColor=document.querySelector("#gui-titlebar-color").value; saveGuiPreferences();
});
document.addEventListener("ewp-preferences-changed",syncPersonalization);
document.addEventListener("ewp-palettes-loaded",syncPersonalization);
syncPersonalization();
