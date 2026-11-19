"""Safe FFmpeg adapter for canonical working-audio preparation."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from ewp_transcripts.domain.errors import AudioPreparationError

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _run_command(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(arguments), check=False, capture_output=True, text=True)


def prepare_working_audio(
    source: Path,
    destination: Path,
    *,
    stream_index: int,
    channel_index: int | None = None,
    sample_rate_hz: int = 16_000,
    executable: str = "ffmpeg",
    runner: CommandRunner = _run_command,
) -> Path:
    """Decode one selected stream/channel to a new mono PCM WAV in a workdir."""

    if stream_index < 0:
        raise ValueError("stream_index must be non-negative")
    if channel_index is not None and channel_index < 0:
        raise ValueError("channel_index must be non-negative")
    if sample_rate_hz < 1:
        raise ValueError("sample_rate_hz must be positive")
    if destination.exists() or destination.is_symlink():
        raise AudioPreparationError(f"Working-audio destination already exists: {destination}")
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise AudioPreparationError(
            f"Working-audio parent must be an existing regular directory: {destination.parent}"
        )

    arguments = [
        executable,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-n",
        "-i",
        str(source.absolute()),
        "-map",
        f"0:{stream_index}",
        "-vn",
        "-sn",
        "-dn",
    ]
    if channel_index is not None:
        arguments.extend(("-af", f"pan=mono|c0=c{channel_index}"))
    arguments.extend(
        (
            "-ac",
            "1",
            "-ar",
            str(sample_rate_hz),
            "-c:a",
            "pcm_s16le",
            "-f",
            "wav",
            str(destination.absolute()),
        )
    )
    try:
        completed = runner(arguments)
    except FileNotFoundError as error:
        raise AudioPreparationError("ffmpeg executable is missing") from error
    except (OSError, subprocess.SubprocessError) as error:
        raise AudioPreparationError("ffmpeg working-audio preparation failed") from error
    if completed.returncode != 0:
        raise AudioPreparationError(
            f"ffmpeg could not prepare working audio (exit code {completed.returncode})"
        )
    if not destination.is_file() or destination.is_symlink() or destination.stat().st_size == 0:
        raise AudioPreparationError("ffmpeg did not create a valid working-audio file")
    return destination


def mix_working_audio(
    sources: Sequence[Path],
    destination: Path,
    *,
    executable: str = "ffmpeg",
    runner: CommandRunner = _run_command,
) -> Path:
    """Mix synchronous mono previews from time zero, retaining the longest source timeline."""
    if len(sources) < 2 or destination.exists() or destination.is_symlink():
        raise AudioPreparationError("A new mix requires at least two prepared audio files")
    arguments = [executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-n"]
    for source in sources:
        arguments.extend(("-i", str(source.absolute())))
    arguments.extend(
        (
            "-filter_complex",
            f"amix=inputs={len(sources)}:duration=longest:dropout_transition=0:normalize=1",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(destination.absolute()),
        )
    )
    try:
        completed = runner(arguments)
    except (OSError, subprocess.SubprocessError) as error:
        raise AudioPreparationError("FFmpeg could not mix recording audio") from error
    if completed.returncode or not destination.is_file() or destination.stat().st_size == 0:
        raise AudioPreparationError("FFmpeg could not mix recording audio")
    return destination
