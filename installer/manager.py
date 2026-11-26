"Managed install/update/uninstall; standard library only, runnable before app dependencies."

from __future__ import annotations

import argparse
import contextlib
import contextvars
import getpass
import hashlib
import json
import os
import platform
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import Any

MAGIC = "ewp-transcripts-managed-v1"
CANCEL_FILE: contextvars.ContextVar[Path | None] = contextvars.ContextVar(
    "installer_cancel_file", default=None
)


class InstallError(ValueError):
    pass


def check_cancelled() -> None:
    marker = CANCEL_FILE.get()
    if marker is not None and marker.exists():
        raise InstallError(
            "INSTALL_CANCELLED: Operation cancelled; previous active app is preserved"
        )


def stop_child(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        import signal

        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def emit(stage: str, message: str, **values: Any) -> None:
    print(
        json.dumps(
            {"time": datetime.now(UTC).isoformat(), "stage": stage, "message": message, **values},
            ensure_ascii=False,
        ),
        flush=True,
    )


def atomic_copy(source: Path, destination: Path) -> None:
    temporary = destination.with_name(destination.name + ".tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)


def atomic_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def default_root() -> Path:
    return (
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "EwPTranscripts"
        if os.name == "nt"
        else Path.home() / ".local/share/ewp-transcripts/installation"
    )


def validate_root_shape(value: PurePath, home: PurePath, *, windows: bool) -> None:
    """A Windows drive child is a valid dedicated folder; depth is not ownership."""
    if value == home or value == type(value)(value.anchor):
        raise InstallError("Choose a separate application folder, not a drive or home root")
    if not windows and len(value.parts) < 4:
        raise InstallError("Choose a separate application directory")


def safe_root(value: Path) -> Path:
    if any(ord(c) < 32 for c in str(value)):
        raise InstallError("Install path must not contain control characters")
    value = value.expanduser().absolute()
    for parent in (value, *value.parents):
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise InstallError("Install path must not contain symbolic links or junctions")
    resolved = value.resolve()
    validate_root_shape(resolved, Path.home().resolve(), windows=os.name == "nt")
    if os.name != "nt" and any(
        resolved == Path(p) or Path(p) in resolved.parents
        for p in ("/usr", "/etc", "/bin", "/lib", "/var")
    ):
        raise InstallError("Choose a user directory, not a system location")
    for name in ("versions", "tools", "runtime", "cache", "wizards"):
        child = resolved / name
        if child.is_symlink() or (hasattr(child, "is_junction") and child.is_junction()):
            raise InstallError("Managed directories must not be links or junctions")
    return resolved


def load_owner(root: Path) -> dict[str, Any] | None:
    marker = root / "owner.json"
    if not marker.exists():
        return None
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        if data["kind"] != MAGIC or data["root"] != str(root):
            raise ValueError()
        return data
    except (ValueError, KeyError, TypeError) as error:
        raise InstallError("Invalid installation owner marker") from error


def load_state(root: Path) -> dict[str, Any] | None:
    path = root / "installation.json"
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["kind"] != MAGIC or state["root"] != str(root):
            raise ValueError()
        active_path(root, state)
        return state
    except (KeyError, ValueError, TypeError) as error:
        raise InstallError("Invalid installation inventory; no files were changed") from error


def active_path(root: Path, state: dict[str, Any]) -> Path:
    relative = state["active"]
    if not isinstance(relative, str):
        raise InstallError("Invalid active release path")
    path = root / relative
    if (
        (root / "versions").is_symlink()
        or (hasattr(root / "versions", "is_junction") and (root / "versions").is_junction())
        or not isinstance(relative, str)
        or Path(relative).is_absolute()
        or len(Path(relative).parts) != 2
        or Path(relative).parts[0] != "versions"
        or path.is_symlink()
        or path.resolve().parent != (root / "versions").resolve()
    ):
        raise InstallError("Invalid active release path")
    return path


def process_identity(pid: int) -> tuple[str, float, str] | None:
    """Identify a live process, including its creation time (PID alone is not identity)."""
    if pid <= 0:
        return None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x101000, False, pid)
        if not handle:
            if ctypes.get_last_error() == 87:
                return None
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            state = kernel.WaitForSingleObject(handle, 0)
            if state == 0:
                return None
            if state != 0x102:
                raise ctypes.WinError(ctypes.get_last_error())
            code = wintypes.DWORD()
            kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            if code.value != 259:  # STILL_ACTIVE; an open handle can outlive a terminated process.
                return None
            times = [wintypes.FILETIME() for _ in range(4)]
            kernel.GetProcessTimes.argtypes = [
                wintypes.HANDLE,
                *([ctypes.POINTER(wintypes.FILETIME)] * 4),
            ]
            if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                raise ctypes.WinError(ctypes.get_last_error())
            creation = times[0].dwLowDateTime | times[0].dwHighDateTime << 32
            buffer, size = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
            kernel.QueryFullProcessImageNameW.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.LPWSTR,
                ctypes.POINTER(wintypes.DWORD),
            ]
            if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                raise ctypes.WinError(ctypes.get_last_error())
            return str(creation), creation / 10_000_000 - 11644473600, buffer.value
        finally:
            kernel.CloseHandle(handle)
    try:
        values = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        if values[0] == "Z":
            return None
        ticks = int(values[19])
        boot = next(
            line.split()[1]
            for line in Path("/proc/stat").read_text().splitlines()
            if line.startswith("btime ")
        )
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        return (
            f"{boot_id}:{ticks}",
            int(boot) + ticks / os.sysconf("SC_CLK_TCK"),
            os.readlink(f"/proc/{pid}/exe"),
        )
    except FileNotFoundError:
        return None


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return True
    try:
        return process_identity(pid) is not None
    except OSError:
        return True  # Unknown ownership is never permission to terminate a process.


def legacy_lock_active(path: Path) -> bool:
    """Read earlier PID files conservatively, but reject terminated/reused PID ownership."""
    if path.is_symlink():
        raise InstallError("Linked installation lock is not allowed")
    if os.name == "nt":
        import ctypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetTickCount64.restype = ctypes.c_ulonglong
        boot_time = time.time() - kernel.GetTickCount64() / 1000
        if path.stat().st_mtime < boot_time - 1:
            return False
    try:
        pid = int(path.read_text())
    except ValueError:
        return time.time() - path.stat().st_mtime < 2
    if pid <= 0:
        return False
    try:
        identity = process_identity(pid)
    except OSError:
        return True
    return bool(identity and identity[1] <= path.stat().st_mtime + 0.01)


@contextlib.contextmanager
def windows_exclusive(root: Path):
    """The OS releases this mutex on crash, terminal close and reboot; files are diagnostics."""
    import ctypes
    from ctypes import wintypes

    lock = lifecycle_lock_path(root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateMutexW(
        None,
        False,
        "Local\\EwP.Transcripts." + hashlib.sha256(str(lock).casefold().encode()).hexdigest(),
    )
    if not handle:
        raise InstallError("Cannot access the installation activity lock")
    acquired = False
    try:
        acquired = kernel.WaitForSingleObject(handle, 3000) in (0, 0x80)
        if not acquired:
            raise InstallError("Another installer/application is active; close it and retry")
        for previous in (lock, root / ".lifecycle.lock"):
            if previous.exists() or previous.is_symlink():
                if legacy_lock_active(previous):
                    raise InstallError(
                        "Another installer/application is active; close it and retry"
                    )
                try:
                    previous.unlink()
                except PermissionError:
                    if previous == lock:
                        raise
                emit("recovery", "Recovered an interrupted application lock; no job is resumed")
        # Keep a readable PID for diagnostics and compatibility with earlier launchers.
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(str(os.getpid()))
        try:
            yield
        finally:
            if lock.exists() and not lock.is_symlink() and lock.read_text() == str(os.getpid()):
                lock.unlink()
    finally:
        if acquired:
            kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)


def runtime_session_path(root: Path) -> Path:
    return lifecycle_lock_path(root).with_suffix(".session.json")


def runtime_record(root: Path) -> dict[str, Any] | None:
    path = runtime_session_path(root)
    if not path.exists():
        return None
    if path.is_symlink() or path.stat().st_size > 8192:
        raise InstallError("Invalid application runtime record")
    record = json.loads(path.read_text(encoding="utf-8"))
    if (
        record.get("root") != str(root)
        or not isinstance(record.get("token"), str)
        or len(record["token"]) < 32
        or not isinstance(record.get("pid"), int)
        or record.get("port") != 8765
    ):
        raise InstallError("Invalid application runtime record")
    identity = process_identity(record["pid"])
    if not identity or identity[0] != record.get("identity"):
        if record.get("desktop") is True:
            host = process_identity(record.get("desktop_pid", 0))
            if host and host[0] == record.get("desktop_identity"):
                raise InstallError("Close the EwP Transcripts desktop window before maintenance")
        path.unlink(missing_ok=True)
        return None
    return record


