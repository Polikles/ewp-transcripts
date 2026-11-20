"""Strict allocation and cleanup of isolated per-job work directories."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from collections.abc import Iterable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

from ewp_transcripts.domain import WorkDirectory
from ewp_transcripts.domain.errors import UnsafeWorkDirectoryError

MARKER_FILENAME = ".ewp-transcripts-work.json"


def find_work_directories(
    work_root: Path,
    *,
    older_than_days: int = 0,
    now: datetime | None = None,
) -> tuple[WorkDirectory, ...]:
    """Find only structurally valid, owner-marked workspaces below one root."""

    if older_than_days < 0:
        raise ValueError("older_than_days must not be negative")
    if not work_root.exists():
        return ()
    if work_root.is_symlink() or not work_root.is_dir():
        raise UnsafeWorkDirectoryError("Work root must be a regular directory")
    cutoff = (now or datetime.now(UTC)) - timedelta(days=older_than_days)
    candidates: list[WorkDirectory] = []
    try:
        run_directories = sorted(work_root.iterdir(), key=lambda path: path.name)
    except OSError as error:
        raise UnsafeWorkDirectoryError("Cannot inspect work root") from error
    for run_directory in run_directories:
        if run_directory.is_symlink() or not run_directory.is_dir():
            continue
        try:
            run_id = UUID(run_directory.name)
            job_directories = sorted(run_directory.iterdir(), key=lambda path: path.name)
        except (ValueError, OSError):
            continue
        for path in job_directories:
            marker_path = path / MARKER_FILENAME
            if path.is_symlink() or not path.is_dir() or marker_path.is_symlink():
                continue
            workspace = WorkDirectory(
                work_root=work_root,
                run_id=run_id,
                job_id=path.name,
                path=path,
                marker_path=marker_path,
            )
            try:
                marker = work_directory_metadata(workspace)
                marker_time = (
                    datetime.fromisoformat(marker["created_at"])
                    if marker["marker_version"] == "2.0"
                    else datetime.fromtimestamp(marker_path.stat().st_mtime, UTC)
                )
            except (OSError, UnsafeWorkDirectoryError):
                continue
            if marker_time <= cutoff:
                candidates.append(workspace)
    return tuple(candidates)


def _safe_component(value: str, *, label: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value or "\x00" in value:
        raise UnsafeWorkDirectoryError(f"Unsafe {label} for work directory: {value!r}")
    return value


def allocate_work_directory(
    work_root: Path,
    *,
    run_id: UUID,
    job_id: str,
) -> WorkDirectory:
    """Create a new owner-marked work directory without reusing an existing path."""

    if work_root.is_symlink():
        raise UnsafeWorkDirectoryError(f"Work root must not be a symbolic link: {work_root}")
    safe_job_id = _safe_component(job_id, label="job ID")
    run_component = str(run_id)
    run_directory = work_root / run_component
    if run_directory.is_symlink():
        raise UnsafeWorkDirectoryError(
            f"Run directory must not be a symbolic link: {run_directory}"
        )
    path = run_directory / safe_job_id
    marker_path = path / MARKER_FILENAME
    try:
        work_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        run_directory.mkdir(exist_ok=True, mode=0o700)
        path.mkdir(mode=0o700)
        marker = {
            "marker_version": "2.0",
            "run_id": run_component,
            "job_id": safe_job_id,
            "created_at": datetime.now(UTC).isoformat(),
            "owner_pid": os.getpid(),
            "retention_reason": "active",
        }
        descriptor = os.open(
            marker_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            payload = (json.dumps(marker) + "\n").encode("utf-8")
            remaining = memoryview(payload)
            while remaining:
                remaining = remaining[os.write(descriptor, remaining) :]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except FileExistsError as error:
        raise UnsafeWorkDirectoryError(f"Work directory already exists: {path}") from error
    except OSError as error:
        raise UnsafeWorkDirectoryError(f"Cannot allocate work directory: {path}") from error
    return WorkDirectory(
        work_root=work_root,
        run_id=run_id,
        job_id=safe_job_id,
        path=path,
        marker_path=marker_path,
    )


def cleanup_work_directory(workspace: WorkDirectory) -> None:
    """Delete exactly one verified owned workspace, never its root or siblings."""

    _validate_work_directory(workspace)
    try:
        shutil.rmtree(workspace.path)
    except OSError as error:
        raise UnsafeWorkDirectoryError(f"Cannot clean work directory: {workspace.path}") from error
    # A shared run directory remains while it contains another job workspace.
    with suppress(OSError):
        workspace.path.parent.rmdir()


def work_directory_metadata(workspace: WorkDirectory) -> dict[str, Any]:
    """Verify path structure and marker ownership without changing the workspace."""

    expected_path = workspace.work_root / str(workspace.run_id) / workspace.job_id
    if workspace.path != expected_path or workspace.marker_path != expected_path / MARKER_FILENAME:
        raise UnsafeWorkDirectoryError("Work directory paths do not match ownership metadata")
    if (
        workspace.work_root.is_symlink()
        or workspace.path.parent.is_symlink()
        or workspace.path.is_symlink()
        or workspace.marker_path.is_symlink()
    ):
        raise UnsafeWorkDirectoryError("Symbolic-link work directories cannot be cleaned")
    try:
        marker = json.loads(workspace.marker_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise UnsafeWorkDirectoryError("Work directory marker is missing or invalid") from error
    expected_marker = {
        "marker_version": "1.0",
        "run_id": str(workspace.run_id),
        "job_id": workspace.job_id,
    }
    if marker == expected_marker:
        return cast(dict[str, Any], marker)
    if not isinstance(marker, dict) or set(marker) != {
        "marker_version",
        "run_id",
        "job_id",
        "created_at",
        "owner_pid",
        "retention_reason",
    }:
        raise UnsafeWorkDirectoryError("Work directory marker does not match ownership")
    try:
        valid = (
            marker["marker_version"] == "2.0"
            and marker["run_id"] == str(workspace.run_id)
            and marker["job_id"] == workspace.job_id
            and type(marker["owner_pid"]) is int
            and marker["owner_pid"] > 0
            and datetime.fromisoformat(marker["created_at"]).utcoffset() is not None
            and marker["retention_reason"]
            in {"active", "failed", "cancelled", "successful-retained"}
        )
    except (ValueError, TypeError):
        valid = False
    if not valid:
        raise UnsafeWorkDirectoryError("Work directory marker does not match ownership")
    return marker


def _validate_work_directory(workspace: WorkDirectory) -> None:
    work_directory_metadata(workspace)


def retain_work_directory(
    workspace: WorkDirectory, reason: Literal["failed", "cancelled", "successful-retained"]
) -> None:
    """Record the terminal reason without changing the immutable allocation identity/time."""
    marker = work_directory_metadata(workspace)
    if (
        marker["marker_version"] != "2.0"
        or marker["retention_reason"] != "active"
        or marker["owner_pid"] != os.getpid()
    ):
        raise UnsafeWorkDirectoryError("Only the active owner can finish a work directory")
    marker["retention_reason"] = reason
    temporary = workspace.marker_path.with_suffix(".pending")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            os.chmod(temporary, 0o600)
            handle.write(json.dumps(marker) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(workspace.marker_path)
    finally:
        temporary.unlink(missing_ok=True)


def cleanup_identity(
    workspace: WorkDirectory, references: Iterable[Path] = ()
) -> tuple[str, int, str]:
    """Return a fingerprint/size and conservative deletion blocker."""
    marker = work_directory_metadata(workspace)
    reason = marker.get("retention_reason", "legacy-unknown")
    blocker = ""
    if reason == "legacy-unknown":
        blocker = "legacy-unknown"
    elif reason == "active":
        try:
            os.kill(marker["owner_pid"], 0)
            blocker = "active"
        except ProcessLookupError:
            pass  # A crashed owner's workdir is explicitly previewed as interrupted.
        except (PermissionError, OSError):
            blocker = "active"
    base = workspace.path.resolve()
    for reference in references:
        resolved = reference.expanduser().resolve()
        if resolved == base or base in resolved.parents or resolved in base.parents:
            blocker = "referenced"
    items: list[Any] = [marker]
    size = 0
    for directory, dirs, files in os.walk(workspace.path, followlinks=False):
        for name in sorted([*dirs, *files]):
            path = Path(directory) / name
            metadata = path.lstat()
            relative = path.relative_to(workspace.path).as_posix()
            items.append(
                [
                    relative,
                    metadata.st_ino,
                    metadata.st_mode,
                    metadata.st_size,
                    metadata.st_mtime_ns,
                ]
            )
            if stat.S_ISLNK(metadata.st_mode) or not (
                stat.S_ISREG(metadata.st_mode) or stat.S_ISDIR(metadata.st_mode)
            ):
                blocker = "unsafe-entry"
            elif stat.S_ISREG(metadata.st_mode):
                size += metadata.st_size
                # The current pipeline owns only working WAVs and its marker. Protect all other
                # artifacts, models and unknown files even if someone moved them into a workdir.
                if name != MARKER_FILENAME and path.suffix.lower() != ".wav":
                    blocker = "unknown-artifact"
    digest = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()
    return digest, size, blocker
