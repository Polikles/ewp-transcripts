# Installation and updates

## Choose the environment

Windows 11 x64 and WSL2 Ubuntu 24.04/26.04 use the same repository and workflow. Use a separate checkout and virtual environment for each operating system. Native Windows installation and workflow have passed owner tests; this is not a claim that all Windows/GPU combinations are qualified.

For local ASR, prepare an NVIDIA driver, CUDA-capable GPU and pinned local models. Reference testing used RTX 3090 24 GB; other NVIDIA GPUs with at least 8 GB VRAM are expected to work without a guarantee. Reserve at least 20 GB for the environment/model cache plus recordings, temporary audio and results. Download/storage sizes vary with caches and options.

Cloud ASR uses FFmpeg and the application environment but does not load local WhisperX/alignment/diarization models. Reviewing an existing result and exporting it also do not initialize ML. Local-model doctor checks can fail on a deliberately cloud-only setup; distinguish those from media-tool or provider errors. The normal installer still prepares the locked environment.

## Fresh Windows installation

1. Install Git, the NVIDIA Windows driver for local ASR and the Microsoft Visual C++ x64 runtime. Install uv, then reopen PowerShell:

```powershell
winget install --id astral-sh.uv --exact
```

2. Clone into an ordinary user directory and enter that checkout:

```powershell
git clone https://github.com/Polikles/ewp-transcripts.git
cd ewp-transcripts
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
```

3. For local ASR, explicitly download the pinned models:

```powershell
uv run --locked --no-sync python scripts/setup-models.py
```

4. Check the speech runtime and launch:

```powershell
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

The script pins Python 3.12, Torch/CUDA and a private shared FFmpeg build. It does not install a driver or download models by default. See [Windows details](windows-native.md) for runtime location and repair.

## Fresh WSL installation

1. Install WSL2 and Ubuntu 24.04 or 26.04. Install the Windows NVIDIA driver with WSL CUDA support. Use the Linux filesystem for the checkout and preferably heavy working files. Do not install a Linux display driver inside WSL.
2. In Ubuntu, install Git and clone:

```bash
sudo apt update
sudo apt install git
git clone https://github.com/Polikles/ewp-transcripts.git
cd ewp-transcripts
./scripts/install-fresh-ubuntu.sh --install
```

3. Reopen the shell if uv is not on PATH. For local ASR, prepare models explicitly, then check and launch:

```bash
./scripts/setup-models.sh
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

The installer asks before system changes, installs the locked environment and checks native audio libraries. It can prepare private FFmpeg 7 libraries when the distribution provides an incompatible shared ABI. Model preparation remains a separate explicit download.

## Model access and offline operation

Accept the terms for `pyannote/speaker-diarization-community-1` on Hugging Face before downloading it. Use a read token privately when prompted; never put a token into commands or a shared document. `--public-only` prepares public ASR/alignment models and language data while skipping the gated diarizer. It does not prepare the complete mixed-speaker local workflow.

Both model scripts support `--help`, `--yes` and `--public-only`. Defaults pin ASR large-v2, Polish/English alignment and pyannote revisions. Models normally live under `~/.cache/huggingface` (Windows: `%USERPROFILE%\.cache\huggingface`). Normal local transcription does not silently fetch a missing model. A missing `HF_TOKEN` is harmless once all required local snapshots are present. Optional provider APIs still need a network connection.

## Start, stop and update

Run commands from the transcriber checkout, not the separate waveform repository:

```text
uv run --locked transcriber gui
```

Open the printed `http://127.0.0.1:8765/` URL. Use `gui --no-open-browser` to open it yourself, or `gui --port 8766` if the default port is busy. Closing a browser tab does not stop a running transcription. Save work and let active jobs finish or cancel safely before stopping the terminal server with Ctrl+C.

An ordinary update is not a fresh installation:

```text
git pull
uv sync --locked
uv run --locked transcriber gui
```

Stop the server before updating; keep a work checkpoint and backup first. Do not redownload models or reinstall Windows components after every update. Run doctor after installation, system/runtime changes or a relevant error. Reinstall/repair only when diagnostics justify it. [Troubleshooting](troubleshooting.md) includes launch and Ubuntu-upgrade failures.

## Removal and future installer

A complete uninstaller (including an explicit model-cache choice), standalone graphical Windows installer, desktop shortcut and Add/Remove Programs integration are planned work. They are not shipped by the current repository setup script. Before manually removing a checkout or cache, preserve outputs, workspace catalogs and private dictionaries, and consider whether another application uses the same Hugging Face snapshots. Saved OS credentials are separate: remove the OpenRouter entry explicitly through the application if desired. No automatic removal command is prescribed here because shared caches and user work must not be guessed.
