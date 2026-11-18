# GUI launch and transcription-start diagnosis

## Objective and baseline

Investigate the owner's blocked WSL retest following the integrated GUI changes. Separate
application launch failures from transcription jobs failing after queue start. Preserve
the supplied GUI direction and leave durable recovery notes for every task.

- Date: 2026-11-18.
- Branch/baseline: `main`, `a1a2460` (initial tree clean), application 0.20.0.
- Recent implementation: `9fbab60` integrated preview, `a1a2460` grouped speaker tracks
  and dependency/failure diagnostics.
- Reference bundle on this VM:
  `/home/linuch/ewp-transcripts-ui-handoff-v0.1.0/transcripts-ui-handoff/`.
- Existing product roadmap: `docs/99-roadmap-v2.md`, GUI-34 owner qualification pending.
- Owner instructions: `Instructions/GUI_QUICKSTART.md` and
  `Instructions/GUI_PREVIEW_TEST_PLAN.md`.

## Checkpoint 1: recovered context

Previous work recorded 781 local tests and five integration cases passing. It did not
establish real transcription success. The VM previously showed FFmpeg 8 native-library
incompatibility and lacks GPU/model snapshots; the WSL backend exception was still unknown.
The handoff's old GUI-55 manual gate is superseded; GUI-55 is owner-confirmed closed.

Created `WORK_POLICY.md` and `TODO.md`; the existing roadmap remains authoritative.
Requested the actual WSL failing step/error while local investigation continues.

## Verification and findings

### Checkpoint 2: confirmed WSL launch cause

The owner supplied terminal output from `~/waveform/ewp-waveform`:
`uv run --locked transcriber gui` rebuilt `ewp-waveform`, installed 24 packages, then
failed to spawn `transcriber` with OS error 2. The same command repeated the spawn error.
This is the wrong project/environment for the console script. No GUI server or transcription
backend started in that attempt. The previous transcription-start problem is separate and
has no current WSL exception yet.

Recovery: enter the existing `ewp-transcripts` checkout (documented owner location
`~/transkrypcje/ewp-transcripts`, actual location must be checked), confirm `pyproject.toml`
names `ewp-transcripts`, then follow the guarded pull/start in `Instructions/GUI_QUICKSTART.md`.
No application patch, environment deletion, ML upgrade or model download is indicated by
the supplied launch error.

### Checkpoint 3: completed local verification

- `UV_CACHE_DIR=/tmp/ewp-uv-cache uv run --locked --no-sync transcriber --version`:
  PASS, 0.20.0; GUI help also PASS.
- The actual CLI server started on an allocated loopback port with `--no-open-browser
  --port 0` and printed `GUI http://127.0.0.1:38833/`; stopped cleanly with Ctrl+C.
  The first sandbox attempt denied socket binding; the approved outside-sandbox retry
  succeeded. That sandbox denial is unrelated to the owner's WSL OS error 2.
  This was a process-start check, not browser/HTTP/visual acceptance.
- `UV_CACHE_DIR=/tmp/ewp-uv-cache make check`: PASS, Ruff lint/format, mypy and 781 tests.
  Existing cases cover staging/start, grouped source validation and controlled backend errors.
- `UV_CACHE_DIR=/tmp/ewp-uv-cache make test-integration`: PASS, five tests, four deselected.
- Native checks via `application.doctor(config=load_config(), test_speech_runtime=True)`:
  media executables PASS; this VM lacks NVIDIA/CUDA visibility and pinned model snapshots;
  TorchCodec fails to find FFmpeg 4–7 shared libraries under installed FFmpeg 8.
  These VM limitations do not establish the WSL transcription failure's cause and do not
  prevent the observed GUI server startup. No model/provider call or download was performed.
- `git diff --check`: PASS after documentation edits.

### Changes

Added `WORK_POLICY.md`, `TODO.md` and this checkpoint; linked recovery instructions from
`AGENTS.md`, `WORK_STATUS.md`, the handoff and existing product roadmap. Added project-name
verification and the exact wrong-checkout recovery case to the GUI quick start and changelog.
No application code, version or ML dependency pin changed in this initial diagnosis.
These notes were local at that handoff and are included with the subsequent dependency/settings fix.

## Resume steps

1. Read `WORK_POLICY.md`, `WORK_STATUS.md`, `TODO.md` and this checkpoint.
2. Inspect Git status; retain all current edits.
3. Ask for the result of launching from the correct WSL transcription checkout. Record its
   actual full SHA/version; do not assume the VM path equals the owner's checkout path.
4. If startup succeeds, run the consolidated owner plan. Use Test local dependencies before
   real transcription; inspect, dry-run, explicitly stage, then Start queue.
5. If a job fails, capture its diagnostic code and Failure technical details without secrets
   or transcript text. Diagnose that evidence before changing native packages or model pins.
6. Keep WSL launch confirmation and real transcription/GUI qualification pending until observed.
