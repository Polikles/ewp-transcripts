# Guided workflow and prototype reconciliation

2026-11-18; baseline `68a80ea`, internal 0.20.0 preview. Current task evidence:
[checkpoint](checkpoints/2026-11-18-guided-workflow.md). The owner qualified real local-only
transcription through source subtitle export on WSL/RTX 3090 before these usability changes.
API-assisted correction/translation is not qualified by that report.

## Workflow instructions

The central workspace has a short numbered list below the recording context and stage strip.
Each item links to its matching numbered control group. The same action names and numbers
are used in [the per-stage documentation](gui/README.md): transcription, optional correction,
source review/export, optional translation, translation review/export, plus dictionaries,
saved work and Settings. English/Polish short instructions are independent of processing
languages. Full English guides open in a separate tab and are packaged for offline use.

The guide metadata is `web_assets/guides/index.json`. Repository Markdown and packaged copies
must remain byte-identical; tests verify the copies and short-step numbering. Help routes use
a fixed guide allowlist rather than requested filesystem paths. No model/provider is needed
to open instructions, choose a stage or select a recording.

## Direct owner fixes

- The installer already synchronized locked dependencies and ran native audio repair.
  New mocked install/verify tests prove the ordering, prerequisites, and failure propagation.
  Doctor and relevant queue errors now identify an Ubuntu 24.04 → 26.04 upgrade as a possible
  native-library mismatch cause and point to the [upgrade guide](../WSL%20config/UBUNTU_UPGRADE.md),
  also bundled at `/help/ubuntu-upgrade`. No second installation/dependency stack is introduced.
- Source review places compact Prepare and validate / Draft and history panels side by side
  below the transcript, above human verification. Narrow phone layouts stack them. Preview
  validates without its former scroll-to-Apply; an unchanged saved editor retains its DOM,
  caret and section. A newer edit arriving during a save is retained and requires another save.
- Speaker names and colors contains the YTT profile and dynamic swatches. Selecting configured
  production or brand previews updates the displayed/export colors, preserves saved custom
  overrides, and never changes previous exports. Add speaker is shorter wording for the same
  revision-local identity operation; canonical speaker IDs and source results remain immutable.
- Split at cursor snapshots the real caret for pointer/keyboard activation, preserves it across
  saving, focuses the right block and shows invalid-position feedback beside the text. It still
  requires complete words and nonempty sides. Selection isolation remains a separate action;
  no synthetic timing is introduced. A baseline valid-word split already succeeded; the fix
  addresses state/feedback failure modes without claiming every cursor position is valid.
- Source and target text boxes grow with text and resize after hidden-stage transitions, viewport
  changes and font loading. Border height is included, preventing the former small internal
  scrollbar. Optional skip and clear-current-review controls have secondary visual emphasis.
- Stage queues and workflow markers use compact spacing and wrapping rather than reserved
  feedback gaps or forced marker rows. Item identity, all stage states, batch selection and
  actions remain available.

## Comparison with the private reference

The approved private handoff 0.1.0 / brandbook 0.4.0 was inspected read-only, including the
actual prototype and workflow/visual specifications. Screenshots of both the original product
and prototype were local disposable comparison evidence. No private bundle, transcript excerpt,
mock sample data or prototype implementation was copied into this repository.

| Reference behavior/layout | Product reconciliation |
| --- | --- |
| Recording queue on the left | The left rail now leads with recording cards and a real Add audio files shortcut. Staged rows have an explicit active identity, separate from batch selection. |
| Central stage strip | Five numbered workflow stages run across the workspace and stay reachable while editing. Dictionaries, saved work and Settings remain independent tools in the rail. |
| Active recording and task context | The recording frame retains identity, draft status and batch scope. A wide-screen panel shows actual language/target, local audio processing and current speaker colors. The same read-only details collapse into the frame at narrower widths. |
| Speaker palette context | Profile, stable speaker IDs/names, additions and live previews are consolidated. Additional speakers are supported beyond six palette roles; custom colors persist. |
| Compact source editing/actions | The transcript has growing regular-weight text fields, adjacent split/selection actions, local feedback and compact validation/history controls after the editor. |
| Understandable workflow progression | Each stage has a numbered short guide, matching controls and offline detailed instructions. Assistance remains optional and source export precedes translation. |
| Local typography/identity and theme/locale | Existing approved local fonts, icons, identity, patterns and independent EN/PL/theme preferences are retained. |
| Context remains accessible at half-screen | The side context collapses to Recording details; no unique operation exists only in the wide panel. The stage strip wraps, and source/target columns stack when needed. |

