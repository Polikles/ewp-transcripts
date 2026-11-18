# Ubuntu upgrade and native dependency recovery

This guide applies when transcription worked on Ubuntu 24.04 and failed after upgrading to Ubuntu 26.04, or when the native speech check reports missing FFmpeg shared libraries.

1. Save current work state and stop the GUI with Ctrl+C. Enter the existing transcription checkout, not the separate waveform project.
2. Update the checkout with `git pull --ff-only`, preserving local changes. Do not delete the Python environment or model caches.
3. Run `bash scripts/repair-dependencies.sh`. If it lists missing build prerequisites, run its exact install command and rerun the repair.
4. Restart with `uv run --locked transcriber gui`, open Settings & About and run Test local dependencies.
5. Retry the short staged episode. If it still fails, retain the diagnostic code and Failure technical details without transcript text or credentials.

## Why an OS upgrade can cause this

The Python packages remain pinned to TorchCodec 0.7 and PyTorch 2.8. Ubuntu 24.04 normally supplies compatible FFmpeg 6 libraries; Ubuntu 26.04 supplies FFmpeg 8. The newer executable can work while TorchCodec cannot find its FFmpeg 4–7 shared-library ABI. Errors include `libavutil.so.59` (or .58/.57/.56), `Could not load libtorchcodec`, and pyannote reporting `torchcodec is not available. Cannot read audio file`.

## Installation already includes the native setup

`scripts/install-fresh-ubuntu.sh --install` synchronizes locked packages and automatically invokes the native check/repair. An OS upgrade after installation can change the system libraries, so run the focused repair above instead of repeating a complete distribution or model setup.

## What the focused repair does

The script restores locked TorchCodec and pyannote packages, checks a real WAV decode, and builds private compatible FFmpeg 7.1.5 audio libraries only if decoding fails. It downloads the official source with a pinned SHA-256 check. Compilation can take a few minutes. System FFmpeg, ML package versions, model caches and prior exports are retained.

If build tools are missing, the script prints this prerequisite command:

```bash
sudo apt update && sudo apt install build-essential ca-certificates curl xz-utils
```

After installing prerequisites, rerun the repair. Native library failures and failed build logs remain explicit. A native-only recheck can use `bash scripts/repair-dependencies.sh --native-only`. Never symlink FFmpeg 8 libraries to older ABI filenames.

## Other checks

A missing HF_TOKEN does not block complete offline model snapshots. Missing GPU/CUDA, pinned model paths or a different backend exception require their own failed-check guidance. Passing a native test is not a substitute for actual model/GPU execution. Full repair/background information is in `WSL config/TROUBLESHOOTING.md`.
