# Transcribe

Use the numbered steps below with the matching GUI stage.

1. Choose output and recordings: Choose the shared output directory first, then audio/video or saved canonical result JSON files. Select matching speaker tracks for one episode together.
2. Plan and add to queue: Choose language and speaker count per recording. Dry-run checks and plans all unqueued files. Review the full plan, confirm it and Add to queue once for the batch.
3. Start queue: Start queue runs staged episodes in order. After completion, continue to optional correction or source review.

## 1. Choose output and recordings

Choose one durable shared output folder before adding files. The main file picker and Add files in the left rail both accept supported audio/video and canonical `*_results.json`. Add all synchronized speaker tracks of one episode together. Video audio is extracted for processing; the original video is not changed. A canonical JSON result is imported for review, without ASR. Failure/partial JSON and arbitrary JSON are not completed results.

Supported defaults: WAV, MP3, FLAC, M4A, OGG, OPUS; MP4, MKV, MOV, WEBM, AVI, M4V. Actual decoding depends on FFmpeg and the source codec. A server-side path is an alternative to the picker; it must be accessible to the server. User-space Windows/WSL paths are accepted; system directories, symlinks and junction targets are blocked.

Names such as `s0e01-Szymon.wav` and `s0e01-Damian.wav` group as one episode, `s0e01`, with separate speaker streams. Different episode names stay separate. Tracks share time zero: they are not concatenated or drift-corrected. Matching sample rates are required. Duration differences above 100 ms warn; above 500 ms block unless an explicit supported mismatch override is used. If a file has multiple audio streams, read the warning and choose the intended stream arrangement before planning.

Language and speaker count belong to each recording, not to the whole queue. Select PL, EN or automatic language, and automatic or a known speaker count. Selected fallback values have `*`/`**` explanations when metadata does not provide them; these are choices, not detected facts. EN selected for Polish speech has occasionally produced plausible English text, but correctness is not guaranteed; use the explicit translation workflow for reviewed translations.

## 2. Plan and add to queue

Dry-run performs inspection and planning for all selected recordings that are not already queued. There is no separate GUI Inspect action. Read source grouping, language, speaker count, processing/skip decisions and warnings for every row. Resolve errors, confirm the exact plan and Add to queue once for the batch. A changed source, output or option requires a new plan and confirmation. Planning does not start ASR. Remove from list removes only an input selection.

The local GPU provider is the default. Cloud ASR is optional; expand the engine controls and choose OpenRouter plus a model. A queue can contain local and cloud jobs. Every active staged/running job must share the output folder. To use another output folder, finish or remove active rows first; terminal history alone does not lock the old output.

## Cloud model and cost choices

Available presets are `openai/whisper-large-v3`, `openai/whisper-large-v3-turbo`, `elevenlabs/scribe-v2` and `microsoft/mai-transcribe-2`. Availability and prices can change. Refresh and estimate cost checks current provider information and selected media duration. Checking a key or refreshing prices does not upload audio or create a transcription charge. The final bill can differ from the estimate; the internal guard is not a provider billing limit.

Whisper requires one speaker per track; mixed multiple-speaker audio is better handled by Scribe/MAI. The endpoint must return word timestamps, not just text. Long audio is automatically divided into requests below the 24 MB complete-request limit, including encoding overhead; overlapping context is merged on the original timeline. Uncertain speaker continuity needs manual review. The app does not invent word timestamps or silently make another paid attempt after a failed response.

Use [the shared OpenRouter key controls](settings.md). Cloud upload consent is specific to the currently staged jobs and is not saved. Restoring work, retrying or changing those jobs requires fresh consent. The application checks consent and the active key before starting any worker in a mixed queue. Loading saved work never authorizes an upload.

## 3. Start queue and continue

Start queue processes staged jobs sequentially, skipping completed ASR. Percentage and phases are approximate activity indicators; elapsed time is shown without needing ETA. The spinning gear means work is in progress. A completed ASR row continues to correction/source review; it does not mark the entire workflow finished.

Cancel task immediately cancels waiting work; running work waits for a safe boundary. Wait for a terminal status. Retry replaces the failed/cancelled row with a fresh staged attempt and starts processing from the beginning only after Start queue; it does not rerun completed jobs. Remove completed tasks from queue keeps unfinished/failed ones. Removing a queue row does not delete published files.

By default successful ASR writes `*_results.json`, `*_segments.json` and `*_transcript.txt`. These are raw results, not manually approved subtitles. See [Files and exports](outputs.md). Continue with [Optional correction](optional-correction.md) or directly [Source review & export](source-review.md). Save a checkpoint before stopping; [Saved work](saved-work.md) explains restart behavior.
