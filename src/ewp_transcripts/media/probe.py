"""Safe ffprobe adapter and normalized media inspection."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ewp_transcripts.domain import AudioStream, MediaProbeResult
from ewp_transcripts.domain.errors import MediaProbeError, NoAudioStreamError

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _run_command(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _milliseconds(value: object) -> int | None:
    if value in (None, "", "N/A"):
        return None
    try:
        seconds = Decimal(str(value))
    except InvalidOperation as error:
        raise MediaProbeError("ffprobe returned an invalid duration") from error
    if not seconds.is_finite() or seconds < 0:
        raise MediaProbeError("ffprobe returned an invalid duration")
    return int((seconds * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _positive_integer(value: object, *, field: str) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as error:
        raise MediaProbeError(f"ffprobe returned an invalid {field}") from error
    if parsed <= 0:
        raise MediaProbeError(f"ffprobe returned an invalid {field}")
    return parsed


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _audio_stream(stream: Mapping[str, Any]) -> AudioStream:
    tags = stream.get("tags")
    metadata = tags if isinstance(tags, Mapping) else {}
    try:
        index = int(stream["index"])
        codec = str(stream["codec_name"])
    except (KeyError, TypeError, ValueError) as error:
        raise MediaProbeError("ffprobe returned incomplete audio-stream metadata") from error
    if index < 0 or not codec:
        raise MediaProbeError("ffprobe returned incomplete audio-stream metadata")

    return AudioStream(
        index=index,
        codec=codec,
        sample_rate_hz=_positive_integer(stream.get("sample_rate"), field="sample rate"),
        channels=_positive_integer(stream.get("channels"), field="channel count"),
        channel_layout=_optional_text(stream.get("channel_layout")),
        duration_ms=_milliseconds(stream.get("duration")),
        language=_optional_text(metadata.get("language")),
        title=_optional_text(metadata.get("title")),
    )


def _parse_probe(path: Path, serialized: str) -> MediaProbeResult:
    try:
        document = json.loads(serialized)
    except json.JSONDecodeError as error:
        raise MediaProbeError("ffprobe returned invalid JSON") from error
    if not isinstance(document, dict):
        raise MediaProbeError("ffprobe returned an invalid result object")

    raw_streams = document.get("streams")
    if not isinstance(raw_streams, list):
        raise MediaProbeError("ffprobe result is missing the streams list")
    streams = tuple(
        _audio_stream(stream)
        for stream in raw_streams
        if isinstance(stream, Mapping) and stream.get("codec_type") == "audio"
    )
    if not streams:
        raise NoAudioStreamError(
            f"No audio stream found in input: {path}. Choose a recording with an audio track."
        )

    raw_format = document.get("format")
    format_data = raw_format if isinstance(raw_format, Mapping) else {}
    format_duration = _milliseconds(format_data.get("duration"))
    stream_durations = [stream.duration_ms for stream in streams if stream.duration_ms is not None]
    duration_ms = (
        format_duration if format_duration is not None else max(stream_durations, default=0)
    )
    format_name = _optional_text(format_data.get("format_name"))
    format_names = tuple(part.strip() for part in (format_name or "").split(",") if part.strip())

    return MediaProbeResult(
        path=path,
        format_names=format_names,
        duration_ms=duration_ms,
        audio_streams=streams,
        has_video=any(
            isinstance(stream, Mapping)
            and stream.get("codec_type") == "video"
            and not (stream.get("disposition") or {}).get("attached_pic", 0)
            for stream in raw_streams
        ),
    )


def probe_media(
    path: Path,
    *,
    executable: str = "ffprobe",
    runner: CommandRunner = _run_command,
) -> MediaProbeResult:
    """Inspect one file with ffprobe without modifying it."""

    absolute_path = path.absolute()
    arguments = [
        executable,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(absolute_path),
    ]
    try:
        completed = runner(arguments)
    except FileNotFoundError as error:
        raise MediaProbeError("ffprobe executable is missing") from error
    except (OSError, subprocess.SubprocessError) as error:
        raise MediaProbeError("ffprobe execution failed") from error
    if completed.returncode != 0:
        raise MediaProbeError(f"ffprobe rejected the input with exit code {completed.returncode}")
    return _parse_probe(absolute_path, completed.stdout)
