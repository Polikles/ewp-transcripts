# Reference Environment: WSL2

Operational clean-machine instructions and verification checklists are maintained in [`../WSL config/`](../WSL%20config/README.md). This document remains the normative environment policy.

## 1. MVP baseline

- Windows 11;
- current Windows NVIDIA driver with WSL2 support;
- WSL2;
- Ubuntu 24.04 LTS as the initial reference distribution;
- Python 3.12;
- `uv` and a lockfile;
- FFmpeg/ffprobe;
- CUDA-enabled PyTorch compatible with the selected WhisperX version;
- stable WhisperX release, not a prerelease;
- local `pyannote/speaker-diarization-community-1` model.

Ubuntu24.04 and26.04 are maintained current WSL targets, with recorded qualification in checkpoints. The list above records the initial baseline. For current GPU/driver/VRAM limits use [HARDWARE.md](HARDWARE.md); do not infer bare-metal GPU qualification from a WSL or model-free VM pass.

## 2. CUDA rules in WSL

- the GPU driver is installed on Windows;
- do not install a Linux NVIDIA display driver inside WSL;
- the application must verify `nvidia-smi` and `torch.cuda.is_available()`;
- the exact PyTorch/CUDA combination is pinned in the lockfile after smoke tests pass.

## 3. File locations

The following should reside in the WSL filesystem:

```text
/home/<user>/projects/ewp-transcripts
/home/<user>/.cache/ewp-transcripts
/home/<user>/.cache/huggingface
```

Source media may remain on `D:` and be read through `/mnt/d`, but frequently accessed temporary files and caches remain inside WSL.

## 4. User path forms

The CLI should accept:

```text
D:\podcast\S01E01.wav
D:/podcast/S01E01.wav
/mnt/d/podcast/S01E01.wav
```

The path normalizer stores both the user-provided representation and the normalized working path in JSON.

## 5. Gated models

Application installation does not automatically download the pyannote model.

User procedure:

1. accept the model terms on Hugging Face;
2. create a read token;
3. set `HF_TOKEN` in the environment;
4. explicitly download the model to a local directory;
5. run `transcriber doctor`;
6. use the local model path in offline mode.

A missing model during `transcribe` returns exit code 3 with instructions; it does not trigger an automatic download.

## 6. Installer/bootstrap behavior

The installer or developer bootstrap should:

- install application dependencies from the lockfile;
- verify FFmpeg and the `rg` text-search tool used by documented checks;
- verify CUDA;
- detect `HF_TOKEN` without displaying its value;
- explain that gated-model terms must be accepted;
- never download gated models without an explicit operation.

The v0.3 source checkout implements this boundary in
`scripts/install-fresh-ubuntu.sh`. Its default `--verify-only` mode is read-only.
`--install` explicitly confirms before running Ubuntu package updates, installing base
packages and uv/Python, and synchronizing the committed lockfile. It never clones, pulls,
or downloads gated models, so existing-checkout updates and model preparation remain
separate operator decisions.

## 7. Offline mode

Offline mode means:

- models are loaded only from local paths or caches;
- there is no network fallback;
- there is no telemetry;
- there is no remote diarization;
- a missing local resource is an error.

## 8. Minimum diagnostics

`doctor` should report:

```text
WSL2: OK
Ubuntu: supported / warning
NVIDIA driver: OK
GPU: RTX 3090
PyTorch CUDA: OK
FFmpeg: OK
WhisperX: pinned version
ASR model: present
Alignment model PL: present
Diarization model: present
Offline readiness: OK / missing resources
```
