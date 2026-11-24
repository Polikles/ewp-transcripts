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


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return True
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() != 87
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


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
    command: list[str], *, cwd: Path, environment: dict[str, str], capture: bool = False
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
    if code:
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
    check(
        "gpu",
        "pass" if devices else ("fail" if local else "warning"),
        "NVIDIA driver visible" if devices else "No usable NVIDIA driver detected",
        devices=devices,
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
    targets: list[str] = []
    if state or release:
        release = release or active_path(root, state)
        program = (
            "import json;from ewp_transcripts.config import load_config;c=load_config();"
            "print(json.dumps([str(c.models.asr_snapshot_path),str(c.models.alignment_snapshot_path),"
            "str(c.models.english_alignment_snapshot_path),str(c.diarization.local_model_path)]))"
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
            if (
                isinstance(value, list)
                and len(value) == len(entries)
                and all(isinstance(p, str) for p in value)
            ):
                targets = value
    return [
        dict(entry, path=targets[i] if targets else str(Path(entry["path"]).expanduser()))
        for i, entry in enumerate(entries)
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
            "status": "fail" if issues else "pass",
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
    owner["models"] = sorted(set(owner.get("models", []) + [m["path"] for m in entries]))
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


def register(root: Path, state: dict[str, Any]) -> None:
    if os.name == "nt":
        import winreg

        registry_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts"
        with (
            contextlib.suppress(FileNotFoundError),
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as existing,
        ):
            if winreg.QueryValueEx(existing, "InstallLocation")[0] != str(root):
                raise InstallError("Use the existing installation location, or uninstall it first")
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
                Path(os.environ["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            ),
            "EWP_ARGS": f'-NoProfile -ExecutionPolicy Bypass -File "{root / "launch.ps1"}"',
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
) -> dict[str, Any]:
    root = safe_root(root)
    check_cancelled()
    meta = inspect_bundle(bundle)
    expected = "windows-x64" if os.name == "nt" else "ubuntu-x64"
    if meta["platform"] != expected:
        raise InstallError("Choose the bundle for this operating system")
    old = load_state(root)
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
    report = host_report(root, local)
    emit("host", "Host checks completed", **report)
    if check_host and not report["ready"]:
        raise InstallError("Resolve failed host checks before installation")
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
            env.pop("UV_NO_CONFIG", None)
            env["UV_PYTHON_PREFERENCE"] = "only-managed"
            env["UV_PROJECT_ENVIRONMENT"] = str(release / "app/.venv")
            emit(
                "dependencies",
                "Installing locked application dependencies; this can take several minutes",
            )
            run([str(uv), "python", "install", "3.12"], cwd=release, environment=env)
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
            report_text = (
                run(
                    [
                        str(python),
                        "-m",
                        "ewp_transcripts",
                        "doctor",
                        "--test-speech-runtime",
                        "--json-output",
                    ],
                    cwd=release / "app",
                    environment=env,
                    capture=True,
                )
                if local and model_codes != []
                else run(
                    [str(python), "-m", "ewp_transcripts", "--help"],
                    cwd=release / "app",
                    environment=env,
                    capture=True,
                )
            )
            del report_text
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
            state = {
                "kind": MAGIC,
                "root": str(root),
                "active": str(release.relative_to(root)),
                "version": meta["version"],
                "previous": old["active"] if old else None,
                "local_models": local,
                "updated_at": time.time(),
            }
            for name in (
                "manager.py",
                "Install-EwP.ps1",
                "Install-EwP.sh",
                "Remove-EwP.ps1",
                "models.json",
                "EwP.ico",
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


def write_launchers(root: Path) -> None:
    if os.name == "nt":
        (root / "EwP.cmd").write_text('@echo off\n"%~dp0tools-launch.cmd"\n')
        # PowerShell reads the atomic pointer, never executes it as code.
        script = r"""$ErrorActionPreference='Stop'
$r=$PSScriptRoot
$s=Get-Content -Encoding UTF8 -LiteralPath (Join-Path $r 'installation.json') -Raw|ConvertFrom-Json
if($s.kind -ne 'ewp-transcripts-managed-v1' -or
   $s.active -notmatch '^versions[\\/][a-zA-Z0-9.\\-]+$' -or $s.root -ne $r){
 throw 'Invalid installation inventory'
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


def launch(root: Path) -> None:
    state = load_state(root)
    if state is None:
        raise InstallError("No managed installation found")
    with exclusive(root):
        release = active_path(root, state)
        environment = app_env(root)
        environment["EWP_GUI_STATE_DIR"] = str(gui_state_directory(root))
        process = subprocess.Popen(
            [str(app_python(release)), "-m", "ewp_transcripts", "gui"],
            cwd=release / "app",
            env=environment,
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
) -> dict[str, Any]:
    root = safe_root(root)
    preview = removal_preview(root)
    emit("preview", "Removal preview; user media/publications are never selected", **preview)
    if not confirmed:
        return preview
    state = load_state(root)
    release = active_path(root, state) if state else None
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
            defer_windows_removal(root, preview["paths"], wizard_pid)
            emit("complete", "Close the installer to finish removal; user work is preserved")
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


def defer_windows_removal(root: Path, paths: list[str], wizard_pid: int) -> None:
    temporary = removal_worker_directory()
    plan = temporary / "plan.json"
    atomic_json(
        plan,
        {
            "root": str(root),
            "paths": paths,
            "pids": [os.getpid(), os.getppid(), *([wizard_pid] if wizard_pid > 0 else [])],
            "owner_id": (load_owner(root) or {}).get("id", ""),
        },
    )
    script = temporary / "remove.ps1"
    shutil.copyfile(Path(__file__).with_name("Remove-EwP.ps1"), script)
    emit("removal", "Removal will finish after installer closure", report_directory=str(temporary))
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


def rollback(root: Path) -> dict[str, Any]:
    state = load_state(root)
    if state is None or not state.get("previous"):
        raise InstallError("No previous verified installation available")
    with exclusive(root):
        previous = {**state, "active": state["previous"], "previous": state["active"]}
        release = active_path(root, previous)
        if not app_python(release).is_file():
            raise InstallError("Previous installation is unavailable")
        version = run(
            [str(app_python(release)), "-m", "ewp_transcripts", "--version"],
            cwd=release / "app",
            environment=app_env(root),
            capture=True,
        ).strip()
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
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--remove-models", action="store_true")
    parser.add_argument("--remove-key", action="store_true")
    parser.add_argument("--secrets-stdin", action="store_true")
    parser.add_argument("--cancel-file", type=Path)
    parser.add_argument("--save-openrouter-key", action="store_true")
    parser.add_argument("--model", action="append")
    parser.add_argument("--redownload", action="store_true")
    args = parser.parse_args(argv)
    secrets: dict[str, Any] = {}
    try:
        CANCEL_FILE.set(args.cancel_file)
        check_cancelled()
        root = safe_root(args.root)
        secrets: dict[str, str] = json.loads(sys.stdin.readline()) if args.secrets_stdin else {}
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
                state["local_models"] = True
                atomic_json(root / "installation.json", state)
                register(root, state)
                emit("complete", "Selected local models prepared; application files unchanged")
        elif args.action == "rollback":
            rollback(root)
        elif args.action == "launch":
            launch(root)
        elif args.action == "uninstall":
            uninstall(
                root,
                confirmed=args.yes,
                remove_models=args.remove_models,
                remove_key=args.remove_key,
                wizard_pid=int(secrets.get("wizard_pid", "0")),
            )
        else:
            if args.bundle is None:
                raise InstallError("Select a versioned bundle with --bundle")
            local_requested = args.local
            existing = load_state(root)
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
