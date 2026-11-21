# Transcribe

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose output and recordings: Choose the shared output directory first, then audio or video files. Select matching speaker tracks for one episode together.
2. Plan and add to queue: Choose language and speaker count per recording. Dry-run checks and plans all unqueued files. Review the full plan, confirm it and Add to queue once for the batch.
3. Start queue: Start queue runs staged episodes in order. After completion, continue to optional correction or source review.

## Detailed instructions

Picking files does not start ASR. Dry-run inspects and plans the selected files without loading models. Transcription uses pinned local models and the system media tools. A grouped episode must contain synchronized, compatible tracks.

Failed items retain a diagnostic code and technical details; other completed work remains available. Settings & About contains optional dependency diagnostics and the Ubuntu upgrade repair guide.

Use Add saved results in a stage queue to work from existing canonical JSON without repeating transcription. Save current work state before stopping the GUI.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

Dry-run checks and plans all selected, unqueued episodes. Add to queue advances to the next available episode; staged inputs cannot be planned again. Each inactive queue row has Remove. Remove completed tasks from the queue appears only for recordings whose workflow is finished and preserves unfinished/failed jobs and every saved file. Recording cards on the left open that recording’s next unfinished stage.

The language selector belongs to the selected recording; switching recordings restores its language. Grouped tracks share their episode language. Planning uses each recording’s selection. Start queue handles newly staged items alongside completed history and never reruns completed ASR. Adding later files and removing completed items do not leave Start disabled.

The path help belongs directly below the server input field, before the selected-file list. The (i) control beside language selection notes an observed behavior: EN for Polish audio has sometimes produced readable English text, but this is not a guaranteed translation mode and still requires review/correction. It does not change the actual transcription task or replace the optional translation workflow.

Video input supports MP4, MKV, MOV, WebM, AVI and M4V with one decodable audio stream.
The video is retained as the original hashed source; FFmpeg extracts its selected audio stream
into the normal private working WAV. Frame/image analysis is not performed. The normal
Dry-run → Add to queue → Start queue sequence is unchanged. A video without audio
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

## Cancel and retry a task

Use Cancel task on a waiting or running row. Waiting work becomes Cancelled immediately. Running
work shows Cancellation requested until its current FFmpeg/model stage returns and reaches a safe
checkpoint; it may take time during a long ASR call. There is no forced thread/GPU interruption.
Cancellation is refused after final publication starts. A cancelled attempt publishes no incomplete
canonical result, and its temporary work follows keep_temp_on_error. Other queue tasks continue.
Retry stages a new attempt with the same settings; Start queue runs it after checking
the original source hashes again. Changed sources require a new Dry-run/confirmation.
Retry replaces that cancelled/failed queue row with a fresh staged attempt. Existing files and retained temporary workdirs remain unchanged.

## Raw ASR files

With the shipped output defaults, successful ASR creates three raw, unreviewed files in the shared
output folder: `<episode>_results.json` (canonical word/timing/speaker data),
`<episode>_segments.json` (derived segments), and `<episode>_transcript.txt` (readable text).
The JSON is the source of truth; the other two outputs are derived and may be disabled in config.
These are raw ASR results, not a manually verified publication. Review the transcript and export
from the accepted revision for publication. A `*_results.failed.json` records failure/cancellation
state and is not a completed canonical result.

## Audio streams and recording identities

Audio streams and recording ID applies to the selected episode. Read audio streams displays each
source's stream index/language/title. A multi-stream source requires an explicit choice; channel
analysis and ASR use that same selected stream. Changing the choice invalidates the processing
plan. Queue retry and saved-work recovery retain it. A single audio stream needs no manual choice.

Recording ID is optional. For separate inputs with the same basename, select each episode and
assign a distinct ID before planning; IDs are visible in the input list and output plan. Source
filenames/bytes remain unchanged. Multi-file episode grouping is retained; an ID names the whole
group. Duplicate planned IDs are rejected rather than overwriting another episode.

Choose directory fills the server input path. Add media from this directory then scans its first
500 entries by decodable content, including unusual extensions. It is non-recursive and never
starts ASR. Review the resulting list, language/count and any stream choices, then plan/add/start.
Native file/directory buttons are also available for result, dictionary and workspace paths.
Without a desktop picker, use direct path entry. Windows/WSL dialog output uses UTF-8.
