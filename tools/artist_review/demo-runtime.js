/* Artist-only in-memory adapter. No request is forwarded to a network or transcription backend. */
"use strict";
(() => {
  const data = window.EWP_ARTIST_DATA;
  const copy = value => structuredClone(value);
  const stages = ["transcription","correction","review","original_export","assisted_translation","translation","translated_export"];
  const root = "/demo/project";
  function job(index) {
    const name = `DEMO0${index}`, result = `${root}/${name}_results.json`;
    return {job_id:`demo-${index}`, status:index===3?"staged":"completed", input_path:`/demo/media/${name}.wav`, output_directory:root,
      planned_job_id:name, planned_result_path:result, result_path:index===3?null:result, language:"en", speaker_count:2,
      created_at:new Date().toISOString(), updated_at:new Date().toISOString(), group_sources:{}, source_sha256:"0".repeat(64), error:null,
      workflow:Object.fromEntries(stages.map(stage=>[stage,{state:stage==="transcription"&&index!==3?"complete":"pending",path:stage==="transcription"&&index!==3?result:null}]))};
  }
  let jobs=[job(1),job(2),job(3)], dictionaries=[], reviews={}, translations={}, workspaces=[], serial=0, simulationStarted=0, credentialConfigured=false, credentialSaved=false, savedProfile=null;
  const profiles=copy(data.profiles);
  const dictionary={dictionary_version:"1.1",dictionary_id:"demo-pl-v1",project_id:"artist-demo",job_ids:["*"],language:"pl",proposal_sha256:"0".repeat(64),manual_conventions:[],entries:[{source:"przykładowy termin",target:"preferowany termin",status:"approved"}]};
  dictionaries.push({document:dictionary,path:"/demo/dictionaries/demo-pl-v1.json",sha256:"0".repeat(64),kind:"correction",dictionary_id:dictionary.dictionary_id,project_id:dictionary.project_id,language:"pl",version:"1.1",hidden:false});
  const response=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{"Content-Type":"application/json"}});
  const failure=(code,message)=>response({error:{code,message}},400);
  function selected(result) { return jobs.find(item=>item.result_path===result || item.planned_result_path===result) || jobs[0]; }
  function review(result) {
    if (!reviews[result]) {
      const item=selected(result), doc=copy(data.review);
      doc.result_path=result || item.planned_result_path;doc.review_path=`${root}/reviews/${item.planned_job_id}.review.txt`;doc.job_id=item.planned_job_id;doc.review_sha256=String(++serial).padStart(64,"0");reviews[doc.result_path]=doc;
    }
    return reviews[result] || reviews[jobs[0].planned_result_path];
  }
  function translation(request) {
    const key=request.result_path || jobs[0].planned_result_path;
    if (!translations[key]) { const doc=copy(data.translation);doc.result_path=key;doc.job_id=selected(key).planned_job_id;doc.review_path=`${root}/translation-reviews/${doc.job_id}.txt`;doc.review_sha256="1".repeat(64);doc.revision_path=request.revision_path||"";doc.parent_translation_path=request.parent_translation_path||"";translations[key]=doc; }
    return translations[key];
  }
  const session = doc => ({project_output_directory:root,result_path:doc.result_path,review_path:doc.review_path,review_output_directory:`${root}/reviews`,revision_output_directory:`${root}/revisions`,export_output_directory:`${root}/exports`,applied_revision_path:"",source_revision_path:""});
  const stamp = () => String(++serial).padStart(64,"0");
  window.fetch=async (input,options={})=>{
    const raw=String(input instanceof Request?input.url:input);
    const path=new URL(raw,location.href).pathname;
    let request={};try { request=JSON.parse(options.body||"{}"); } catch (_) { /* Native file selection is ignored. */ }
    const headers=new Headers(options.headers||{});
    if(path==="/api/v1/health")return response({status:"ok",api_version:"1.0",application_version:"0.20.0-design-demo"});
    if(path==="/api/v1/about")return response({application:"EwP design demo",application_version:"0.20.0",api_version:"1.0",license_url:"LICENSE.txt",repository_url:"README.html",issues_url:"README.html"});
    if(path==="/api/v1/session")return response({csrf_token:"artist-demo-not-a-secret",openrouter_key_configured:credentialConfigured});
    if(path==="/api/v1/guides")return response(data.guides);
    if(path==="/api/v1/operations")return response({operations:[]});
    if(path==="/api/v1/transcriptions" && (!options.method||options.method==="GET")) {
      const active=jobs.find(item=>item.status==="running");
      if(active){const elapsed=Math.floor((Date.now()-simulationStarted)/1000);active.runtime_progress={phase:"transcribe",percent:Math.min(85,12+elapsed),estimated:true,elapsed_seconds:elapsed,phase_elapsed_seconds:elapsed,eta_seconds:60,eta_min_seconds:30,eta_max_seconds:100,calibrated:true,overdue:false,stream_index:1,stream_count:2};}
      return response({jobs:copy(jobs)});
    }
    if(path==="/api/v1/workspaces/locations")return response({locations:{output_directory:root,workspace_directory:"",recent_directories:[]}});
    if(path==="/api/v1/projects/list")return response({recent:[],locations:[]});
    if(path.startsWith("/api/v1/projects/"))return response({updated:true,results:[]});
    if(path==="/api/v1/credentials/openrouter") {
      if(request.action==="remove"){credentialSaved=false;credentialConfigured=false;}
      else if(request.action==="clear-session")credentialConfigured=false;
      else if(request.action==="save"){credentialSaved=true;credentialConfigured=true;}
      else if(request.action==="use")credentialConfigured=credentialSaved;
      else credentialConfigured=true;
      return response({configured:credentialConfigured,stored:credentialSaved,environment_configured:false});
    }
    if(path==="/api/v1/speech/check")return response({ready:true,detail:"Synthetic connection check only; no key or recording is sent."});
    if(path==="/api/v1/speech/estimate")return response({models:[],estimates:[],estimated_total_usd:0});
    if(path.startsWith("/api/v1/profile/")) {
      if(path.endsWith("save"))savedProfile={name:request.name,preferences:copy(request.preferences),fields:copy(request.fields),workspaces:[],dictionaries:[]};
      if(path.endsWith("import"))savedProfile=copy(request.profile);
      return savedProfile?response({profile:copy(savedProfile)}):failure("GUI_PROFILE_INVALID","Save a synthetic demo profile first.");
    }
    if(path==="/api/v1/exports/list")return response({exports:[],directory:request.export_output_directory});
    if(path==="/api/v1/workdirs/inventory")return response({entries:[]});
    if(path==="/api/v1/select-output-directory")return response({path:root});
    if(path==="/api/v1/selected-media/upload")return response({path:`/demo/media/${decodeURIComponent(headers.get("X-EWP-Filename")||"selected.mp4")}`});
    if(path==="/api/v1/import-canonical-file")return response({imported:true,job:copy(jobs[0])});
    if(path==="/api/v1/inspect")return response({operation_id:"demo-inspect",kind:"inspect",status:"completed",input_path:request.path,language:request.language||"en",speaker_count:2,result:{episodes:[{job_id:"DEMO04",duration_ms:8000,sample_rate_hz:16000,sources:[{fingerprint:{filename:String(request.path).split("/").pop(),path:request.path},stream:{channels:1,sample_rate_hz:16000,index:0,codec:"pcm_s16le"},duration_ms:8000,media_type:"audio",channel_mode:"mono",channel_classification:{processing_mode:"mono"}}],warnings:[]}],discovery:{files:[],skipped:[]}}});
    if(path==="/api/v1/dry-run")return response({operation_id:"demo-plan",kind:"dry-run",status:"completed",input_path:request.path,result:{output_directory:request.output_directory||root,jobs:[{job_id:"DEMO04",decision:"process",episode_signature_sha256:"0".repeat(64),outputs:{results_json:`${root}/DEMO04_results.json`,result_version:1},warnings:[]}],warnings:[]}});
    if(path==="/api/v1/transcriptions") {const item=job(jobs.length+1);item.input_path=request.path;item.status="staged";jobs.push(item);return response(item,202);}
    if(path==="/api/v1/transcriptions/start"){simulationStarted=Date.now();jobs.filter(item=>item.status==="staged").forEach(item=>item.status="running");return response({queued:1});}
    if(path.includes("/transcriptions/clear-current")){const removed=jobs.length;jobs=[];return response({removed});}
    if(path.includes("/transcriptions/remove")){jobs=jobs.filter(item=>request.job_ids?!request.job_ids.includes(item.job_id):item.status!=="completed");return response({removed:1});}
    if(path.includes("/transcriptions/workflow-")){const item=selected(request.result_path);if(path.endsWith("skip"))item.workflow[request.stage]={state:"skipped"};if(path.endsWith("reopen"))item.workflow[request.stage]={state:"pending"};if(path.endsWith("error"))item.workflow[request.stage]={state:"failed"};return response({updated:true});}
    if(path.startsWith("/api/v1/reviews/")){
      const action=path.split("/").pop(),doc=review(request.result_path);
      if(action==="playback")return response({url:"demo-audio.wav",source_id:"mix"});
      if(action==="playback-position")return response({start_ms:request.block_index?4320:1240,approximate:false});
      if(action==="restore")return response({...copy(doc),session:session(doc),session_path:`${root}/demo-session.json`});
      if(action==="save" && path.includes("/session/"))return response({session_path:`${root}/demo-session.json`});
      if(action==="save"){doc.anchors=copy(request.anchors);doc.speaker_labels=copy(request.speaker_labels||doc.speaker_labels);doc.review_sha256=stamp();return response(doc);}
      if(action==="preview")return response({revision_number:1,statistics:{source_tokens:8,revision_tokens:8,substitutions:1,insertions:0,deletions:0,speaker_changes:0,alignment_warnings:0},warnings:[]});
      if(action==="apply"){selected(doc.result_path).workflow.review={state:"complete",path:`${root}/revisions/${doc.job_id}_revision_001.json`};return response({revision_path:selected(doc.result_path).workflow.review.path,revision_number:1,warnings:[]});}
      if(action==="export"){selected(doc.result_path).workflow.original_export={state:"complete",path:`${root}/exports/${doc.job_id}.srt`};return response({written:[`${root}/exports/${doc.job_id}.srt`],skipped:[]});}
      return response(doc);
    }
    if(path.startsWith("/api/v1/translation-reviews/")){
      const action=path.split("/").pop(),doc=translation(request);
      if(action==="save"){for(const target of request.targets||[]){const unit=doc.units.find(item=>item.unit_id===target.unit_id);if(unit)unit.target_text=target.target_text;}doc.review_sha256=stamp();return response(doc);}
      if(action==="preview")return response({statistics:{unit_count:doc.units.length,translated_unit_count:doc.units.length,empty_unit_count:0},warnings:[]});
      if(action==="apply"){selected(doc.result_path).workflow.translation={state:"complete",path:`${root}/accepted-translations/demo.json`};return response({translation_path:`${root}/accepted-translations/demo.json`,warnings:[]});}
      if(action==="audit-export"){selected(doc.result_path).workflow.translated_export={state:"complete",path:`${root}/translation-exports/demo.srt`};return response({written:[`${root}/translation-exports/demo.srt`],audit:{status:"passed",findings:[]}});}
      return response(doc);
    }
    if(path==="/api/v1/dictionaries/profiles")return response(profiles);
    if(path==="/api/v1/dictionaries/profile-save"){profiles.profiles.push({id:request.name,name:request.name,colors:request.colors,custom:true});return response(profiles);}
    if(path==="/api/v1/dictionaries/catalog")return response({items:copy(dictionaries.filter(item=>request.include_hidden||!item.hidden).map(({document,...item})=>item))});
    if(path==="/api/v1/dictionaries/view")return response(copy(dictionaries.find(item=>item.path===request.path)||dictionaries[0]));
    if(path==="/api/v1/dictionaries/visibility"){const item=dictionaries.find(item=>item.path===request.path);if(item)item.hidden=!request.visible;return response({updated:true});}
    if(path==="/api/v1/dictionaries/edition"){const doc=request.document;const item={document:copy(doc),path:`/demo/dictionaries/${doc.dictionary_id}.json`,sha256:stamp(),kind:doc.source_language?"translation":"correction",dictionary_id:doc.dictionary_id,project_id:doc.project_id,language:doc.language||"",version:doc.dictionary_version,hidden:false};dictionaries.push(item);return response(item);}
    if(path==="/api/v1/corrections/models")return response({items:(request.model_ids||[]).map(id=>({id,available:true,input:null,output:null}))});
    if(path.includes("/corrections/check")||path.includes("/translations/check"))return response({ready:true,provider:"demo",model:"synthetic-demo",detail:"Offline visual preview; no API call."});
    if(path.includes("/corrections/generate")){const item=selected(request.result_path);item.workflow.correction={state:"complete",path:`${root}/correction-candidates/demo.json`};return response({result_path:item.result_path,candidate_path:item.workflow.correction.path,provider:"demo",model:"synthetic-demo",statistics:{substitutions:1},warnings:[]});}
    if(path.includes("/corrections/") && path.endsWith("review"))return response(review(request.result_path));
    if(path.includes("/translations/generate")){const item=selected(request.result_path);item.workflow.assisted_translation={state:"complete",path:`${root}/translation-candidates/demo.json`,candidate_path:`${root}/translation-candidates/demo.json`};return response({result_path:item.result_path,candidate_path:item.workflow.assisted_translation.path,source_verification:"manually_verified",direction:{source_language:"en",target_language:request.target_language||"pl"},provider:"demo",model:"synthetic-demo",statistics:{unit_count:2},warnings:[]});}
    if(path.startsWith("/api/v1/workspaces/")){
      if(path.endsWith("/list"))return response({workspaces:copy(workspaces.map(item=>({...item,available:true,catalog:"Default",storage_directory:""})))});
      if(path.endsWith("/save")){const item={workspace_id:request.workspace_id||`demo-workspace-${++serial}`,name:request.name||"Visual review",saved_at:new Date().toISOString(),current_step:request.current_step,fields:copy(request.fields),staged_jobs:[],terminal_jobs:[]};workspaces=workspaces.filter(workspace=>workspace.workspace_id!==item.workspace_id);workspaces.push(item);return response({workspace:item});}
      if(path.endsWith("/load"))return response({workspace:workspaces.find(item=>item.workspace_id===request.workspace_id),restored_jobs:0});
      if(path.endsWith("/delete")){workspaces=workspaces.filter(item=>item.workspace_id!==request.workspace_id);return response({removed:true});}
    }
    if(path==="/api/v1/managed-sources/inventory")return response({sources:[],workspace_count:workspaces.length});
    if(path.startsWith("/api/v1/dependencies/"))return response({application_version:"design-demo",ready:true,checks:[{code:"demo",status:"pass",message:"Visual preview only — no runtime dependencies tested.",context:{}}]});
    if(path.includes("openrouter"))return response({configured:false,ready:true});
    return failure("GUI_DEMO_ROUTE_UNAVAILABLE","This backend action is simulated in the artist reference. Use the demo stage controls to review the interface.");
  };
  document.addEventListener("click",event=>{const anchor=event.target.closest("a");const href=anchor?.getAttribute("href")||"";if(href.startsWith("/help")){event.preventDefault();const url=new URL(href,"https://demo.invalid"),slug=url.pathname==="/help"?"index":url.pathname.slice(6);const locale=url.searchParams.get("lang")==="pl"?"pl/":"";window.open(`guides/${locale}${slug}.html`,"_blank","noopener");}},true);
  document.addEventListener("DOMContentLoaded",()=>{
    const toolbar=document.createElement("aside");toolbar.id="artist-demo-toolbar";toolbar.dataset.guiContent="true";
    toolbar.style.cssText="position:fixed;bottom:0;left:0;right:0;z-index:30;background:#fff7df;color:#243d4c;border-top:2px solid #c69d44;padding:.4rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;font:12px system-ui";
    const label=document.createElement("strong");label.textContent="ARTIST DEMO • Dane syntetyczne • No transcription / API";toolbar.append(label);
    for(const [text,action] of [["Running",()=>{simulationStarted=Date.now();jobs[2] ||= job(3);jobs[2].status="running";}],["Failed",()=>{jobs[2] ||= job(3);jobs[2].status="failed";jobs[2].error={code:"GUI_DEMO_FAILURE",message:"Synthetic error state for artwork review."};}],["Completed",()=>{jobs.forEach(item=>{item.status="completed";item.result_path=item.planned_result_path;item.workflow.transcription={state:"complete",path:item.result_path};});}],["Reset demo",()=>{for(const storage of [localStorage,sessionStorage])for(const key of Object.keys(storage))if(key.startsWith("ewp-"))storage.removeItem(key);location.reload();}]]){const button=document.createElement("button");button.textContent=text;button.style.cssText="font:12px system-ui;padding:.25rem .5rem";button.addEventListener("click",()=>{action();if(typeof refreshJobs==="function"){jobsSignature="";void refreshJobs();}});toolbar.append(button);}
    const gallery=document.createElement("a");gallery.href="icon-inventory.html";gallery.target="_blank";gallery.textContent="Icons / artwork inventory";toolbar.append(gallery);document.body.append(toolbar);document.body.style.paddingBottom="5rem";
    const output=document.querySelector("#output-path");output.value=root;output.dispatchEvent(new Event("change"));
  });
})();
