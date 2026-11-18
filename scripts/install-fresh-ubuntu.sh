#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./scripts/install-fresh-ubuntu.sh [--verify-only | --install] [--yes]

Verify or prepare a fresh Ubuntu 24.04 / 26.04 checkout of EWP Transcriber.

  --verify-only  Read-only prerequisite and application verification (default).
  --install      Install Ubuntu prerequisites, uv/Python, and the locked environment.
  --yes          Skip this script's confirmation prompt; package tools may still prompt.
  --help         Show this help.

The script must be run from a cloned source checkout. It does not clone/update Git,
download gated transcription models, or install an NVIDIA display driver.
EOF
}

mode="verify"
confirmed="false"
while (($#)); do
    case "$1" in
        --verify-only) mode="verify" ;;
        --install) mode="install" ;;
        --yes) confirmed="true" ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Error: unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
if [[ ! -f "$repo_root/pyproject.toml" || ! -f "$repo_root/uv.lock" ]]; then
    printf 'Error: script is not inside an EWP Transcriber source checkout.\n' >&2
    exit 2
fi

if [[ ! -r /etc/os-release ]]; then
    printf 'Error: /etc/os-release is unavailable. Ubuntu 24.04 or 26.04 is required.\n' >&2
    exit 2
fi
# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "ubuntu" || ( "${VERSION_ID:-}" != "24.04" && "${VERSION_ID:-}" != "26.04" ) ]]; then
    printf 'Error: supported baselines are Ubuntu 24.04 and 26.04; detected %s %s.\n' \
        "${ID:-unknown}" "${VERSION_ID:-unknown}" >&2
    exit 2
fi

if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
    printf 'Environment: Ubuntu %s under WSL2\n' "$VERSION_ID"
else
    printf 'Environment: Ubuntu %s outside WSL2 (expected but not release-validated)\n' "$VERSION_ID"
fi

available_kib="$(df -Pk "$repo_root" | awk 'NR==2 {print $4}')"
minimum_kib=$((20 * 1024 * 1024))
if [[ ! "$available_kib" =~ ^[0-9]+$ ]]; then
    printf 'Error: cannot determine available repository filesystem space.\n' >&2
    exit 2
fi
if ((available_kib < minimum_kib)); then
    printf 'WARNING: less than the recommended 20 GB of free Linux-filesystem space.\n' >&2
else
    printf 'Storage: at least 20 GB free\n'
fi

if [[ "$mode" == "install" ]]; then
    if [[ "$confirmed" != "true" ]]; then
        printf '%s\n' \
            'This will run Ubuntu package updates, install base packages and uv/Python,' \
            'then synchronize uv.lock and repair native audio libraries if needed.' \
            'Native repair may download/build private FFmpeg 7 libraries. No gated models.'
        read -r -p 'Continue? [y/N] ' answer
        [[ "$answer" =~ ^[Yy]$ ]] || { printf 'Cancelled.\n'; exit 4; }
    fi

    sudo apt update
    sudo apt upgrade
    sudo apt install build-essential ca-certificates curl ffmpeg git ripgrep xz-utils

    if ! command -v uv >/dev/null 2>&1; then
        uv_installer="$(mktemp /tmp/ewp-uv-install-XXXXXXXX.sh)"
        trap 'rm -f -- "$uv_installer"' EXIT
        printf 'Downloading the official uv installer to %s\n' "$uv_installer"
        curl -LsSf https://astral.sh/uv/install.sh -o "$uv_installer"
        sh "$uv_installer"
        export PATH="$HOME/.local/bin:$PATH"
    fi
    uv python install 3.12
    (cd -- "$repo_root" && uv sync --locked)
    bash "$repo_root/scripts/repair-dependencies.sh" --native-only
    printf '%s\n' \
        'Application installation completed.' \
        'If uv is unavailable after this script exits, open a new shell or run:' \
        '  source "$HOME/.local/bin/env" 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"'
fi

required_commands=(git ffmpeg ffprobe curl rg uv)
for command_name in "${required_commands[@]}"; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        printf 'Error: required command is missing: %s\n' "$command_name" >&2
        printf 'Run this script with --install or follow Instructions/README.md.\n' >&2
        exit 3
    fi
done

git --version
rg --version | head -n 1
ffmpeg -version | head -n 1
ffprobe -version | head -n 1
uv --version
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
else
    printf 'WARNING: nvidia-smi is unavailable; current GPU presets are not ready.\n' >&2
fi

cd -- "$repo_root"
uv pip check
uv run --locked --no-sync transcriber --version
uv run --locked --no-sync transcriber --help >/dev/null

doctor_report="$(mktemp /tmp/ewp-doctor-XXXXXXXX.json)"
trap 'rm -f -- "$doctor_report" "${uv_installer:-}"' EXIT
set +e
uv run --locked --no-sync transcriber doctor --json-output >"$doctor_report"
doctor_exit=$?
set -e
if [[ "$doctor_exit" -eq 0 ]]; then
    printf 'Doctor: complete model readiness passed\n'
elif [[ "$doctor_exit" -eq 3 ]]; then
    printf '%s\n' \
        'Doctor: application environment passed; one or more pinned models are missing.' \
        'Continue with WSL config/MODEL_SETUP.md. Gated models require explicit terms/token access.'
else
    printf 'Error: doctor failed with unexpected exit code %s.\n' "$doctor_exit" >&2
    exit "$doctor_exit"
fi

printf 'Fresh-checkout verification completed. No Git update or gated-model download was performed.\n'
