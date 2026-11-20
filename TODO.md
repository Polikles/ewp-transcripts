# Immediate work queue

Updated: 2026-11-20. Read WORK_POLICY.md, WORK_STATUS.md and the active checkpoint after resume.
Authoritative sequencing: [roadmap](docs/99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20).

## Current state: package A owner-feedback fixes implemented; focused retest pending

Active checkpoint: [package A execution](docs/checkpoints/2026-11-20-package-a.md).
The owner explicitly instructed “ok, zaczynaj z A”. The earlier planning-only hold is revoked
for A1–A4 and its verification/checklist. A is implemented and automatically verified; use the
[owner checklist](Instructions/GUI_PACKAGE_A_TEST_CHECKLIST.md). Package B remains gated on
owner acceptance of A.

## Active A acceptance fixes — owner feedback

Checkpoint: [A acceptance fixes](docs/checkpoints/2026-11-20-package-a-feedback.md).

- [x] Correct rail next-step labels for staged/queued/running/failed/cancelled ASR; distinguish ASR complete from workflow finished.
- [x] Show modal/translucent restore progress with loaded/total saved queue jobs until queue and editor recovery finish; no automatic ASR/consent.
- [x] Retry replaces the failed/cancelled queue row with a fresh attempt; label Retry / Ponów.
- [x] Fix valid cancelled attempts being omitted from saved work; accurately report actual omissions and localize the message.
- [x] Merge GUI Inspect and Dry-run into one planning step, keeping safety/hash/explicit confirmation; first-use planning must remain valid when confirmation is checked.
- [x] Show the custom gear during batch planning and restoration, and correct untranslated new cancellation/cleanup messages.
- [x] Infer skipped optional LLM correction when manual review/downstream work begins, so next-step/finished state follows actual work.
- [x] Explain raw ASR results/segments/transcript files and distinguish retained durable media from temporary cleanup; preserve owner-qualified cleanup/export behavior.
- [x] Fix cramped/unstable native audio controls; remove the redundant permanent speed selector once browser controls have sufficient room, preserving seeking/mixed playback.
- [x] Run focused regression/browser/restart/package checks, update retest checklist and commit/push A fixes. Package B remains gated.
- [x] Record the final two-column EN–PL approval requirement after functional additions and before the full EN/PL manual rewrite. The actual task-10 export is still pending; no artist ZIP changes.
- [ ] Owner runs [the focused feedback retest](Instructions/GUI_PACKAGE_A_RETEST.md); fix/retest any remaining A defects before B.

Owner evidence: restart preserves edits and leaves ASR/checkboxes stopped/unset; waiting/running
cancellation and no rerun of completed ASR work on WSL; temporary cancelled workdir deletion and
versioned export downloads/restart recovery pass. Legacy workdirs remain protected, durable media
remains present. These successes are retained while the reported defects are fixed.

## Package A — original tasks 1–4, in order

- [x] A1: Check latest restart recovery (queue, saved source/translation reviews, publication/export pointers). Preserve owner acceptance of already tested workflows. Full profile transfer may be checked during Windows work.
- [x] A2: Cancel waiting/running tasks safely with honest requested/cancelled status, no incomplete final publication, and restart-from-beginning retry semantics.
- [x] A3: Workdir immutable creation time and retained reason (failed/cancelled/successful-retained); preview/filter explicit cleanup without deleting referenced or final artifacts.
- [x] A4: Download verified existing exports through the GUI, preserving exact artifact/version identity and avoiding ASR reruns.
- [x] Run relevant regression/packaging checks, then deliver one concrete manual checklist for the implemented A package.
- [ ] Owner tests A; fix reported defects, update checkpoint/checklist and repeat until accepted.
- [ ] Gate: package B starts only after A fixes pass and owner approves progression. Package A is authorized; package B is not started.

## Package B — original tasks 5–9, with cloud ASR inserted as 8a