def runtime_request(record: dict[str, Any], action: str) -> dict[str, Any] | None:
    import http.client
    import urllib.request

    base = f"http://127.0.0.1:{record['port']}"
    request = urllib.request.Request(
        base + "/api/v1/runtime-control",
        data=b"" if action == "stop" else None,
        headers={"Origin": base, "X-EWP-Runtime-Token": record["token"]},
    )

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=2) as response:
            result = json.load(response)
        return result if result.get("pid") == record["pid"] else None
    except (OSError, ValueError, http.client.HTTPException):
        return None


def reopen_running_application(root: Path) -> bool:
    record = runtime_record(root)
    if record is None:
        return False
    if not runtime_request(record, "ping"):
        raise InstallError(
            "The running EwP application is not responding; close it or use Uninstall"
        )
    import webbrowser

    webbrowser.open(f"http://127.0.0.1:{record['port']}/")
    emit("complete", "Opened the running EwP Transcripts application")
    return True


def terminate_installed_process(root: Path, pid: int, expected: str) -> None:
    """Terminate the retained, creation-verified process object, never a recycled PID."""
    current = process_identity(pid)
    if current is None or current[0] != expected:
        return
    if not Path(current[2]).is_relative_to(root):
        raise InstallError("Cannot safely stop a process outside this installation")
    if os.name != "nt":
        os.kill(pid, signal.SIGTERM)
        return
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x100001, False, pid)
    if not handle:
        raise InstallError("Cannot stop the running application")
    try:
        current = process_identity(pid)
        if current is None:
            return
        if current[0] != expected:
            raise InstallError("Application process identity changed")
        if not kernel.TerminateProcess(handle, 1):
            raise InstallError("Cannot stop the running application")
    finally:
        kernel.CloseHandle(handle)