## Intentional compatibility differences

The prototype is a visual/workflow reference, not a backend. The product retains explicit
inspect → exact-plan confirmation → stage → Start queue rather than starting ASR on selection.
It uses real aligned source anchors, protected immutable revisions and separate Preview/human
Apply/export actions. It does not copy demo midpoint timing, fake pause/progress, demo ZIP
publication, metadata-only file import or non-running provider buttons. A previously approved
larger title/logo and current production YTT profile remain available. New-palette YouTube
qualification, actual Windows/browser zoom and paid provider qualification remain separate.

## Verification record

Final `make check` passed Ruff, formatting, mypy and 810 tests; integration passed five cases
(four deselected). Playwright/Chromium passed all 72 locale/theme/stage/viewport cases, guide
links and numbered targets, real pointer/keyboard splitting, newer-edit retention during a
pending save, manual Save/Preview position, long-text reflow, live palettes, source/manual
translation approval/export and exact workspace recovery. No page errors or external requests;
no internal text scrolling or desktop queue overflow. Additional visual/context checks passed.

Wheel/source builds passed. All 47 packaged frontend/guide files matched source bytes, and all
nine offline help routes rendered directly from the wheel without ML imports. The source
archive contains each guide and this comparison record. Root details and actual delivery
baseline are recorded in the task checkpoint and Git history.

These are model-free VM checks. The owner-qualified local ASR/export result belongs to the
preceding build; this revised UI needs a WSL retest. No new real provider, Windows zoom or
YouTube result is claimed. Only content-free evidence belongs in Git; disposable synthetic
outputs, screenshots, browser tooling and archives are removed. No public release or tag.


## Owner feedback follow-up — 2026-11-18

The [workflow polish checkpoint](checkpoints/2026-11-18-gui-workflow-polish.md) records the
follow-up against the same read-only handoff and prototype. The left rail now opens each
recording's next unfinished stage, Quick steps are vertical, the header is tighter and light
artwork is clearer. Legends follow queues; technical details and optional fields are quieter.
Queue selection for assistance remains distinct from per-row removal and finished-only cleanup.

The dictionary workspace now matches the reference's editing intent using real validated,
immutable editions rather than browser-only demo entries: view, compare, edit, create/import,
remove from list and restore. A corpus-derived proposal remains an optional separate panel.
The color panel lists actual configured presets plus saved custom profiles; full swatches make
EwP brand distinguishable even when the first two speaker colors are similar. Preview is
explicitly separate from Apply/export and Save of a reusable custom profile.

Source controls use equal-height panels and aligned history/Clear actions. Translation has
visible direction selection, an inline accepted-change warning and a source-language mismatch
explanation; it never relabels canonical audio to satisfy a requested direction. Skip LLM
assistance opens manual translation, while provider generation remains scoped and consented.
Queue-filled source fields and dictionaries collapse. No native timing, revision, provider or
approval contract was replaced by prototype behavior. Cursor splitting and selection isolation
remain owner-confirmed and covered by the browser checks.

The artist's frontend-only review package is deferred until the GUI fixes/tweaks are accepted.
No private prototype, reference text corpus or example runtime data is distributed in this task.


Follow-up verification: 830 tests plus five integration cases pass; 144 browser matrix cases
and focused library/profile/queue/direction checks pass. Fresh-server saved-work recovery and
final screenshot comparison with the private prototype pass. At 960px Undo/Redo/Clear align;
at 1920px all seven source controls share a single row. The wheel contains all 48 byte-matched
frontend/guide assets and all nine help routes work without ML imports. This follow-up remains
an internal preview requiring owner visual qualification on WSL.
