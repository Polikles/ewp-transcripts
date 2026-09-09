"""Application service for safe, model-free derived exports."""

from __future__ import annotations

import hashlib
import os
import re
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from ewp_transcripts.config import SubtitlesConfig
from ewp_transcripts.domain.canonical import CanonicalResult, CanonicalSpeaker
from ewp_transcripts.domain.errors import (
    ApplicationError,
    InvalidCanonicalResultError,
    InvalidRevisionError,
    OutputReservationError,
)
from ewp_transcripts.domain.revision import (
    TranscriptRevision,
    load_transcript_revision,
    validate_revision_base,
)
from ewp_transcripts.effective_transcript import (
    EffectiveTranscript,
    effective_canonical_result,
    resolve_effective_transcript,
)
from ewp_transcripts.exporters import (
    build_subtitle_cues,
    render_html_transcript,
    render_segments_json,
    render_srt,
    render_transcript,
    render_vtt,
    render_ytt,
)
from ewp_transcripts.output_lock import output_directory_lock
from ewp_transcripts.review_discovery import discover_review_results


class ExportFormat(StrEnum):
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    SEGMENTS = "segments"
    YTT = "ytt"
    HTML = "html"


_SAFE_RENDER_FAILURES = frozenset(
    {
        "subtitle line limits must be positive",
        "subtitle cue text must not be empty",
        "a subtitle word exceeds max_chars_per_line",
        "subtitle cue exceeds max_lines",
        "subtitle cue timestamps are invalid",
        "subtitle cues must contain non-empty lines",
        "subtitle cues must be sorted chronologically",
        "ordinary subtitle cues must not overlap",
        "results_sha256 must be a lowercase hexadecimal SHA-256",
        "generated_at must be timezone-aware",
    }
)


@dataclass(frozen=True, slots=True)
class ExportOutcome:
    result_version: int
    written: tuple[Path, ...]
    skipped: tuple[Path, ...]
    revision_number: int | None = None
    revision_path: Path | None = None


@dataclass(frozen=True, slots=True)
class BatchExportJobOutcome:
    results_path: Path
    status: str
    outcome: ExportOutcome | None = None
    failure_code: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchExportOutcome:
    jobs: tuple[BatchExportJobOutcome, ...]
    stopped_early: bool = False

    @property
    def exported(self) -> int:
        return sum(job.status == "exported" for job in self.jobs)

    @property
    def failed(self) -> int:
        return sum(job.status == "failed" for job in self.jobs)

    @property
    def written(self) -> int:
        return sum(len(job.outcome.written) for job in self.jobs if job.outcome is not None)

    @property
    def skipped(self) -> int:
        return sum(len(job.outcome.skipped) for job in self.jobs if job.outcome is not None)


