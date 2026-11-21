"""Locked allocation and atomic publication for immutable transcript revisions."""

from __future__ import annotations

import json
import os
import re
from contextlib import suppress
from pathlib import Path

from ewp_transcripts.domain.errors import OutputReservationError, UnsafeOutputNameError
from ewp_transcripts.domain.revision import TranscriptRevision
from ewp_transcripts.output_lock import output_directory_lock
from ewp_transcripts.platform_runtime import fsync_directory


def _safe_job_id(job_id: str) -> str:
    if not job_id or job_id in {".", ".."} or Path(job_id).name != job_id or "\x00" in job_id:
        raise UnsafeOutputNameError(f"Job ID is not safe for output filenames: {job_id!r}")
    return job_id


def revision_filename(*, job_id: str, result_version: int, revision_number: int) -> str:
    """Return the contract filename for one base-result/revision identity."""

    safe_job_id = _safe_job_id(job_id)
    if result_version < 1 or revision_number < 1:
        raise ValueError("result and revision numbers must be positive")
    result_suffix = "" if result_version == 1 else f"_v{result_version:03d}"
    return f"{safe_job_id}{result_suffix}_revision_{revision_number:03d}.json"


def _revision_pattern(*, job_id: str, result_version: int) -> re.Pattern[str]:
    first_name = revision_filename(
        job_id=job_id,
        result_version=result_version,
        revision_number=1,
    )
    prefix = first_name.removesuffix("001.json")
    return re.compile(rf"^{re.escape(prefix)}(?P<number>[0-9]{{3,}})\.json$")


def _next_revision_number(
    output_directory: Path,
    *,
    job_id: str,
    result_version: int,
) -> int:
    pattern = _revision_pattern(job_id=job_id, result_version=result_version)
    allocated = [
        int(match.group("number"))
        for path in output_directory.iterdir()
        if path.is_file() and (match := pattern.fullmatch(path.name)) is not None
    ]
    return max(allocated, default=0) + 1


def _write_all(descriptor: int, payload: bytes) -> None:
    remaining = memoryview(payload)
    while remaining:
        remaining = remaining[os.write(descriptor, remaining) :]


def _publish_exclusive(path: Path, payload: bytes, *, revision_id: str) -> None:
    temporary = path.parent / f".{path.name}.{revision_id}.tmp"
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
        raise OutputReservationError(f"Revision output already exists: {path}") from error
    except OSError as error:
        raise OutputReservationError(f"Cannot publish transcript revision: {path}") from error
    finally:
        if created:
            with suppress(FileNotFoundError):
                temporary.unlink()
            fsync_directory(path.parent)


def publish_next_revision(
    revision: TranscriptRevision,
    *,
    output_directory: Path,
    lock_timeout_seconds: float = 0,
) -> tuple[TranscriptRevision, Path]:
    """Allocate and atomically publish the next standalone revision under one lock."""

    with output_directory_lock(output_directory, timeout_seconds=lock_timeout_seconds):
        revision_number = _next_revision_number(
            output_directory,
            job_id=revision.job_id,
            result_version=revision.base_result.result_version,
        )
        allocated = revision.model_copy(update={"revision_number": revision_number})
        # Revalidate the copied model before it becomes a final artifact.
        allocated = TranscriptRevision.model_validate(allocated.model_dump())
        path = output_directory / revision_filename(
            job_id=allocated.job_id,
            result_version=allocated.base_result.result_version,
            revision_number=allocated.revision_number,
        )
        artifact = allocated.model_dump(mode="json", exclude_none=True)
        if allocated.parent_revision is None:
            artifact["parent_revision"] = None
        payload = (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        _publish_exclusive(path, payload, revision_id=str(allocated.revision_id))
        return allocated, path
