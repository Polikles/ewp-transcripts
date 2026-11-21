"""Locked publication for translation reviews and immutable snapshots."""

from __future__ import annotations

import json
import os
import re
from contextlib import suppress
from pathlib import Path

from ewp_transcripts.domain.errors import OutputReservationError, UnsafeOutputNameError
from ewp_transcripts.domain.translation import Language, TranscriptTranslation
from ewp_transcripts.domain.translation_review import TranslationReview
from ewp_transcripts.output_lock import output_directory_lock
from ewp_transcripts.platform_runtime import fsync_directory
from ewp_transcripts.translation_review_format import render_translation_review


def _safe_component(value: str, *, label: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value or "\x00" in value:
        raise UnsafeOutputNameError(f"{label} is not safe for translation filenames: {value!r}")
    return value


def translation_review_filename(*, job_id: str, target_language: Language, version: int) -> str:
    safe_job_id = _safe_component(job_id, label="Job ID")
    _safe_component(target_language, label="Target language")
    if version < 1:
        raise ValueError("translation review version must be positive")
    suffix = "" if version == 1 else f"_v{version:03d}"
    return f"{safe_job_id}_{target_language}.translation.review{suffix}.txt"


def translation_filename(*, job_id: str, target_language: Language, translation_number: int) -> str:
    safe_job_id = _safe_component(job_id, label="Job ID")
    _safe_component(target_language, label="Target language")
    if translation_number < 1:
        raise ValueError("translation number must be positive")
    return f"{safe_job_id}_{target_language}_translation_{translation_number:03d}.json"


def _allocated_numbers(directory: Path, pattern: re.Pattern[str], group: str) -> list[int]:
    return [
        int(match.group(group))
        for path in directory.iterdir()
        if path.is_file() and (match := pattern.fullmatch(path.name)) is not None
    ]


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
        raise OutputReservationError(f"Translation output already exists: {path}") from error
    except OSError as error:
        raise OutputReservationError(f"Cannot publish translation output: {path}") from error
    finally:
        if created:
            with suppress(FileNotFoundError):
                temporary.unlink()
            fsync_directory(path.parent)


def publish_translation_review(
    review: TranslationReview, *, output_directory: Path, lock_timeout_seconds: float = 0
) -> Path:
    with output_directory_lock(output_directory, timeout_seconds=lock_timeout_seconds):
        first = translation_review_filename(
            job_id=review.header.job_id,
            target_language=review.header.target_language,
            version=1,
        )
        prefix = first.removesuffix(".review.txt")
        pattern = re.compile(rf"^{re.escape(prefix)}\.review(?:_v(?P<version>[0-9]{{3,}}))?\.txt$")
        versions = [
            int(match.group("version") or "1")
            for path in output_directory.iterdir()
            if path.is_file() and (match := pattern.fullmatch(path.name)) is not None
        ]
        version = max(versions, default=0) + 1
        path = output_directory / translation_review_filename(
            job_id=review.header.job_id,
            target_language=review.header.target_language,
            version=version,
        )
        _publish_exclusive(path, render_translation_review(review).encode("utf-8"))
        return path


def publish_next_translation(
    translation: TranscriptTranslation,
    *,
    output_directory: Path,
    lock_timeout_seconds: float = 0,
) -> tuple[TranscriptTranslation, Path]:
    with output_directory_lock(output_directory, timeout_seconds=lock_timeout_seconds):
        first = translation_filename(
            job_id=translation.job_id,
            target_language=translation.direction.target_language,
            translation_number=1,
        )
        prefix = first.removesuffix("001.json")
        pattern = re.compile(rf"^{re.escape(prefix)}(?P<number>[0-9]{{3,}})\.json$")
        parent_number = (
            translation.parent_translation.translation_number
            if translation.parent_translation is not None
            else 0
        )
        number = (
            max(
                (*_allocated_numbers(output_directory, pattern, "number"), parent_number),
                default=0,
            )
            + 1
        )
        allocated = TranscriptTranslation.model_validate(
            translation.model_copy(update={"translation_number": number}).model_dump()
        )
        path = output_directory / translation_filename(
            job_id=allocated.job_id,
            target_language=allocated.direction.target_language,
            translation_number=number,
        )
        artifact = allocated.model_dump(mode="json", exclude_none=True)
        if allocated.parent_translation is None:
            artifact["parent_translation"] = None
        payload = (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        _publish_exclusive(path, payload)
        return allocated, path


def publish_translation_bytes(
    path: Path,
    payload: bytes,
    *,
    lock_timeout_seconds: float = 0,
) -> bool:
    """Publish deterministic derived translation data or skip identical bytes."""

    with output_directory_lock(path.parent, timeout_seconds=lock_timeout_seconds):
        if path.is_file():
            if path.read_bytes() == payload:
                return False
            raise OutputReservationError(
                f"Translation-derived output already exists with other content: {path}"
            )
        _publish_exclusive(path, payload)
        return True
