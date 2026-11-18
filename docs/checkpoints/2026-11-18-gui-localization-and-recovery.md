# GUI localization and recovery — 2026-11-18

Baseline: clean main at cd7ce044a0e46e727f9a8676e4d31f3a995b1961.
Scope: complete active TODO list; preserve canonical language/revisions/exports, credentials,
provider consent and immutable artifacts. Repository stays English except Polish localization
and documentation. Full Polish documentation follows explicit terminology acceptance.

## Resume

Read AGENTS.md, WORK_POLICY.md, TODO.md, WORK_STATUS.md and roadmap before each slice/reset.
Prioritize Start queue and translation reopen regressions, then per-file language, UI wording,
layout and an exhaustive localization audit. Tests must reproduce stage navigation after
applied translation and starting later staged work alongside completed/failed history.
No paid provider calls, real ASR or model downloads are needed for these GUI fixes.

## Progress

- Complete user checklist recorded before implementation.
- Implementation, verification and delivery are complete. Owner retest/terminology approval remain pending.

## Diagnosis and first fixes

- Start handler dereferenced event.currentTarget after await; the event target is null by
  then, so the button stayed disabled. Capture/state-based activation now uses live job
  statuses and a separate in-flight request flag. Backend start already skips terminal jobs.
- Translation Apply/export incorrectly required translationCandidate.output_root, although
  reopening optional translation legitimately clears that transient candidate. Both operations
  now derive the output root from the active saved review; canonical source/lineage stays exact.
- Per-recording selected-file language is stored/restored and Inspect uses each recording's
  setting. Dictionary catalog loads on session initialization. Output is ordered before input.
- Source/translation action labels and guides updated without changing validation/publication
  semantics. Source validation Apply precedes preparation on a single control line.
- Initial full DOM audit plus static text/title audit found additional omissions in dialogs,
  provider controls, running/restored states, summaries and hover text. Supplementary EN→PL
  copy/error catalog and parameterized status translations added. Codes and source text stay raw.
- Temporary verification root was /tmp/ewp-gui-locale.sVIIW3; removed after final verification.


## Acceptance and verification

- All implementation items in the active TODO checklist are complete. Updated root EN guides
  and matching packaged copies explain the new names without changing immutable publication,
  source lineage or explicit human approval. Full Polish documentation awaits terminology approval.
- Added a source-copy audit for direct text/title assignments and conditional/confirmation text,
  alongside exact requested labels, loaded guide overrides, summary/decision/status samples,
  hover states and a Polish OpenRouter dialog. English identity names, presets, codes, model IDs,
  actual paths, source/target text and user dictionary entries remain unchanged.
- Stable errors keep their original code. Known descriptions are localized; unknown backend
  details receive a localized action description with the exact original in a collapsed technical
  message. Diagnostics use smaller type. Cleared statuses remove stale technical messages.
- Exact dictionary translations take precedence over parameterized rules; visual inspection
  caught and fixed the service-ready prefix and empty recording-path hint. Real path nodes have
  explicit data protection rather than suppressing translation of every path-style placeholder.
- Start activation depends on staged/queued/running work and a request-in-flight flag. Empty or
  completed-only queues are disabled. Browser tests exercise mixed completed/staged state and
  successful/rejected Start responses without invoking ASR. The real queue worker unit test runs
  successive synthetic jobs including a failure, retaining history and never rerunning terminal jobs.
- The translation regression opens optional translation after applying a manual translation,
  verifies the transient candidate is null, returns to stage five and exports successfully.
- Selected tracks for one episode share language; separate episodes restore independent choices.
  A grouped PL episode and separate EN recording are inspected with their own request languages.
- Automated gate: make check PASS (831 tests, Ruff/format/mypy); make test-integration PASS
  (five tests, four deselected); explicit Ruff check for the browser helper PASS.
- Browser matrix: 144 cases (six stages × six viewports × EN/PL × light/dark), no page errors,
  external requests, page/control overflow, internal transcript scroll or desktop queue overflow.
  Cursor splitting/isolation, pending-save edit preservation, source/manual translation exports,
  workspace recovery and prior library/palette coverage continue to pass.
- Focused exact-name/error-original/dialog checks PASS, including modal widths 390px and 960px.
  Source Add speaker no longer overlaps the preceding row. Apply precedes preparation on one line.
- Wheel/source build PASS. All 49 frontend/guide assets byte-match source. All nine help routes
  render directly from the wheel without ML imports. Packaged combined JS passes node --check.
- Temporary tooling, screenshots, synthetic outputs and archives under
  /tmp/ewp-gui-locale.sVIIW3 were removed after recording delivery evidence. No private corpus or prototype content was copied.

## Remaining owner work

Pull main in the transcription checkout and launch `uv run --locked transcriber gui`.
Retest PL/EN file selection, inspect/plan/stage, starting later files beside completed ASR,
returning to a saved translation for export, and the revised Polish names at half/full width.
Approve function/section terminology before creating the complete Polish user documentation.
The artist review package remains a separate later TODO. No release, tag, version bump,
provider operation, model download or new GPU qualification is part of this task.


Final delivery gate: verified-delivery browser run PASS on the final catalog and initial Start
state, including exact guide-overridden generation labels, cleared diagnostic lifecycle, ASR
artifact hover text and source-warning handling. Error parsing requires a stable underscore code;
ASR artifact hints and WARNING prefixes are not mislabeled as failures. Final asset/wheel check
and packaged combined-JS syntax check PASS. Implementation delivered to origin/main in af1b771872a1ed511f37dec4f3f9ea031d0413cc.
This documentation follow-up closes the delivery checklist; owner naming/WSL approval remains pending.