- [ ] B5: Native Windows dependency/media/model/path/CLI/GUI launch support, sharing the same application and frontend as WSL.
- [ ] B6: Opt-in OS credential storage: save/read/remove API keys; preserve session-only fallback and exclude secrets from profiles/exports/logs.
- [ ] B7: Recent projects/sessions, named input/output locations, canonical-result directory scanning and optional profile export without embedded dictionaries.
- [ ] B8: Audio-stream choice, remaining native picker conveniences, content-aware media discovery and explicit IDs for same-name recordings.
- [ ] B8a: Optional cloud ASR, after B8 and before B9. Select the initial provider/model and cost/consent boundary before implementing/calling that integration; no paid calls or media uploads are authorized now.
- [ ] B9: Complete package regression and prepare the one full native-Windows + WSL workflow test/checklist.
- [ ] Owner runs full Win/WSL workflow; fix issues and repeat until accepted, then freeze chosen functionality.

Before B, confirm the target Windows test environment and how the owner and agent will divide
native-Windows execution. This does not block A planning or its later authorized implementation.

## After package B acceptance

- [ ] Task 10: Generate the complete editable EN–PL label/message/error/state/hint/tooltip/guide/dynamic-template file, preserving diagnostic codes; owner corrects and approves it.
- [ ] Task 11: Finalize English instructions and full Polish documentation after terminology approval.
- [ ] Task 12: Later installer/distribution preparation; actual release/publishing remains a separate owner decision.
- [ ] Parallel, no deadline/non-blocking: integrate artist icons/feedback when supplied. Do not modify the sent ZIP/demo. Documentation screenshots wait for final custom GUI/icons.

## Nice-to-have only

- Ollama/further local-model expansion; word/phrase-level playback highlighting (not whole-block highlighting).
- Alignment/timing refinements and optional instruction review with less-technical users.
- Non-speech authoring, advanced channels/crosstalk/surround, audio repair/comparison and additional subtitle formats.
- Earlier optional research: private/public corpus benchmarks, universal dictionaries, model benchmark automation and hardware presets. No ETA/percentage accuracy study is scheduled.

## Removed / outside selected scope

- Full model catalog/favorites/local model-loading management; manual timing overrides.
- Alternative translation chunking and owned input snapshots; whole-block audio-follow highlighting.
- Additional LLM punctuation/editorial modes, speaker-count research, bilingual HTML and Docker from the old roadmap.
- Other unselected broad deployment/research/scheduling ideas are not package obligations and must not reappear as completion gates.

## Acceptance already retained

Owner accepts recent GUI/workflow, browsers/palette and current profiles provisionally. Owner confirms restart recovery (with missing progress feedback); full profile exchange remains
provisionally accepted without a complete owner test. Actual browser page zoom
200% remains optional/unchecked. Existing regression/security/lineage checks remain required.
Tested hardware is RTX 3090 24 GB; >=8 GB VRAM elsewhere is an unqualified expectation, without
a compatibility/performance guarantee. No completed acceptance is reopened because an old plan
calls it future.

## Delivered history

- [Batch planning, sentence-aware review and portable profiles](docs/checkpoints/2026-11-20-batch-sentences-profiles.md)
- [Mixed playback, progress and artist reference](docs/checkpoints/2026-11-19-review-mix-progress-artist.md)
- [Artist package sent for review](docs/checkpoints/2026-11-19-artist-review-package.md)
- [Playback and video](docs/checkpoints/2026-11-19-playback-video-progress.md)
- [Brand/palette and feedback](docs/checkpoints/2026-11-19-gui-review-and-brand-feedback.md)
- [Polish UI and recovery fixes](docs/checkpoints/2026-11-18-gui-localization-and-recovery.md)
- [Workflow polish](docs/checkpoints/2026-11-18-gui-workflow-polish.md)
- [Guided workflow](docs/checkpoints/2026-11-18-guided-workflow.md)
- [Native dependency repair](docs/checkpoints/2026-11-18-gui-dependency-repair.md)
- [Resolved launch diagnosis](docs/checkpoints/2026-11-18-gui-launch.md)

The repaired local-only ASR/source-export path on WSL/RTX 3090 and the later MP4/mixed playback
owner successes remain accepted. GUI-55 stays closed. Do not tag/publish a release as part of this
planning update. Do not reopen delivered work merely because a historical plan calls it future.
