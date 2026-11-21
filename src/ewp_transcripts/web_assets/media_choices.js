"use strict";

// Ordinary media needs no stream/identity panel. Reveal only choices that are necessary.
const mediaOptionsPanel=document.createElement("div");mediaOptionsPanel.id="gui-media-options";mediaOptionsPanel.hidden=true;
document.querySelector(".workflow-options").after(mediaOptionsPanel);
let directMediaStreams={},directMediaIdentity="",directMediaPath="";
function invalidateMediaPlan() {guiBatchPlan=null;document.querySelector('#workflow input[name="confirmed"]').checked=false;}
function appendStreamChoice(host,file,disabled=false) {
  if(!file.streams || file.streams.length<2)return;
  const warning=document.createElement("p");warning.className="notice";
  warning.textContent="Multiple audio streams found. Choose the stream to transcribe.";
  const label=document.createElement("label");const name=document.createElement("span");name.dataset.guiContent="true";name.textContent=file.name;label.append(name);
  const select=document.createElement("select");select.dataset.sourcePath=file.path;
  const empty=document.createElement("option");empty.value="";empty.textContent="Choose an audio stream";select.append(empty);
  for(const stream of file.streams) {const option=document.createElement("option");option.value=String(stream.index);option.textContent=`${stream.index} · ${stream.language || "—"} · ${stream.title || stream.codec} · ${stream.channels} ch`;select.append(option);}
  select.value=file.stream_index===undefined ? "" : String(file.stream_index);select.disabled=disabled;
  select.addEventListener("change",()=>{file.stream_index=select.value==="" ? undefined : Number(select.value);invalidateMediaPlan();});
  label.append(select);host.append(warning,label);
}
function appendGuiMediaControls(row,episode) {
  for(const file of episode.files) appendStreamChoice(row,file,file.staged || guiBatchBusy);
  if(episode.files.some(file=>file.needs_recording_id || file.recording_id)) {
    const label=document.createElement("label");label.textContent="Recording ID (distinct for same-name recordings)";
    const input=document.createElement("input");input.maxLength=100;input.value=episode.files[0].recording_id || "";input.disabled=episode.files.some(file=>file.staged) || guiBatchBusy;
    input.addEventListener("input",()=>{episode.files.forEach(file=>file.recording_id=input.value.trim());invalidateMediaPlan();});label.append(input);row.append(label);
  }
}
function drawMediaOptions() {
  mediaOptionsPanel.replaceChildren();mediaOptionsPanel.hidden=Boolean(selectedGuiAudio.length) || !directMediaStreams.streams || directMediaStreams.streams.length<2;
  if(!mediaOptionsPanel.hidden)appendStreamChoice(mediaOptionsPanel,directMediaStreams,guiBatchBusy);
}
async function readEpisodeMediaOptions(episode) {
  for(const file of episode.files) {
    if(file.streams || file.staged)continue;
    const payload=await queuePost("/api/v1/media/probe",{path:file.path},{feedback:false});
    file.streams=payload.streams;file.duration_ms=payload.duration_ms;
  }
}
async function prepareGuiMediaBatch() {
  let missing=false;
  for(const episode of guiAudioEpisodes().filter(item=>!item.files.some(file=>file.staged))) {
    await readEpisodeMediaOptions(episode);
    if(episode.files.some(file=>file.streams.length>1 && file.stream_index===undefined))missing=true;
  }
  renderGuiAudioChoices();
  if(missing)throw new Error("GUI_AUDIO_STREAM_REQUIRED: Choose an audio stream before planning this episode.");
}
async function prepareDirectGuiMedia() {
  const path=workflowInput.value.trim();if(!path)return true;
  try {
    if(directMediaPath!==path) {
      const payload=await queuePost("/api/v1/media/probe",{path},{feedback:false});
      directMediaStreams={...payload};directMediaPath=path;
    }
    drawMediaOptions();
    if(directMediaStreams.streams.length>1 && directMediaStreams.stream_index===undefined)throw new Error("GUI_AUDIO_STREAM_REQUIRED: Choose an audio stream before planning this episode.");
    return true;
  }catch(error){document.querySelector("#operation-status").textContent=error.message;return false;}
}
function decorateGuiMediaRequest(request,episode=null) {
  const files=episode?.files || activeGuiAudio?.files;
  const identity=files?.[0]?.recording_id || (!files ? directMediaIdentity : "");
  if(identity) {if(request.group_paths)request.group_id=identity;else request.recording_id=identity;}
  const streams={};
  if(files)files.forEach(file=>{if(file.stream_index!==undefined)streams[file.path]=file.stream_index;});
  else if(directMediaPath===request.path && directMediaStreams.stream_index!==undefined)streams[request.path]=directMediaStreams.stream_index;
  if(Object.keys(streams).length)request.selected_streams=streams;
  return request;
}
workflowInput.addEventListener("input",()=>{if(!activeGuiAudio && workflowInput.value!==directMediaPath){directMediaStreams={};directMediaPath="";drawMediaOptions();}});
nativeMediaInput.accept="";
