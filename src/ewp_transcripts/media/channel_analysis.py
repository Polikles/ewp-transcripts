"""Streaming FFmpeg boundary for non-destructive channel analysis."""

from __future__ import annotations

import subprocess
import sys
from array import array
from collections.abc import Iterable, Iterator
from pathlib import Path

from ewp_transcripts.domain import ChannelMetrics
from ewp_transcripts.domain.errors import ChannelAnalysisError
from ewp_transcripts.media.channel_metrics import measure_stereo_channels

ANALYSIS_SAMPLE_RATE_HZ = 16000
_FRAME_BYTES = 4
_READ_BYTES = 64 * 1024


def _pcm16_stereo_samples(chunks: Iterable[bytes]) -> Iterator[tuple[int, int]]:
    """Convert arbitrary byte chunks of little-endian stereo PCM into sample pairs."""

    remainder = b""
    for chunk in chunks:
        combined = remainder + chunk
        usable_length = len(combined) - (len(combined) % _FRAME_BYTES)
        usable = combined[:usable_length]
        remainder = combined[usable_length:]
        decoded = array("h")
        decoded.frombytes(usable)
        if sys.byteorder != "little":
            decoded.byteswap()
        yield from zip(decoded[0::2], decoded[1::2], strict=True)
    if remainder:
        raise ChannelAnalysisError("FFmpeg returned an incomplete stereo PCM frame")


def _stdout_chunks(stream: subprocess.Popen[bytes]) -> Iterator[bytes]:
    if stream.stdout is None:
        raise ChannelAnalysisError("FFmpeg channel-analysis output is unavailable")
    while chunk := stream.stdout.read(_READ_BYTES):
        yield chunk


def measure_file_channels(
    path: Path,
    *,
    executable: str = "ffmpeg",
    sample_rate_hz: int = ANALYSIS_SAMPLE_RATE_HZ,
    window_ms: int = 500,
    stream_index: int | None = None,
) -> ChannelMetrics:
    """Decode and measure one stream incrementally without writing temporary audio."""

    arguments = [
        executable,
        "-v",
        "error",
        "-i",
        str(path.absolute()),
        "-map",
        "0:a:0" if stream_index is None else f"0:{stream_index}",
        "-ac",
        "2",
        "-ar",
        str(sample_rate_hz),
        "-acodec",
        "pcm_s16le",
        "-f",
        "s16le",
        "pipe:1",
    ]
    try:
        process = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError as error:
        raise ChannelAnalysisError("Unable to start FFmpeg channel analysis") from error

    try:
        metrics = measure_stereo_channels(
            _pcm16_stereo_samples(_stdout_chunks(process)),
            sample_rate_hz=sample_rate_hz,
            window_ms=window_ms,
        )
        return_code = process.wait(timeout=30)
    except Exception:
        process.kill()
        process.wait()
        raise
    if return_code != 0:
        raise ChannelAnalysisError(f"FFmpeg channel analysis failed with exit code {return_code}")
    return metrics
