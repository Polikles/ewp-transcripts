"use strict";

const guiAmdProfile = document.documentElement.dataset.localAccelerator === "amd";

const cloudAsrPanel=document.createElement("details"); cloudAsrPanel.id="cloud-asr-panel";
cloudAsrPanel.innerHTML=`<summary>Transcription engine</summary>
  <label>ASR provider<select id="cloud-asr-provider"><option value="local">Local GPU (default)</option><option value="openrouter">OpenRouter cloud ASR</option></select></label>
  <label id="local-asr-options">Local ASR model<select id="local-asr-model"><option value="configured">Configured local model (default)</option><option value="large-v3">Whisper Large v3</option><option value="large-v3-turbo">Whisper Large v3 Turbo</option></select><span class="field-hint">Install optional local models using Add local models in the installer. Scribe v2 and MAI are cloud-only here.</span></label>
  <div id="cloud-asr-options" hidden>
    <label>Cloud ASR model<select id="cloud-asr-model"></select></label>
    <div class="actions"><button type="button" id="cloud-asr-key">Manage OpenRouter key</button><button type="button" id="cloud-asr-check">Check key and OpenRouter connection</button><button type="button" id="cloud-asr-refresh">Refresh and estimate cost</button></div>
    <p id="cloud-asr-check-status" role="status">Not checked</p>
    <p id="cloud-asr-estimate-status" role="status">Refresh models to see current hourly prices and an estimate for pending recordings.</p>
    <div id="cloud-asr-prices" class="table-scroll"></div>
    <p class="field-hint">Key checks and price refresh do not upload audio. Estimates use current prices and source duration. Final billing can differ. Estimating does not incur provider charges.</p>
    <p class="field-hint">Whisper models need one speaker per track. Scribe and MAI handle mixed-speaker audio better.</p>
  </div>`;
