# GUI workflow polish — 2026-11-18

Baseline: clean main at 7d029e4beb94fff2cefbfe0f2a5c748be1d67858.
Scope: every item in TODO.md's GUI workflow polish checklist; artist package is deferred.
Owner confirms cursor splitting and selected-text separation work. Local WSL transcription
through source export is already qualified; do not reopen the native ASR blocker.

## Resume

Read AGENTS.md, WORK_POLICY.md, TODO.md, WORK_STATUS.md and docs/99-roadmap-v2.md.
Inspect existing dictionary/palette contracts before extending their UI. Preserve immutable
results, revision history, locked ML pins and explicit human approval. Record evidence per
slice here. No provider calls or model downloads are authorized by this UI task.

## Progress

- Full user checklist persisted before implementation.
- Implementation is complete. Final verification and delivery are recorded below.

## First implementation slice

- Inspect now handles all unqueued selected episodes; staging advances selection and locks
  staged entries. Removed duplicate main-queue checkbox/bulk controls; inactive rows retain
  Remove, and finished-only cleanup is separate. Recording rail follows workflow state.
- Reduced header spacing; vertical Quick steps; stronger light artwork; muted hints and
  below-table legends; optional dictionaries collapsed; source/target controls rearranged.
- Added versioned dictionary editor, comparison, example/import and reversible library
  hiding. Manual edition provenance is separate from corpus proposals. Four service tests
  plus three existing dictionary tests pass. No dictionaries in the repository changed.
- Configured named color profiles plus persistent custom profiles; explicit preview/apply
  separation. Translation direction has active state and inline accepted-change feedback;
  source-language mismatch blocks generation rather than changing canonical language.
- Temporary verification root: /tmp/ewp-gui-polish.gtvxFa. Browser/complete gates pending.


## Acceptance and decisions

- All TODO implementation slices are complete. Inspect processes the whole selected unqueued
  set; staging advances, locks staged entries, and removing a queue row makes it eligible again.
  Both individual and grouped files were exercised without starting ASR.
- Library removal hides a path/hash from pickers, with Show removed / Restore. Files and earlier
  run references remain unchanged. Manual edits require a new ID and unchanged parent hash;
  an atomic exclusive publication plus hashed manual-edit manifest preserves provenance.
  The legacy corpus proposal workflow remains accessible. No bundled dictionary was altered.
- Configured production and EwP brand stay distinct. Full preset swatches show their six colors;
  their first two colors alone are visually similar by design. Preview does not alter export
  colors; Apply commits per-recording colors, Save persists a named custom profile. Configured
  names are protected. Custom profiles and hidden dictionary entries survive service restarts.
- Direction buttons show current target/default from the actual source. Changing requires an
  inline acceptance action. A direction conflicting with the source language blocks generation
  and asks for a matching recording; canonical language is never changed implicitly.
- All legends follow queues. Optional dictionaries and queue-filled source/target details start
  collapsed; manual translation uses Skip LLM-assisted translation below the queue. Translation
  Apply/export has prerequisite hover help. Clear is secondary and aligned. Source panels match
  height with Undo/Redo/Clear on one row at 960px and 1920px.
- Consulted the private handoff/workflow reference again. Updated docs/29 reconciliation.
  The artist-only frontend package remains explicitly deferred in TODO and roadmap.

## Final verification

- make check: PASS — Ruff, formatting, mypy, 830 tests.
- make test-integration: PASS — five tests, four deselected.
- Expanded browser delivery run: PASS — 144 layout cases (six stages × six viewports × EN/PL
  × light/dark), no page errors or external requests; no page/control/textarea overflow,
  no feedback overlaps or desktop queue scrolling. Pointer/keyboard split, isolation,
  pending-save edit preservation, workspace recovery, source and manual translation exports pass.
- Focused browser checks: dictionary example/edit/compare/hide/restore and immutable-ID rejection;
  grouped and separate episode staging; sidebar progression; direction default/warning/accept/
  mismatch guard; collapsed inputs; equal-height/aligned controls; completed-only cleanup all pass.
- Full preset swatches: PASS. Final wheel/source build: PASS. All 48 frontend/guide assets
  byte-match source; all nine help routes render from the wheel with no heavy ML imports.
- Fresh-server workspace recovery and actual prototype screenshot comparison: PASS. At 1920px
  all seven source-control buttons share the same top position; at 960px Undo/Redo/Clear align.
  Screenshot evidence is disposable; content-free outcomes are retained here.
- Delivery to main follows verification; delivery SHA is recorded after push.
- No actual provider, GPU, Windows zoom or YouTube qualification claimed by these VM checks.


## Remaining owner check

From `~/transkrypcje/ewp-transcripts`, pull main and run `uv run --locked transcriber gui`.
Check multi-episode Inspect/stage progression, left-rail routing, dictionary comparison/edit/
hide/restore, palette Preview/Apply/Save and direction warnings at half/full screen. Retest one
short local recording through subtitles. Keep API/provider, actual Windows zoom and YouTube
qualification separate. Artist package remains a future TODO after GUI tweaks are accepted.
No release/tag/version change is part of this internal preview task.
