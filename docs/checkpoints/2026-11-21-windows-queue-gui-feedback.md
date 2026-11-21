# Native Windows queue and GUI owner feedback

Date 2026-11-21. Baseline clean main 761109f. Owner confirms native Windows 11 installation,
model preparation, GUI launch and doctor/dependency checks all pass on RTX3090 / CUDA12.8 /
Python3.12.16. Local audio-group and MP4 queue tasks fail before ASR logs with a masked
GUI_TRANSCRIPTION_FAILED. No exception details are retained by that catch. Owner asked for all
UI/cloud-cost changes tracked in the opening TODO; uninstall and EXE distribution work is later.

## Diagnosis / implementation order

1. Storage _fsync_directory uses POSIX directory descriptors on Windows. state publication wraps
   an initial OSError but finally repeats the directory sync and masks it with raw PermissionError,
   consistent with both jobs failing before model logs. This is a reproducible platform defect,
   not yet direct proof of the owner's exact exception. Audit all revision/translation/export
   directory flushes, preserve file fsync/atomic immutable publication, skip unsupported native
   Windows directory fd operations. Add faithful simulated-Windows pipeline tests.
2. Retain useful sanitized unexpected exception type/errno/winerror/frame details and terminal
   logging, without credentials, transcript payloads or locals; remove doubled generic UI errors.
3. Implement single picker/media list, conditional stream controls, merged batch-plan summary.
4. Add explicit OpenRouter key/connection and four-model availability/hourly-pricing estimate
   actions, no audio sent; replace user-entered job cap with estimates and internal protection.
5. Regression/browser/FFmpeg checks, necessary docs/ENPL copy/evidence, cleanup, commit/push.

Owner confirms only initial results.partial.json remains, status running, identical creation/update
times and null failure fields. This matches failure between exclusive state publication and
reservation return; it supports the reproduced defect but is not an unmasked native traceback. Native Windows actual workflow still requires owner retest.
No uninstall execution, model deletion, paid API call or artist-package update is authorized here.
Earlier paid ASR authorization remains scoped to original short pilot/budget; no repetition needed.


## Implemented / verified

- Shared platform directory flush replaces six publication families: state, source review, source
  revision, translation publication, source exports and translated exports. File fsync/atomic
  link/replace are retained. Native Windows skips unsupported directory fds; POSIX still flushes
  and propagates real errors. State cleanup cannot mask an earlier publication failure.
- Unexpected failures retain exception type, errno/winerror, basename/line/function frames and
  local terminal logging without arbitrary exception messages, source lines, locals or secrets.
  Known application failures also log safe locations. GUI has one collapsed disclosure per failed
  job and nested technical JSON; the Ubuntu upgrade instructions remain available where relevant.
- Unified main/rail picker imports saved canonical JSON and selects media. Removed directory-media
  and per-episode action buttons; per-recording language/count and Remove remain. Language (i)
  still works per recording and closes outside/Escape. Removing the internally active source selects
  a remaining source so browser required-field validation cannot block planning the rest.
- Automatic per-file probe reveals choices only for multiple audio streams. Actual batch output-ID
  collisions reveal ID fields; recording IDs retain original filenames and selected streams.
  Dry-run has one source/decision/warnings/language/count table and selection footnotes.
- Explicit shared-key /key check and four-model availability/pricing refresh. Public duration rates
  normalize to hourly USD, then local source/selected-stream durations plus chunk rounding/context
  estimate cost. Stereo uncertainty shows a range; changed inputs mark the estimate stale without
  background network calls. New GUI jobs derive internal job-wide reserves from all source/stream
  durations/current prices with a USD100 safety ceiling; old fixed-guard jobs retain their guard.
  No user-entered cap and no audio upload during checks; Start still needs fresh paid-upload consent.
- Updated EN/PL copy, guide/index/bundled mirror, changed-step quickstart, full B/focused owner
  checklist, changelog and roadmap. Deferred uninstall/model-removal and standalone GUI EXE
  installer/desktop icon/Add-Remove Programs/GUI uninstall are recorded only, not implemented now.

Evidence: [content-free record](../evidence/2026-11-21-windows-queue-gui-feedback.json).
make check passes 1008 tests, Ruff/format and mypy 115 source files; integration passes 17 tests
(4 deselected). Six Windows CRT publication families preserve file flushes. Real FFmpeg/fake speech
pipeline tests reach final canonical/raw output, cleanup and playback with Windows directory-open
restrictions. Linux shutil keeps its Linux fd behavior in this test; no real native claim.
The first global-os shim also intercepted Linux shutil directory traversal, so it was narrowed to
the application's publication adapters; production cleanup was not changed to satisfy that shim.

Chromium 159.0.8154.6 / Playwright 1.65.2: 144 full layout cases and focused media/JSON/stream,
per-recording settings, one table, collision IDs, removal, ENPL cloud/error panels and 8 width/locale
geometries pass. No page errors or external browser requests. Cloud checks use mock transports and
mock local browser responses; prior paid qualification is retained, not repeated. No private
media/key/model, uninstall action or artist ZIP modification is included. Actual server shutdown/restart and saved source/translation draft/export recovery also pass.
Local servers are stopped and /tmp/ewp-win-feedback.KwPQAK is removed after evidence capture.
Delivery target is main; native owner acceptance remains next.

## Owner retest / next gate

Stop GUI, pull main in the native Windows checkout, launch uv run --locked transcriber gui and
refresh the browser. No model reinstall is needed for this storage fix. Restore failed jobs and
Retry, or plan/add the original sources again. Existing partial files are preserved; allocation
uses the next free result version rather than overwriting them. Check both grouped audio and MP4,
then revision/translation/subtitle publication. If another operation fails, send the safe technical
JSON/terminal frame locations. Use the focused section of Instructions/GUI_PACKAGE_B_TEST_CHECKLIST.md.
A stays closed; B native/full-WSL acceptance is pending. Task 10 ENPL approval waits for functional
freeze/B acceptance; full manuals follow terminology approval. Frozen artist ZIP hash is unchanged.
