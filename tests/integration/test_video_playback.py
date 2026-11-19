"""Real video extraction, provenance and review playback without ML models."""

import json
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from ewp_transcripts.application import dry_run, inspect_input, transcribe_one
from ewp_transcripts.config import ApplicationConfig, DiarizationConfig, RuntimeConfig
from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.errors import MultipleAudioStreamsError, NoAudioStreamError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.engines import (
    AlignedSegment,
    AlignedTranscript,
    AlignedWord,
    EngineModelInfo,
    TranscriptionDraft,
    TranscriptionSegment,
)
from ewp_transcripts.web_media import GuiMediaController
from ewp_transcripts.web_workflows import GuiWorkflowController

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg required"
    ),
]


def video(path: Path, tracks: int = 1) -> None:
    arguments = [
        "ffmpeg",
        "-nostdin",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=blue:s=32x32:r=10:d=2",
    ]
    for number in range(tracks):
        arguments.extend(
            [
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={440 + number * 220}:sample_rate=16000:duration=2",
            ]
        )
    arguments.extend(["-map", "0:v:0"])
    for number in range(tracks):
        arguments.extend(["-map", f"{number + 1}:a:0"])
    subprocess.run(
        [*arguments, "-c:v", "mpeg4", "-c:a", "aac", str(path)],
        check=True,
        capture_output=True,
        timeout=30,
    )


class Asr:
    model_info = EngineModelInfo(role="asr", name="fake", revision="test")

    def transcribe(self, audio_path, *, language, batch_size):
        with wave.open(str(audio_path)) as audio:
            assert audio.getnchannels() == 1 and audio.getframerate() == 16000
        return TranscriptionDraft(
            language="pl",
            segments=(TranscriptionSegment(text="Test audio.", start_ms=100, end_ms=900),),
        )

    def close(self):
        pass


class Alignment:
    model_info = EngineModelInfo(role="alignment", name="fake", revision="test")

    def align(self, audio_path, transcription, *, language):
        return AlignedTranscript(
            language="pl",
            segments=(
                AlignedSegment(
                    text="Test audio.",
                    start_ms=100,
                    end_ms=900,
                    words=(
                        AlignedWord(text="Test", start_ms=100, end_ms=400),
                        AlignedWord(text="audio.", start_ms=400, end_ms=900),
                    ),
                ),
            ),
        )

    def close(self):
        pass


@pytest.mark.parametrize("observer_fails", [False, True])
def test_video_through_discovery_plan_pipeline_and_private_playback(
    tmp_path: Path, observer_fails
) -> None:
    source = tmp_path / "s0e01.mp4"
    video(source)
    digest = sha256_file(source)
    config = ApplicationConfig(
        diarization=DiarizationConfig(speaker_count=1),
        runtime=RuntimeConfig(work_root=tmp_path / "work"),
    )
    inspection = inspect_input(tmp_path, config=config)
    assert [file.filename for file in inspection.discovery.files] == [source.name]
    inspected = inspection.episodes[0].sources[0]
    assert inspected.media_type == "video" and inspected.stream.index == 1
    output = tmp_path / "output"
    assert len(dry_run(source, config=config, output_directory=output).jobs) == 1
    events = []

    def observe(event):
        events.append(event)
        if observer_fails:
            raise RuntimeError("observability failure")

    outcome = transcribe_one(
        source,
        progress=observe,
        config=config,
        output_directory=output,
        asr_factory=lambda _: Asr(),
        alignment_factory=lambda _: Alignment(),
    )
    assert [event.phase for event in events if event.state == "completed"] == [
        "inspect",
        "plan",
        "prepare_audio",
        "transcribe",
        "align",
        "normalize",
        "publish",
        "export",
        "cleanup",
    ]
    assert next(event for event in events if event.state == "planned").media_duration_ms >= 2000
    base = load_canonical_result(outcome.result_path)
    assert base.sources[0].media_type == "video"
    assert base.sources[0].normalized_path == str(source)
    assert base.sources[0].sha256 == digest
    assert base.sources[0].stream_index == 1
    paths = GuiWorkflowController()
    media = GuiMediaController(resolve_path=paths.resolve_allowed_path)
    try:
        preview = media.prepare(str(outcome.result_path), "source_001")
        with media.open(preview["url"].rsplit("/", 1)[1]) as handle, wave.open(handle) as audio:
            assert audio.getframerate() == 16000
            assert audio.getnframes() >= 32000
    finally:
        media.close()
    assert sha256_file(source) == digest
    assert not list(output.rglob("*.wav"))
    assert json.loads(outcome.result_path.read_text())["status"] == "completed"


@pytest.mark.parametrize(
    ("tracks", "exception"), [(0, NoAudioStreamError), (2, MultipleAudioStreamsError)]
)
def test_video_without_unique_audio_has_actionable_error(tmp_path: Path, tracks, exception) -> None:
    source = tmp_path / "video.mp4"
    video(source, tracks)
    with pytest.raises(exception) as error:
        inspect_input(source, config=ApplicationConfig())
    assert "audio" in str(error.value)
    assert (
        "Choose a recording" in str(error.value)
        if tracks == 0
        else "Export the intended" in str(error.value)
    )


def test_shared_timeline_mix_contains_both_alternating_speakers(tmp_path: Path) -> None:
    import math
    import struct

    from ewp_transcripts.web_reviews import GuiReviewController

    template = Path(__file__).resolve().parents[2] / "examples/results.example.json"
    document = json.loads(template.read_text())
    for index, source in enumerate(document["sources"]):
        path = tmp_path / f"speaker-{index}.wav"
        frames = [
            int(14000 * math.sin(2 * math.pi * (440 + 220 * index) * n / 16000))
            if (1.24 <= n / 16000 < 3.9 if index == 0 else 4.32 <= n / 16000 < 6.32)
            else 0
            for n in range(8 * 16000)
        ]
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(16000)
            handle.writeframes(struct.pack(f"<{len(frames)}h", *frames))
        source.update(
            normalized_path=str(path),
            input_path=str(path),
            filename=path.name,
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
            duration_ms=8000,
        )
    result = tmp_path / "mixed_results.json"
    result.write_text(json.dumps(document))
    paths = GuiWorkflowController()
    media = GuiMediaController(resolve_path=paths.resolve_allowed_path)
    try:
        url = media.prepare(str(result), "mix")["url"]
        with media.open(url.rsplit("/", 1)[1]) as handle, wave.open(handle) as audio:
            assert audio.getnframes() == 8 * 16000
            for second in (2, 5):
                audio.setpos(second * 16000)
                samples = struct.unpack("<1600h", audio.readframes(1600))
                assert math.sqrt(sum(value * value for value in samples) / len(samples)) > 2000
    finally:
        media.close()
    review = GuiReviewController(
        config=ApplicationConfig(), resolve_path=paths.resolve_allowed_path
    ).prepare(str(result), str(tmp_path / "reviews"))
    assert review["anchors"][0]["block_sources"] == [["speaker-0.wav"], ["speaker-1.wav"]]
