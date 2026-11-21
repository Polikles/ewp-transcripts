"""Locked, non-destructive publication of human-editable review files."""

from __future__ import annotations

import os
import re
from contextlib import suppress
from pathlib import Path

from ewp_transcripts.domain.errors import OutputReservationError, UnsafeOutputNameError
from ewp_transcripts.domain.review import TranscriptReview
from ewp_transcripts.output_lock import output_directory_lock
from ewp_transcripts.platform_runtime import fsync_directory
from ewp_transcripts.review_format import render_review


def _safe_job_id(job_id: str) -> str:
    if not job_id or job_id in {".", ".."} or Path(job_id).name != job_id or "\x00" in job_id:
        raise UnsafeOutputNameError(f"Job ID is not safe for review filenames: {job_id!r}")
    return job_id


def review_filename(*, job_id: str, version: int) -> str:
    """Return a stable non-destructive review work filename."""

    safe_job_id = _safe_job_id(job_id)
    if version < 1:
        raise ValueError("review version must be positive")
    suffix = "" if version == 1 else f"_v{version:03d}"
    return f"{safe_job_id}.review{suffix}.txt"


def _next_version(output_directory: Path, *, job_id: str) -> int:
    first = review_filename(job_id=job_id, version=1)
    pattern = re.compile(
        rf"^{re.escape(first.removesuffix('.review.txt'))}\.review"
        rf"(?:_v(?P<version>[0-9]{{3,}}))?\.txt$"
    )
    versions = []
    for path in output_directory.iterdir():
        match = pattern.fullmatch(path.name) if path.is_file() else None
        if match is not None:
            versions.append(int(match.group("version") or "1"))
    return max(versions, default=0) + 1


def _write_all(descriptor: int, payload: bytes) -> None:
    remaining = memoryview(payload)
    while remaining:
        remaining = remaining[os.write(descriptor, remaining) :]


def _publish_exclusive(path: Path, payload: bytes) -> None:
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        created = True
        try:
            _write_all(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.link(temporary, path)
        fsync_directory(path.parent)
    except FileExistsError as error:
        raise OutputReservationError(f"Review output already exists: {path}") from error
    except OSError as error:
        raise OutputReservationError(f"Cannot publish transcript review: {path}") from error
    finally:
        if created:
            with suppress(FileNotFoundError):
                temporary.unlink()
            fsync_directory(path.parent)


def publish_review(
    review: TranscriptReview,
    *,
    output_directory: Path,
    lock_timeout_seconds: float = 0,
) -> Path:
    """Allocate and publish a review without replacing existing work."""

    with output_directory_lock(output_directory, timeout_seconds=lock_timeout_seconds):
        version = _next_version(output_directory, job_id=review.header.job_id)
        path = output_directory / review_filename(job_id=review.header.job_id, version=version)
        _publish_exclusive(path, render_review(review).encode("utf-8"))
        return path
