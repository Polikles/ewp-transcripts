"""Small native-platform operations shared by storage and maintenance."""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path

WINDOWS = sys.platform == "win32"


def prepare_native_environment() -> None:
    """Expose the user's private Windows media/CUDA DLLs without changing system PATH."""
    if not WINDOWS:
        return
    from ewp_transcripts.engines.ffmpeg_compat import compatibility_prefix

    paths = [compatibility_prefix() / "bin", Path(sys.prefix) / "Lib/site-packages/torch/lib"]
    current = os.environ.get("PATH", "").split(os.pathsep)
    additions = [str(path) for path in paths if path.is_dir() and str(path) not in current]
    if additions:
        os.environ["PATH"] = os.pathsep.join([*additions, *current])


def private_descriptor_mode(descriptor: int) -> None:
    """Set POSIX private permissions where supported; Windows uses directory ACLs."""
    if not WINDOWS:
        os.fchmod(descriptor, 0o600)


def process_is_alive(pid: int) -> bool:
    """Conservatively probe ownership without sending a signal on Windows."""
    if pid <= 0:
        return True
    if not WINDOWS:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except OSError:
            return True
        return True
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return bool(ctypes.get_last_error() != 87)  # type: ignore[attr-defined]  # ERROR_INVALID_PARAMETER: PID absent
    try:
        code = wintypes.DWORD()
        return not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
    finally:
        kernel.CloseHandle(handle)
