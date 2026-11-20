# Package A owner-feedback fixes

Date: 2026-11-20. Baseline: clean main abe9ed2. Scope: the owner's A1–A4 feedback and active TODO.
Implementation and automated verification are complete. Owner focused retest/acceptance is next;
package B remains gated. Use [the focused retest](../../Instructions/GUI_PACKAGE_A_RETEST.md).

## Owner evidence retained

The owner confirms WSL saved edits/queue recovery without automatic ASR or restored confirmations;
waiting/running cancellation with USER_CANCELLED and no rerun of completed ASR; temporary cancelled
workdir cleanup; unchanged earlier YTT versions and existing source/translation downloads after a
server restart. These successes are not reopened as unqualified research/GPU gates.

## Defects reproduced and changes

- Rail next-step inference previously ignored ASR state. Pre-ASR jobs now point to transcription;
  canonical/completed ASR says ASR completed, separately from whole workflow completion.
- Restore used to expose partially populated queues without feedback. A thread-safe progress owner
  records loaded/total real jobs; a modal/backdrop/gear stays through queue and editor restoration.
  Overlapping restores are refused. Save/load immediately replace stale success text with busy text.
- Retry kept its old terminal row. It now replaces that selected row with a fresh attempt ID, clears
  its old live-progress token, and ignores stale pending queue tuples. Published/source/workdir files
  remain independent. Previously saved duplicate history is not silently deleted.
- Reproduced cancelled-history rejection when a later retry created the planned result: a file was
  validated as a directory. Reproduced omission when terminal media was missing. Safe optional-file
  validation fixes both; strict staged source hashes/plans and completed canonical requirements stay.
- Reproduced first-use Add-without-confirmation discarding the reviewed batch plan. Missing consent
  now preserves an unchanged plan; real option/source changes still reject it. Public GUI Inspect
  is merged into Dry-run (choose / plan-confirm-add / start); diagnostic CLI/API Inspect remains.
- Planning N/M and restore feedback use the custom gear. PL rail/cancellation/Ponów, cleanup reasons,
  preview counts and save omissions are localized while diagnostic codes/user data remain exact.
- Successful manual review starts imply skipping unused optional LLM correction. Existing downstream
  immutable artifacts give the same inference on recovery; real correction candidates still complete.
- The player was squeezed into the narrow rail. Source review reserves enough width for complete
  native controls, retaining usable half-screen navigation/history alignment. The permanent duplicate
  speed selector is removed. Native rates persist in existing preferences/profiles (0.25–4x); loading
  media does not overwrite the user's stored rate with a transient default.
- Fast cleanup filter changes exposed stale selectable rows in browser testing. Inventory request
  generations, disabled stale inputs and preview invalidation prevent selecting the wrong old view.
  Durable media is intentionally separate from temporary WAV cleanup and is explained in the UI.
- Minimal changed-stage guides describe the single planning step, raw results/segments/transcript
  files, native controls and terminal history. Full EN revision/PL manuals still wait for the complete
  two-column EN–PL approval after feature completion. Artist assets/ZIP are untouched.

## Verification

- Final make check: PASS, Ruff/format, mypy 106 source files, **928 tests**. Optional browser helper
  lint/format: PASS. make test-integration: **12 passed, 4 deselected**. No application pipeline,
  model/pin/canonical-schema changes, provider calls or model downloads.
- New regressions cover cancelled history with existing planned output/missing media, retry row
  replacement, stale pending-item races, optional correction inference, restore progress ownership
  and native speed preference validation. Previously accepted security/lineage tests stay intact.
- Chromium 159.0.8154.6 / Playwright 1.65.2 full `final` workflow PASS: **144** EN/PL/theme/width/stage
  cases, batch planning directly after picking files, missing-confirmation recovery, changed-option
  rejection, three-job modal progress with partial counters, review/save/load/export/profile/dictionary
  regressions and native playback. Zero page errors or external requests.
- `localized-maintenance-3`: PASS, **12** locale/theme/width cases, PL Ponów/cancelled/reason/preview,
  actual safe cleanup, waiting/running fake-service cancellation and one-row retry. No real GPU work.
- Fresh server/browser `final-recovered`: saved source/translation edits and applied pointers restore;
  **11 actual export downloads** match original bytes/name/hash, foreign requests are rejected,
  **24** download-panel locale/theme/width checks and sentence/fallback guidance pass. No ASR/re-export.
- Native menu check: actual ellipsis/speed-menu clicks at **1440/960/900/390** widths on initial load
  and **three page reloads** (16 menu checks); actual 1.5x choice each cycle persists. Native animation/
  font/scroll settlement is awaited before clicking native label controls. No CSP relaxation.
- Wheel/sdist PASS offline. Installed-wheel smoke reuses existing model-free base dependencies:
  **57 resource files** byte-match source, **13** page/asset/help responses and CLI/gui help pass,
  with no eager torch/WhisperX/pyannote import. This is not a full clean ML installation qualification.
- Artist ZIP SHA-256 remains
  1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1.

## Limits / resume

Owner WSL GPU successes remain accepted; the agent did not rerun pinned models or qualify native
Windows/full profile exchange/new providers. Native controls were exercised in Chromium, not every
browser/OS. Actual browser zoom at 200% remains optional/unclaimed. Package B and task-10 final
terminology export are not started. Address focused owner retest feedback, then wait for explicit
acceptance before B. Do not recreate the sent artist package.

Disposable root /tmp/ewp-a-feedback.e11RZn was removed after content-free evidence capture;
shared /tmp/ewp-uv-cache was preserved. Helpers closed their test servers. No screenshots,
private material, generated media/transcripts, runtime state, model or wheel are committed.