def export_result(
    results_path: Path,
    *,
    formats: tuple[ExportFormat, ...],
    output_directory: Path | None = None,
    force: bool = False,
    subtitles_config: SubtitlesConfig | None = None,
    generated_at: datetime | None = None,
    revision: Path | str | None = None,
) -> ExportOutcome:
    """Generate requested exports atomically from one completed canonical result."""

    if not formats:
        raise InvalidCanonicalResultError("At least one export format is required")
    unique_formats = tuple(dict.fromkeys(formats))
    result, payload = _read_result(results_path)
    if result.status != "completed":
        raise InvalidCanonicalResultError("Only completed canonical results can be exported")
    destination = results_path.parent if output_directory is None else output_directory.expanduser()
    if not destination.is_absolute():
        destination = (Path.cwd() / destination).absolute()

    selected_revision, revision_path = _select_revision(
        revision,
        result=result,
        results_path=results_path,
        results_sha256=hashlib.sha256(payload).hexdigest(),
    )
    try:
        effective = resolve_effective_transcript(
            result,
            selected_revision,
            base_path=results_path if selected_revision is not None else None,
        )
        rendered_result = effective_canonical_result(result, effective)
        if selected_revision is not None and selected_revision.transcript.speaker_labels:
            labels = selected_revision.transcript.speaker_labels
            existing_speakers = {speaker.speaker_id for speaker in rendered_result.speakers}
            additional_speakers = tuple(
                CanonicalSpeaker(
                    speaker_id=speaker_id,
                    speaker_label=label,
                    speaker_source="default",
                    first_seen_ms=next(
                        (
                            token.start_ms
                            for token in effective.tokens
                            if token.speaker_id == speaker_id
                        ),
                        0,
                    ),
                )
                for speaker_id, label in labels.items()
                if speaker_id not in existing_speakers
            )
            rendered_result = rendered_result.model_copy(
                update={
                    "speakers": tuple(
                        speaker.model_copy(
                            update={
                                "speaker_label": labels.get(
                                    speaker.speaker_id, speaker.speaker_label
                                )
                            }
                        )
                        for speaker in rendered_result.speakers
                    )
                    + additional_speakers
                }
            )
    except (ValidationError, ValueError) as error:
        if selected_revision is not None:
            raise InvalidCanonicalResultError(
                "Cannot resolve revised transcript for export"
            ) from error
        raise InvalidCanonicalResultError("Cannot resolve transcript for export") from error

    with output_directory_lock(destination):
        if selected_revision is None:
            version = _select_version(
                destination,
                job_id=result.job_id,
                formats=unique_formats,
                base_version=result.result_version,
                force=force,
            )
            paths = {
                format_: _export_path(destination, result.job_id, format_, version)
                for format_ in unique_formats
            }
        else:
            version = _select_revision_export_version(
                destination,
                result=result,
                revision=selected_revision,
                formats=unique_formats,
                force=force,
            )
            paths = {
                format_: _revision_export_path(
                    destination,
                    result=result,
                    revision_number=selected_revision.revision_number,
                    format_=format_,
                    export_version=version,
                )
                for format_ in unique_formats
            }
        skipped = tuple(path for path in paths.values() if path.exists()) if not force else ()
        pending = tuple((format_, path) for format_, path in paths.items() if path not in skipped)
        rendered = _render_exports(
            rendered_result,
            pending,
            results_path=results_path,
            results_sha256=hashlib.sha256(payload).hexdigest(),
            subtitles_config=subtitles_config or SubtitlesConfig(),
            generated_at=generated_at or datetime.now(UTC),
            revision=selected_revision,
            revision_path=revision_path,
            effective_transcript=effective,
        )
        for path, content in rendered:
            _publish_exclusive(path, content)
        return ExportOutcome(
            result_version=version,
            written=tuple(path for path, _ in rendered),
            skipped=skipped,
            revision_number=(
                selected_revision.revision_number if selected_revision is not None else None
            ),
            revision_path=revision_path,
        )


def export_batch(
    input_path: Path,
    *,
    formats: tuple[ExportFormat, ...],
    output_directory: Path | None = None,
    force: bool = False,
    subtitles_config: SubtitlesConfig | None = None,
    revision: Path | str | None = None,
    recursive: bool = False,
    continue_after_error: bool = True,
) -> BatchExportOutcome:
    """Export discovered canonical results sequentially with per-result isolation."""

    results = discover_review_results(input_path, recursive=recursive)
    if not results:
        raise InvalidCanonicalResultError(
            f"No completed canonical result files were found in: {input_path}"
        )
    jobs: list[BatchExportJobOutcome] = []
    stopped_early = False
    for results_path in results:
        try:
            outcome = export_result(
                results_path,
                formats=formats,
                output_directory=output_directory,
                force=force,
                subtitles_config=subtitles_config,
                revision=revision,
            )
            jobs.append(
                BatchExportJobOutcome(
                    results_path=results_path,
                    status="exported",
                    outcome=outcome,
                )
            )
        except ApplicationError as error:
            jobs.append(
                BatchExportJobOutcome(
                    results_path=results_path,
                    status="failed",
                    failure_code=error.code,
                    failure_message=str(error),
                )
            )
            if not continue_after_error:
                stopped_early = True
                break
    return BatchExportOutcome(tuple(jobs), stopped_early=stopped_early)


