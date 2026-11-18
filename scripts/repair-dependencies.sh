#!/usr/bin/env bash
set -euo pipefail

# Run in a terminal after stopping the GUI. No sudo, model download or system
# FFmpeg replacement. Python packages are restored only to their locked versions.
if [[ "${1:-}" == "--help" ]]; then
    printf '%s\n' \
        'Usage: bash scripts/repair-dependencies.sh [--native-only]' \
        'Stop the GUI first. Restores locked TorchCodec/pyannote packages and, if needed,' \
        'downloads/builds private FFmpeg 7 audio libraries. Requires network access.' \
        '--native-only skips Python package reinstallation (useful for an intact lock install).'
    exit 0
fi
if (($# > 1)) || [[ "${1:-}" != "" && "${1:-}" != "--native-only" ]]; then
    printf 'Unknown option; use --help.\n' >&2
    exit 2
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd -- "$script_dir/.."
if ! command -v uv >/dev/null; then
    printf 'uv is missing. Follow WSL config/INSTALL_TOOLS.md.\n' >&2
    exit 2
fi
native_audio_check() {
    uv run --locked --no-sync python - <<'PY'
import tempfile
import wave
from pathlib import Path
from ewp_transcripts.engines.ffmpeg_compat import prepare_speech_libraries

prepare_speech_libraries()
from torchcodec.decoders import AudioDecoder

with tempfile.TemporaryDirectory(prefix="ewp-native-decode-", dir="/tmp") as root:
    path = Path(root) / "probe.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x10" * 1600)
    decoded = AudioDecoder(str(path)).get_all_samples()
    assert decoded.sample_rate == 16000
    assert tuple(decoded.data.shape) == (1, 1600)
    assert (decoded.data - 0.125).abs().max().item() < 1e-6
print("PASS: TorchCodec loaded and decoded a real PCM WAV with exact sample values.")
PY
}
if [[ "${1:-}" != "--native-only" ]]; then
    uv sync --locked --reinstall-package torchcodec --reinstall-package pyannote-audio
fi
if native_audio_check >/dev/null 2>&1; then
    printf 'Native audio libraries already work. No FFmpeg build needed.\n'
    exit 0
fi
for required_tool in curl gcc make tar xz sha256sum; do
    if ! command -v "$required_tool" >/dev/null; then
        printf 'Missing build tool: %s\nRun: sudo apt update && sudo apt install build-essential ca-certificates curl xz-utils\n' "$required_tool" >&2
        exit 3
    fi
done

repair_prefix="$(uv run --locked --no-sync python -c 'from ewp_transcripts.engines.ffmpeg_compat import compatibility_prefix; print(compatibility_prefix())')"
repair_root="$(mktemp -d /tmp/ewp-ffmpeg-repair.XXXXXXXX)"
trap 'printf "Repair failed; build evidence retained in %s\n" "$repair_root" >&2' ERR
printf 'Building private FFmpeg 7.1.5 audio libraries in %s\nBuild log: %s/build.log\n' "$repair_prefix" "$repair_root"
curl --fail --location --proto '=https' --tlsv1.2 --connect-timeout 30 --max-time 300 \
    https://ffmpeg.org/releases/ffmpeg-7.1.5.tar.xz -o "$repair_root/ffmpeg.tar.xz"
printf '%s  %s\n' de668509caf9e35e3cd162473441fdb29538c6d96ed080292b3cf9e6fc5d558f \
    "$repair_root/ffmpeg.tar.xz" | sha256sum --check
tar -xJf "$repair_root/ffmpeg.tar.xz" -C "$repair_root"
(
    cd -- "$repair_root/ffmpeg-7.1.5"
    ./configure --prefix="$repair_prefix" --libdir="$repair_prefix/lib" \
        --disable-everything --enable-shared --disable-static --disable-programs \
        --disable-doc --disable-autodetect --disable-x86asm \
        --enable-protocol=file --enable-demuxer=wav --enable-muxer=wav \
        --enable-decoder=pcm_s16le,pcm_s24le,pcm_s32le,pcm_f32le,pcm_f64le \
        --enable-encoder=pcm_s16le --enable-filter=aresample
    make -j2
    make install
) >"$repair_root/build.log" 2>&1
native_audio_check
printf 'Repair complete. Restart the GUI, then use Settings & About → Test local dependencies.\n'
# Only this script's mktemp directory is disposable; never delete the install or model cache.
rm -rf -- "$repair_root"
