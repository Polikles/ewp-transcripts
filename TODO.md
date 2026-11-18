# Immediate work queue

Updated: 2026-11-18.

Policy: [WORK_POLICY.md](WORK_POLICY.md). Product roadmap:
[docs/99-roadmap-v2.md](docs/99-roadmap-v2.md).

## Active: Polish UI audit and queue/translation recovery

Checkpoint: [localization and recovery](docs/checkpoints/2026-11-18-gui-localization-and-recovery.md).

- [x] Automatically load the dictionary catalog on first session initialization.
- [x] Put shared output before input paths; retain processing language separately per selected episode/file.
- [x] Fix Polish Transcribe wording: Sprawdź plik, Zaplanuj przetwarzanie, complete summaries/statuses/decision labels.
- [x] Audit all stages, dialogs, dynamic statuses, errors and hover text in EN/PL; preserve diagnostic codes and user content.
- [x] Translate the OpenRouter key dialog and correction/translation running/candidate states.
- [x] Reduce technical detail font size and prevent Add speaker overlapping the preceding input.
- [x] Rename source Prepare text for review / Apply and Polish equivalents; align Apply first on one line.
- [x] Rename source publication Save and prepare for export; make Export subtitles a normal section heading.
- [x] Update correction/translation generation and Continue to translation review wording.
- [x] Rename translation stage/Apply translation/Save translation/Save and prepare for export/Save and export consistently in guides and controls.
- [x] Fix reopening a saved/applied translation and exporting after stage navigation without regenerating a candidate.
- [x] Fix Start queue activation whenever staged work exists; preserve completed ASR jobs and support later additions after completion/cleanup.
- [x] Verify regressions, complete localization audit, update changelog/roadmap/checkpoints and deliver for WSL testing.
- [ ] Owner approves final EN/PL function and section names and qualifies this revised workflow on WSL.

## Deferred: full Polish user documentation

- [ ] After the owner accepts function/section terminology, prepare the complete user guide and documentation in Polish. English remains the repository's primary language; Polish documentation is explicitly supported.

## Previous delivery: GUI workflow polish and library management

Checkpoint: [workflow polish](docs/checkpoints/2026-11-18-gui-workflow-polish.md).

- [x] Reduce top header gap; make Quick steps vertical; strengthen light-theme artwork.
- [x] Advance Inspect across selected episodes; prevent inspecting/planning already staged episodes.
- [x] Remove queue selection checkboxes/bulk removal; retain per-row removal and add completed-only cleanup.
- [x] Route recording-rail selection to that recording's current workflow step.
- [x] Mute technical details, hints and legends; place every legend below its queue.
- [x] Collapse optional correction dictionaries by default.
- [x] Add dictionary viewing, version comparison, new/example creation, immutable editing and library removal.
- [x] Replace duplicate palette choices with configured profiles and Preview / Apply / Save; support custom profiles; name preset EwP brand; remove browser confirmation.
- [x] Equalize source review panels; align Undo/Redo/Clear at half-screen and all controls on wide screens.
- [x] Preserve owner-confirmed cursor splitting and selected-text separation.
- [x] Translation: move Skip below queue/legend; remove Open manual translation; rename step 3 Generate candidate.
- [x] Translation: highlight inferred direction and show an explicit accept action when changing source direction.
- [x] Collapse auto-filled translation inputs and optional dictionary; prevent status-label word splitting.
- [x] Translation review: secondary right-aligned Clear below Preview; add Apply and Audit/export hover explanations.
- [x] Update per-stage instructions, prototype comparison, changelog, roadmap and checkpoints.
- [x] Run required checks and model-free browser workflows; deliver verified changes for WSL retest.
- [ ] Owner retests these changes on WSL; API/provider and YouTube qualification stay pending.

## Deferred: artist reference package

- [ ] After GUI fixes/tweaks are complete, create a small frontend-only GUI review package the artwork artist can open to review the interface and design replacement icons.

## Completed delivery history