def stop_legacy_application(root: Path) -> None:
    """Support earlier managed launchers only after verifying their root, role and process tree."""
    if os.name != "nt":
        return
    lock = lifecycle_lock_path(root)
    if not lock.exists():
        lock = root / ".lifecycle.lock"
    if not lock.exists() or not legacy_lock_active(lock):
        return
    owner_pid = int(lock.read_text())
    owner_identity = process_identity(owner_pid)
    if not owner_identity or not Path(owner_identity[2]).is_relative_to(root):
        return  # An installer/foreign owner remains protected; the activity gate will explain it.
    script = r"""[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$pending=@([int]$env:EWP_TARGET_PID);$items=@();$seen=@{}
while($pending.Count){
 $current=$pending[0];$pending=@($pending|Select-Object -Skip 1)
 if($seen.ContainsKey($current)){continue};$seen[$current]=$true
 $entry=Get-CimInstance Win32_Process -Filter "ProcessId = $current"
 if($entry){$items+=@{pid=$entry.ProcessId;command=$entry.CommandLine}}
 $children=Get-CimInstance Win32_Process -Filter "ParentProcessId = $current"
 $pending+=@($children|ForEach-Object{$_.ProcessId})
}
ConvertTo-Json -InputObject @($items) -Compress
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        env={**os.environ, "EWP_TARGET_PID": str(owner_pid)},
        text=True,
        encoding="utf-8-sig",
        capture_output=True,
        timeout=15,
    )
    if result.returncode:
        raise InstallError("Cannot verify the running legacy application; close its console first")
    import re

    entries = json.loads(result.stdout)
    owner = next((entry for entry in entries if entry["pid"] == owner_pid), None)
    command = str((owner or {}).get("command") or "")
    if str(root / "manager.py").casefold() not in command.casefold() or not re.search(
        r'manager\.py["\s]+launch(?:\s|$)', command, re.IGNORECASE
    ):
        return  # Never stop update/repair/uninstall workers or unrelated programs.
    if process_identity(owner_pid) != owner_identity:
        return
    targets = []
    for entry in entries:
        pid = entry["pid"]
        if pid in (owner_pid, os.getpid()):
            continue
        identity = process_identity(pid)
        if identity and Path(identity[2]).is_relative_to(root):
            # The known GUI's private Python/FFmpeg descendants belong to this app.
            name = Path(identity[2]).name.casefold()
            args = str(entry.get("command") or "")
            if (
                name in {"python.exe", "pythonw.exe", "ffmpeg.exe", "ffprobe.exe"}
                and "manager.py" not in args.casefold()
            ):
                targets.append((pid, identity[0]))
    emit("shutdown", "Closing the verified older EwP Transcripts application")
    for pid, identity in reversed(targets):
        terminate_installed_process(root, pid, identity)
    terminate_installed_process(root, owner_pid, owner_identity[0])
    deadline = time.monotonic() + 5
    while process_identity(owner_pid) and time.monotonic() < deadline:
        time.sleep(0.1)


def stop_running_application(root: Path) -> None:
    record = runtime_record(root)
    if record is None:
        stop_legacy_application(root)
        return
    emit("shutdown", "Closing the running EwP Transcripts application and saving queue state")
    runtime_request(record, "stop")
    native = record.get("desktop") is True
    deadline = time.monotonic() + (90 if native else 15)
    while time.monotonic() < deadline:
        identity = process_identity(record["pid"])
        host = process_identity(record.get("desktop_pid", 0)) if native else None
        host_alive = host is not None and host[0] == record.get("desktop_identity")
        if (identity is None or identity[0] != record["identity"]) and not host_alive:
            runtime_session_path(root).unlink(missing_ok=True)
            return
        if native:
            status = runtime_request(record, "ping")
            if status and status.get("close_refused"):
                raise InstallError(
                    "The application could not save work; resolve this before removal"
                )
        time.sleep(0.1)
    if native:
        raise InstallError(
            "The desktop application is still saving or closing; retry after it exits"
        )
    terminate_installed_process(root, record["pid"], record["identity"])
    deadline = time.monotonic() + 5
    while process_alive(record["pid"]) and time.monotonic() < deadline:
        time.sleep(0.1)
    if process_alive(record["pid"]):
        raise InstallError("The application has not stopped yet")
    runtime_session_path(root).unlink(missing_ok=True)


def lifecycle_lock_path(
    root: Path, *, windows: bool | None = None, local_app_data: Path | None = None
) -> Path:
    if windows is None:
        windows = os.name == "nt"
    if not windows:
        return root / ".lifecycle.lock"
    state = local_app_data or Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    name = hashlib.sha256(str(root).casefold().encode()).hexdigest()
    lock = state / "EwPTranscriptsState" / "locks" / (name + ".lock")
    for parent in (lock.parent, *lock.parent.parents):
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise InstallError("Installer runtime state must not contain links or junctions")
    return lock


@contextlib.contextmanager
def exclusive(root: Path):
    if os.name == "nt":
        with windows_exclusive(root):
            yield
        return
    lock = lifecycle_lock_path(root)
    legacy = root / ".lifecycle.lock"
    if lock != legacy:
        # Old launchers wrote here. Read compatibility state without requiring root write access.
        if legacy.exists():
            try:
                if legacy.is_symlink() or process_alive(int(legacy.read_text())):
                    raise ValueError()
            except (ValueError, OSError) as error:
                raise InstallError(
                    "Another installer/application has an unverified active lock"
                ) from error
        lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        try:
            before = lock.lstat()
            if lock.is_symlink():
                raise ValueError()
            pid = int(lock.read_text())
            if process_alive(pid) or lock.lstat() != before:
                raise ValueError()
            lock.unlink()
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            emit("recovery", "Recovered an interrupted installer lock; no job is resumed")
        except (ValueError, OSError):
            raise InstallError(
                "Another installer/application is active or its lock cannot be verified. "
                "Close it and retry."
            ) from error
    identity = os.fstat(descriptor)
    try:
        os.write(descriptor, str(os.getpid()).encode())
        os.close(descriptor)
        yield
    finally:
        if lock.exists() and lock.lstat().st_ino == identity.st_ino:
            lock.unlink()


def run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    capture: bool = False,
    acceptable_codes: tuple[int, ...] = (0,),
) -> str:
    # Never print command arguments/environment: credentials can be present only in child stdin/env.
    check_cancelled()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=os.name != "nt",
    )
    collected: list[str] = []
    assert process.stdout is not None
    lines: queue.Queue[str | None] = queue.Queue()

    def read_lines() -> None:
        try:
            for line in process.stdout:
                lines.put(line)
        finally:
            lines.put(None)

    reader = threading.Thread(target=read_lines, daemon=True)
    reader.start()
    try:
        while True:
            check_cancelled()
            try:
                line = lines.get(timeout=0.1)
            except queue.Empty:
                continue
            if line is None:
                break
            for name in ("HF_TOKEN", "OPENROUTER_API_KEY"):
                if environment.get(name):
                    line = line.replace(environment[name], "[redacted]")
            if capture:
                collected.append(line)
            else:
                try:
                    event = json.loads(line)
                except ValueError:
                    event = None
                if isinstance(event, dict) and event.get("stage") in {
                    "download",
                    "model-item",
                    "model-complete",
                    "python",
                    "dependencies",
                    "media",
                    "verify",
                }:
                    emit(
                        event["stage"],
                        event.pop("message", "Downloading model"),
                        **{k: v for k, v in event.items() if k not in {"stage", "time"}},
                    )
                else:
                    emit("log", line.rstrip())
        code = process.wait()
    except BaseException:
        stop_child(process)
        raise
    finally:
        reader.join(timeout=2)
        process.stdout.close()
    if code not in acceptable_codes:
        raise InstallError(
            "Installation step failed; previous active version is preserved. S"
            "ee the preceding dependency diagnostic."
        )
    return "".join(collected)


def inspect_bundle(bundle: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(bundle) as archive:
            meta = json.loads(archive.read("bundle.json"))
            if meta["format"] != 1 or meta["platform"] not in ("windows-x64", "ubuntu-x64"):
                raise InstallError("Unsupported installer bundle")
            seen: set[str] = set()
            folded: set[str] = set()
            total = 0
            import re

            if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", meta["version"]):
                raise InstallError("Invalid release version")
            for item in archive.infolist():
                name = item.filename
                path = Path(name)
                if (
                    name.casefold() in folded
                    or "\\" in name
                    or path.is_absolute()
                    or name.startswith("/")
                    or ".." in path.parts
                    or ":" in name
                    or any(
                        p.endswith((".", " "))
                        or p.split(".")[0].upper()
                        in {
                            "CON",
                            "PRN",
                            "AUX",
                            "NUL",
                            *(f"COM{i}" for i in range(1, 10)),
                            *(f"LPT{i}" for i in range(1, 10)),
                        }
                        for p in path.parts
                    )
                    or (item.external_attr >> 16) & 0o170000 == 0o120000
                ):
                    raise InstallError("Unsafe or duplicate bundle path")
                seen.add(name)
                folded.add(name.casefold())
                total += item.file_size
                if total > 512 * 1024 * 1024:
                    raise InstallError("Unexpectedly large expanded bundle")
                if item.file_size > 256 * 1024 * 1024:
                    raise InstallError("Unexpectedly large bundle member")
            expected = {"bundle.json", *meta["sha256"]}
            if seen != expected:
                raise InstallError("Bundle has missing or unexpected files")
            for name, digest in meta["sha256"].items():
                if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                    raise InstallError("Bundle integrity check failed")
            return meta
    except (OSError, KeyError, ValueError, TypeError, AttributeError, zipfile.BadZipFile) as error:
        if isinstance(error, InstallError):
            raise
        raise InstallError("Cannot read a valid versioned installer bundle") from error


def check_hf_access(token: str) -> None:
    """Read-only gated-repository check. Never follow a redirect with a bearer token."""
    import urllib.error
    import urllib.request

    if not token.isascii() or any(c.isspace() for c in token) or len(token) > 512:
        raise InstallError("Enter one HF read token without whitespace")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    request = urllib.request.Request(
        "https://huggingface.co/api/models/pyannote/speaker-diarization-community-1/auth-check",
        headers={"Authorization": "Bearer " + token},
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            if response.status != 200:
                raise InstallError("HF access check failed; verify token and model terms")
    except (urllib.error.URLError, TimeoutError):
        raise InstallError(
            "HF access check failed; verify connection, token and accepted pyannote terms"
        ) from None


def windows_vc_files() -> bool:
    directory = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32"
    return all(
        (directory / name).is_file()
        for name in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll")
    )


def validate_elevated_model_targets(paths: list[str], home: Path | None = None) -> None:
    """Elevated default-model downloads may not follow user-controlled links into system files."""
    base = (home or Path.home()).resolve()
    for value in paths:
        path = Path(value).expanduser()
        if not path.resolve().is_relative_to(base):
            raise InstallError(
                "Prepare custom model caches as a normal user before elevated installation"
            )
        for parent in (path, *path.parents):
            if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
                raise InstallError(
                    "Elevated model download cannot follow directory links or junctions"
                )
        if path.exists():
            for item in path.rglob("*"):
                if (hasattr(item, "is_junction") and item.is_junction()) or (
                    item.is_symlink() and not item.resolve().is_relative_to(base)
                ):
                    raise InstallError("Elevated model download would leave the user profile")


def amd_display_adapters() -> list[dict[str, str]]:
    """Query PCI display adapters; an AMD CPU/AMD64 architecture is not an AMD GPU."""
    if platform.system() != "Windows":
        return []
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
                "@(Get-CimInstance Win32_VideoController | Where-Object { "
                "$_.PNPDeviceID -match 'VEN_1002' } | Select-Object "
                "Name,DriverVersion,PNPDeviceID) | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
            creationflags=0x08000000,
        )
        value = json.loads(result.stdout.lstrip("\ufeff")) if result.returncode == 0 else []
        rows = value if isinstance(value, list) else [value]
        return [
            {
                "name": str(row["Name"]),
                "driver": str(row.get("DriverVersion") or ""),
                "vendor": "amd",
            }
            for row in rows
            if isinstance(row, dict)
            and "VEN_1002" in str(row.get("PNPDeviceID", "")).upper()
            and isinstance(row.get("Name"), str)
        ]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def host_report(root: Path, local: bool) -> dict[str, Any]:
    system = platform.system()
    checks: list[dict[str, Any]] = []

    def check(code: str, status: str, message: str, **context: Any) -> None:
        checks.append({"code": code, "status": status, "message": message, "context": context})

    arch = platform.machine().lower() in {"amd64", "x86_64"}
    cpu = platform.processor() or platform.machine()
    if system == "Windows":
        import winreg

        with (
            contextlib.suppress(OSError, StopIteration),
            winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            ) as key,
        ):
            cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    elif system == "Linux":
        with contextlib.suppress(OSError, StopIteration):
            cpu = next(
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            )
    check(
        "architecture",
        "pass" if arch else "fail",
        cpu,
        cpu_model=cpu,
        architecture=platform.machine(),
    )
    if system == "Windows":
        import re
        import winreg

        display = ""
        build = platform.version()
        with (
            contextlib.suppress(OSError),
            winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            ) as key,
            contextlib.suppress(OSError),
        ):
            display = str(winreg.QueryValueEx(key, "DisplayVersion")[0])
        major = "11" if platform.release() == "11" else platform.release()
        label = "Windows " + major + (" " + display if display else " (" + build + ")")
        version = re.fullmatch(r"(\d{2})H([12])", display.upper())
        older = major != "11" or version is None or tuple(map(int, version.groups())) < (26, 2)
        check(
            "platform",
            "warning" if older else "pass",
            label,
            name=label,
            display_version=display,
            build=build,
            warning="older_windows" if older else "",
        )
    elif system == "Linux":
        release = platform.freedesktop_os_release()
        ok = release.get("ID") == "ubuntu" and release.get("VERSION_ID") in {"24.04", "26.04"}
        label = release.get("PRETTY_NAME", "Unknown Linux")
        check("platform", "pass" if ok else "fail", label, name=label)
    else:
        check("platform", "fail", "Only Windows and Ubuntu x64 are supported", name=system)
    existing = next(parent for parent in (root, *root.parents) if parent.exists())
    free = shutil.disk_usage(existing).free
    owner = load_owner(root)
    required = 8 * 1024**3 if owner else 25_000_000_000
    check(
        "disk",
        "pass" if free >= required else "fail",
        f"{free / 1e9:.1f} GB free; {required / 1e9:g} GB required",
        free_bytes=free,
        required_bytes=required,
        installation_bytes=20_000_000_000,
        additional_bytes=required,
        reserve_bytes=0 if owner else 5_000_000_000,
    )
    devices: list[dict[str, str]] = []
    gpu = shutil.which("nvidia-smi")
    if gpu:
        try:
            result = subprocess.run(
                [gpu, "--query-gpu=name,driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                import csv

                devices = [
                    {"name": row[0].strip(), "driver": row[1].strip()}
                    for row in csv.reader(result.stdout.splitlines())
                    if len(row) >= 2
                ]
        except (OSError, subprocess.TimeoutExpired):
            pass
    amd_devices = amd_display_adapters()
    selected_accelerator = "amd" if amd_devices and not devices else "nvidia"
    check(
        "gpu",
        "pass" if devices or amd_devices else ("fail" if local else "warning"),
        "AMD ROCm (experimental); CPU alignment/diarization"
        if selected_accelerator == "amd"
        else "NVIDIA driver visible"
        if devices
        else "No usable NVIDIA or AMD GPU driver detected",
        devices=[*devices, *amd_devices],
        amd_devices=amd_devices,
        accelerator=selected_accelerator,
    )
    if system == "Linux":
        missing = [name for name in ("ffmpeg", "ffprobe") if not shutil.which(name)]
        check(
            "media",
            "fail" if missing else "pass",
            "Missing " + ", ".join(missing) if missing else "FFmpeg/ffprobe available",
        )
    if system == "Windows":
        import winreg

        installed, version = False, ""
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
            ) as key:
                installed = winreg.QueryValueEx(key, "Installed")[0] == 1
                with contextlib.suppress(OSError):
                    version = str(winreg.QueryValueEx(key, "Version")[0])
        except OSError:
            pass
        files_ready = windows_vc_files()
        status = "fail" if not installed or not files_ready else "pass" if version else "warning"
        check(
            "vc_runtime",
            status,
            "Microsoft Visual C++ x64",
            version=version,
            required_dlls_present=files_ready,
        )
    return {"ready": all(c["status"] != "fail" for c in checks), "checks": checks}


def app_python(release: Path) -> Path:
    return release / "app/.venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def app_env(root: Path) -> dict[str, str]:
    return {
        **os.environ,
        "EWP_FFMPEG_PREFIX": str(root / "runtime/ffmpeg-7"),
        "UV_PYTHON_INSTALL_DIR": str(root / "tools/python"),
        "UV_CACHE_DIR": str(root / "cache"),
        "UV_LINK_MODE": "hardlink",
        "PYTHONUNBUFFERED": "1",
        "UV_NO_CONFIG": "1",
        "PYTHONIOENCODING": "utf-8",
        "EWP_LOCAL_ACCELERATOR": (load_state(root) or {}).get("local_accelerator", "nvidia"),
    }


def installed_size(root: Path) -> int:
    """Logical installed bytes, including reused models; never follow directory links."""
    seen: set[str] = set()
    total = 0
    paths = [root, *(Path(p) for p in (load_owner(root) or {}).get("models", []))]
    for base in paths:
        for directory, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [
                d
                for d in dirs
                if not (Path(directory) / d).is_symlink()
                and not (
                    hasattr(Path(directory) / d, "is_junction")
                    and (Path(directory) / d).is_junction()
                )
            ]
            for name in files:
                path = Path(directory) / name
                with contextlib.suppress(OSError):
                    identity = str(path.resolve())
                    if identity not in seen:
                        total += path.stat().st_size
                        seen.add(identity)
    return total


def model_catalog(source: Path) -> list[dict[str, Any]]:
    return json.loads(source.read_text(encoding="utf-8"))["models"]


def model_targets(
    root: Path, entries: list[dict[str, Any]], release: Path | None = None
) -> list[dict[str, Any]]:
    state = load_state(root)
    # Read the installed configuration to respect custom paths; missing app falls back to pins.
    targets: dict[str, str] = {}
    if state or release:
        release = release or active_path(root, state)
        program = (
            "import json;from ewp_transcripts.config import load_config;c=load_config();"
            "print(json.dumps(dict(asr=str(c.models.asr_snapshot_path),"
            "alignment_pl=str(c.models.alignment_snapshot_path),"
            "alignment_en=str(c.models.english_alignment_snapshot_path),"
            "diarization=str(c.diarization.local_model_path))))"
        )
        with contextlib.suppress(OSError, ValueError):
            result = subprocess.run(
                [str(app_python(release)), "-c", program],
                cwd=release / "app",
                env=app_env(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            value = json.loads(result.stdout)
            if isinstance(value, dict) and all(
                isinstance(k, str) and isinstance(p, str) for k, p in value.items()
            ):
                targets = value
    return [
        dict(entry, path=targets.get(entry["code"], str(Path(entry["path"]).expanduser())))
        for entry in entries
    ]


def verify_models(root: Path, catalog: Path) -> list[dict[str, Any]]:
    """Offline verification against pinned upstream SHA256/git-blob hashes, no model load."""
    results = []
    for entry in model_targets(root, model_catalog(catalog)):
        target = Path(entry["path"])
        issues = []
        for name, size in entry["files"].items():
            check_cancelled()
            path = target / name
            try:
                expected = entry["hashes"][name]
                if path.stat().st_size != size:
                    raise ValueError("size")
                digest = hashlib.sha256() if expected["algorithm"] == "sha256" else hashlib.sha1()
                if expected["algorithm"] == "git-sha1":
                    digest.update(f"blob {size}\0".encode())
                with path.open("rb") as stream:
                    while block := stream.read(4 * 1024 * 1024):
                        check_cancelled()
                        digest.update(block)
                if digest.hexdigest() != expected["digest"]:
                    raise ValueError("hash")
            except (OSError, ValueError, KeyError):
                issues.append(name)
        result = {
            "code": entry["code"],
            "repository": entry["repository"],
            "path": str(target),
            "revision": entry["revision"],
            "status": "not-installed"
            if entry.get("optional") and not target.exists()
            else "fail"
            if issues
            else "pass",
            "issues": issues,
        }
        results.append(result)
        emit("model-check", "Model integrity checked", **result)
    emit("model-verification", "Offline model verification complete", models=results)
    return results


def prepare_models(
    root: Path,
    release: Path,
    *,
    selected: list[str] | None,
    redownload: bool,
    terms: bool,
    secrets: dict[str, str],
    hf_checked: bool = False,
) -> None:
    catalog = release / "control/models.json"
    entries = model_targets(root, model_catalog(catalog), release)
    if selected is not None and set(selected) - {m["code"] for m in entries}:
        raise InstallError("Unknown model selection")
    downloads = []
    for entry in entries:
        if selected is None and entry.get("optional"):
            continue
        if selected is not None and entry["code"] not in selected:
            continue
        target = Path(entry["path"])
        complete = all(
            (target / n).is_file() and (target / n).stat().st_size == size
            for n, size in entry["files"].items()
        )
        if redownload or not complete:
            downloads.append(entry)
    owner = load_owner(root)
    assert owner is not None
    owner["models"] = sorted(
        set(
            owner.get("models", [])
            + [
                m["path"]
                for m in entries
                if not m.get("optional") or selected and m["code"] in selected
            ]
        )
    )
    atomic_json(root / "owner.json", owner)
    if not downloads:
        emit("models", "Pinned local models preserved; no download or HF token required")
        return
    gated = any(m.get("gated", m["code"] == "diarization") for m in downloads)
    if gated and (not terms or not secrets.get("hf_token")):
        raise InstallError(
            "Accept pyannote terms and provide HF token for the selected gated download"
        )
    if gated and not hf_checked:
        check_hf_access(secrets["hf_token"])
    if os.name == "nt":
        import ctypes

        if ctypes.windll.shell32.IsUserAnAdmin():
            validate_elevated_model_targets([m["path"] for m in downloads])
    command = [str(app_python(release)), "scripts/setup-models.py", "--yes", "--progress-json"]
    for entry in downloads:
        command += ["--model", entry["code"]]
    if redownload:
        command += ["--force-download"]
    emit("models", "Downloading selected models", selected=[m["code"] for m in downloads])
    run(
        command,
        cwd=release / "app",
        environment={**app_env(root), "HF_TOKEN": secrets.get("hf_token", "")},
    )


def diagnose_runtime(
    root: Path, release: Path, *, local: bool, accelerator: str | None = None
) -> None:
    """Always diagnose after maintenance; missing unselected models are a reported warning."""
    emit("verify", "Running automatic runtime and model diagnostics")
    command = [str(app_python(release)), "-m", "ewp_transcripts", "doctor", "--json-output"]
    if local:
        command.append("--test-speech-runtime")
    report = run(
        command,
        cwd=release / "app",
        environment={
            **app_env(root),
            **({"EWP_LOCAL_ACCELERATOR": accelerator} if accelerator else {}),
        },
        capture=True,
        acceptable_codes=(0, 3),
    )
    try:
        result = json.loads(report)
    except ValueError:
        # Tiny qualification fixtures do not implement the full doctor JSON contract.
        emit("diagnostic", "Automatic diagnostics completed")
        return
    emit("diagnostic", "Automatic diagnostics completed", report=result)


def changed_model_codes(root: Path, bundle: Path) -> list[str]:
    """An app update prepares only models whose pinned identity changed."""
    state = load_state(root)
    if state is None or not state.get("local_models"):
        return []
    config_path = "app/src/ewp_transcripts/resources/default-config.toml"
    old = tomllib.loads((active_path(root, state) / config_path).read_text(encoding="utf-8"))
    with zipfile.ZipFile(bundle) as archive:
        new = tomllib.loads(archive.read(config_path).decode())
    fields = {
        "asr": ("models", "asr_revision"),
        "alignment_pl": ("models", "alignment_revision"),
        "alignment_en": ("models", "english_alignment_revision"),
        "diarization": ("diarization", "model_revision"),
    }
    return [
        code
        for code, (section, name) in fields.items()
        if old.get(section, {}).get(name) != new.get(section, {}).get(name)
    ]


def registered_installations() -> list[tuple[Path, str]]:
    """Read registration before any dependency/model work, across Windows hives/views."""
    if os.name != "nt":
        desktop = Path.home() / ".local/share/applications/ewp-transcripts.desktop"
        if not desktop.exists():
            return []
        if desktop.is_symlink():
            raise InstallError("Existing desktop entry preserved; verify the original installation")
        for line in desktop.read_text(encoding="utf-8").splitlines():
            if line.startswith("X-EwP-Root="):
                return [(Path(line.removeprefix("X-EwP-Root=")), "")]
        raise InstallError("Existing desktop entry preserved; use the original install location")
    import winreg

    found = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(
                    hive,
                    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts",
                    0,
                    winreg.KEY_READ | view,
                ) as key:
                    location = winreg.QueryValueEx(key, "InstallLocation")[0]
                    with contextlib.suppress(FileNotFoundError):
                        version = str(winreg.QueryValueEx(key, "DisplayVersion")[0])
                        found.append((Path(location), version))
                        continue
                    found.append((Path(location), ""))
            except FileNotFoundError:
                continue
            except OSError as error:
                raise InstallError(
                    "Cannot verify the existing installation registration"
                ) from error
    return found


def existing_installation_message(version: str, selected: str) -> str:
    try:
        order = tuple(map(int, version.split(".")))
        target = tuple(map(int, selected.split(".")))
    except ValueError:
        return "An existing installation was detected; uninstall it before installing again"
    if order < target:
        return f"Installed version {version}; choose Update instead of Install"
    if order == target:
        return f"Version {version} is already installed; choose Repair"
    return (
        f"Installed version {version} is newer; choose Restore previous version or download "
        "a newer installer: https://github.com/Polikles/ewp-transcripts/tree/main/releases"
    )


def registration_preflight(root: Path, version: str) -> None:
    for location, registered_version in registered_installations():
        if os.path.normcase(str(location.resolve())) != os.path.normcase(str(root.resolve())):
            state = load_state(location)
            current = state["version"] if state else registered_version
            raise InstallError(f"{existing_installation_message(current, version)}: {location}")


def new_installation_preflight(root: Path, version: str) -> None:
    registration_preflight(root, version)
    state = load_state(root)
    if state:
        raise InstallError(existing_installation_message(state["version"], version))


def register(root: Path, state: dict[str, Any]) -> None:
    registration_preflight(root, state["version"])
    if os.name == "nt":
        import winreg

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts",
        ) as key:
            for name, value in {
                "DisplayName": "EwP Transcripts",
                "DisplayVersion": state["version"],
                "Publisher": "Damian Szczech",
                "InstallLocation": str(root),
                "DisplayIcon": str(root / "EwP.ico"),
                "EstimatedSize": min(0xFFFFFFFF, max(1, installed_size(root) // 1024)),
                "UninstallString": (
                    f'"{state["wizard"]}" --maintenance --root "{root}"'
                    if state.get("wizard")
                    else (
                        "powershell.exe -NoProfile -ExecutionPolicy Bypass "
                        f'-File "{root / "Install-EwP.ps1"}" '
                        f'-Action uninstall -Root "{root}"'
                    )
                ),
                "NoModify": 1,
                "NoRepair": 1,
            }.items():
                winreg.SetValueEx(
                    key,
                    name,
                    0,
                    winreg.REG_DWORD if isinstance(value, int) else winreg.REG_SZ,
                    value,
                )
        # COM handles Unicode paths without interpolating user text into a PowerShell program.
        script = (
            "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut((Join"
            "-Path ([Environment]::GetFolderPath('Desktop')) 'EwP Transcripts."
            "lnk'));$s.TargetPath=$env:EWP_LAUNCH;$s.Arguments=$env:EWP_ARGS;$s.WorkingDirectory=$env:EWP"
            "_ROOT;$s.IconLocation=$env:EWP_ICON;$s.Save()"
        )
        environment = {
            **os.environ,
            "EWP_SHORTCUT": str(Path.home() / "Desktop/EwP Transcripts.lnk"),
            "EWP_LAUNCH": str(
                native_executable(root, state)
                or (
                    Path(os.environ["SYSTEMROOT"])
                    / "System32/WindowsPowerShell/v1.0/powershell.exe"
                )
            ),
            "EWP_ARGS": ""
            if native_executable(root, state)
            else f'-NoProfile -ExecutionPolicy Bypass -File "{root / "launch.ps1"}"',
            "EWP_ROOT": str(root),
            "EWP_ICON": str(root / "EwP.ico"),
        }
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            env=environment,
            check=True,
            capture_output=True,
        )
    else:
        launcher = Path.home() / ".local/share/applications/ewp-transcripts.desktop"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        if launcher.exists() and (
            launcher.is_symlink() or f"X-EwP-Root={root}\n" not in launcher.read_text()
        ):
            raise InstallError(
                "Existing desktop entry preserved; use the original install location"
            )
        executable = str(root / "ewp").replace("%", "%%").replace('"', '\\"')
        launcher.write_text(
            (
                "[Desktop Entry]\nType=Application\nName=EwP Transcripts\n"
                f'Exec="{executable}"\nTerminal=true\nCategories=AudioVideo;\n'
                f"X-EwP-Root={root}\n"
            ),
            encoding="utf-8",
        )


def install(
    root: Path,
    bundle: Path,
    *,
    local: bool,
    terms: bool,
    secrets: dict[str, str],
    check_host: bool = True,
    model_codes: list[str] | None = None,
    redownload: bool = False,
    amd_accepted: bool = False,
) -> dict[str, Any]:
    root = safe_root(root)
    check_cancelled()
    meta = inspect_bundle(bundle)
    expected = "windows-x64" if os.name == "nt" else "ubuntu-x64"
    if meta["platform"] != expected:
        raise InstallError("Choose the bundle for this operating system")
    old = load_state(root)
    registration_preflight(root, meta["version"])
    report = host_report(root, local)
    emit("host", "Host checks completed", **report)
    gpu_context = next(
        (item.get("context", {}) for item in report["checks"] if item["code"] == "gpu"), {}
    )
    accelerator = gpu_context.get("accelerator", "nvidia")
    if old and old.get("local_accelerator") == "amd" and gpu_context.get("amd_devices"):
        accelerator = "amd"
    if accelerator == "amd" and not (amd_accepted or old and old.get("amd_acknowledged")):
        raise InstallError(
            "AMD GPU support is experimental and has not been tested. "
            "Acknowledge it with --accept-amd-experimental to continue."
        )
    if check_host and not report["ready"]:
        raise InstallError("Resolve failed host checks before installation")
    hf_checked = False
    if local and model_codes != []:
        with zipfile.ZipFile(bundle) as archive:
            entries = model_targets(root, json.loads(archive.read("control/models.json"))["models"])
        gated_missing = any(
            m.get("gated", m["code"] == "diarization")
            and (model_codes is None or m["code"] in model_codes)
            and (
                redownload
                or any(
                    not (Path(m["path"]) / n).is_file()
                    or (Path(m["path"]) / n).stat().st_size != size
                    for n, size in m["files"].items()
                )
            )
            for m in entries
        )
        if gated_missing:
            if not terms:
                raise InstallError("Confirm gated-model terms before downloading pyannote")
            if not secrets.get("hf_token"):
                raise InstallError("Provide an HF read token for the selected gated model")
            check_hf_access(secrets["hf_token"])
            hf_checked = True
    if old and tuple(map(int, meta["version"].split("."))) < tuple(
        map(int, old["version"].split("."))
    ):
        raise InstallError("Downgrade refused; use rollback to the verified previous installation")
    owner = load_owner(root)
    if root.exists() and any(root.iterdir()) and old is None and owner is None:
        raise InstallError(
            "Choose an empty directory; existing non-managed files will not be replaced"
        )
    root.mkdir(parents=True, exist_ok=True)
    with exclusive(root):
        if owner is None:
            owner = {
                "kind": MAGIC,
                "root": str(root),
                "id": uuid.uuid4().hex,
                "releases": [],
                "models": [],
            }
        release = root / "versions" / (meta["version"] + "-" + uuid.uuid4().hex[:12])
        owner["releases"].append(str(release.relative_to(root)))
        atomic_json(root / "owner.json", owner)
        release.mkdir(parents=True)
        published = False
        try:
            emit("extract", "Verifying and extracting the selected version")
            with zipfile.ZipFile(bundle) as archive:
                archive.extractall(release)
            uv = release / "tools" / ("uv.exe" if os.name == "nt" else "uv")
            if os.name != "nt":
                uv.chmod(0o700)
            env = app_env(root)
            env["EWP_LOCAL_ACCELERATOR"] = accelerator
            env.pop("UV_NO_CONFIG", None)
            env["UV_PYTHON_PREFERENCE"] = "only-managed"
            env["UV_PROJECT_ENVIRONMENT"] = str(release / "app/.venv")
            emit(
                "dependencies",
                "Installing locked application dependencies; this can take several minutes",
            )
            emit("python", "Preparing the managed Python runtime")
            run([str(uv), "python", "install", "3.12"], cwd=release, environment=env)
            emit("dependencies", "Installing locked application dependencies")
            run(
                [str(uv), "sync", "--locked", "--no-dev", "--python", "3.12"],
                cwd=release / "app",
                environment=env,
            )
            python = app_python(release)
            if os.name == "nt":
                run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(release / "app/scripts/setup-windows.ps1"),
                        "-Install",
                        "-ProgressJson",
                        *([] if local else ["-CloudOnly"]),
                    ],
                    cwd=release / "app",
                    environment={**env, "PATH": str(uv.parent) + os.pathsep + env.get("PATH", "")},
                )
            else:
                run(
                    ["bash", "scripts/repair-dependencies.sh", "--native-only"],
                    cwd=release / "app",
                    environment={**env, "PATH": str(uv.parent) + os.pathsep + env.get("PATH", "")},
                )
            if local:
                prepare_models(
                    root,
                    release,
                    selected=model_codes,
                    redownload=redownload,
                    terms=terms,
                    secrets=secrets,
                    hf_checked=hf_checked,
                )
            if local:
                emit("models", "Checking local sentence-tokenizer data")
                with tempfile.TemporaryDirectory(
                    prefix="ewp-language-", dir=root / "cache"
                ) as neutral:
                    program = (
                        "from nltk import data;"
                        "data.find('tokenizers/punkt_tab/english/');"
                        "data.find('tokenizers/punkt_tab/polish/')"
                    )
                    probe = subprocess.run(
                        [str(python), "-I", "-c", program],
                        cwd=neutral,
                        env=env,
                        capture_output=True,
                    )
                if probe.returncode:
                    run(
                        [
                            str(python),
                            "-c",
                            "import runpy;"
                            "runpy.run_path('scripts/setup-models.py')"
                            "['prepare_language_data']()",
                        ],
                        cwd=release / "app",
                        environment=env,
                    )
            emit("verify", "Checking installed version and runtime")
            actual = run(
                [str(python), "-m", "ewp_transcripts", "--version"],
                cwd=release / "app",
                environment=env,
                capture=True,
            ).strip()
            if actual != meta["version"]:
                raise InstallError("Installed version does not match the selected bundle")
            diagnose_runtime(root, release, local=local, accelerator=accelerator)
            if secrets.get("openrouter_key"):
                emit("credentials", "Saving the optional OpenRouter key in the OS store")
                # stdin, not argv/history or persistent config. Child emits sanitized failures only.
                program = (
                    "import sys;from ewp_transcripts.credentials import OSCredentialSt"
                    "ore;OSCredentialStore().perform('save',sys.stdin.read())"
                )
                result = subprocess.run(
                    [str(python), "-c", program],
                    input=secrets["openrouter_key"],
                    cwd=release / "app",
                    env=env,
                    text=True,
                    capture_output=True,
                )
                if result.returncode:
                    raise InstallError(
                        "OS credential storage is unavailable. No plaintext fallback was u"
                        "sed; retry without saving a key or enable the OS store."
                    )
            emit("register", "Registering the installed application")
            state = {
                "kind": MAGIC,
                "root": str(root),
                "active": str(release.relative_to(root)),
                "version": meta["version"],
                "previous": (
                    old["active"]
                    if old and old["version"] != meta["version"]
                    else old.get("previous")
                    if old
                    else None
                ),
                "local_models": local,
                "local_accelerator": accelerator,
                "amd_acknowledged": bool(amd_accepted or old and old.get("amd_acknowledged")),
                "updated_at": time.time(),
            }
            for name in (
                "manager.py",
                "Install-EwP.ps1",
                "Install-EwP.sh",
                "Remove-EwP.ps1",
                "models.json",
                "EwP.ico",
                "EwP.Transcripts.exe",
            ):
                if (release / "control" / name).exists():
                    atomic_copy(release / "control" / name, root / name)
            exe = release / "control/EwP-Setup.exe"
            if exe.exists():
                shutil.copyfile(exe, root / "EwP-Setup.exe")
            (root / "tools").mkdir(exist_ok=True)
            target_uv = root / "tools" / uv.name
            if not target_uv.exists():
                atomic_copy(uv, target_uv)
            if os.name != "nt":
                (root / "tools" / uv.name).chmod(0o700)
            if secrets.get("wizard_source"):
                source = Path(secrets["wizard_source"])
                if source.suffix.lower() != ".exe" or not source.is_file():
                    raise InstallError("Invalid wizard source")
                target = root / "wizards" / release.name / "EwP-Setup.exe"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                state["wizard"] = str(target)
                atomic_copy(source, root / "uninstall.exe")
            write_launchers(root)
            check_cancelled()
            register(root, state)
            atomic_json(root / "installation.json", state)
            published = True
            with contextlib.suppress(OSError, InstallError):
                prune_releases(root, owner, {state["active"], state.get("previous")})
            emit(
                "complete",
                "Installation ready; saved work and model caches were preserved",
                version=state["version"],
            )
            return state
        except BaseException:
            if not published:
                if old:
                    with contextlib.suppress(Exception):
                        register(root, old)
                # After atomic publication the new active directory must never be discarded.
                shutil.rmtree(release)
            raise


def native_executable(root: Path, state: dict[str, Any]) -> Path | None:
    executable = root / "EwP.Transcripts.exe"
    return (
        executable
        if executable.is_file()
        and (active_path(root, state) / "control/EwP.Transcripts.exe").is_file()
        else None
    )


def write_launchers(root: Path) -> None:
    if os.name == "nt":
        (root / "EwP.cmd").write_text('@echo off\n"%~dp0tools-launch.cmd"\n')
        # PowerShell reads the atomic pointer, never executes it as code.
        script = r"""param([switch]$Browser)
