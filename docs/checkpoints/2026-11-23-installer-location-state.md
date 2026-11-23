# Installer location, state and presentation follow-up

2026-11-23. Baseline3158ebe clean. Owner reports0.22.1 blocks an empty D:\Transcripts-test-01
at Check computer; radio dots misaligned; stale Install state leaks into maintenance; autodetection
must cover every maintenance action; conditional VC help, Windows DisplayVersion/old-version
warnings, real info icon and readable credits required. Full installer EN/PL review waits until
GUI is finished. Keep previous app/model/cloud acceptance and all delivered packages immutable.
New patch0.22.2; no paid/model campaign and no artist archive regeneration.

Reproduced cause from code: safe_root rejects len(parts)<4, which incorrectly treats a valid
Windows drive-child installation as too shallow. Fix Windows shape using drive/home/root identity,
not an arbitrary depth. Preserve Linux system-directory protections and managed ownership checks.
ProgramFiles must work with real OS permissions, not only an accepting text field. Prepare a
same-user elevated worker for mutations via authenticated local pipe; no credentials in argv/files,
no UAC for host tests. Keep runtime locks outside protected install roots. No user confirmation
needed for implementing this; actual UAC on owner PC is handled by Windows when execution starts.

Plan: tasks/policy→path+host/version/lock regression→detected-action state model→modern controls/
conditional UI/credits→safe permission runner→native behavioral tests/screenshots→checks/docs/
new clean artifact/hash handoff. Actual owner native installation remains pending.

Implementation in progress (task root /tmp/ewp-installer-location.FeRwQy): Windows root shape now
accepts drive-child folders; drive/home and Linux system-root guards retained. External per-user
Windows activity lock preserves legacy lock observation without requiring protected-root writes.
Host context reads registry DisplayVersion (26H2 baseline; older/unknown warning, not a block),
and detects missing/inconclusive VC data/DLL set.44 focused Python cases pass,2 native-only tests
skip on Linux; original full gate not yet rerun. Native CI adds real D: child host input and a
Program Files stdlib-only venv/launcher check, not speech/model install.

New WPF helpers: InstallationDiscovery validates owner/state metadata and all maintenance actions
use it. WizardState resets fields/epochs/logs/keys/consents; Symbols provides centered radio card,
vector info/warning; ModernTheme rounds fields/navigation. Credits reflow preserves exact words.
C# compilation prototypes PASS before final broker refinement; expanded native reset/discovery/
radio-center/VC/OS/info/credits/helper transport tests await actual Windows CI. New source0.22.2
and editable metadata synced; dependency/model pins unchanged. Full EN/PL copy review is deferred.

Program Files support: elevated mutation helper via same-SID ACL pipe with kernel peer-PID/image/
parent verification; never send tokens via argv/files. Host/preview stays normal-user. Windows UAC
may consent only at actual mutation. Reject a different Windows-account elevation to preserve
models/profile/OS-store identity. A trusted Windows PowerShell bootstrap sets native single-file
extraction under an admin-only Common Files session BEFORE launching the elevated EXE. The worker
also extracts/checks the embedded payload in a separate protected session. Running EXE held read-
locked across elevation/copy. No Modify grants to normal users under Program Files. The normal
launcher lock stays in user state, outside the app root. Actual consent UI cannot be qualified by
an already-admin CI runner: test authenticated bootstrap/transport there, report owner gate honestly.

Primary references verified: Microsoft PipeOptions docs say CurrentUserOnly also enforces elevation
level, so custom same-SID PipeSecurity bridges UAC with kernel PID checks. Microsoft single-file
.NET docs require protected extraction when privilege differs; use DOTNET_BUNDLE_EXTRACT_BASE_DIR.
Release-health table confirms DisplayVersion26H2/build26300; do not guess names from build alone.
No actual owner tokens/models/provider audio or paid calls used. Before handoff finish current
compile/tests/native previews/docs/artifact hash proof; shutdown tools and delete task root only.

Local final quality gate PASS:1127 tests,2 native-only skips, mypy116; integration17 PASS.
Last C# publish compiled successfully; disposable artifact copy exceeded task tmp quota after
retaining four obsolete prototypes. Only those own prototype/publish outputs were removed;
there is no source/runtime failure and no delivered archive was touched. Build next from the
clean source commit into a new0.22.2 delivery. EN/PL installation docs/offline mirrors and focused
GUI-first checklist updated; installer-only copy reference118 pairs, broad review remains deferred.
Native broker/path/UI tests and screenshots still await CI; no native installation PASS claimed.


Final source: d51b1068aefc347babc8277b28b08642e025bbc9. Native run45238109373 PASS:
https://github.com/Polikles/ewp-transcripts/actions/runs/45238109373 . Native report records20
named coverage groups including actual authenticated PowerShell/EXE broker transport. Both real
filesystem tests PASS (no skip): D: child host validation with no target writes, and tiny model-free
Program Files launcher using external per-user lock. This is NOT a full transcription-app install
or interactive medium-account UAC/model qualification. No real token/key/audio/provider used.

Local final gates:1127 tests,2 native-only skips on Linux, mypy116; installer46 PASS; integration17
PASS. Final clean-source build succeeded. All six local artifact SHA256 values match the native-
tested CI values byte-for-byte. New path: ../deliveries/ewp-0.22.2-installers. EXE digest:
efd99684b69fa5c90d6741471bd5c638cab8483c0e3803d9f106cf46151570b5.
Native preview ZIP digest was verified against Actions; all19 PNGs visually inspected for radio
alignment, centered header/icon, install/detected/missing paths, OS/VC warnings, vector info/help,
models, masked dialogs and progress/result/removal views. preview.html and preview-only ZIP allow
review without execution; checklist/START-HERE-PL/installer-only118-pair reference included.
Content-free exact report/digests: 2026-11-23-installer-location-evidence.json; copy DELIVERY.json
alongside artifacts.0.22.0/.1 checksum entries and both artist ZIP digests reverified unchanged.

Next owner step is the corrected wizard GUI review. Existing Git checkout cannot be detected as
managed installation; do not adopt/delete it. After appearance acceptance, actual Win11 install
and interactive UAC/local-model lifecycle remain owner tests. Full installer descriptions EN/PL
are deliberately deferred until the GUI is finished, not a request to edit the CSV immediately.
No public online-bootstrap activation, signing, paid test or artist rebuild performed.

Cleanup complete: task SDK build servers stopped, own /tmp/ewp-installer-location.FeRwQy removed.
No task runtime remains. Final delivery and historical archives remain outside Git.
