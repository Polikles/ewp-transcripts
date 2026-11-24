# Runtime, autosave and installer wizard follow-up

2026-11-24. Baselinef20f161, product0.23.1 source5442167. Latest owner authorizes all opening
TODO items. Target0.23.2. Owner confirms removal deletes program files and retains work-state.

Report `/home/linuch/EwP-setup-report-20261124-155528-962-+0100.txt` is private and stays outside Git.
Previous inactive PID2580 lock/no port8765 listener is owner evidence. Current code checks only
OpenProcess success, not exit status or process creation identity. Reproduce terminated/reused
PID, crash/terminal-close/reboot recovery, healthy concurrent ownership, reopen and uninstall stop.
Windows runtime owner metadata must never authorize terminating a different process.

Implement default managed outputs and focused two-track persistence without selecting output;
keep user output choices, explicit planning, no restored cloud consent, stable reviewed copy.
First install needs separate optional OpenRouter step and red token-password reminder; operations
may have different step counts. Missing required checks must indicate the target on Next attempt.
Overall phase progress must be honest about unknown download byte totals.

Old internal installers may be cleaned under latest authorization. Retain useful accepted
baselines and artist archives. Later: local/OpenRouter ASR parity (planning only), complete
installer EN/PL/notices review and native Windows app shell after installer closure. No new
paid requests, model qualification or artist work. Verification and delivery pending.

## Implementation and focused evidence

Windows activity uses an OS-lifetime named mutex plus conservative legacy PID-file recovery.
The process probe waits on the real process object and checks creation time/image; terminated
handles, PID reuse and older-boot metadata no longer imply a running application. The actual
GUI server privately publishes its own process identity (including Windows venv redirectors),
port and transient management credential. Repeated launch authenticates this instance and
reopens the browser; uninstall requests graceful shutdown/cancellation before acquiring its
released activity lock. Unresponsive termination is limited to the creation-verified installed
interpreter; no arbitrary PID/name deletion. The console title is EwP Transcripts.

Managed launches supply root/outputs, with protected-location per-user fallback and retained
custom paths. Picker completion saves immediately; ordinary edits debounce500ms, in-flight
changes schedule another save, and a15-second fallback covers non-DOM queue changes/retries.
Browser/actual server restart of two synchronized unplanned files with untouched default output
passes without any planning/staging/processing/upload consent. Actual production runtime endpoint
rejects wrong Host/token, accepts authenticated ping and closes its server cleanly.

First-install flow is5 steps: action/location/models+HF/OpenRouter/installation. Missing required
checks get visible frames on blocked-Next attempts; shorter maintenance flows remain. Both token
instructions show the red password reminder. OR guidance was verified against official sources:
https://learn.openrouter.ai/courses/first-request/create-an-api-key and
https://learn.openrouter.ai/courses/what-is-openrouter/navigate-the-platform (accessed2026-11-24).
Overall stage progress and completed dependency/model-download counts accompany fixed-width
per-file amount/rate/ETA fields and reserved activity lines. Equal-version update is rejected in
both UI and backend; same-version Repair remains valid.

Local WPF compilation passes with no warnings/errors. Focused browser checks pass. Full checks,
Windows kernel/process/reopen/uninstall cases, final native previews/artifacts follow.
Removed1.4GiB of unneeded0.23.0 INTERNAL candidates under owner authorization; retained all sent
baselines and artist archives. No API/model qualification or paid calls. Later model parity is
recorded in TODO/roadmap only, with no model/runtime pin change in this task.

Local full checks now1146 PASS,12 native cases skipped on Linux (including legacy-runtime
qualification). Native cases cover a still-open terminated process handle (exit0 and259),
healthy ownership, crash, reused/prior-boot PID, normal/orphan repeated launch, authenticated
uninstall stop and older PID-only launchers. The server publishes its own identity, which avoids
confusing Windows venv redirector/launcher PIDs with the actual listener. A legacy launcher may
be stopped only after verifying its exact managed manager.py launch role, root and descendants;
installer workers and unrelated images remain protected. No native PASS is claimed yet.

First native run45436119635/sourcee815221:32 WPF groups and12 real Windows cases PASS,
including healthy/orphan reopen and old PID-only launcher stop through the real removal adapter.
Before final packaging, align uninstall phase order with its preview→shutdown→removal events,
clear completed requirement feedback immediately and remove remaining obsolete EN removal prose.
No candidate has been delivered; final source-native artifact verification follows.

## Final verified delivery

Product source05cebd12fcf42d3eae42aa4fc4736bd14241bce3; final native run45436776960 SUCCESS.
32 WPF coverage groups and12 actual Windows cases PASS. All32 final native previews inspected,
including missing-HF acknowledgment highlighting and separate EN/PL OpenRouter screens.
Six delivery hashes exactly match native-tested CI. Canonical directory:
`/home/linuch/project-ewp/deliveries/ewp-0.23.2-installers/` (EXE, six packages/scripts, SHA256SUMS,
preview.html/ZIP, focused checklist, Polish START-HERE and content-free browser/CI evidence).
EXE SHA256 `fca0830d6ed218949a0818e268561e6cda44a9e6b72e0bfa64d1a131a5be3976`.
Evidence is `2026-11-24-runtime-wizard-autosave-evidence.json`.

Local1146 PASS/12 native skips (17 integrations included), Ruff/format/mypy PASS, WPF compiles
without warnings/errors. Browser verifies untouched outputs, two synchronized unplanned sources,
change-aware save BEFORE a5-second deadline (independent of the15-second fallback), fresh-browser
and actual server restart without planning/processing/consent. Actual production RPC rejects
wrong Host/token and supports authenticated ping/clean close. Reviewed-copy browser check passes
2221 reference rows/102 changed-copy checks and36 layouts without page errors/external requests.
Installer copy reference has177 pairs; application owner baseline/workbook stays unchanged.
Affected EN/PL guides match their packaged offline counterparts.

Owner0.23.1 installation-report completion and removal/work-state pass are retained alongside
previous install/transcription/update passes. No owner0.23.2 acceptance is claimed yet. Next is
only focused retest in START-HERE/checklist, not a repeated full ASR/reinstall/paid/model campaign.
Later parity across local/API model choices is recorded, not implemented. Full installer EN/PL/
notices review and native Windows interface retain the owner's sequencing. Unsigned/internal;
public release/online bootstrap activation remain separate pending actions. All sent baselines
and artist archives remain intact. Disposable local test/build directories are cleaned at handoff.
