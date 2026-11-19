"""Unit tests for normalized ffprobe parsing."""

import json
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from ewp_transcripts.domain.errors import MediaProbeError, NoAudioStreamError
from ewp_transcripts.media.probe import probe_media


def _runner_for(
    document: object,
    captured: list[str],
) -> Callable[[Sequence[str]], subprocess.CompletedProcess[str]]:
    def run(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        captured.extend(arguments)
        return subprocess.CompletedProcess(arguments, 0, json.dumps(document), "")

    return run


def test_probe_normalizes_audio_streams_and_metadata(tmp_path: Path) -> None:
    source = tmp_path / "Zażółć track.bin"
    source.write_bytes(b"unchanged")
    captured: list[str] = []
    document = {
        "streams": [
            {"index": 0, "codec_type": "video", "codec_name": "png"},
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "pcm_s16le",
                "sample_rate": "48000",
                "channels": 2,
                "channel_layout": "stereo",
                "duration": "95.3755",
                "tags": {"language": "pol", "title": "Main mix"},
            },
        ],
        "format": {"format_name": "wav", "duration": "95.375521"},
    }

    result = probe_media(source, runner=_runner_for(document, captured))

    assert result.path == source
    assert result.duration_ms == 95376
    assert result.format_names == ("wav",)
    assert len(result.audio_streams) == 1
    assert result.audio_streams[0].model_dump() == {
        "index": 1,
        "codec": "pcm_s16le",
        "sample_rate_hz": 48000,
        "channels": 2,
        "channel_layout": "stereo",
        "duration_ms": 95376,
        "language": "pol",
        "title": "Main mix",
    }
    assert captured[-1] == str(source)
    assert "shell=True" not in captured
    assert source.read_bytes() == b"unchanged"


def test_probe_lists_multiple_audio_streams(tmp_path: Path) -> None:
    source = tmp_path / "multi.mka"
    source.write_bytes(b"media")
    document = {
        "streams": [
            {
                "index": 0,
                "codec_type": "audio",
                "codec_name": "flac",
                "sample_rate": "48000",
                "channels": 1,
            },
            {
                "index": 2,
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "44100",
                "channels": 2,
            },
        ],
        "format": {"format_name": "matroska,webm", "duration": "12.5"},
    }

    result = probe_media(source, runner=_runner_for(document, []))

    assert [stream.index for stream in result.audio_streams] == [0, 2]
    assert result.format_names == ("matroska", "webm")
    assert result.duration_ms == 12500


def test_probe_rejects_input_without_audio(tmp_path: Path) -> None:
    document = {
        "streams": [{"index": 0, "codec_type": "video", "codec_name": "h264"}],
        "format": {"duration": "1.0"},
    }

    with pytest.raises(NoAudioStreamError, match="No audio stream"):
        probe_media(tmp_path / "video.bin", runner=_runner_for(document, []))


@pytest.mark.parametrize("serialized", ["not-json", "[]", '{"format": {}}'])
def test_probe_rejects_malformed_output(tmp_path: Path, serialized: str) -> None:
    def runner(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(arguments, 0, serialized, "")

    with pytest.raises(MediaProbeError):
        probe_media(tmp_path / "bad.bin", runner=runner)


def test_probe_reports_nonzero_exit_without_exposing_stderr(tmp_path: Path) -> None:
    secret = "private-path-or-token"

    def runner(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(arguments, 1, "", secret)

    with pytest.raises(MediaProbeError) as raised:
        probe_media(tmp_path / "bad.bin", runner=runner)

    assert secret not in str(raised.value)


@pytest.mark.parametrize(
    ("disposition", "expected"),
    [({}, True), ({"attached_pic": 1}, False), ({"attached_pic": 0}, True)],
)
def test_video_provenance_excludes_embedded_cover_art(
    tmp_path: Path, disposition, expected
) -> None:
    document = {
        "streams": [
            {"index": 0, "codec_type": "video", "codec_name": "png", "disposition": disposition},
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "16000",
                "channels": 1,
            },
        ],
        "format": {"duration": "2"},
    }
    result = probe_media(tmp_path / "source.mp4", runner=_runner_for(document, []))
    assert result.has_video is expected
