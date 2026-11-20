# Transcribe

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose output and recordings: Choose the shared output directory first, then audio or video files. Select matching speaker tracks for one episode together.
2. Inspect file: Choose processing language separately for each selected recording and speaker count or auto-detection. Inspect checks all unqueued selections.
3. Plan and add to queue: Run Dry-run for all unqueued selections, review and confirm the full plan, then Add to queue once for the entire batch.
4. Start queue: Start queue runs staged episodes in order. After completion, continue to optional correction or source review.

## Detailed instructions

Picking files does not start ASR. Inspect and Dry-run do not load models. Transcription uses pinned local models and the system media tools. A grouped episode must contain synchronized, compatible tracks.

Failed items retain a diagnostic code and technical details; other completed work remains available. Settings & About contains optional dependency diagnostics and the Ubuntu upgrade repair guide.

Use Add saved results in a stage queue to work from existing canonical JSON without repeating transcription. Save current work state before stopping the GUI.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

Inspect checks all selected, unqueued episodes. Add to queue advances to the next available episode; staged inputs cannot be inspected or planned again. Each inactive queue row has Remove. Remove completed tasks from the queue appears only for recordings whose workflow is finished and preserves unfinished/failed jobs and every saved file. Recording cards on the left open that recording’s next unfinished stage.

The language selector belongs to the selected recording; switching recordings restores its language. Grouped tracks share their episode language. Inspect uses each recording’s selection. Start queue handles newly staged items alongside completed history and never reruns completed ASR. Adding later files and removing completed items do not leave Start disabled.

The path help belongs directly below the server input field, before the selected-file list. The (i) control beside language selection notes an observed behavior: EN for Polish audio has sometimes produced readable English text, but this is not a guaranteed translation mode and still requires review/correction. It does not change the actual transcription task or replace the optional translation workflow.

Video input supports MP4, MKV, MOV, WebM, AVI and M4V with one decodable audio stream.
The video is retained as the original hashed source; FFmpeg extracts its selected audio stream
into the normal private working WAV. Frame/image analysis is not performed. The normal
Inspect → Dry-run → Add to queue → Start queue sequence is unchanged. A video without audio
reports NO_AUDIO_STREAM. Multiple audio tracks report MULTIPLE_AUDIO_STREAMS: export the
intended audio track to a separate file and process it. The application does not choose a
possibly wrong track silently. Container/codec availability depends on the installed FFmpeg.

While running, the queue shows the real backend phase, a gear, elapsed time and approximate phase
percentage. The first run uses coarse phase weights; an opaque inference call can hold its percent
while elapsed time continues. ETA becomes a range after successful comparable runs on this machine.
It uses local measured phase timings, duration, model/runtime settings and source topology. If a
phase takes too long, ETA is withdrawn instead of counting down to zero. Completion is 100% only
after result publication, configured exports and required cleanup finish. A failed job never displays
100%. These estimates do not predict human correction/review time. No transcript text is retained
in the bounded timing cache. See the runtime progress assessment for algorithm details.

The (i) language popup closes on outside click/tap or Escape; Escape returns focus to the icon.

Inspect does not run ASR and media metadata does not supply spoken language or speaker count.
Its summary shows language with * and speaker count with **, with separate full-width wrapping
notes below the tables after both Inspect and Dry-run;
automatic detection remains a processing request until transcription resolves it. Dry-run displays
one combined plan for all pending selected episodes, with per-episode settings. Changing the
selection/output/settings requires a new dry-run and confirmation. Already staged inputs are
excluded. A completed matching result is shown as skipped, rather than transcribed again.
If staging fails partway, earlier staged jobs remain visible; fix the error and replan the remaining
list. Planning/staging does not start ASR; Start queue is a separate explicit action.

The confirmation reads I reviewed the plan and want to add jobs to the queue. It still requires
review of this exact batch snapshot; the shorter plural wording does not weaken validation.
