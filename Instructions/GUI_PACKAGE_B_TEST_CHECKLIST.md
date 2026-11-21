# Package B — full Windows 11 x64 and WSL workflow acceptance

Date: 2026-11-21. Agent implementation/automated checks and short live cloud checks are complete.
This is the owner acceptance gate, not a claim that the Linux VM qualified native Windows/GPU.
A remains accepted. Use a separate test output directory; do not modify the artist review ZIP.
Record the Git commit, OS, GPU/driver, browser and language with the results. Mark each item
separately for **Windows native** and **WSL**. Send diagnostic codes/technical details without keys.

## 1. Update, install and launch

- [ ] Windows: pull main in a Windows user directory, using a separate checkout/`.venv` from WSL.
  Follow [native setup](WINDOWS_NATIVE.md), including the Visual C++ runtime/NVIDIA driver and
  `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install`.
- [ ] Windows: explicitly prepare missing model snapshots with
  `uv run --locked --no-sync python scripts/setup-models.py`; gated models need accepted HF terms.
  Model preparation must complete without an NLTK blocked-regex import error.
  Model downloads must not occur during ordinary discovery/planning/transcription.
- [ ] WSL: pull main in the existing WSL checkout and run `uv sync --locked`.
  Existing model caches remain usable. Use the documented repair only if diagnostics fail.
- [ ] Both: run `uv run --locked transcriber --help`, then
  `uv run --locked transcriber doctor --test-speech-runtime` and
  `uv run --locked transcriber gui`. Windows is identified as native, not a missing WSL baseline.
- [ ] Both: Test local dependencies in Settings & About; verify FFmpeg executables **and** speech
  shared libraries load. Doctor/repair controls are enabled after testing. Do not confuse missing
  local models/CUDA with cloud ASR compatibility. Preserve failures for diagnosis.
- [ ] Windows: use normal user paths with spaces and Polish characters. Try native file/directory
  pickers and direct entry. WSL Windows drive paths still map to `/mnt/<drive>/…`.

## 2. Shared key and portable user state

- [ ] Enter a low-limit OpenRouter key for this session. Input clears after submission. ASR,
  correction and translation use this same key; keys never appear in JSON diagnostics/downloads.
- [ ] Explicitly Save key in OS credential store, clear the session, then Use saved OpenRouter key.
  Restart GUI: it must not silently unlock/use an OS credential; choose Use saved key explicitly.
  Test Remove saved key and confirm it cannot be loaded again. On WSL without Secret Service,
  a useful unavailable message and session-only fallback are expected; no plaintext store.
- [ ] Save/load/export a user profile with dictionaries included; import it in the other environment.
  Repeat with dictionaries excluded. Preferences, palettes, project references and workspace
  manifests transfer; dictionary-free export has no embedded dictionary bytes.
- [ ] Keys, consent checkboxes and running jobs never transfer. Missing foreign paths are visible
  and require selecting local equivalents; importing a profile must not create/use those paths.
  Transfer recordings/output trees separately. Dictionary import/export still works independently.

## 3. Projects, media streams and exact planning

- [ ] Remember an input/output location and a project; restart and open them. Remove their list
  entries: source/output files must remain. Missing locations/projects are indicated clearly.
- [ ] Scan a directory containing valid canonical results, an arbitrary JSON and a renamed valid
  result. Only valid canonical contents are offered. Add selected items to review queues; no ASR.
  If a result changes after scanning, it must be scanned again before adding.
- [ ] Choose synchronized speaker tracks plus a separate MP4. Test per-recording language/count.
  Dry-run plans all pending episodes, then one confirmation/Add stages all planned jobs.
- [ ] Use the shared file picker with media and canonical result JSON. No input-directory/discovery
  or Select episode actions remain. Media is probed by content; invalid files produce useful errors.
- [ ] Selected multi-stream media automatically reveals a warning and stream chooser. Choose one explicitly; ordinary one-stream media shows no extra panel.
  Check the selected language/title/index and transcribe the intended stream. Ambiguous inputs
  require a choice. Changing the stream/recording ID invalidates the old reviewed plan.
- [ ] Give same-name recordings distinct portable recording IDs. Planned output names differ;
  canonical provenance retains original source names/hashes. Save/restart/load a staged example:
  stream/ID/provider/model persist, ASR stays stopped and confirmation/consent stay unchecked.

## 4. Local transcription through source export

- [ ] Keep Local GPU selected initially. Run one short two-track PL episode and one video.
  Raw completed ASR creates `*_results.json`, `*_segments.json`, `*_transcript.txt` with default
  outputs enabled. They are raw, unreviewed results; the canonical JSON is authoritative.
- [ ] Queue progress/elapsed time update; completed ASR is not repeated. Cancel a waiting job and
  a running job; Retry replaces its row with a stopped staged attempt. Start skips completed ASR.
- [ ] Open source review directly (without manually skipping LLM correction); the next-step rail
  follows actual progress. Test audio seeking for each source and browser playback speed controls.
- [ ] Optionally generate a short OpenRouter correction with the shared key; manually review its
  candidate. Also test the local/manual path. A generated candidate is not a verified publication.
- [ ] Edit text/speakers/colors, split/merge blocks, undo/redo, Save draft and Restore saved draft.
  Apply/Confirm validates the saved draft. Save and prepare for export requires manual-review
  confirmation, with an explicit message/highlight if missing.
