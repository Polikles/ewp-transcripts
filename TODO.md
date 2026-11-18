# Immediate work queue

Updated: 2026-11-18.

Policy: [WORK_POLICY.md](WORK_POLICY.md). Product roadmap:
[docs/99-roadmap-v2.md](docs/99-roadmap-v2.md).

## GUI launch diagnosis completed; WSL launch confirmed

Checkpoint: [2026-11-18 launch diagnosis](docs/checkpoints/2026-11-18-gui-launch.md).

- [x] Recover repository state, previous verification and private reference location.
- [x] Establish persistent work policy, todo and task checkpoint.
- [x] Reproduce package/CLI/server launch with the locked Python environment.
- [x] Inspect staging/start/error paths and run existing queue/integration coverage.
- [x] Reproduce native speech-runtime diagnostics without models or downloads.
- [x] Identify supplied WSL error: `uv` ran in `ewp-waveform`, which lacks `transcriber`.
- [x] Document recovery and run required local checks (781 tests; five integration tests).
- [x] Record remaining WSL evidence and a bounded owner retest in the checkpoint.
- [x] Owner confirms GUI launch from the correct transcription checkout.
- [x] Capture actual WSL queue/backend error: missing FFmpeg libraries disable TorchCodec.

## Active: dependency repair and GUI feedback

Checkpoint: [dependency repair](docs/checkpoints/2026-11-18-gui-dependency-repair.md).

- [x] Add a guided native-runtime repair preserving locked ML versions.
- [x] Put Test, doctor and repair controls in Settings & About, with post-test activation.
- [x] Accept Ubuntu 26.04 alongside 24.04 in diagnostics and installation tools.
- [x] Rename Remove from list and reduce queue width/spacing at half-screen.
- [x] Run automated gates, real native audio decoding and available browser checks.
- [x] Record remaining GPU/WSL qualification and exact owner retest commands.
- [ ] Owner runs repair and retries the short staged episode on the RTX 3090.

## Following work

- Resume the consolidated GUI preview acceptance session after startup is understood.
- Record WSL/browser, real GPU/provider and actual zoom results against the existing
  owner test plan; leave the new-palette YouTube qualification pending until observed.
- Keep GUI-55 closed. Do not tag or publish the internal 0.20.0 preview.
