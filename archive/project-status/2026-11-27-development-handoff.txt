# Development Handoff

Current resume point (2026-11-24): [session handoff](checkpoints/2026-11-24-session-handoff.md).
The owner is reviewing installer0.22.2 and will send new-session feedback. No product work now.
Everything below is historical; do not reopen its obsolete acceptance gates.

Active resume point (latest 2026-11-20 decision): [WORK_STATUS](../WORK_STATUS.md),
[TODO](../TODO.md), [package checkpoint](checkpoints/2026-11-20-package-a.md) and the
[roadmap package sequence](99-roadmap-v2.md#accepted-package-sequence--package-a-authorized).
Package A implementation and automated checks are complete; owner acceptance is pending.
Use the [focused A checklist](../Instructions/GUI_PACKAGE_A_TEST_CHECKLIST.md).
A1–A4 → owner checklist/fix/retest gate → B5–B8 → B8a cloud ASR → B9 full
native-Windows/WSL acceptance → task 10 EN–PL approval and later documentation. Artist waiting
is non-blocking/no-deadline. Historical candidate lists below do not override selected/declined
scope in the current roadmap.

Previous handoff text below is retained as historical context.

Active resume point (2026-11-20): [WORK_STATUS](../WORK_STATUS.md),
[work policy](../WORK_POLICY.md), [TODO](../TODO.md), and the
[current scope/summary checkpoint](checkpoints/2026-11-20-scope-and-summary-polish.md).
The [owner scope and current backlog](99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20)
supersede older dates, manual gates and research/preset requirements below.

Owner accepts the current GUI/workflow and browser/palette behavior with the reported small
footnote/navigation fixes. Full profile exchange and current restart recovery remain untested by
the owner but have automated coverage; do not repeat all completed acceptance work. Actual 200%
browser zoom is an optional unchecked layout case. Precise percentage/ETA calibration is no longer
required. Broad benchmarks, universal dictionaries and hardware presets are nice-to-have.

Finish adding chosen functions before preparing the complete editable EN–PL string-pair file for
owner approval, then write Polish manuals. Screenshots wait for final custom GUI/icons. Waiting
for the artist has no deadline and blocks no other work; the sent ZIP/demo stays unchanged.
Native Windows remains planned convenience work. Read the roadmap for recovered proposals,
including cancellation, verified downloads, provider catalogs/favorites, Ollama, optional credential
storage and conditional timing/translation/cleanup refinements.

The dated snapshot below is historical context, not the current implementation queue.

## Snapshot

- Date: 2026-09-25
- Branch: `main`
- Implementation baseline: `5dddef2` (`fix(gui): allow removing unavailable workspaces`)
- Application version: `0.19.0`
- Release state: internal requirements work only; do not tag or publish a release yet.
- Working-tree expectation: this handoff and the acceptance-status reconciliation are the only
  changes after the implementation baseline.

## Current state

The WSL GUI functional-fix pass is substantially complete. The operator has qualified the full
two-item workflow in Chrome and Firefox: native source selection, inspect/dry-run/transcription,
optional batch correction or skip, distinct manual transcript reviews, verified revisions and
exports, optional batch translation or skip, distinct semantic reviews, intentional empty-unit
handling, and translated exports. Browser restart and cross-browser workspace restoration retain
durable queue sources and saved review edits.

The active acceptance record in [the GUI roadmap](99-roadmap-v2.md#13-gui) has been reconciled
with those reports. GUI-01 through GUI-54 are WSL-qualified where applicable, except:

- GUI-34 is deliberately deferred to the dedicated responsive visual overhaul;
- GUI-40 has a qualified WSL adapter but still needs bare-metal Ubuntu and future-container
  qualification;
- GUI-55 is implemented but still needs the short manual confirmation below.

Managed source inventory and cleanup now account for active queues, saved workspaces, explicit
auto-save behavior, and hidden transcript-review lineage. The saved-workspace list combines the
private default catalog with the selected custom catalog and routes operations to the owning
catalog. Stale records with missing referenced paths are selectable for deletion while restore
and auto-save remain disabled.

## Immediate manual gate: GUI-55

Using one of the remaining **paths unavailable** records in the default workspace catalog:

1. Select the stale workspace record.
2. Confirm that **Load selected** and auto-save targeting remain unavailable.
3. Choose **Delete selected**, accept the warning, and refresh the list.
4. Confirm that the record is gone and that no workflow, source, review, revision, export, or
   unrelated workspace artifact was deleted.

If this passes, change GUI-55 to **WSL pass** in `docs/99-roadmap-v2.md` and replace the pending
sentence in `WORK_STATUS.md`. Do not claim GUI-40 bare-metal/container qualification from this
WSL result.

## Next implementation slice: GUI-34

Begin the dedicated responsive visual overhaul after GUI-55 is closed. Keep it as reviewable
vertical slices rather than replacing the complete frontend at once. The first slice should:

1. inventory the current breakpoints, overflow, overlapping controls, and keyboard focus order at
   desktop, narrow-window, and zoomed layouts;
2. make the workflow queues, action rows, provider controls, saved-workspace controls, and review
   editors responsive without hiding status text or relying on color alone;
3. preserve every existing DOM identifier, API request, workflow transition, dirty-review guard,
   and accessibility label unless a focused test-backed change requires otherwise;
4. add or update deterministic asset/server tests for the structural contract, then perform a
   manual Chrome/Firefox viewport and keyboard pass;
5. update the changelog for each user-visible slice and record its acceptance separately.

The later visual slices already recorded in the roadmap include collapsible or tabbed workflow
navigation, a floating stage navigator, the approved icon system, explicit light/dark mode, and
alignment with the Ethics in the Loop visual language. The Polish/English interface selector is
scheduled shortly before public release. Do not combine all of these into the first responsive
commit without separate acceptance criteria.

Primary frontend files:

- `src/ewp_transcripts/web_assets/index.html`
- `src/ewp_transcripts/web_assets/app.css`
- `src/ewp_transcripts/web_assets/app.js`
- `src/ewp_transcripts/web_assets/workflow_tracker.css`
- `src/ewp_transcripts/web_assets/review_editor_display.css`
- `src/ewp_transcripts/web_assets/review_editor_recovery.css`
- `src/ewp_transcripts/web_assets/translation_review_editor.css`

Relevant automated coverage begins in `tests/unit/test_web_server.py` and the focused
`tests/unit/test_web_*.py` modules. Read the complete GUI contract before changing behavior:
[Local browser GUI contract](26-local-web-gui-contract.md).

## Remaining environment qualification

GUI-40 intentionally uses one frontend control with deployment-specific server adapters:

- WSL: Windows host folder dialog through the `/init` interop bridge — passed;
- bare-metal desktop Ubuntu: Zenity, KDialog, or Yad — not yet manually qualified;
- headless/future Docker: direct server-visible paths inside explicit mounts — not yet qualified.

A browser directory upload is not a substitute: it exposes directory contents but cannot provide
the server path required by Python and FFmpeg. Typed paths must continue to work when no desktop
dialog adapter exists.

## Non-negotiable constraints

- Keep the GUI loopback-only, self-contained, and free of CDNs, telemetry, and remote assets.
- The web adapter calls application services directly; it never shells out to the CLI or creates a
  second transcript/revision/translation model.
- API keys remain process-memory-only and must never enter browser storage, workspaces, logs, or
  artifacts.
- Canonical results are immutable. LLM outputs remain non-final candidates until manual review,
  preview, and explicit application.
- Preserve exact source hashes, artifact lineage, atomic writes, and output-root ownership.
- Do not commit private corpus material, generated transcripts, provider state, or runtime output.
- Use conventional commits and update `CHANGELOG.md` in the same commit as every user-visible
  behavior change.

## Resume checklist

```bash
git pull --ff-only
git status --short
sed -n '680,885p' docs/99-roadmap-v2.md
sed -n '1,130p' WORK_STATUS.md
UV_CACHE_DIR=/tmp/ewp-uv-cache ./scripts/check.sh
```

The checklist and GUI-55/GUI-34 implementation instructions above describe the historical
snapshot. For current work follow the active resume links at the top; GUI-55 is closed.
Keep GUI-40 open until its actual deployment environments are available.