- [ ] Export SRT/VTT/YTT (and any normally used formats), download the exact versions and check
  source/speaker/timing identity. Changing a palette creates a new export, preserving older files.

## 5. Cloud ASR, same downstream workflow

Use short disposable excerpts, not full episodes for initial acceptance. These owner-run calls
are separate from the agent's completed USD 2 pilot; choose a dedicated low-limit provider key deliberately.
No benchmark or live EN sample is required: owner explicitly accepted PL-only pilot material.

- [ ] In Transcription engine choose OpenRouter and verify the four IDs: `openai/whisper-large-v3`,
  `openai/whisper-large-v3-turbo`, `elevenlabs/scribe-v2`, `microsoft/mai-transcribe-2`.
  Set the model before planning. Use Check key and OpenRouter connection, then Refresh models and estimate cost: no audio upload, four-model availability, current hourly prices and duration-based estimates. No user-entered job cap appears. Queue rows identify cloud jobs and their model.
- [ ] Plan/stage without audio upload. Start without cloud consent is rejected and jobs stay
  staged. Check upload/paid-usage consent and Start: only then may provider requests begin.
- [ ] Whisper: use separate synchronized speaker tracks, or explicitly select one speaker for a
  single source. Scribe/MAI: use a short mixed two-speaker source. Provider word timestamps and
  labels must survive into canonical results; missing capabilities fail with actionable details.
- [ ] Long mixed recordings split automatically; the full recording may exceed 24 MB. Every
  serialized JSON/base64 request stays below 24 MB, normally with 120-second core intervals plus
  shared context. Check the merged original timeline, text without boundary duplicates, real
  repetitions and consistent speaker labels. If overlap does not identify a voice confidently,
  source review shows a warning and preserves a distinct label for manual reassignment.
- [ ] Open the cloud canonical result in the same source review; save/apply a draft and export
  SRT/VTT/YTT. Cloud processing must not load local WhisperX/alignment/pyannote models.
- [ ] Internal cost protection rejects excessive workloads before upload; legacy fixed-guard jobs retain their limits.
  Invalid key/credits/model failures are useful and do not trigger automatic retries. An uncertain
  submitted request may be charged; explicit Retry can incur new charges. The guard is an estimate,
  not a hard OpenRouter billing cap. Cancellation waits for a safe request checkpoint.
- [ ] Save/restart/load a staged cloud job. Provider/model/cost mode survive; cloud consent and key do
  not. Confirm deliberately before starting again. Inspect content-free charge/model provenance
  in canonical processing stages; a failed retained workdir has `cloud-asr-usage.json`.

## 6. Translation, restart, cleanup and visual checks

- [ ] Generate a short optional translation with the shared key, or choose manual translation.
  Verify PL→EN default for a PL source; changing direction requires confirmation.
- [ ] Review/save/apply translation; navigate away/back, then Save and export without regenerating
  the candidate. Compare downloads with the exact accepted translation/revision lineage.
- [ ] Save work with staged/completed/failed tasks plus saved source and translation drafts.
  Stop server, restart, load: loading overlay stays through restoration; editors, exports and
  next-step rail return; no ASR/provider request starts and consent stays unchecked.
- [ ] Refresh saved exports; previous versions remain downloadable. Preview cleanup for cancelled
  temporary work; delete only explicitly selected eligible workdirs. Durable media/final outputs,
  references and protected legacy/unknown directories remain. Do not remove the private corpus.
- [ ] Check EN/PL, light/dark and half/full-screen layouts. Technical details remain secondary;
  custom gear appears during work. Actual 200% browser zoom is optional, not a new blocking gate.

## Report and next gate

Report **Windows / WSL / not available** for each group, failed action, expected/actual behavior,
terminal/technical code and commit. Do not send credentials or full private transcripts.
After fixes pass owner acceptance, freeze B functions and prepare task 10: the complete editable
EN–PL string-pair file. Owner terminology approval precedes full EN/PL documentation. Screenshots
wait for custom artwork/icons; the existing artist ZIP remains frozen and blocks no other work.

## Focused Windows feedback retest (2026-11-21)

- [ ] Pull the fix, stop/restart the GUI and refresh its browser page. No model reinstall is needed.
  Retry the failed audio group and MP4. Both should progress beyond initial state reservation,
  produce canonical/raw outputs and allow revision/translation/export publication. Keep old partial
  state for diagnosis; output versions are allocated without overwriting it.
- [ ] Main picker and Add audio accept both media and canonical result JSON. No input-directory
  picker, Add media from this directory or Select episode buttons remain. Output picker remains.
- [ ] Set different language/count for two pending episodes. One Dry-run table lists both with
  their settings and selection footnotes; Add to queue stages both.
- [ ] A single-stream file shows no stream/ID panel; a multi-stream file reveals a warning/chooser.
  Duplicate IDs reveal fields only when needed, then different IDs allow planning.
- [ ] An unexpected queue failure has one expandable summary per job, a Polish description and
  technical exception/OS codes/frame locations; the terminal also reports safe frame locations.
  With two failed jobs, neither generic guidance paragraph is repeated outside its disclosure.
- [ ] Cloud checks use the same key as correction/translation. Refresh with selected/staged media,
  compare four hourly prices and estimates; change source/settings and check the stale-estimate
  notice. No audio is uploaded by these checks. Start still requires fresh paid-upload consent.
