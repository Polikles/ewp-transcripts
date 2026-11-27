# System requirements

## Required for the MVP reference environment

| Component | Requirement |
|---|---|
| Host | Windows 11 with virtualization enabled |
| WSL | Current stable WSL, distribution running as WSL2 |
| Distribution | Ubuntu 24.04 LTS or Ubuntu 26.04 LTS |
| GPU | Compatible NVIDIA CC7.0+;12GB+ VRAM recommended; tested RTX3090/24GB |
| Driver | Windows NVIDIA572.61+ with WSL support; CUDA12.8 Update1 project baseline |
| Python | 3.12 |
| Package manager | `uv`; dependencies are reproduced from the committed lockfile |
| Media tools | System FFmpeg/ffprobe; compatible private FFmpeg 7 audio libraries when TorchCodec cannot use the system ABI |
| Text search | ripgrep (`rg`) from Ubuntu packages, used by documented verification checks |
| Storage | Linux-filesystem space for source checkout, environments, models, and work files |
| Network | Required during initial package and model setup; not required for normal offline transcription |

## Capacity guidance

Ubuntu 26.04 is an accepted development/WSL baseline. Its FFmpeg 8 executable can work
while TorchCodec 0.7 lacks compatible native libraries. The fresh-install script prepares
these automatically; an existing installation can run `bash scripts/repair-dependencies.sh`.
See [troubleshooting](TROUBLESHOOTING.md). This preserves locked CUDA/ML versions and models.

Reserve enough Linux-filesystem space for the Git checkout, Python environment, model
snapshots, working audio, retained failure artifacts, and archive outputs. The accepted
151-minute test peaked near 4.14 GiB process RAM and 14.6 GiB sampled total GPU use on the
24 GiB reference GPU, but these observations are not minimum hardware guarantees.

Validation was performed on an NVIDIA GeForce RTX 3090 with 24 GB VRAM. Other NVIDIA
Smaller compatible GPUs may work, but have not been tested and are not guaranteed. Below12GB
VRAM use cloud ASR. Pascal/Maxwell cannot run the current local library stack; no GTX1070 tests or
legacy profile are planned. See [current hardware/library policy](../docs/HARDWARE.md). No separate
system CUDA Toolkit or Linux display driver inside WSL is required by that policy.

## Expected paths

```text
/home/<user>/transkrypcje/ewp-transcripts
/home/<user>/.cache/ewp-transcripts
/home/<user>/.cache/huggingface
```

Source recordings may be read from Windows drives, but temporary audio, environments, caches, and active development files should remain in the Linux filesystem for performance.