## GUI launch diagnosis completed; WSL launch confirmed

Checkpoint: [2026-11-18 launch diagnosis](docs/checkpoints/2026-11-18-gui-launch.md).

- [x] Recover repository state, previous verification and private reference location.
- [x] Establish persistent work policy, todo and task checkpoint.
- [x] Reproduce package/CLI/server launch with the locked Python environment.
- [x] Inspect staging/start/error paths and run existing queue/integration coverage.
- [x] Reproduce native speech-runtime diagnostics without models or downloads.
- [x] Identify supplied WSL error: `uv` ran in `ewp-waveform`, which lacks `transcriber`.
- [x] Document recovery and run required local checks (781 tests; five integration tests).
- [x] Record remaining WSL evidence and a bounded owner retest in the checkpoint.
- [x] Owner confirms GUI launch from the correct transcription checkout.
- [x] Capture actual WSL queue/backend error: missing FFmpeg libraries disable TorchCodec.

## Completed: dependency repair and GUI feedback

Checkpoint: [dependency repair](docs/checkpoints/2026-11-18-gui-dependency-repair.md).

- [x] Add a guided native-runtime repair preserving locked ML versions.
- [x] Put Test, doctor and repair controls in Settings & About, with post-test activation.
- [x] Accept Ubuntu 26.04 alongside 24.04 in diagnostics and installation tools.
- [x] Rename Remove from list and reduce queue width/spacing at half-screen.
- [x] Run automated gates, real native audio decoding and available browser checks.
- [x] Record remaining GPU/WSL qualification and exact owner retest commands.
- [x] Owner runs repair and retries the short staged episode on the RTX 3090 (local workflow through subtitle export passed).

## Previous delivery: guided workflow, review fixes and prototype comparison

Checkpoint: [workflow usability](docs/checkpoints/2026-11-18-guided-workflow.md).

Consult this list before each implementation slice and after any context reset.

- [x] Verify native dependency setup is automatic in installation; add installer regression coverage.
- [x] Explain Ubuntu 24.04 → 26.04 upgrade mismatch in errors and link exact recovery instructions.
- [x] Add short numbered instructions below active-recording context for every workflow stage.
- [x] Ship one detailed instruction document per stage, including optional stages, linked from the GUI.
- [x] Match section numbering and action names to each stage's instructions; clarify next actions.
- [x] Reduce the visual emphasis of Skip LLM-assisted correction.
- [x] Place compact Prepare and validate / Draft and history panels side by side below transcript review and above human verification.
- [x] Keep Preview from scrolling away from the current review position.
- [x] Reduce the vertical footprint of workflow queue lists without losing item identity or actions.
- [x] Combine YTT profile with Speaker names and colors; update visible swatches on profile changes.
- [x] Rename Add revision-only speaker to Add speaker.
- [x] Reproduce and fix Split at cursor with actual user caret, draft saving, pointer and keyboard activation.
- [x] Make transcript text boxes grow with content on load, edits, navigation and width changes.
- [x] Compare the updated app against the private prototype and workflow/visual references; fix in-scope discrepancies and record exclusions.
- [x] Verify automated gates, browser workflows, package/help resources and update durable checkpoints.
- [x] Prepare verified changes and a commit-ready handoff for the next WSL test without a release/tag.
- [ ] Owner retests the new guided workflow, compact review and caret behavior on WSL.

Owner evidence: local-only transcription through subtitle export succeeded on WSL/RTX 3090;
API-assisted correction/translation is not qualified by that report. Reported ONNX DRM and
WhisperX VAD terminal lines did not prevent completion. Do not reopen the resolved ASR blocker.

## Other following work

- Resume the consolidated GUI preview acceptance session after startup is understood.
- Record WSL/browser, real GPU/provider and actual zoom results against the existing
  owner test plan; leave the new-palette YouTube qualification pending until observed.
- Keep GUI-55 closed. Do not tag or publish the internal 0.20.0 preview.
