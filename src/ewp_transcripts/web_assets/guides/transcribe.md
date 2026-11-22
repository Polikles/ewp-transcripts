# Transcribe

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose output and recordings: Choose the shared output directory first, then audio/video or saved canonical result JSON files. Select matching speaker tracks for one episode together.
2. Plan and add to queue: Choose language and speaker count per recording. Dry-run checks and plans all unqueued files. Review the full plan, confirm it and Add to queue once for the batch.
3. Start queue: Start queue runs staged episodes in order. After completion, continue to optional correction or source review.

## Detailed instructions

Picking files does not start ASR. Dry-run inspects and plans the selected files without loading models. Transcription uses pinned local models and the system media tools. A grouped episode must contain synchronized, compatible tracks.

Failed items retain a diagnostic code and technical details; other completed work remains available. Settings & About contains optional dependency diagnostics and the Ubuntu upgrade repair guide.

Use the same main file picker or Add files in the left rail to add existing canonical JSON without repeating transcription; stage queues also retain Add saved results. Save current work state before stopping the GUI.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

Dry-run checks and plans all selected, unqueued episodes. Add to queue stages the full reviewed batch; staged inputs cannot be planned again. Each inactive queue row has Remove. Remove completed tasks from the queue appears only for recordings whose workflow is finished and preserves unfinished/failed jobs and every saved file. Recording cards on the left open that recording’s next unfinished stage.

Each pending recording has its own language and speaker-count controls in the file list. Grouped tracks share their episode settings; no Select episode action is needed. Planning uses each recording’s selection. Start queue handles newly staged items alongside completed history and never reruns completed ASR. Adding later files and removing completed items do not leave Start disabled.

The path help belongs directly below the server input field, before the selected-file list. The (i) control beside language selection notes an observed behavior: EN for Polish audio has sometimes produced readable English text, but this is not a guaranteed translation mode and still requires review/correction. It does not change the actual transcription task or replace the optional translation workflow.

Video input supports MP4, MKV, MOV, WebM, AVI and M4V with a decodable audio stream.
The video is retained as the original hashed source; FFmpeg extracts its selected audio stream
into the normal private working WAV. Frame/image analysis is not performed. The normal
Dry-run → Add to queue → Start queue sequence is unchanged. A video without audio
reports NO_AUDIO_STREAM. Multiple audio tracks reveal a warning and stream selector under that recording; choose the intended stream before planning. The application does not choose a
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

Dry-run does not run ASR and media metadata does not supply spoken language or speaker count.
Its summary shows language with * and speaker count with **, with separate full-width wrapping
notes below the tables after Dry-run;
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

Selected media is probed automatically. A multi-stream source reveals a warning and each stream's
index/language/title under its recording. Choose one explicitly; channel analysis and ASR use that
same stream. Single-stream files need no extra action. Changing the choice invalidates the plan.
Retry and saved-work recovery retain it.

Only an actual duplicate-ID collision reveals Recording ID fields. Assign distinct IDs and replan;
source names/bytes remain unchanged and an ID names the whole multi-file group.

Choose audio or video files and Add files share one picker, including saved canonical result JSON.
Removing a pending entry only removes it from the list. Direct server paths remain available.
Native file/directory buttons remain for output, result, dictionary and workspace paths.
Without a desktop picker, enter the path directly. Windows/WSL dialog output uses UTF-8.

## Optional OpenRouter ASR (package B)

Local GPU ASR remains the default. Open **Transcription engine**, choose OpenRouter and one of
Whisper Large V3, Whisper Large V3 Turbo, Scribe v2 or MAI-Transcribe 2. Manage the same OpenRouter
key used by correction/translation. No audio is uploaded during discovery, planning or staging.

1. Choose the recording language, speaker count, media/streams and cloud model before planning.
   Check key and OpenRouter connection verifies the shared session/environment key with /key.
   Refresh and estimate cost checks availability of the four presets, their live endpoint
   prices in USD per audio hour, and estimates pending selected/staged-cloud source durations.
   Both are explicit read-only actions: no audio/transcript is uploaded. No key is needed for
   public pricing. A missing/unpriced model is shown explicitly. After settings/selection changes,
   refresh the estimate; there are no automatic network refreshes. Replan after job settings change.