def _select_revision(
    requested: Path | str | None,
    *,
    result: CanonicalResult,
    results_path: Path,
    results_sha256: str,
) -> tuple[TranscriptRevision | None, Path | None]:
    if requested is None or requested == "none":
        return None, None
    if requested == "latest":
        result_suffix = "" if result.result_version == 1 else f"_v{result.result_version:03d}"
        pattern = re.compile(
            rf"^{re.escape(result.job_id + result_suffix)}_revision_(?P<number>[0-9]{{3,}})\.json$"
        )
        candidates = sorted(
            (
                (int(match.group("number")), path)
                for path in results_path.parent.iterdir()
                if path.is_file() and (match := pattern.fullmatch(path.name)) is not None
            ),
            reverse=True,
        )
        for _, path in candidates:
            candidate = load_transcript_revision(path)
            try:
                validate_revision_base(candidate, result, base_sha256=results_sha256)
            except InvalidRevisionError:
                continue
            return candidate, path
        raise InvalidRevisionError("No compatible transcript revision was found")
    path = Path(requested).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).absolute()
    if path.is_dir():
        return _latest_compatible_revision(
            path,
            result=result,
            results_sha256=results_sha256,
        )
    selected = load_transcript_revision(path)
    validate_revision_base(selected, result, base_sha256=results_sha256)
    return selected, path


def _latest_compatible_revision(
    directory: Path,
    *,
    result: CanonicalResult,
    results_sha256: str,
) -> tuple[TranscriptRevision, Path]:
    result_suffix = "" if result.result_version == 1 else f"_v{result.result_version:03d}"
    pattern = re.compile(
        rf"^{re.escape(result.job_id + result_suffix)}_revision_(?P<number>[0-9]{{3,}})\.json$"
    )
    candidates = sorted(
        (
            (int(match.group("number")), path)
            for path in directory.iterdir()
            if path.is_file() and (match := pattern.fullmatch(path.name)) is not None
        ),
        reverse=True,
    )
    for _, candidate_path in candidates:
        candidate = load_transcript_revision(candidate_path)
        try:
            validate_revision_base(candidate, result, base_sha256=results_sha256)
        except InvalidRevisionError:
            continue
        return candidate, candidate_path
    raise InvalidRevisionError(f"No compatible transcript revision was found for {result.job_id}")


def _read_result(path: Path) -> tuple[CanonicalResult, bytes]:
    try:
        payload = path.read_bytes()
        return CanonicalResult.model_validate_json(payload), payload
    except (OSError, ValidationError) as error:
        raise InvalidCanonicalResultError(f"Cannot read canonical result: {path}") from error


def _select_version(
    directory: Path,
    *,
    job_id: str,
    formats: tuple[ExportFormat, ...],
    base_version: int,
    force: bool,
) -> int:
    if not force:
        return base_version
    version = max(2, base_version + 1)
    while any(_export_path(directory, job_id, format_, version).exists() for format_ in formats):
        version += 1
    return version


def _export_path(directory: Path, job_id: str, format_: ExportFormat, version: int) -> Path:
    if (
        not job_id
        or job_id in {".", ".."}
        or Path(job_id).name != job_id
        or any(character in job_id for character in ("/", "\\", "\x00"))
    ):
        raise InvalidCanonicalResultError("Canonical job_id is unsafe for export filenames")
    suffix = "" if version == 1 else f"_v{version:03d}"
    role, extension = {
        ExportFormat.TXT: ("transcript", "txt"),
        ExportFormat.SRT: ("subtitles", "srt"),
        ExportFormat.VTT: ("subtitles", "vtt"),
        ExportFormat.SEGMENTS: ("segments", "json"),
        ExportFormat.YTT: ("subtitles_srv3", "ytt"),
        ExportFormat.HTML: ("transcript", "html"),
    }[format_]
    return directory / f"{job_id}_{role}{suffix}.{extension}"


