# Package B Windows workflow/state polish

Date: 2026-11-21. Baseline clean main 3c413ce. Owner reports successful native Windows local
ASR/source subtitle export and cloud ASR after prior storage fix. Key save/load actions work but
closure/check flow is unclear. Full B acceptance remains pending; every new issue is in opening TODO.

## Acceptance / investigation order

1. Trace streaming disconnect handling and artifact-derived workflow progress, including cloud
   canonical results, selected export formats and translation candidates. Fix reproducible defects
   without rerunning accepted ASR or spending on provider tests.
2. Fix missing consent highlights/messages, key-dialog close/API check and clearer missing-key
   guidance. No credentials silently restored from workspace and no implicit OS-store unlock.
3. Adjust plan labels/layout, source/translation action rows, optional dictionary picker placement,
   download guidance, rail/pricing labels; EN/PL stay coherent.
4. Functional regression/browser checks, ordinary gate and relevant integrations, focused owner
   checklist and content-free evidence. Record findings here before handoff, remove dedicated
   temporary outputs and commit/push main. Artist ZIP stays frozen; task10/manual gate unchanged.

Owner terminal trace is ConnectionAbortedError at review-audio socket write (WinError10053),
consistent with a browser aborting/replacing an audio request; investigate existing exception scope.
The SPEECH_ENGINE_ERROR at openrouter.py:226 is the reported missing session key after restart,
not evidence of cloud ASR failing after the key is loaded. Keep these causes distinct.

## Findings and implementation

- Reproduced source-export status defect: inference required a transcript TXT and used the revision
  JSON suffix order instead of the exporter's role/version order. It now recognizes actual
  TXT/SRT/VTT/YTT/HTML/segments publication names, canonical/export versions, and regular files only.
  The regression failed before the fix; real service/browser SRT-only result-v003 export now moves
  the rail to translation without TXT. Previous filename forms remain readable.
- Translation single-provider handler unconditionally reenabled generation and did not immediately
  report/refresh assisted completion. Success/error now refresh that exact assisted stage; the
  button tracks a generated source/busy state and durable completed state, with explicit Reopen
  translation (or verified source handoff) allowing a fresh attempt. Manual review remains separate.
  Fixed semantic review UI forcing pending whenever any candidate existed, even after verified
  manual publication. Completed source and assisted translation now route the rail to semantic
  review. The source/translation real publication workflow passes with a deterministic local test
  provider (no actual model/API calls) and explicit reopen re-enables generation.
- Catch only broken-pipe/reset/aborted connections at audio headers/body and ordinary responses;
  audio descriptor always closes. Genuine OSError still propagates. Before-fix regression reproduces
  ConnectionAbortedError and header exceptions; unit cases now pass. Trace alone cannot establish
  which browser/host component interrupted the owner's connection, and no firewall/antivirus cause
  is asserted. Separate missing-key SpeechEngineError remains real/readable and is not suppressed.
- Missing cloud/correction/translation disclosure is validated before requests, outlines/focuses the
  checkbox with aria-invalid/description and localized explanation, then clears when checked.
  Cloud consent uses smaller text and is not permanently saved. Missing-key message explicitly
  offers enter/load; removed obsolete user cost-limit guidance, including old displayed messages.
- Key dialog: Close window/×/Escape, return focus and cleared unsubmitted input; session activation
  stays open for subsequent save/check/use. Explicit API check can validate a typed key without
  setting/saving it, or the current shared key when empty. API remains CSRF guarded, never echoes
  keys and does not implicitly access OS storage. OS save/load implementation is unchanged.
- Source/translation main row has Apply first, Undo, Redo, Save draft, Restore saved draft; Clear
  alone below aligned with the rightmost action. Compact medium widths keep controls in one row,
  wrapping labels at word boundaries within a button. Phone views can reflow. Measured 12 ENPL
  panel/width cases; caught/fixed actual long-label wrapping, not just simulated screenshot checks.
- Plan headers keep whole words in a local scroll region on phone widths; process -> przetwórz,
  speaker auto -> automatycznie. Rail Add files and shorter refresh-cost action. Native dictionary
  picker stays inside optional disclosure regardless of asynchronous guide/DOM order. Both download
  panels have two clear instruction lines; translation names translation-exports and refreshes
  links immediately after export. Changed-step docs and bundled mirrors remain synchronized.

## Verification so far / resume

make check: 1031 pass, Ruff/format and mypy115. Integration: 17 pass / 4 deselected.
Focused Chromium/Playwright source-v003-SRT-only -> deterministic candidate -> manual translation ->
export passes; consent stops requests, typed/shared-key modal flow (mock responses/OS actions),
progress/generation lock/reopen and ENPL action rows/plan widths pass without page errors or external
browser requests. A full 144-layout workflow suite passed before final compact-label refinement;
current final suite is running. No paid calls, real keys, corpus, model changes or artist ZIP changes.
Disposable root /tmp/ewp-b-polish.RgQFAl; retain only reviewed content-free evidence and remove at
completion. Next: inspect final suite, actual restart/recovery, evidence/pointers/checklist cleanup,
commit/push main and owner focused retest. Native Windows full B/WSL gate remains owner-run.

Final focused workflow also checks explicit Reopen translation after completion (button enabled,
no automatic provider request), checkbox error reset and finished next-step inference. Passes.
Full-suite rerun first encountered an accumulated test-catalog count (8 instead of 1) because
multiple prior suites shared the same disposable server state. This is fixture isolation: running
again on a separate fresh state-clean directory under the same disposable root, without changing
production dictionary behavior. Inspect gui-final-clean/report.json and then restart/recover it.


## Final verification / handoff

[Content-free evidence](../evidence/2026-11-21-b-workflow-state-polish.json): make check 1031 pass,
Ruff/format and mypy115; 17 FFmpeg integrations / 4 deselected. Final full Chromium suite passes
144 ENPL/theme/width/section cases on clean state-clean. Focused workflow passes real source-v003
SRT-only export, one deterministic translation generation, manual review/export, progress and
explicit reopen, required-consent focus/reset, key dialog mock checks/save/use/close, dictionary
picker and responsive row/header checks. No page errors/external browser requests or paid calls.
Actual server restart and saved draft/translation/export recovery pass as well. No native Windows
qualification is claimed from Linux/mocked disconnect/OS-store tests; retain owner's real ASR/export
success and repeat only the focused feedback checklist, then remaining full B Windows/WSL gate.

No private key/media/model/raw provider response is included. Artist ZIP SHA256 remains
1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1. Test servers are stopped and the dedicated /tmp/ewp-b-polish.RgQFAl directory is removed
after reviewed evidence capture. Delivery target is main; focused owner native retest is next.
A stays closed; task10 final ENPL approval/manuals and deferred installers remain separate.
