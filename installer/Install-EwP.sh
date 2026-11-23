#!/usr/bin/env bash
set -euo pipefail
# After extracting a complete Ubuntu bundle: bash control/Install-EwP.sh install --bundle /path/file.zip
control_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ $# == 0 || "${1:-}" == --help ]]; then
 printf 'Usage: bash Install-EwP.sh check|install|update|repair|rollback|launch|uninstall [--root DIR] [--bundle FILE.zip] [--local --accept-model-terms] [--yes] [--remove-models] [--remove-key]\n'
 exit 0
fi
if [[ -f "$control_dir/owner.json" ]]; then
 uv_binary="$control_dir/tools/uv"
 if [[ " $* " != *" --root "* ]]; then set -- "$@" --root "$control_dir"; fi
else uv_binary="$control_dir/../tools/uv"; fi
if [[ ! -f "$uv_binary" ]]; then printf 'Extract the complete bundle; bundled uv is missing.\n' >&2; exit 2; fi
chmod u+x "$uv_binary"
bootstrap_root="$(mktemp -d "${TMPDIR:-/tmp}/ewp-bootstrap.XXXXXX")"
trap 'rm -rf -- "$bootstrap_root"' EXIT
export UV_PYTHON_INSTALL_DIR="$bootstrap_root/python"
export UV_CACHE_DIR="$bootstrap_root/cache"
export UV_NO_CONFIG=1
offline_options=()
if [[ -f "$control_dir/owner.json" && "${1:-}" =~ ^(uninstall|rollback|launch)$ ]]; then
 # The existing managed Python works without a fresh bootstrap download for maintenance.
 export UV_PYTHON_INSTALL_DIR="$control_dir/tools/python"
 offline_options=(--offline)
fi
if [[ "${1:-}" == install || "${1:-}" == update || "${1:-}" == repair ]]; then
 missing=()
 for tool in ffmpeg ffprobe gcc make curl xz; do command -v "$tool" >/dev/null || missing+=("$tool"); done
 if ((${#missing[@]})); then
  printf 'Missing Ubuntu prerequisites: %s\nInstall required Ubuntu packages using sudo? [y/N] ' "${missing[*]}"
  read -r answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then exit 2; fi
  sudo apt-get update
  sudo apt-get install -y ffmpeg build-essential ca-certificates curl xz-utils
 fi
fi
"$uv_binary" run "${offline_options[@]}" --no-project --python 3.12 python "$control_dir/manager.py" "$@"
