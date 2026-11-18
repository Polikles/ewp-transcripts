# Troubleshooting

## `wsl --install` prints help

WSL may already be installed. Run `wsl --list --online` and `wsl --list --verbose`, then install the required distribution explicitly. Microsoft also documents `--web-download` for Store-download problems.

## Distribution is WSL1

```powershell
wsl --set-version <distribution-name> 2
```

Do not continue with GPU setup until `wsl --list --verbose` reports version 2.

## `nvidia-smi` is unavailable inside WSL

1. Confirm it works in Windows PowerShell.
2. Run `wsl --update` and `wsl --shutdown` in PowerShell.
3. Reopen Ubuntu.
4. Try `/usr/lib/wsl/lib/nvidia-smi`.
5. Confirm the Windows driver supports WSL.

Do not fix this by installing a Linux NVIDIA display driver inside WSL.

## PyTorch reports CUDA unavailable

Check that WSL is version 2, `nvidia-smi` works inside WSL, the PyTorch build includes CUDA support, it is driver-compatible, and the command uses the intended `uv` environment.

Do not install random CUDA or PyTorch versions over the project environment. Restore it
with `uv sync --locked`.

## FFmpeg or ffprobe is missing

```bash
sudo apt update
sudo apt install ffmpeg
```

## TorchCodec cannot load FFmpeg libraries / pyannote cannot read audio

Symptoms include `libavutil.so.59` (or `.58`, `.57`, `.56`) missing, `Could not load
libtorchcodec`, and pyannote reporting `torchcodec is not available. Cannot read audio file`.
Ubuntu 26.04 ships FFmpeg 8, but the locked TorchCodec 0.7 supports FFmpeg 4–7. A working
`ffmpeg -version` or CUDA check does not establish native audio-library compatibility.

Save your workspace, stop the GUI with Ctrl+C, and run this in the transcription checkout:

```bash
bash scripts/repair-dependencies.sh
uv run --locked transcriber gui
```

The script restores locked TorchCodec/pyannote packages, verifies an actual WAV decode,
and builds compatible private audio libraries only if needed. It downloads the pinned
official FFmpeg 7.1.5 source with a SHA-256 check; compilation can take a few minutes.
It uses `~/.local/share/ewp-transcripts/ffmpeg-7.1.5` (or the XDG data directory), loaded
only by speech engines/explicit native tests. It preserves the system FFmpeg, CUDA pins,
model caches and output artifacts. No model download or transcription is performed.
The private build handles the pipeline's prepared PCM WAV; original input formats still
go through the system FFmpeg. This is not a replacement system multimedia installation.

If build tools are absent, the script prints the exact prerequisite command:

```bash
sudo apt update && sudo apt install build-essential ca-certificates curl xz-utils
```

After that command, rerun the script. Build failures retain their log in the printed
temporary directory. `--native-only` skips Python package reinstallation for an intact
locked environment. Successful repeated native checks avoid rebuilding/downloading FFmpeg.
For temporary verification, `EWP_FFMPEG_PREFIX` selects a separate private prefix.

In **Settings & About**, run **Test local dependencies** again. That enables **Run doctor**
and **Reinstall dependencies…**; the latter shows the terminal repair steps. Package repair
runs after stopping the GUI so its live Python environment is not modified underneath it.
Doctor remains a read-only environment report; the native test also verifies speech imports.
The terminal equivalent of the complete test is:

```bash
uv run --locked transcriber doctor --test-speech-runtime --json-output
```

A passing native test does not certify full model/GPU execution. Retry the bounded staged
job and retain its exact backend details if it still fails. Missing `HF_TOKEN` is harmless
when the pinned models already exist and the workflow is offline.

Sources: [TorchCodec 0.7 installation](https://raw.githubusercontent.com/pytorch/torchcodec/v0.7.0/README.md),
[official FFmpeg releases](https://ffmpeg.org/releases/).

## Gated model returns 401 or 403

Confirm that the correct account accepted every required model's terms, `HF_TOKEN` is present without printing it, the token can read gated repositories, and the exact pinned model identifier is used.

## Offline run tries to connect

Confirm local model completeness and enable the library offline flags in [`OFFLINE_MODE.md`](OFFLINE_MODE.md). Treat hidden network fallback as a failed offline test.

## Work is slow under `/mnt/c` or `/mnt/d`

Move the repository, environment, caches, and workdir into `/home/<user>`. Windows-mounted paths remain acceptable for source recordings when necessary.