mediaOptionsPanel.after(cloudAsrPanel);
if (guiAmdProfile) {
  cloudAsrPanel.querySelector('option[value="local"]').textContent="Local GPU · AMD (experimental)";
  const info=document.createElement("p");info.className="field-hint";
  info.textContent="AMD support is experimental and has not been tested on physical hardware. ASR uses ROCm; word alignment and diarization use CPU.";
  document.querySelector("#local-asr-options").after(info);
}
const cloudProvider=document.querySelector("#cloud-asr-provider"), cloudModel=document.querySelector("#cloud-asr-model");
for(const model of ["openai/whisper-large-v3","openai/whisper-large-v3-turbo","elevenlabs/scribe-v2","microsoft/mai-transcribe-2"]) {
  const option=document.createElement("option"); option.value=model; option.textContent=model; cloudModel.append(option);
}
const cloudConsent=document.createElement("label"); cloudConsent.id="cloud-asr-consent"; cloudConsent.className="confirmation";
cloudConsent.innerHTML=`<input type="checkbox" id="cloud-asr-confirmed"> <span>I agree to upload the staged cloud audio to OpenRouter and its model provider, with paid API usage. This consent is not permanently saved.</span>`;
document.querySelector("#start-queue").before(cloudConsent);
let cloudConsentToken="",cloudConsentSnapshot="",cloudConsentPending=null,cloudConsentGeneration=0;
function cloudQueueConsentSnapshot() {return JSON.stringify(guiQueueJobs.filter(job=>job.status==="staged").map(job=>[job.job_id,job.speech]).sort((a,b)=>a[0].localeCompare(b[0])));}
function resetGuiCloudConsent() {cloudConsentGeneration+=1;cloudConsentToken="";cloudConsentSnapshot="";document.querySelector("#cloud-asr-confirmed").checked=false;}
function currentGuiCloudConsentToken(){return cloudConsentToken;}
document.querySelector("#cloud-asr-confirmed").addEventListener("change",event=>{
  cloudConsentGeneration+=1;cloudConsentToken="";cloudConsentSnapshot="";
  if(!event.target.checked || !event.isTrusted)return;
  const generation=cloudConsentGeneration,snapshot=cloudQueueConsentSnapshot();
  const ids=guiQueueJobs.filter(job=>job.status==="staged" && job.speech?.provider==="openrouter").map(job=>job.job_id);
  cloudConsentPending=queuePost("/api/v1/transcriptions/cloud-consent",{cloud_confirmed:true,cloud_job_ids:ids},{feedback:false}).then(payload=>{
    if(generation===cloudConsentGeneration && event.target.checked && snapshot===cloudQueueConsentSnapshot()){cloudConsentToken=payload.cloud_consent_token;cloudConsentSnapshot=snapshot;}
  }).catch(error=>{if(generation===cloudConsentGeneration){resetGuiCloudConsent();document.querySelector("#operation-status").textContent=error.message;}});
});
async function ensureGuiCloudConsent() {
  if(cloudConsentPending)await cloudConsentPending;
  if(!guiQueueJobs.some(job=>job.status==="staged" && job.speech?.provider==="openrouter"))return true;
  if(!cloudConsentToken || cloudConsentSnapshot!==cloudQueueConsentSnapshot())resetGuiCloudConsent();
  return requireGuiVerification(document.querySelector("#cloud-asr-confirmed"),document.querySelector("#operation-status"),"Confirm audio upload and paid API usage before starting cloud ASR.","GUI_CLOUD_CONSENT_REQUIRED");
}
function updateCloudAsrControls() {
  if(cloudConsentSnapshot && cloudConsentSnapshot!==cloudQueueConsentSnapshot())resetGuiCloudConsent();
  document.querySelector("#local-asr-options").hidden=cloudProvider.value!=="local";
  document.querySelector("#cloud-asr-options").hidden=cloudProvider.value!=="openrouter";
  cloudConsent.hidden=cloudProvider.value!=="openrouter" && !guiQueueJobs.some(job=>job.speech?.provider==="openrouter" && job.status==="staged");
}
for(const element of [cloudProvider,cloudModel,document.querySelector("#local-asr-model")]) element.addEventListener("change",()=>{
  resetGuiCloudConsent(); invalidateMediaPlan(); updateCloudAsrControls();
});
document.querySelector("#cloud-asr-key").addEventListener("click",()=>openRouterKeyButton.click());
document.querySelector("#cloud-asr-check").addEventListener("click",async event=>{
  const button=event.currentTarget,status=document.querySelector("#cloud-asr-check-status");button.disabled=true;status.textContent="Checking OpenRouter key and connection…";
  try {const result=await queuePost("/api/v1/speech/check",{},{trigger:button});showOpenRouterCheckResult(result,status);}
  catch(error){status.textContent=error.message;}
  finally{button.disabled=false;}
});
function cloudEstimateItems() {
  const pending=guiBatchRequests().map(item=>item.request);
  const staged=guiQueueJobs.filter(job=>job.status==="staged" && job.speech?.provider==="openrouter");
  for(const job of staged) {
    const paths=Object.keys(job.group_sources || {});
    pending.push({path:job.input_path,...(paths.length ? {group_paths:paths} : {}),speaker_count:job.speaker_count,selected_streams:job.selected_streams || {}});
  }
  if(!pending.length && !selectedGuiAudio.length && workflowInput.value.trim() && !guiInputAlreadyStaged()) {
    pending.push(decorateGuiMediaRequest({path:workflowInput.value.trim(),speaker_count:document.querySelector("#workflow-speaker-auto").checked ? "auto" : Number(document.querySelector("#workflow-speaker-count").value)}));
  }
  return pending;
}
function cloudEstimateSignature() {return JSON.stringify(cloudEstimateItems());}
let cloudLastEstimateSignature=null;
function renderCloudPrices(payload) {
  const container=document.querySelector("#cloud-asr-prices");container.replaceChildren();
  const table=document.createElement("table");table.className="queue-table";
  table.innerHTML="<thead><tr><th>Cloud ASR model</th><th>Availability</th><th>USD / audio hour</th><th>Estimated cost (USD)</th></tr></thead>";
  const body=document.createElement("tbody");
  const range=(low,high)=>{const a=Number(low).toFixed(4),b=Number(high).toFixed(4);return a===b ? a : `${a}–${b}`;};
  for(const model of payload.models) {
    const row=document.createElement("tr");
    const option=[...cloudModel.options].find(item=>item.value===model.id);
    if(option)option.disabled=!model.available;
    const values=[model.id,model.available ? "Available" : "Unavailable",model.status==="ok" ? range(model.minimum_usd_per_hour,model.maximum_usd_per_hour) : "Price unavailable",model.status==="ok" && payload.recordings ? range(model.estimated_minimum_usd,model.estimated_maximum_usd) : "—"];
    for(const [index,value] of values.entries()) {const cell=document.createElement("td");cell.textContent=value;if(index===0)cell.dataset.guiContent="true";row.append(cell);}
    body.append(row);
  }
  table.append(body);container.append(table);
}
document.querySelector("#cloud-asr-refresh").addEventListener("click",async event=>{
  const button=event.currentTarget,status=document.querySelector("#cloud-asr-estimate-status");button.disabled=true;status.textContent="Refreshing OpenRouter models and prices…";
  try {
    const items=cloudEstimateItems(),signature=JSON.stringify(items);
    const payload=await queuePost("/api/v1/speech/estimate",{items},{trigger:button});renderCloudPrices(payload);
    cloudLastEstimateSignature=signature;
    status.textContent=signature===cloudEstimateSignature() ? `Estimated recordings: ${payload.recordings} · Audio duration (min): ${(payload.audio_seconds/60).toFixed(1)}` : "Recordings or settings changed. Refresh the cost estimate.";
  }catch(error){status.textContent=error.message;}
  finally{button.disabled=false;}
});
// Keep the comparison current without background network calls.
setInterval(()=>{if(cloudLastEstimateSignature!==null && cloudLastEstimateSignature!==cloudEstimateSignature())document.querySelector("#cloud-asr-estimate-status").textContent="Recordings or settings changed. Refresh the cost estimate.";},1000);
const decorateBeforeCloudAsr=decorateGuiMediaRequest;
decorateGuiMediaRequest=function(request,episode=null) {
  decorateBeforeCloudAsr(request,episode);
  if(cloudProvider.value==="openrouter")request.speech={provider:"openrouter",model:cloudModel.value,cost_mode:"estimated"};
  else request.speech={provider:"local",local_model:document.querySelector("#local-asr-model").value};
  return request;
};
// Retain the legacy field allowlist for saved profiles; its removed input is never restored.
workspaceFieldIds.push("local-asr-model","cloud-asr-provider","cloud-asr-model","cloud-asr-budget");
const restoreFieldsBeforeCloudAsr=applyWorkspaceFields;
applyWorkspaceFields=async function(...args) {
  resetGuiCloudConsent();const result=await restoreFieldsBeforeCloudAsr(...args);resetGuiCloudConsent();updateCloudAsrControls();return result;
};
const refreshJobsBeforeCloudAsr=refreshJobs;
refreshJobs=async function(...args) {const result=await refreshJobsBeforeCloudAsr(...args);updateCloudAsrControls();return result;};
updateCloudAsrControls();
const applyProfileBeforeCloudAsr=applyUserProfile;
applyUserProfile=async function(...args) {resetGuiCloudConsent();return await applyProfileBeforeCloudAsr(...args);};