def _revision_export_path(
    directory: Path,
    *,
    result: CanonicalResult,
    revision_number: int,
    format_: ExportFormat,
    export_version: int,
) -> Path:
    role, extension = {
        ExportFormat.TXT: ("transcript", "txt"),
        ExportFormat.SRT: ("subtitles", "srt"),
        ExportFormat.VTT: ("subtitles", "vtt"),
        ExportFormat.SEGMENTS: ("segments", "json"),
        ExportFormat.YTT: ("subtitles_srv3", "ytt"),
        ExportFormat.HTML: ("transcript", "html"),
    }[format_]
    result_suffix = "" if result.result_version == 1 else f"_v{result.result_version:03d}"
    export_suffix = "" if export_version == 1 else f"_v{export_version:03d}"
    return directory / (
        f"{result.job_id}_{role}{result_suffix}_revision_{revision_number:03d}"
        f"{export_suffix}.{extension}"
    )


def _select_revision_export_version(
    directory: Path,
    *,
    result: CanonicalResult,
    revision: TranscriptRevision,
    formats: tuple[ExportFormat, ...],
    force: bool,
) -> int:
    if not force:
        return 1
    version = 2
    while any(
        _revision_export_path(
            directory,
            result=result,
            revision_number=revision.revision_number,
            format_=format_,
            export_version=version,
        ).exists()
        for format_ in formats
    ):
        version += 1
    return version


def _render_exports(
    result: CanonicalResult,
    pending: tuple[tuple[ExportFormat, Path], ...],
    *,
    results_path: Path,
    results_sha256: str,
    subtitles_config: SubtitlesConfig,
    generated_at: datetime,
    revision: TranscriptRevision | None,
    revision_path: Path | None,
    effective_transcript: EffectiveTranscript,
) -> tuple[tuple[Path, str], ...]:
    cues = None
    rendered: list[tuple[Path, str]] = []
    for format_, path in pending:
        try:
            if format_ is ExportFormat.TXT:
                content = render_transcript(result)
            elif format_ is ExportFormat.HTML:
                content = render_html_transcript(
                    effective_transcript,
                    speaker_labels={
                        speaker.speaker_id: speaker.speaker_label for speaker in result.speakers
                    },
                )
            elif format_ is ExportFormat.SEGMENTS:
                content = render_segments_json(
                    result,
                    results_file=results_path,
                    results_sha256=results_sha256,
                    generated_at=generated_at,
                    revision_file=revision_path,
                    revision_number=revision.revision_number if revision else None,
                )
            else:
                if cues is None:
                    cues = build_subtitle_cues(result, subtitles_config)
                if format_ is ExportFormat.SRT:
                    content = render_srt(cues)
                elif format_ is ExportFormat.VTT:
                    content = render_vtt(cues)
                else:
                    content = render_ytt(
                        cues,
                        speaker_ids=(speaker.speaker_id for speaker in result.speakers),
                        speaker_palette=subtitles_config.ytt_speaker_palette,
                    )
        except ValueError as error:
            detail = str(error)
            safe_detail = detail if detail in _SAFE_RENDER_FAILURES else "invalid renderer input"
            raise InvalidCanonicalResultError(
                f"Cannot render {format_.value} export: {safe_detail}"
            ) from error
        rendered.append((path, content))
    return tuple(rendered)


def _publish_exclusive(path: Path, content: str) -> None:
    temporary = path.parent / f".{path.name}.{uuid4()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        created = True
        try:
            payload = content.encode("utf-8")
            while payload:
                written = os.write(descriptor, payload)
                payload = payload[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.link(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except FileExistsError as error:
        raise OutputReservationError(f"Export already exists: {path}") from error
    except OSError as error:
        raise OutputReservationError(f"Cannot publish export: {path}") from error
    finally:
        if created:
            with suppress(FileNotFoundError):
                temporary.unlink()
