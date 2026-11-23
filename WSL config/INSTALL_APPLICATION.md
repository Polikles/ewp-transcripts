# Install the internal preview

For the current guided setup and normal updates, use [Installation and updates](../docs/gui/installation.md) ([PL](../docs/gui/pl/installation.md)). The manual locked-environment equivalent below remains available.

The supported installation is a source checkout synchronized from the committed
`uv.lock`. Installation does not download transcription models.

## 1. Clone into the Linux filesystem

```bash
mkdir -p "$HOME/transkrypcje"
cd "$HOME/transkrypcje"
git clone https://github.com/Polikles/ewp-transcripts.git ewp-transcripts
cd ewp-transcripts
```

The repository is public but `0.22.1` is an internal beta. No public version
tag or hosted release exists; use the intended commit on `main`.

## 2. Install the locked environment

```bash
uv sync --locked
uv pip check
uv run --locked transcriber --version
uv run --locked transcriber --help
```

Expected application version: `0.22.1`. Help must list `gui`, `doctor`, `inspect`, `dry-run`,
`transcribe`, `export`, `revise`, `translate`, `dictionary`, `benchmark`, and `clean`.

## 3. Check the machine before model setup

```bash
test -z "${HF_TOKEN:-}" && echo "HF_TOKEN: absent"
uv run --locked transcriber doctor
```

On a fresh machine, `doctor` should pass Python, WSL, Ubuntu, FFmpeg, GPU, and CUDA but
exit with code 3 because pinned model snapshots are not present. Continue with
[`MODEL_SETUP.md`](MODEL_SETUP.md); transcription never downloads a missing model.

## 4. Update an existing checkout

```bash
cd "$HOME/transkrypcje/ewp-transcripts"
git pull --ff-only
uv sync --locked
uv pip check
```

Review `CHANGELOG.md` before using a newer commit on irreplaceable archive material.
