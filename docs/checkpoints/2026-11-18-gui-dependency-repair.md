# GUI settings, native dependency repair and queue layout

## Objective / baseline

2026-11-18, baseline `a1a2460`, version 0.20.0. Preserve the uncommitted context-recovery
documentation from the preceding task. Owner confirms GUI startup now works in the correct
WSL checkout, but actual queue execution fails in pyannote because TorchCodec cannot read audio.

## Checkpoint 1: owner evidence / authorized scope

- WSL Ubuntu 26.04, Python 3.12.14, RTX 3090 and PyTorch CUDA 12.8 checks pass.
- All four pinned local model snapshots pass; missing HF_TOKEN is informational offline.
- TorchCodec 0.7 cannot find libavutil.so.59/58/57/56. Its FFmpeg 4–7 native libraries
  are absent; the ffmpeg executable check alone is insufficient.
- Actual backend: SPEECH_ENGINE_ERROR / Pyannote diarization execution failed, caused
  by unavailable TorchCodec. This now connects the native check to real queue failure.
- Move Test local dependencies to Settings & About. Enable doctor and dependency-repair
  controls after a test. Accept Ubuntu 24.04 and 26.04. Rename Forget selection to Remove
  from list. Reduce unnecessary transcription-table horizontal scrolling at half-screen.

## Implementation / verification

### Checkpoint 2: implemented repair and controls

- Settings owns the dependency panel. Doctor and repair start disabled; a completed native
  test enables them. Doctor has a CSRF-protected, post-test-gated read-only API. Repair shows
  the terminal command because the live GUI environment must be stopped before reinstallation.
- `doctor --test-speech-runtime` exposes the same explicit native test in the terminal.
- `scripts/repair-dependencies.sh` restores locked TorchCodec/pyannote packages, tests actual
  audio decoding, and only on failure builds private FFmpeg 7.1.5 audio libraries from the
  official SHA-256-pinned source. The speech adapters load those libraries before lazy imports.
  Original media still uses system FFmpeg; no ABI symlinks, system downgrade or ML-pin change.
- Ubuntu 24.04 and 26.04 pass the distribution check. Fresh installation accepts both and
  invokes native repair; prerequisites and current environment decisions are documented.
- Remove from list replaces Forget selection in EN/PL. The queue minimum is 36rem instead
  of 64rem; narrower cells/padding remove forced desktop-width spacing while retaining local
  scrolling when the available width is genuinely small.

### Checkpoint 3: final executed verification

- Final 7.1.5 repair compiled successfully in the dedicated `/tmp/ewp-native-repair.*` root.
  TorchCodec decoded an actual synthetic PCM WAV with exact expected sample values.
- The real pyannote Audio reader decoded the same prepared format exactly, after importing
  WhisperX in the same process. No models, GPU inference, private audio or provider calls.
  A further smoke check passed actual faster-whisper/PyAV decoding and pyannote timed
  cropping with exact sample values, confirming both native FFmpeg versions coexist.
- Default repair command reinstalled exactly `torchcodec==0.7.0` and `pyannote-audio==4.0.7`;
  its second native check passed and skipped rebuild/download. ML lockfile is unchanged.
- `make check`: PASS, Ruff lint/format, mypy, 793 tests. New coverage includes both accepted
  baselines, post-test API gating, explicit CLI native tests, optional/lazy compatibility
  loading, private-prefix failure/location guards, idempotence and source checksum rejection.
- `make test-integration`: PASS, five tests, four deselected. No ML pins or lockfile change.
- Final Chromium 159 / Playwright 1.65.2 check: PASS, all 72 layout cases, no page errors or
  external requests. Every populated workspace case at 720/768/900/960/1440px has zero local
  horizontal overflow in EN/PL and light/dark. Phone-width local keyboard scrolling, post-test
  Settings controls/report/repair command, native file upload/plan/stage, Remove from list
  preserving staged rows, reviews/exports and empty-state workspace recovery all pass.
- Browser verification caught stale helper assumptions about the already-selected episode
  label and mandatory 720px scrolling. The helper now uses the stable selection control and
  tests keyboard scrolling at 390px. Screenshot review also led to balanced percentage column
  widths and wrapping Polish workflow labels. These pre-final runs are not final failures.
- Wheel/source builds PASS, including an offline rebuild after final asset changes. The new
  compatibility module and every packaged frontend file matched source bytes. The source
  archive contains the repair script, work policy, todo and task checkpoint.
- `bash -n` for both install/repair scripts and `git diff --check`: PASS.

Do not claim GPU/E2E qualification from this VM; its NVIDIA device and model snapshots
are unavailable. The owner must retry the bounded real queue after repair.

## Owner repair / bounded retest

1. Save current work, stop the GUI with Ctrl+C and enter the existing WSL transcription
   checkout (`~/transkrypcje/ewp-transcripts`, not the waveform project).
2. Pull the delivered commit with `git pull --ff-only`, preserving any local changes.
3. Run `bash scripts/repair-dependencies.sh`. If it lists missing build tools, execute
   its exact prerequisite command and rerun. Do not delete the environment or model caches.
4. Start `uv run --locked transcriber gui`. In Settings & About, verify Doctor/repair
   start disabled, run Test local dependencies and inspect all failed checks if any.
5. Retry the short two-track episode: select, inspect, dry-run, explicitly stage and Start
   queue. Record the actual SHA and outcome; capture exact backend details if it fails.
6. Confirm Remove from list wording and populated half-screen queue layout. Continue the
   consolidated preview plan; actual zoom, WSL/GPU/provider and YouTube-palette gates remain.

## Resume / delivery

Read WORK_POLICY.md, TODO.md, WORK_STATUS.md and this checkpoint. Implementation and local
verification are complete. Await the owner's actual repaired WSL queue result; do not repeat
the completed VM matrix unless code changes or a new failure justifies it. Private artifacts,
synthetic transcripts, screenshots, build products and browser tooling stay under the dedicated
temporary root and are removed after recording content-free evidence. No release or tag.
