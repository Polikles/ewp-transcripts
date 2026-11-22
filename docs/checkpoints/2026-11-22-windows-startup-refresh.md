# Windows startup and queue refresh feedback

2026-11-22. Baseline clean mainb0c2ddf. Owner startup fails with null href assignment, About remains
Loading and queue polling/progress/results never update despite reported real GPU/WhisperX activity.
Cancel later rejects a stale row; initial output mismatch cleared after restart/browser reset.
Also fix Escape in key dialog, language info label position and subtitle EN/PL.

Hypothesis from code: localized help URLs gain ?lang, but win32 startup still queries exact
[href="/help/ubuntu-upgrade"]. Failure precedes About/polling installation. Reproduce Windows-session
branch with real browser and synthetic local job before concluding causal connection. Do not rerun
owner private media or paid ASR. Keep output-root safety check. Artist/manual stages remain gated.

Temporary root /tmp/ewp-win-startup.xqMIAk. Use model-free service/session fixtures for startup,
phase/progress/completion polling and key focus/keyboard tests; retain evidence then remove root.
Prior cloud spend unchanged USD0.0291461230985028369. Next reproduce and implement focused fix.

## Reproduced cause and changes

A browser with win32 session metadata reproduced the exact null-href text. Help localization had
already changed the link to /help/ubuntu-upgrade?lang=en, so start's exact href selector returned
null. The exception preceded About and polling setup. A real synthetic queue then completed on the
server while browser guiQueueJobs stayed running. This explains the displayed stale cancellation
without treating the owner's terminal VAD messages as a proven speech-engine failure.

- Give the dependency help anchor a stable ID; initialize metadata and idempotent polling before
  optional Windows presentation/restored review. Optional client failures now use
  GUI_INITIALIZATION_FAILED, rather than blaming an unavailable API. Poll exceptions cannot stop
  its interval. Restore-failure regression confirms one timer remains installed.
- Handle Escape on document capture whenever the key modal is visible; trap Tab/Shift-Tab within
  enabled visible controls and restore opener focus. Baseline failure was reproduced with focus
  outside the modal; the owner's exact focus at report time is unknown. No credentials are saved
  or cleared by closing except unsubmitted text.
- Language label explicitly associates with select by ID; caption and (i) share the row above it.
  Outside-click/Escape popup behavior and per-recording settings remain intact.
- Subtitle uses exact requested EN/PL. Reference remains stable-ID, now2219 rows including the new
  initialization diagnostic; originals remain untouched. No workflow/data/model format change.
- Shared-output rule remains intact. Seven status regressions confirm only staged/queued/running/
  cancel_requested tasks lock output. Completed/failed/cancelled history does not. Original one-off
  mismatch is not reproduced, so no speculative weakening of the guard.

## Verification and reproducibility

make check:1056 tests, Ruff/format and mypy115 pass. Integration17 pass/4 deselected.
Full Chromium216 layouts EN/PL/light/dark/nine widths390–3840 pass. Focused Windows-session test
loads versions/Windows help, deliberately fails optional restore without losing polling, sees live
transcribe/align bars, then completion without manual refresh. Queued and active cancellation pass;
finished row loses Cancel. Four dialog entry points × two locales pass Escape/focus containment.
Label/icon association and centers pass390/960/1920; screenshot inspected. Zero browser errors or
external/model/provider calls. This does not claim an actual native Windows/GPU run.

Reusable model-free fixture: run tools/run_gui_progress_fixture.py --root <fresh-mktemp> --port8877
in repository Python, then tools/check_gui_windows_startup.py --url http://127.0.0.1:8877
--fixture-root <same-root> --output <test-output> --confirm-synthetic-service in the Playwright env.
Both require disposable data; fixture forbids cloud jobs and never initializes a model.
[Evidence](../evidence/2026-11-22-windows-startup-refresh.json) retains baseline reproduction,
limits and final results. Four changed JS syntax checks, optional helper Ruff/format and workbook/
CSV copy consistency pass. Current reference validator accepts2219 IDs and109 changed/noted rows.

## Handoff

[Targeted owner Windows retest](../../Instructions/GUI_WINDOWS_REFRESH_RETEST.md). No reinstall,
model preparation, browser-data deletion or paid API test. Preserve existing completed results;
add their canonical JSON if already present instead of rerunning ASR solely to recover GUI state.
Then owner interface approval, EN manual review/update, complete PL documentation, NEW artist package.
Original artist archive unchanged; cumulative prior cloud spend USD0.0291461230985028369.
Disposable servers stopped and `/tmp/ewp-win-startup.xqMIAk` removed after saving evidence.
Final maintained workbook/CSV and original private files remain intact. Delivery targets main.
