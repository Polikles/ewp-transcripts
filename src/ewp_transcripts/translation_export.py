"""Deterministic derived exports from immutable translation snapshots."""

from __future__ import annotations

import json
import os
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ewp_transcripts.config import SubtitlesConfig
from ewp_transcripts.domain.errors import InvalidTranslationError, OutputReservationError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.domain.translation import TranscriptTranslation, load_transcript_translation
from ewp_transcripts.exporters.html import HtmlTranscriptUnit, render_html_units
from ewp_transcripts.exporters.subtitles import (
    SubtitleCue,
    render_srt,
    render_vtt,
    wrap_subtitle_text,
)
from ewp_transcripts.output_lock import output_directory_lock


class TranslationExportFormat(StrEnum):
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    HTML = "html"


@dataclass(frozen=True, slots=True)
class TranslationExportOutcome:
    translation_path: Path
    written: tuple[Path, ...]
    skipped: tuple[Path, ...]


def render_translation_text(translation: TranscriptTranslation) -> str:
    """Render stable speaker blocks without inventing display-name metadata."""

    blocks: list[str] = []
    current_speaker: str | None = None
    current_lines: list[str] = []
    included_units = tuple(unit for unit in translation.units if unit.target_status == "translated")
    multiple_speakers = len({unit.speaker_id for unit in included_units}) > 1
    for unit in included_units:
        if unit.speaker_id != current_speaker:
            if current_lines:
                blocks.append("\n".join(current_lines))
            current_speaker = unit.speaker_id
            current_lines = [f"{unit.speaker_id}:"] if multiple_speakers else []
        current_lines.append(unit.target_text)
    if current_lines:
        blocks.append("\n".join(current_lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def build_translation_subtitle_cues(
    translation: TranscriptTranslation,
    config: SubtitlesConfig | None = None,
) -> tuple[SubtitleCue, ...]:
    """Build bounded target-text cues within inherited sentence-unit intervals."""

    settings = config or SubtitlesConfig()
    cues: list[SubtitleCue] = []
    previous_speaker: str | None = None
    units = translation.units
    for unit_index, unit in enumerate(units):
        if unit.target_status == "intentionally_empty":
            continue
        prefix = f"{unit.speaker_id}: " if unit.speaker_id != previous_speaker else ""
        chunks = _split_target_text(unit.target_text, settings, first_prefix=prefix)
        duration = unit.end_ms - unit.start_ms
        overlap = any(
            other_index != unit_index
            and other.start_ms < unit.end_ms
            and unit.start_ms < other.end_ms
            for other_index, other in enumerate(units)
        )
        for chunk_index, chunk in enumerate(chunks):
            start_ms = unit.start_ms + duration * chunk_index // len(chunks)
            end_ms = unit.start_ms + duration * (chunk_index + 1) // len(chunks)
            text = f"{prefix}{chunk}" if chunk_index == 0 else chunk
            cues.append(
                SubtitleCue(
                    start_ms=start_ms,
                    end_ms=end_ms,
                    lines=wrap_subtitle_text(
                        text,
                        max_lines=settings.max_lines,
                        max_chars_per_line=settings.max_chars_per_line,
                    ),
                    speaker_id=unit.speaker_id,
                    overlap=overlap,
                )
            )
        previous_speaker = unit.speaker_id
    cues.sort(key=lambda cue: (cue.start_ms, cue.end_ms, cue.speaker_id or ""))
    return tuple(cues)


def _split_target_text(
    text: str, settings: SubtitlesConfig, *, first_prefix: str
) -> tuple[str, ...]:
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        best: str | None = None
        end = start + 1
        while end <= len(words):
            candidate = " ".join(words[start:end])
            prefix = first_prefix if not chunks else ""
            try:
                wrap_subtitle_text(
                    f"{prefix}{candidate}",
                    max_lines=settings.max_lines,
                    max_chars_per_line=settings.max_chars_per_line,
                )
            except ValueError:
                break
            best = candidate
            end += 1
        if best is None:
            raise ValueError("translated subtitle contains a word that exceeds line limits")
        chunks.append(best)
        start += len(best.split())
    return tuple(chunks)


def _publish_or_skip(path: Path, payload: bytes) -> bool:
    if path.is_file():
        if path.read_bytes() == payload:
            return False
        raise OutputReservationError(
            f"Translation export already exists with other content: {path}"
        )
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        created = True
        try:
            remaining = memoryview(payload)
            while remaining:
                remaining = remaining[os.write(descriptor, remaining) :]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.link(temporary, path)
        directory_flags = os.O_RDONLY | (os.O_DIRECTORY if hasattr(os, "O_DIRECTORY") else 0)
        directory_descriptor = os.open(path.parent, directory_flags)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        return True
    except FileExistsError as error:
        raise OutputReservationError(
            f"Translation export was concurrently reserved: {path}"
        ) from error
    finally:
        if created:
            with suppress(FileNotFoundError):
                temporary.unlink()


def export_translation(
    translation_path: str | Path,
    *,
    formats: tuple[TranslationExportFormat, ...] = (TranslationExportFormat.TXT,),
    output_directory: Path | None = None,
    lock_timeout_seconds: float = 0,
    subtitles_config: SubtitlesConfig | None = None,
) -> TranslationExportOutcome:
    """Write or safely skip deterministic translation-derived representations."""

    normalized = Path(translation_path).expanduser().absolute()
    translation = load_transcript_translation(normalized)
    destination = output_directory or normalized.parent
    stem = (
        f"{translation.job_id}_{translation.direction.target_language}_translation_"
        f"{translation.translation_number:03d}"
    )
    selected = tuple(dict.fromkeys(formats))
    if not selected:
        raise ValueError("at least one translation export format is required")
    cues = None
    payloads: list[tuple[Path, bytes]] = []
    for export_format in selected:
        if export_format == TranslationExportFormat.TXT:
            rendered = render_translation_text(translation)
        elif export_format == TranslationExportFormat.HTML:
            rendered = render_html_units(
                language=translation.direction.target_language,
                units=tuple(
                    HtmlTranscriptUnit(
                        speaker_id=unit.speaker_id,
                        text=unit.target_text,
                        start_ms=unit.start_ms,
                        end_ms=unit.end_ms,
                    )
                    for unit in translation.units
                    if unit.target_status == "translated"
                ),
                speaker_labels={
                    speaker_id: speaker_id
                    for speaker_id in {
                        unit.speaker_id
                        for unit in translation.units
                        if unit.target_status == "translated"
                    }
                },
            )
        else:
            try:
                if cues is None:
                    cues = build_translation_subtitle_cues(translation, subtitles_config)
                rendered = (
                    render_srt(cues)
                    if export_format == TranslationExportFormat.SRT
                    else render_vtt(cues)
                )
            except ValueError as error:
                raise InvalidTranslationError(
                    f"Cannot render translated {export_format.value} export: {error}"
                ) from error
        payloads.append((destination / f"{stem}.{export_format.value}", rendered.encode("utf-8")))
    provenance = {
        "schema_version": "ewp-translation-export-provenance-v1",
        "translation": {
            "filename": normalized.name,
            "sha256": sha256_file(normalized),
        },
        "dictionary": (
            translation.dictionary.model_dump(mode="json")
            if translation.dictionary is not None
            else None
        ),
        "exports": [path.name for path, _payload in payloads],
    }
    payloads.append(
        (
            destination / f"{stem}.provenance.json",
            (json.dumps(provenance, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
    )
    written_paths: list[Path] = []
    skipped_paths: list[Path] = []
    with output_directory_lock(destination, timeout_seconds=lock_timeout_seconds):
        for path, payload in payloads:
            if path.is_file() and path.read_bytes() != payload:
                raise OutputReservationError(
                    f"Translation export already exists with other content: {path}"
                )
        for path, payload in payloads:
            if _publish_or_skip(path, payload):
                written_paths.append(path)
            else:
                skipped_paths.append(path)
    return TranslationExportOutcome(
        translation_path=normalized,
        written=tuple(written_paths),
        skipped=tuple(skipped_paths),
    )


def export_translation_text(
    translation_path: str | Path,
    *,
    output_directory: Path | None = None,
    lock_timeout_seconds: float = 0,
) -> TranslationExportOutcome:
    """Backward-compatible focused entry point for deterministic TXT export."""

    return export_translation(
        translation_path,
        output_directory=output_directory,
        lock_timeout_seconds=lock_timeout_seconds,
    )
