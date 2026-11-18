# Guided workflow, source-review fixes and prototype comparison

## Objective / baseline

Final implementation/verification status is in Checkpoint 4 below. Earlier checkpoints record
the actual intermediate state rather than overriding the final resume point.

2026-11-18. Start from clean `main` at `68a80ea`, internal 0.20.0 preview.
Full task checklist: `TODO.md`, section Guided workflow, review fixes and prototype comparison.
Read and update that list before each slice and after context recovery.

## Checkpoint 1: owner evidence and scope

The owner completed the local-only workflow from real transcription to subtitle export on
WSL/RTX 3090. This confirms the repaired native path and replaces the previous pending queue
retry. API-assisted workflows remain untested by that report. Informational WhisperX VAD logs
and the ONNX `/sys/class/drm/card0` discovery warning did not block completion.

Requested changes: automatic installer native setup and OS-upgrade error guidance; numbered
short instructions for each stage plus shipped per-stage documents and matching action names;
secondary correction skip; compact queue; compact side-by-side source-review control panels
below the transcript and above human verification; no Preview scrolling; speaker names/colors
with live profile previews; Add speaker wording; real cursor-split fix; growing transcript
text boxes; then compare with the supplied private prototype and fix remaining in-scope gaps.

Private reference root:
`/home/linuch/ewp-transcripts-ui-handoff-v0.1.0/transcripts-ui-handoff/`.
Do not commit its prototype, private examples or reference history. Record only content-free
comparison findings. Existing immutable model/artifact contracts, ML pins and explicit approval
remain intact. No release/tag, model download or paid provider call.

## Findings / verification

Installer already calls `repair-dependencies.sh --native-only` after locked synchronization
and installs its build prerequisites. Verify this with a regression test and update upgrade
guidance rather than adding a second installation path. Investigation continues.

## Checkpoint 2: functional changes and recovered baseline

Baseline browser evidence used the real application with public synthetic repository fixtures
and the read-only private prototype. A valid whole-word caret split succeeded before changes;
invalid-position feedback was remote from the editor. Source text sizing had a border-height
overflow and no ancestor-stage/viewport reflow handling. Palette selection left current swatches
unchanged. The original control groups stacked and occupied substantial height before the editor.

Implemented so far: compact side-by-side panels moved below review; removed Preview's explicit
scroll-to-Apply; saves preserve unchanged editor DOM/section and retain newer concurrent edits;
cursor snapshots, adjacent feedback and focus of the right split block; source/target auto-height
on edits, visibility, fonts and width; grouped live speaker profile controls and Add speaker label.
The source/target data, anchored timing and approval/export services remain unchanged.

Added eight per-stage English guides in `docs/gui/`, matching packaged copies for offline help,
English/Polish short-step metadata, numbered headings and in-page links for each action group.
Added `WSL config/UBUNTU_UPGRADE.md` and its bundled help route, with conditional OS-upgrade
guidance in doctor/backend errors. Installer tests execute mocked install/verify flows and prove
automatic native decoding follows locked sync without mutating the system or downloading models.

The static/unit gate currently passes 808 tests. Expanded real-browser checks are running;
prototype layout reconciliation and final verification remain pending. No new success claim
about API/provider execution is accepted. Continue consulting TODO.md before the next slice.

## Checkpoint 3: first browser pass and prototype reconciliation

The first expanded browser pass passed all 72 existing layout cases plus all eight instruction
links/targets, guide rendering, live brand/configured/custom swatches, compact side-by-side
panels below the editor, Preview viewport retention, no internal textarea overflow, and the
existing source/translation/export/recovery mechanics. Runtime artifacts stay in the dedicated
temporary root. Additional real pointer/keyboard caret and concurrent-save cases remain.

Comparison identifies remaining product layout differences: the prototype has a left recording
queue, central numbered stage strip and contextual speaker/source information. The current app
instead uses its left rail primarily for navigation and duplicates large stage queue summaries.
Reconcile those layouts while retaining all real endpoints, explicit staging/approval, exact
timing, durable recovery and provider consent. Do not copy demo pause/progress or timing logic.

## Checkpoint 4: final verification and comparison complete

- `make check`: PASS, Ruff lint/format, mypy and 810 tests. Installer tests prove locked sync
  precedes native audio setup, read-only verification avoids installation, and failed repair
  prevents success/launch verification. Guide tests cover numbering/copy parity, all routes,
  arbitrary-path rejection and explicit Ubuntu-upgrade guidance in doctor/queue errors.
- `make test-integration`: PASS, five tests, four deselected. No ML pins/schema changes.
- Final Playwright 1.65.2 / Chromium 159 matrix: PASS, 72 cases across three working surfaces,
  six sizes (1440/960/900 portrait/768/720/390px), EN/PL and light/dark. No page errors or
  external requests; no internal textarea overflow; zero queue overflow at desktop widths.
- Actual pointer placement and button activation, keyboard Tab/Enter splitting, adjacent
  invalid-boundary feedback, Undo, long text after hidden-stage/width transitions, and edits
  made while a real save response was held all PASS. Newer text is retained and the stale split
  is refused. Manual Save and Preview preserve viewport position. Validation/history panels are side by side
  below the editor at desktop widths with compact measured heights.
- All eight guide lists/links and their matching numbered target sections PASS. Live
  configured/brand/custom swatches, wide context colors after profile reset, and speaker
  names unchanged by UI locale PASS. Existing source/manual-translation review, approval,
  exports, mixed states, stage independence and exact workspace recovery PASS.
- Final comparison inspected the private prototype and current app at wide/half-screen sizes.
  The result and intentional backend compatibility differences are in
  `docs/29-guided-workflow-and-prototype.md`. The recording rail remains at 960px; task context
  collapses into Recording details; the central five-stage strip uses a compact responsive grid.
- Wheel/source builds PASS; all 47 packaged frontend/guide files match source. The source
  archive includes per-stage docs, upgrade instructions and the comparison record. All nine
  help routes render directly from the wheel without torch/WhisperX/pyannote imports.
- `git diff --check`, browser-tool lint/format and local documentation links: PASS.

Pre-final browser failures were in test setup: the concurrent-save predicate needed an arrow
function under the unchanged CSP, and the stress test needed to reset the selection later
used by the existing retention check. Final runs pass; CSP was not weakened. No private
prototype sample data, screenshots or generated transcripts are committed.

## Resume / owner retest

Read AGENTS.md, WORK_POLICY.md, TODO.md, WORK_STATUS.md and this checkpoint. Implementation
and local verification are complete. If Git still shows local work, finish review/commit/push;
otherwise verify main matches origin and await owner results. No release or tag.

The owner should save work, stop the GUI, pull main and restart with
`uv run --locked transcriber gui`. No model or native-runtime reinstall is needed for these
UI changes when the previous repair already passes. Follow the numbered source workflow,
test pointer and keyboard splitting between complete words, profile previews, long text,
Preview position, export and saved-work recovery. The standalone upgrade guide applies only
if a later OS/dependency change causes a native error.

The owner already qualified local ASR through export on the preceding build. This task's
browser checks are model-free and do not qualify new Windows/WSL UI behavior, actual 200%
browser zoom, external providers or new-palette YouTube rendering. Disposable runtime roots
are removed after content-free evidence is recorded; private references remain read-only.