2. Plan, review and add the jobs. Starting a queue with cloud jobs requires explicit audio-upload
   and paid-usage consent. It clears after starting and is never saved in a workspace/profile.
   Before starting any worker (including local tasks in a mixed queue), the server checks that
   the shared key exists and authenticates it with OpenRouter's read-only `/key` endpoint.
   Missing/invalid keys or a failed connection leave the whole queue staged, without preparing
   media, creating transcription failure files or sending audio. Enter/load a key and explicitly
   confirm Start again. Local-only queues do not require this network check.
3. Provider word timestamps must be returned; text-only responses fail visibly instead of making
   up alignment. The same canonical JSON, raw TXT/segments, review and immutable exports follow.
4. Whisper needs one speaker or separate synchronized speaker tracks. Use Scribe/MAI for one
   mixed-speaker source. Long audio is split automatically (normally 120-second core intervals),
   with every complete JSON/base64 request kept below 24 MB. The recording itself has no 24 MB cap.
   Mixed chunks share up to five seconds of context on each side of the cut. Shared timed words
   reconcile request-local speaker IDs and prevent duplicate/missing boundary words. Provider word
   times return to the original recording timeline; intentional repetitions remain intact.
   If a speaker cannot be matched confidently, its label stays separate and source review shows
   a warning to check assignments across sections. There is no biometric speaker database.
5. Estimates include chunk context/rounding and show a range for unresolved stereo processing.
   Final provider charges may differ. Prices are checked again when starting cloud work. New GUI
   jobs calculate internal job-wide protection from all planned tracks and current prices (with
   conservative reserve and a USD100 internal safety ceiling), without a guessed user-entered cap.
   Existing saved jobs with explicit fixed guards retain them. This is not a provider billing cap;
   use a dedicated low-limit OpenRouter key. There is no automatic
   retry after a timeout/error. Explicit Retry starts again and can incur new charges.
6. Success records model, provider, word-timing provenance and reported/reserved charges in the
   canonical processing stages. Retained failed work includes a content-free cloud usage ledger.
   API keys and raw provider responses are not included. Cancellation takes effect at safe
   checkpoints; an already submitted request may still be charged. Source media is preserved.

Cloud ASR is exposed through the reviewed GUI queue and the explicitly authorized application
API. Existing CLI batch transcription remains local; it rejects a cloud config instead of silently
uploading media or substituting local models. Secure OS key storage is optional; after restart use
**Use saved key**, or enter a session key again.

Protocol reference: [OpenRouter speech-to-text](https://openrouter.ai/docs/guides/overview/multimodal/stt).


Cloud Start without paid-upload consent highlights/focuses the disclosure and sends no start
request. Consent is not permanently saved and is cleared after starting/restoring work. Missing
OpenRouter key after restart means enter a session key or explicitly use the saved OS key; it
does not require reinstalling models. Dry-run plan headings keep word boundaries; narrow phone
views may scroll only the plan table. Speaker-count automatic selection uses the shorter label
Automatically in the plan, while the language detection control keeps its normal wording.

Each cloud start now needs a fresh one-use confirmation for the exact staged queue. Loading saved
work invalidates an earlier confirmation; a changed/retried queue needs its checkbox selected again.
The server rejects an old browser's confirmation boolean without the matching grant, before any
worker is queued. The grant is not a credential and is never written to saved work or profiles.

## Provider timing and pending selections

Whisper Large V3/Turbo use the DeepInfra/Groq routes qualified for word timing. Text-only routes
are excluded from routing and current-price estimates. A model without an available compatible
endpoint is unavailable; no audio is sent to an arbitrary substitute. Scribe/MAI keep their own
model-provider options. Provider word times remain required; the application never estimates word
positions from plain text. An explicitly empty transcript can represent a no-speech fragment.

If a provider still omits timing, technical details include the model, chunk and response counts,
without transcript text or keys. Retained `cloud-asr-usage.json` has an `invalid-response` entry
and response-shape counts. There is no automatic paid retry. A key/connection check confirms
access, rather than guaranteeing that a later routed transcription response contains timed words.

Saving before Add to queue now preserves pending files and settings. Loading replans metadata
without ASR/upload and leaves confirmation unchecked. Repeat file selection does not duplicate
same-name/same-content items. Failure JSON files are not a cache of upstream transcript responses;
removing them does not fix missing word timestamps.
