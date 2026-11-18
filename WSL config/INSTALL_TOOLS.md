# Install stable base tools

These steps install only the non-ML foundation. Application and ML dependencies are
installed later from the committed lockfile.

Both Ubuntu 24.04 and 26.04 are accepted. On 26.04, installing the `ffmpeg` executable
does not supply the older shared-library ABI needed by locked TorchCodec 0.7. After
`uv sync --locked`, run `bash scripts/repair-dependencies.sh --native-only` if using
these manual steps. The fresh-install script runs that check/repair automatically.

## 1. Update Ubuntu packages

```bash
sudo apt update
sudo apt upgrade
```

Review the proposed changes before confirming. Restart WSL if the kernel or core WSL packages require it.

## 2. Install base packages

```bash
sudo apt install build-essential ca-certificates curl ffmpeg git ripgrep xz-utils
```

Verify:

```bash
git --version
rg --version
ffmpeg -version
ffprobe -version
curl --version
```

## 3. Install `uv`

Download the official installer. Reviewing its contents is optional unless required by
your organization's security policy; users are not expected to independently audit the
installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/ewp-uv-install.sh
```

Then install:

```bash
sh /tmp/ewp-uv-install.sh
```

Start a new shell or follow the PATH instruction printed by the installer, then run `uv --version`.

Source: [Astral — Installing uv](https://docs.astral.sh/uv/getting-started/installation/).

## 4. Prepare Python 3.12

Do not create project metadata yet. Install and verify the required interpreter through `uv`:

```bash
uv python install 3.12
uv run --python 3.12 python --version
```

The second command must report Python 3.12.x. The exact patch version is recorded when the lockfile is created.

Source: [Astral — Installing and managing Python](https://docs.astral.sh/uv/guides/install-python/).

## 5. Prepare Linux-filesystem directories

```bash
mkdir -p "$HOME/projects"
mkdir -p "$HOME/.cache/ewp-transcripts"
mkdir -p "$HOME/.cache/huggingface"
```

Clone the project under `$HOME/projects`, not under `/mnt/c` or another Windows-mounted path.

Source: [Microsoft — Working across file systems](https://learn.microsoft.com/windows/wsl/filesystems).
