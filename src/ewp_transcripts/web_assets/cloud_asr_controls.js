"use strict";

const cloudAsrPanel=document.createElement("details"); cloudAsrPanel.id="cloud-asr-panel";
cloudAsrPanel.innerHTML=`<summary>Transcription engine</summary>
  <label>ASR provider<select id="cloud-asr-provider"><option value="local">Local GPU (default)</option><option value="openrouter">OpenRouter cloud ASR</option></select></label>
  <div id="cloud-asr-options" hidden>
    <label>Cloud ASR model<select id="cloud-asr-model"></select></label>
    <label>Cost guard per queued job (USD)<input id="cloud-asr-budget" type="number" min="0.01" max="100" step="0.01" value="2"></label>
    <p class="field-hint">Uses the same OpenRouter key as correction and translation. Audio is uploaded only after Start queue with consent. Provider prices are checked before upload; uncertain charges are reserved without automatic retries. The guard is an estimate, not a provider billing cap.</p>
    <p class="field-hint">Whisper models need one speaker or separate synchronized speaker tracks. Mixed-speaker audio needs Scribe or MAI and fits in one request (up to 24 MiB of normalized WAV); longer mixed recordings use local ASR or separate speaker tracks. Provider word times are required for subtitles.</p>
    <button type="button" id="cloud-asr-key">Manage OpenRouter key</button>
  </div>`;
mediaOptionsPanel.after(cloudAsrPanel);
const cloudProvider=document.querySelector("#cloud-asr-provider"), cloudModel=document.querySelector("#cloud-asr-model"), cloudBudget=document.querySelector("#cloud-asr-budget");
for(const model of ["openai/whisper-large-v3","openai/whisper-large-v3-turbo","elevenlabs/scribe-v2","microsoft/mai-transcribe-2"]) {
  const option=document.createElement("option"); option.value=model; option.textContent=model; cloudModel.append(option);
}
const cloudConsent=document.createElement("label"); cloudConsent.id="cloud-asr-consent"; cloudConsent.className="confirmation";
cloudConsent.innerHTML=`<input type="checkbox" id="cloud-asr-confirmed"> <span>I agree to upload the staged cloud audio to OpenRouter and its model provider, with paid API usage within each job's cost guard. This consent is not saved.</span>`;
document.querySelector("#start-queue").before(cloudConsent);
function updateCloudAsrControls() {
  document.querySelector("#cloud-asr-options").hidden=cloudProvider.value!=="openrouter";
  cloudConsent.hidden=cloudProvider.value!=="openrouter" && !guiQueueJobs.some(job=>job.speech?.provider==="openrouter" && job.status==="staged");
}
for(const element of [cloudProvider,cloudModel,cloudBudget]) element.addEventListener("change",()=>{
  document.querySelector("#cloud-asr-confirmed").checked=false; invalidateMediaPlan(); updateCloudAsrControls();
});
document.querySelector("#cloud-asr-key").addEventListener("click",()=>openRouterKeyButton.click());
const decorateBeforeCloudAsr=decorateGuiMediaRequest;
decorateGuiMediaRequest=function(request,episode=null) {
  decorateBeforeCloudAsr(request,episode);
  if(cloudProvider.value==="openrouter") request.speech={provider:"openrouter",model:cloudModel.value,max_cost_usd:Number(cloudBudget.value)};
  return request;
};
workspaceFieldIds.push("cloud-asr-provider","cloud-asr-model","cloud-asr-budget");
const restoreFieldsBeforeCloudAsr=applyWorkspaceFields;
applyWorkspaceFields=async function(...args) {
  const result=await restoreFieldsBeforeCloudAsr(...args); document.querySelector("#cloud-asr-confirmed").checked=false; updateCloudAsrControls(); return result;
};
const refreshJobsBeforeCloudAsr=refreshJobs;
refreshJobs=async function(...args) {const result=await refreshJobsBeforeCloudAsr(...args);updateCloudAsrControls();return result;};
updateCloudAsrControls();

const applyProfileBeforeCloudAsr=applyUserProfile;
applyUserProfile=async function(...args) {document.querySelector("#cloud-asr-confirmed").checked=false; return await applyProfileBeforeCloudAsr(...args);};
