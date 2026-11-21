"use strict";

const mediaOptionsPanel = document.createElement("details"); mediaOptionsPanel.id="gui-media-options";
mediaOptionsPanel.innerHTML=`<summary>Audio streams and recording ID</summary>
  <p class="field-hint">Settings belong to the selected episode. Use distinct recording IDs for same-name inputs. Source filenames are preserved. Multiple audio streams require an explicit choice.</p>
  <label>Recording ID (optional)<input id="workflow-recording-id" maxlength="100" autocomplete="off"></label>
  <button type="button" id="read-media-options">Read audio streams</button>
  <div id="media-stream-choices"></div><p id="media-options-status" role="status"></p>`;
document.querySelector(".workflow-options").after(mediaOptionsPanel);
const mediaIdentity = document.querySelector("#workflow-recording-id");
let directMediaStreams = {}, directMediaIdentity = "", directMediaPath = "";
function invalidateMediaPlan() {
  guiBatchPlan=null; document.querySelector('#workflow input[name="confirmed"]').checked=false;
}
mediaIdentity.addEventListener("input",()=>{
  if(activeGuiAudio) activeGuiAudio.files.forEach(file=>{file.recording_id=mediaIdentity.value.trim();});
  else directMediaIdentity=mediaIdentity.value.trim();
  invalidateMediaPlan(); renderGuiAudioChoices();
});
function drawMediaOptions() {
  mediaIdentity.value=activeGuiAudio ? activeGuiAudio.files[0].recording_id || "" : directMediaIdentity;
  const host=document.querySelector("#media-stream-choices"); host.replaceChildren();
  const files=activeGuiAudio?.files || [{path:workflowInput.value, name:shortName(workflowInput.value), streams:directMediaStreams.streams, stream_index:directMediaStreams.stream_index}];
  for(const file of files) {
    if(!file.streams?.length) continue;
    const label=document.createElement("label"); label.append(file.name);
    const select=document.createElement("select"); select.dataset.sourcePath=file.path;
    if(file.streams.length>1) {const option=document.createElement("option"); option.value=""; option.textContent="Choose an audio stream"; select.append(option);}
    for(const stream of file.streams) {
      const option=document.createElement("option"); option.value=String(stream.index);
      option.textContent=`${stream.index} · ${stream.language || "—"} · ${stream.title || stream.codec} · ${stream.channels} ch`;
      select.append(option);
    }
    select.value=file.stream_index !== undefined ? String(file.stream_index) : file.streams.length===1 ? String(file.streams[0].index) : "";
    select.disabled=file.staged === true;
    select.addEventListener("change",()=>{
      const value=select.value==="" ? undefined : Number(select.value);
      if(activeGuiAudio) file.stream_index=value; else directMediaStreams.stream_index=value;
      invalidateMediaPlan();
    });
    label.append(select); host.append(label);
  }
  mediaIdentity.disabled=activeGuiAudio?.files.some(file=>file.staged) || guiBatchBusy;
}
async function readEpisodeMediaOptions(episode) {
  for(const file of episode.files) {
    if(file.streams || file.staged) continue;
    const payload=await queuePost("/api/v1/media/probe", {path:file.path}, {quiet:true});
    file.streams=payload.streams;
  }
}
async function prepareGuiMediaBatch() {
  for(const episode of guiAudioEpisodes().filter(item=>!item.files.some(file=>file.staged))) {
    await readEpisodeMediaOptions(episode);
    for(const file of episode.files) {
      if(file.streams.length>1 && file.stream_index===undefined) {
        selectGuiAudio(episode,false); mediaOptionsPanel.open=true; drawMediaOptions();
        throw new Error("GUI_AUDIO_STREAM_REQUIRED: Choose an audio stream before planning this episode.");
      }
    }
  }
  drawMediaOptions();
}
function decorateGuiMediaRequest(request, episode=null) {
  const files=episode?.files || activeGuiAudio?.files;
  const identity=files?.[0]?.recording_id || (!files ? directMediaIdentity : "");
  if(identity) {
    if(request.group_paths) request.group_id=identity; else request.recording_id=identity;
  }
  const streams={};
  if(files) files.forEach(file=>{if(file.stream_index!==undefined) streams[file.path]=file.stream_index;});
  else if(directMediaPath===request.path && directMediaStreams.stream_index!==undefined) streams[request.path]=directMediaStreams.stream_index;
  if(Object.keys(streams).length) request.selected_streams=streams;
  return request;
}
const renderAudioBeforeMediaOptions=renderGuiAudioChoices;
renderGuiAudioChoices=function() {renderAudioBeforeMediaOptions();drawMediaOptions();};
const selectAudioBeforeMediaOptions=selectGuiAudio;
selectGuiAudio=function(episode,announce=true) {selectAudioBeforeMediaOptions(episode,announce);drawMediaOptions();};
document.querySelector("#read-media-options").addEventListener("click",async event=>{
  const button=event.currentTarget, status=document.querySelector("#media-options-status"); button.disabled=true;
  status.textContent="Reading audio streams…";
  try {
    if(activeGuiAudio) await readEpisodeMediaOptions(activeGuiAudio);
    else { const payload=await queuePost("/api/v1/media/probe",{path:workflowInput.value}); directMediaStreams={streams:payload.streams}; directMediaPath=workflowInput.value; }
    drawMediaOptions(); status.textContent="Audio streams loaded. Review the processing plan after changing a choice.";
  } catch(error) {status.textContent=error.message;}
  finally {button.disabled=false;}
});
workflowInput.addEventListener("input",()=>{
  if(!activeGuiAudio && workflowInput.value!==directMediaPath) { directMediaStreams={}; directMediaIdentity=""; directMediaPath=workflowInput.value; drawMediaOptions(); }
});
nativeMediaInput.accept=""; // Content validation, including media with unusual extensions, happens on the server.
const mediaFolderButton=document.createElement("button"); mediaFolderButton.type="button";
mediaFolderButton.textContent="Add media from this directory";
mediaFolderButton.addEventListener("click",async()=>{
  const status=document.querySelector("#operation-status"); status.textContent="Finding media by content…";
  mediaFolderButton.disabled=true;
  try {
    const payload=await queuePost("/api/v1/media/discover",{path:workflowInput.value});
    for(const file of payload.files) if(!selectedGuiAudio.some(existing=>existing.path===file.path)) selectedGuiAudio.push({...file, language:document.querySelector("#workflow-language").value, speaker_count:document.querySelector("#workflow-speaker-auto").checked ? "auto" : Number(document.querySelector("#workflow-speaker-count").value)});
    const next=guiAudioEpisodes().find(item=>!item.files.some(file=>file.staged));
    if(next) selectGuiAudio(next);
    const label=document.createElement("span");label.textContent="Media files found:";status.replaceChildren(label,` ${payload.files.length}`);
    if(payload.truncated) {const note=document.createElement("span");note.textContent="Scan limit reached; choose a smaller directory.";status.append(" · ",note);}
  }catch(error){status.textContent=error.message;}
  finally{mediaFolderButton.disabled=false;}
});
workflowInput.after(mediaFolderButton);
drawMediaOptions();