$ErrorActionPreference='Stop'
try{$Host.UI.RawUI.WindowTitle='EwP Transcripts'}catch{}
$r=$PSScriptRoot
$s=Get-Content -Encoding UTF8 -LiteralPath (Join-Path $r 'installation.json') -Raw|ConvertFrom-Json
if($s.kind -ne 'ewp-transcripts-managed-v1' -or
   $s.active -notmatch '^versions[\\/][a-zA-Z0-9.\\-]+$' -or $s.root -ne $r){
 throw 'Invalid installation inventory'
}
if(-not $Browser -and
   (Test-Path -LiteralPath (Join-Path $r ($s.active+'\control\EwP.Transcripts.exe'))) -and
   (Test-Path -LiteralPath (Join-Path $r 'EwP.Transcripts.exe'))){
 Start-Process -FilePath (Join-Path $r 'EwP.Transcripts.exe')
 exit 0
}
$python=Join-Path $r ($s.active+'\app\.venv\Scripts\python.exe')
& $python (Join-Path $r 'manager.py') launch --root $r
exit $LASTEXITCODE
"""
        (root / "launch.ps1").write_text(script, encoding="utf-8")
        (root / "tools-launch.cmd").write_text(
            '@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch.ps1"\n'
        )
    else:
        import shlex

        quoted = shlex.quote(str(root))
        script = (
            "#!/bin/sh\nexport UV_PYTHON_INSTALL_DIR="
            + shlex.quote(str(root / "tools/python"))
            + "\nexport UV_CACHE_DIR="
            + shlex.quote(str(root / "cache"))
            + "\nexec "
            + shlex.quote(str(root / "tools/uv"))
            + " run --no-project --python 3.12 python "
            + shlex.quote(str(root / "manager.py"))
            + " launch --root "
            + quoted
            + "\n"
        )
        (root / "ewp").write_text(script)
        (root / "ewp").chmod(0o700)


def gui_state_directory(root: Path) -> Path:
    """Keep recovery beside writable installs, in per-user state for protected folders."""
    directory = root / "work-state"
    try:
        if os.name == "nt" and any(
            Path(os.environ[name]) in root.parents
            for name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "SYSTEMROOT")
            if os.environ.get(name)
        ):
            raise PermissionError("Protected installation uses per-user state")
        if directory.is_symlink() or (
            hasattr(directory, "is_junction") and directory.is_junction()
        ):
            raise InstallError("Work-state directory must not be linked")
        directory.mkdir(exist_ok=True)
        with tempfile.TemporaryFile(dir=directory):
            pass
    except PermissionError:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/state"))
        identity = hashlib.sha256(str(root).encode()).hexdigest()[:24]
        directory = base / "ewp-transcripts/installations" / identity / "work-state"
        directory.mkdir(parents=True, exist_ok=True)
    # Keep directory recall from pre-managed-state versions, without copying secrets or media.
    previous = (
        Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
        / "ewp-transcripts"
    )
    for name in ("workspace-locations.json", "project-catalog.json"):
        source, target = previous / name, directory / name
        if source.is_file() and not source.is_symlink() and not target.exists():
            atomic_copy(source, target)
    return directory


def default_output_directory(root: Path) -> Path:
    directory = root / "outputs"
    try:
        if os.name == "nt" and any(
            Path(os.environ[name]) in root.parents
            for name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "SYSTEMROOT")
            if os.environ.get(name)
        ):
            raise PermissionError("Protected installation uses per-user outputs")
        if directory.is_symlink() or (
            hasattr(directory, "is_junction") and directory.is_junction()
        ):
            raise InstallError("Output directory must not be linked")
        directory.mkdir(exist_ok=True)
        with tempfile.TemporaryFile(dir=directory):
            pass
    except PermissionError:
        directory = gui_state_directory(root).parent / "outputs"
        directory.mkdir(exist_ok=True)
    return directory


def launch(root: Path, *, native: bool = False) -> None:
    if os.name == "nt":
        import ctypes

        kernel = ctypes.WinDLL("kernel32")
        kernel.SetConsoleTitleW.argtypes = [ctypes.c_wchar_p]
        kernel.SetConsoleTitleW("EwP Transcripts")
    state = load_state(root)
    if state is None:
        raise InstallError("No managed installation found")
    if native and runtime_record(root) is not None:
        raise InstallError(
            "An application session is already running; close it before desktop launch"
        )
    if not native and reopen_running_application(root):
        return
    with exclusive(root):
        release = active_path(root, state)
        environment = app_env(root)
        environment["EWP_GUI_STATE_DIR"] = str(gui_state_directory(root))
        environment["EWP_GUI_DEFAULT_OUTPUT_DIR"] = str(default_output_directory(root))
        token = (
            os.environ.get("EWP_NATIVE_TOKEN", "")
            if native
            else uuid.uuid4().hex + uuid.uuid4().hex
        )
        if len(token) < 32:
            raise InstallError("Invalid desktop management handshake")
        environment["EWP_DESKTOP_MODE"] = "1" if native else "0"
        environment["EWP_RUNTIME_TOKEN"] = token
        record_path = runtime_session_path(root)
        environment["EWP_RUNTIME_RECORD"] = str(record_path)
        environment["EWP_RUNTIME_ROOT"] = str(root)
        process = subprocess.Popen(
            [
                str(app_python(release)),
                "-m",
                "ewp_transcripts",
                "gui",
                *(["--no-open-browser"] if native else []),
            ],
            cwd=release / "app",
            env=environment,
            creationflags=subprocess.CREATE_NO_WINDOW if native and os.name == "nt" else 0,
        )
        try:
            code = process.wait()
        except KeyboardInterrupt:
            # The console signal is also delivered to the GUI process. Let it close workers.
            previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                code = process.wait()
            finally:
                signal.signal(signal.SIGINT, previous)
            emit("complete", "Application closed")
            return
        finally:
            with contextlib.suppress(FileNotFoundError):
                if json.loads(record_path.read_text()).get("token") == token:
                    record_path.unlink()
        if code:
            raise InstallError("Application exited with an error")


def removal_preview(root: Path) -> dict[str, Any]:
    state = load_state(root)
    owner = load_owner(root)
    if state is None and owner is None:
        raise InstallError("No managed installation found; original checkout is not modified")
    allowed = [
        "owner.json",
        "tools",
        "runtime",
        "cache",
        "installation.json",
        "manager.py",
        "Install-EwP.ps1",
        "Install-EwP.sh",
        "Remove-EwP.ps1",
        "EwP-Setup.exe",
        "EwP.Transcripts.exe",
        "wizards",
        "EwP.cmd",
        "tools-launch.cmd",
        "launch.ps1",
        "models.json",
        "EwP.ico",
        "uninstall.exe",
        "ewp",
    ]
    paths = [str(root / p) for p in allowed if (root / p).exists()]
    unknown = [
        p.name for p in root.iterdir() if p.name not in {*allowed, "versions", ".lifecycle.lock"}
    ]
    known_releases = (owner or {}).get("releases", [state["active"]] if state else [])
    for value in known_releases:
        release = active_path(root, {"active": value})
        if not release.exists():
            continue
        selected, preserved = owned_release_paths(release)
        paths.extend(str(p) for p in selected)
        unknown.extend(str(p.relative_to(root)) for p in preserved)
    if (root / "versions").exists():
        known = {str((root / p).absolute()) for p in known_releases}
        unknown.extend(
            str(p.relative_to(root))
            for p in (root / "versions").iterdir()
            if str(p.absolute()) not in known
        )
    paths.sort(key=lambda p: Path(p).name == "owner.json")
    models = (owner or {}).get("models", [])
    return {
        "paths": paths,
        "preserved_unknown": unknown,
        "models": models,
        "version": state["version"] if state else "incomplete",
    }


def uninstall(
    root: Path,
    *,
    confirmed: bool,
    remove_models: bool = False,
    remove_key: bool = False,
    wizard_pid: int = 0,
    wizard_source: str = "",
) -> dict[str, Any]:
    root = safe_root(root)
    preview = removal_preview(root)
    emit("preview", "Removal preview; user media/publications are never selected", **preview)
    if not confirmed:
        return preview
    state = load_state(root)
    release = active_path(root, state) if state else None
    stop_running_application(root)
    with exclusive(root):
        if remove_key and release is None:
            raise InstallError(
                "Finish installation or remove the OS key through the existing application"
            )
        python = app_python(release) if release else None
        if remove_key:
            code = (
                "from ewp_transcripts.credentials import OSCredentialStore;OSCrede"
                "ntialStore().perform('remove')"
            )
            run([str(python), "-c", code], cwd=release / "app", environment=app_env(root))
        if remove_models:
            remove_exact_models(root)
        if os.name != "nt":
            desktop = Path.home() / ".local/share/applications/ewp-transcripts.desktop"
            if (
                desktop.is_file()
                and not desktop.is_symlink()
                and f"X-EwP-Root={root}\n" in desktop.read_text()
            ):
                desktop.unlink()
        if os.name == "nt":
            defer_windows_removal(root, preview["paths"], wizard_pid, wizard_source)
            return preview
        for value in preview["paths"]:
            path = Path(value)
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                raise InstallError("Refusing removal through a changed link")
            if path.is_dir():
                shutil.rmtree(path)
            else:
                try:
                    path.unlink(missing_ok=True)
                except PermissionError:
                    # A running Windows wizard cannot unlink its own EXE; retain only this file.
                    if path.name != "EwP-Setup.exe":
                        raise
        emit(
            "complete", "Application removed; original recordings, outputs and user state preserved"
        )
    return preview


def prune_releases(root: Path, owner: dict[str, Any], protected: set[str | None]) -> None:
    # Retain one functioning runtime for each installed version. Same-version repair
    # candidates must never evict the last genuine older version.
    retained_versions: set[str] = set()
    for value in reversed(owner["releases"]):
        release = active_path(root, {"active": value})
        try:
            version = json.loads((release / "bundle.json").read_text(encoding="utf-8"))["version"]
            if app_python(release).is_file() and version not in retained_versions:
                protected.add(value)
                retained_versions.add(version)
        except (OSError, ValueError, KeyError):
            pass
    for value in owner["releases"]:
        if value in protected:
            continue
        release = active_path(root, {"active": value})
        if not release.exists():
            continue
        selected, unknown = owned_release_paths(release)
        for path in selected:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
        emit(
            "cleanup",
            "Removed obsolete application files; added user files preserved",
            preserved=len(unknown),
        )


def owned_release_paths(release: Path) -> tuple[list[Path], list[Path]]:
    """Preserve added project files even if a user put them inside application source."""
    try:
        meta = json.loads((release / "bundle.json").read_text(encoding="utf-8"))
        known = set(meta["sha256"]) | {"bundle.json"}
    except (OSError, ValueError, KeyError):
        return [], [release]
    selected: list[Path] = []
    unknown: list[Path] = []
    for directory, dirs, files in os.walk(release, followlinks=False):
        parent = Path(directory)
        venv = parent / ".venv"
        if parent == release / "app" and ".venv" in dirs:
            selected.append(venv)
            dirs.remove(".venv")
        for name in list(dirs):
            if (parent / name).is_symlink():
                unknown.append(parent / name)
                dirs.remove(name)
        for name in files:
            path = parent / name
            relative = path.relative_to(release).as_posix()
            generated = "__pycache__" in path.parts and path.suffix == ".pyc"
            if (relative in known or generated) and path.resolve().is_relative_to(
                release.resolve()
            ):
                selected.append(path)
            else:
                unknown.append(path)
    return ([release] if not unknown else selected), unknown


def remove_exact_models(root: Path) -> None:
    paths = (load_owner(root) or {}).get("models", [])
    cache = (Path.home() / ".cache/huggingface/hub").resolve()
    # Validate every selected path before deleting any model.
    for value in paths:
        path = Path(value).expanduser()
        if (
            any(
                p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
                for p in (path, *path.parents)
            )
            or path.resolve().parent.parent.parent != cache
            or path.parent.name != "snapshots"
        ):
            raise InstallError("Custom model snapshot preserved; remove it separately")
    for value in paths:
        path = Path(value).expanduser()
        if not path.exists():
            continue
        repo = path.parent.parent
        blobs = {
            p.resolve()
            for p in path.rglob("*")
            if p.is_symlink() and p.resolve().parent == repo / "blobs"
        }
        shutil.rmtree(path)
        remaining = {p.resolve() for p in (repo / "snapshots").rglob("*") if p.is_symlink()}
        for blob in blobs - remaining:
            if blob.is_file() and blob.parent == repo / "blobs":
                blob.unlink()
        emit(
            "models",
            "Removed selected snapshot; blobs used by other snapshots remain protected",
            path=str(path),
        )


def removal_worker_directory() -> Path:
    """Elevated deferred code must never execute from user-writable temporary files."""
    import ctypes
    from ctypes import wintypes

    if not ctypes.windll.shell32.IsUserAnAdmin():
        return Path(tempfile.mkdtemp(prefix="ewp-uninstall-"))
    target = Path(os.environ["COMMONPROGRAMFILES"]) / ("EwP-remove-" + uuid.uuid4().hex)
    descriptor = wintypes.LPVOID()
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)

    class Attributes(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.DWORD),
            ("descriptor", wintypes.LPVOID),
            ("inherit", wintypes.BOOL),
        ]

    convert = security.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        wintypes.LPVOID,
    ]
    if not convert("D:P(A;OICI;FA;;;BA)(A;OICI;FA;;;SY)", 1, ctypes.byref(descriptor), None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = Attributes(ctypes.sizeof(Attributes), descriptor, False)
        kernel.CreateDirectoryW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(Attributes)]
        if not kernel.CreateDirectoryW(str(target), ctypes.byref(attributes)):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.LocalFree.argtypes = [wintypes.LPVOID]
        kernel.LocalFree(descriptor)
    return target


def defer_windows_removal(
    root: Path, paths: list[str], wizard_pid: int, wizard_source: str = ""
) -> None:
    temporary = removal_worker_directory()
    plan = temporary / "plan.json"
    deferred = []
    if wizard_pid > 0 and wizard_source:
        source = Path(wizard_source).resolve()
        state = load_state(root) or {}
        approved = {root / "uninstall.exe", Path(state.get("wizard", root / "uninstall.exe"))}
        if source in approved and root in source.parents:
            deferred.append(str(source))
    atomic_json(
        plan,
        {
            "root": str(root),
            "paths": paths,
            "pids": [os.getpid()],
            "wizard_pid": wizard_pid,
            "deferred_paths": deferred,
            "owner_id": (load_owner(root) or {}).get("id", ""),
        },
    )
    script = temporary / "remove.ps1"
    shutil.copyfile(Path(__file__).with_name("Remove-EwP.ps1"), script)
    emit(
        "removal",
        "Removing program files before installer completion",
        report_directory=str(temporary),
        result_path=str(temporary / "result.json"),
    )
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Plan",
            str(plan),
        ],
        creationflags=0x08000200,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def rollback_candidates(root: Path) -> list[dict[str, str]]:
    state, owner = load_state(root), load_owner(root)
    if not state or not owner:
        return []
    current = tuple(int(p) for p in state["version"].split("."))
    found = []
    for value in owner["releases"]:
        release = active_path(root, {"active": value})
        try:
            version = json.loads((release / "bundle.json").read_text(encoding="utf-8"))["version"]
            if (
                tuple(int(p) for p in version.split(".")) < current
                and app_python(release).is_file()
                and value != state["active"]
            ):
                found.append({"release": value, "version": version})
        except (OSError, ValueError, KeyError):
            continue
    return sorted(found, key=lambda m: tuple(int(p) for p in m["version"].split(".")), reverse=True)


def rollback(root: Path, target: str | None = None) -> dict[str, Any]:
    with exclusive(root):
        state = load_state(root)
        candidates = rollback_candidates(root)
        candidate = next((c for c in candidates if target is None or c["release"] == target), None)
        if state is None or candidate is None:
            raise InstallError("No previous verified installation available")
        previous = {**state, "active": candidate["release"], "previous": state["active"]}
        release = active_path(root, previous)
        version = run(
            [str(app_python(release)), "-m", "ewp_transcripts", "--version"],
            cwd=release / "app",
            environment=app_env(root),
            capture=True,
        ).strip()
        if version != candidate["version"]:
            raise InstallError("Previous runtime version does not match its inventory")
        previous["version"] = version
        register(root, previous)
        atomic_json(root / "installation.json", previous)
        emit(
            "complete",
            "Previous application restored; user data was not migrated or changed",
            version=version,
        )
        return previous


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "check",
            "verify-models",
            "models",
            "install",
            "update",
            "repair",
            "rollback",
            "launch",
            "uninstall",
        ),
    )
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--cloud-only", action="store_true")
    parser.add_argument("--accept-model-terms", action="store_true")
    parser.add_argument("--accept-amd-experimental", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--remove-models", action="store_true")
    parser.add_argument("--remove-key", action="store_true")
    parser.add_argument("--secrets-stdin", action="store_true")
    parser.add_argument("--native-session", action="store_true")
    parser.add_argument("--cancel-file", type=Path)
    parser.add_argument("--save-openrouter-key", action="store_true")
    parser.add_argument("--model", action="append")
    parser.add_argument("--redownload", action="store_true")
    parser.add_argument("--target-release")
    args = parser.parse_args(argv)
    secrets: dict[str, Any] = {}
    try:
        CANCEL_FILE.set(args.cancel_file)
        check_cancelled()
        root = safe_root(args.root)
        secrets: dict[str, str] = (
            json.loads(sys.stdin.readline().lstrip("\ufeff")) if args.secrets_stdin else {}
        )
        if not isinstance(secrets, dict) or any(
            not isinstance(secrets.get(k, ""), str) or len(secrets.get(k, "")) > 4096
            for k in ("hf_token", "openrouter_key", "wizard_source")
        ):
            raise InstallError("Invalid credential input")
        if args.action == "check":
            report = host_report(root, args.local)
            emit("host", "Host checks completed", **report)
            return 0 if report["ready"] else 3
        if args.action == "verify-models":
            verify_models(root, Path(__file__).with_name("models.json"))
        elif args.action == "models":
            state = load_state(root)
            if state is None:
                raise InstallError("No managed installation found")
            with exclusive(root):
                release = active_path(root, state)
                prepare_models(
                    root,
                    release,
                    selected=args.model,
                    redownload=args.redownload,
                    terms=args.accept_model_terms,
                    secrets=secrets,
                )
                diagnose_runtime(root, release, local=True)
                state["local_models"] = True
                atomic_json(root / "installation.json", state)
                emit("register", "Updating the installed model inventory")
                register(root, state)
                emit("complete", "Selected local models prepared; application files unchanged")
        elif args.action == "rollback":
            rollback(root, args.target_release)
        elif args.action == "launch":
            if args.native_session:
                launch(root, native=True)
            else:
                launch(root)
        elif args.action == "uninstall":
            uninstall(
                root,
                confirmed=args.yes,
                remove_models=args.remove_models,
                remove_key=args.remove_key,
                wizard_pid=int(secrets.get("wizard_pid", "0")),
                wizard_source=secrets.get("wizard_source", ""),
            )
        else:
            if args.bundle is None:
                raise InstallError("Select a versioned bundle with --bundle")
            selected_version = inspect_bundle(args.bundle)["version"]
            if args.action == "install":
                new_installation_preflight(root, selected_version)
            else:
                registration_preflight(root, selected_version)
            local_requested = args.local
            existing = load_state(root)
            if args.action == "update" and existing:
                with zipfile.ZipFile(args.bundle) as selected_bundle:
                    requested_version = json.loads(selected_bundle.read("bundle.json"))["version"]
                if requested_version == existing["version"]:
                    raise InstallError("This version is already installed; choose Repair if needed")
            if (
                args.action in {"update", "repair"}
                and existing
                and not args.local
                and not args.cloud_only
            ):
                args.local = existing.get("local_models", False)
            if args.action in {"update", "repair"} and existing is None:
                raise InstallError("No managed installation found")
            if (
                args.action == "repair"
                and existing
                and inspect_bundle(args.bundle)["version"] != existing["version"]
            ):
                raise InstallError("Repair requires a matching bundle; choose update explicitly")
            if not args.yes and input("Install this versioned bundle? [y/N] ").lower() != "y":
                raise InstallError("Cancelled")
            if (
                args.local
                and (local_requested or existing is None)
                and not secrets.get("hf_token")
                and not args.secrets_stdin
            ):
                secrets["hf_token"] = getpass.getpass(
                    "HF read token (blank reuses complete local models; accept terms first): "
                )
            if args.save_openrouter_key and not args.secrets_stdin:
                secrets["openrouter_key"] = getpass.getpass(
                    "Optional OpenRouter key to save in the OS store: "
                )
            install(
                root,
                args.bundle,
                local=args.local,
                terms=args.accept_model_terms,
                secrets=secrets,
                model_codes=(
                    []
                    if args.action == "repair"
                    else changed_model_codes(root, args.bundle)
                    if args.action == "update"
                    else args.model
                ),
                redownload=args.redownload,
                amd_accepted=args.accept_amd_experimental,
            )
        return 0
    except (InstallError, OSError, ValueError) as error:
        message = str(error)
        for name in ("hf_token", "openrouter_key"):
            if (
                isinstance(secrets, dict)
                and isinstance(secrets.get(name), str)
                and secrets.get(name)
            ):
                message = message.replace(secrets[name], "[redacted]")
        emit("error", message)
        return 2
    except KeyboardInterrupt:
        emit("complete", "Operation interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
