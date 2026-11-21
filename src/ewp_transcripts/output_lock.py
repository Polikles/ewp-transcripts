"""Native Windows and POSIX output locking for mutable storage operations."""

from __future__ import annotations

import errno
import json
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from ewp_transcripts.domain.errors import OutputLockUnavailableError
from ewp_transcripts.platform_runtime import WINDOWS, private_descriptor_mode

LOCK_FILENAME = ".ewp-transcripts.lock"


def _lock_descriptor(descriptor: int, *, unlock: bool = False) -> None:
    if WINDOWS:
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(  # type: ignore[attr-defined]
            descriptor, getattr(msvcrt, "LK_UNLCK" if unlock else "LK_NBLCK"), 1
        )
    else:
        import fcntl

        fcntl.flock(descriptor, fcntl.LOCK_UN if unlock else fcntl.LOCK_EX | fcntl.LOCK_NB)


@contextmanager
def output_directory_lock(
    output_directory: Path,
    *,
    timeout_seconds: float = 0,
    poll_interval_seconds: float = 0.05,
) -> Iterator[Path]:
    """Exclusively lock one output directory, creating it when first needed."""

    if timeout_seconds < 0 or poll_interval_seconds <= 0:
        raise ValueError("lock timeout must be non-negative and poll interval positive")
    if output_directory.is_symlink():
        raise OutputLockUnavailableError(
            f"Output directory must not be a symbolic link: {output_directory}"
        )
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise OutputLockUnavailableError(
            f"Cannot create output directory for locking: {output_directory}"
        ) from error
    if not output_directory.is_dir():
        raise OutputLockUnavailableError(
            f"Output destination is not a directory: {output_directory}"
        )

    lock_path = output_directory / LOCK_FILENAME
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as error:
        raise OutputLockUnavailableError(f"Cannot open output lock: {lock_path}") from error

    deadline = time.monotonic() + timeout_seconds
    acquired = False
    try:
        while True:
            try:
                _lock_descriptor(descriptor)
                acquired = True
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise OutputLockUnavailableError("Cannot acquire output lock") from error
                if time.monotonic() >= deadline:
                    raise OutputLockUnavailableError(
                        f"Output directory is locked by another process: {output_directory}"
                    ) from error
                time.sleep(min(poll_interval_seconds, max(0.0, deadline - time.monotonic())))

        metadata = {
            "pid": os.getpid(),
            "acquired_at": datetime.now(UTC).isoformat(),
        }
        payload = (json.dumps(metadata) + "\n").encode("utf-8")
        private_descriptor_mode(descriptor)
        os.ftruncate(descriptor, 0)
        os.lseek(descriptor, 0, os.SEEK_SET)
        remaining = memoryview(payload)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
        yield lock_path
    finally:
        if acquired:
            _lock_descriptor(descriptor, unlock=True)
        os.close(descriptor)
