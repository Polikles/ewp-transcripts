# Native Windows setup and repair

1. Follow [Installation and updates](installation.md) for Git, uv, the NVIDIA Windows driver and Microsoft Visual C++ x64 runtime.
2. In a separate Windows checkout, run `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install`.
3. For local ASR, run `uv run --locked --no-sync python scripts/setup-models.py` after accepting the gated model terms.
4. Run `uv run --locked transcriber doctor --test-speech-runtime`, then `uv run --locked transcriber gui`.

The PowerShell execution-policy override applies only to that invocation. The script uses Python 3.12, locked CUDA 12.8 packages and SHA-256-pinned FFmpeg 7.1.1 shared files. It does not change global PATH, install a GPU driver or fetch models by default. `-SetupModels` requests the separate model stage; `-PublicOnly` skips its gated snapshot. Do not share WSL's virtual environment.

Private FFmpeg is normally under `%LOCALAPPDATA%\ewp-transcripts\ffmpeg-7`. Launch prepares process-specific media/Torch DLL lookup. An explicit `EWP_FFMPEG_PREFIX` can point to another supported shared-build root containing `bin`. A system FFmpeg executable or static build alone does not provide the compatible DLLs required by TorchCodec 0.7.

## Repair

Save work and stop the GUI, then run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Repair
uv run --locked transcriber doctor --test-speech-runtime
```

This restores locked TorchCodec/pyannote packages and the private FFmpeg runtime. Retain diagnostic details for CUDA/cuDNN/Visual C++ errors rather than replacing packages at random. Do not substitute FFmpeg 8+ for the pinned shared build. Normal updates use `git pull` and `uv sync --locked`; working setups do not need routine reinstalls.

Models normally live below `%USERPROFILE%\.cache\huggingface`. Native paths such as `C:\Users\name\Podcast files\Żółć.wav` remain native; use ordinary user directories. System directories and symlink/junction targets are blocked. Portable profiles do not copy recordings: move output/media trees separately and check missing paths.

If older model setup reports `Blocked import of regex`, update and rerun the same model command. Current language-data setup uses an isolated child outside the checkout; no disabling of NLTK import security is needed. Native install, local/cloud workflow and restart checks have passed owner tests on Windows 11 x64/RTX 3090; this does not qualify every machine.
