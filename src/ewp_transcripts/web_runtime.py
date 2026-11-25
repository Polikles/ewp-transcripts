"""Authenticated same-user management of a managed local GUI instance (standard library only)."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from pathlib import Path


def runtime_authorized(supplied: str, expected: str) -> bool:
    """Standalone CLI servers expose no management credential by default."""
    return len(expected) >= 32 and secrets.compare_digest(supplied, expected)


def runtime_status() -> dict[str, object]:
    return {"pid": os.getpid(), "status": "ready"}


def current_process_identity() -> str:
    """Match the manager's creation identity, including Windows venv redirectors."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            *([ctypes.POINTER(wintypes.FILETIME)] * 4),
        ]
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(
            kernel.GetCurrentProcess(), *(ctypes.byref(t) for t in times)
        ):
            raise ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]
        return str(times[0].dwLowDateTime | times[0].dwHighDateTime << 32)
    ticks = Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()[19]
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    return f"{boot_id}:{ticks}"


def publish_runtime(*, port: int) -> None:
    """The listening server publishes its own PID, never its launcher/venv redirector PID."""
    token = os.environ.get("EWP_RUNTIME_TOKEN", "")
    destination = os.environ.get("EWP_RUNTIME_RECORD", "")
    root = os.environ.get("EWP_RUNTIME_ROOT", "")
    if len(token) < 32 or not destination or not root:
        return
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".ewp-runtime-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(
                {
                    "root": root,
                    "pid": os.getpid(),
                    "identity": current_process_identity(),
                    "port": port,
                    "token": token,
                },
                stream,
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def system_ui_language() -> str:
    """Return the Windows user's UI language, or defer to browser preferences."""
    import sys

    if sys.platform == "win32":
        import ctypes
        import locale

        language = locale.windows_locale.get(
            ctypes.windll.kernel32.GetUserDefaultUILanguage(), "en"
        )
        return "pl" if language.lower().startswith("pl") else "en"
    return ""
