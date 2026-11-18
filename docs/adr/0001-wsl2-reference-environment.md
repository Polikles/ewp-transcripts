# ADR-0001: WSL2 as the Reference Environment

- Status: accepted
- Date: 2026-07-29

## Context

The ML stack is strongly aligned with the Linux CUDA ecosystem, while the user works on Windows.

## Decision

MVP Tier 1: WSL2 + Ubuntu 24.04 LTS or Ubuntu 26.04 LTS + NVIDIA CUDA.
The 26.04 baseline was accepted on 2026-11-18 at the owner's request; it is also the current
development VM baseline. Native Linux and native Windows are not required targets.

## Consequences

- the repository, work directories, and model caches reside in the WSL filesystem;
- sources may be read from Windows drives;
- a future Docker image should use the same Linux baseline;
- Ubuntu 26.04 uses the locked ML environment plus private FFmpeg 7 audio libraries when
  the system FFmpeg 8 ABI cannot load in TorchCodec 0.7. Run the supported dependency-repair
  script; do not downgrade system media packages. Baseline acceptance does not imply every
  GPU/browser workflow has been qualified; current evidence remains in the task checkpoints.
