"""Load explicitly installed FFmpeg 7 libraries before lazy speech imports.

Ubuntu 26.04's system FFmpeg 8 is newer than the locked TorchCodec ABI. The
repair script installs a private audio-only build; system media tools stay in use.
"""

from __future__ import annotations

import ctypes
import os
import sys
from functools import cache
from pathlib import Path

FFMPEG_VERSION = "7.1.5"
LIBRARIES = (
    "libavutil.so.59",
    "libswresample.so.5",
    "libavcodec.so.61",
    "libavformat.so.61",
    "libswscale.so.8",
    "libavfilter.so.10",
    "libavdevice.so.61",
)


def compatibility_prefix() -> Path:
    """Return the private installation location, with an explicit test override."""

    override = os.environ.get("EWP_FFMPEG_PREFIX")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        return (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
            / "ewp-transcripts/ffmpeg-7"
        )
    configured_home = os.environ.get("XDG_DATA_HOME", "")
    data_home = Path(configured_home) if configured_home else Path.home() / ".local/share"
    if not data_home.is_absolute():
        data_home = Path.home() / ".local/share"
    return data_home / "ewp-transcripts" / f"ffmpeg-{FFMPEG_VERSION}"


@cache
def _windows_dll_directories(prefix: Path) -> tuple[object, ...]:
    # Retain add_dll_directory handles. Torch's own wheel supplies CUDA/cuDNN DLLs;
    # TorchCodec uses the separately installed FFmpeg 7 shared build.
    paths = [prefix / "bin", Path(sys.prefix) / "Lib/site-packages/torch/lib"]
    paths.extend(Path(part) for part in os.environ.get("PATH", "").split(os.pathsep) if part)
    handles = []
    for path in dict.fromkeys(paths):
        if path.is_dir():
            handles.append(os.add_dll_directory(str(path)))  # type: ignore[attr-defined]
    return tuple(handles)


@cache
def _load_libraries(prefix: Path) -> tuple[ctypes.CDLL, ...]:
    # Retain handles for the process lifetime. Canonical SONAMEs let TorchCodec's
    # existing ELF dependencies resolve without LD_LIBRARY_PATH or ABI symlinks.
    return tuple(
        ctypes.CDLL(str(prefix / "lib" / name), mode=ctypes.RTLD_GLOBAL) for name in LIBRARIES
    )


def prepare_speech_libraries() -> None:
    """Use a repaired installation when present; otherwise retain system loading."""

    prefix = compatibility_prefix()
    if sys.platform == "win32":
        _windows_dll_directories(prefix)
        return
    if prefix.exists():
        try:
            _load_libraries(prefix)
        except OSError as error:
            raise RuntimeError(
                "The private FFmpeg runtime is incomplete or unreadable. Stop the GUI and run "
                "bash scripts/repair-dependencies.sh from the transcription checkout."
            ) from error
