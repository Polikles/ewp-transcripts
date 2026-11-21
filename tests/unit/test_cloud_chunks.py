"""Large requests, timed overlap ownership and request-local speaker continuity."""

import base64
import io
import json
import wave
from decimal import Decimal

import pytest

from ewp_transcripts.cancellation import CancellationToken, TranscriptionCancelled
from ewp_transcripts.config import SpeechConfig
from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines import cloud_chunks
from ewp_transcripts.engines.cloud_chunks import MixedChunkMerger, plan_audio_chunks
from ewp_transcripts.engines.openrouter import CloudAsr, CloudSpeechSession, parse_transcript


def wav(path, seconds):
    with wave.open(str(path), "wb") as out:
        out.setparams((1, 2, 16000, 0, "NONE", ""))
        out.writeframes(b"\0\0" * 16000 * seconds)
    return path


def transport_for(session_holder, calls, *, token=None):
    def request(url, headers, body, timeout):
        calls.append(body)
        payload = json.loads(body)
        with wave.open(io.BytesIO(base64.b64decode(payload["input_audio"]["data"]))) as audio:
            duration = audio.getnframes() / audio.getframerate()
        offset = session_holder[0].calls[-1]["offset_ms"] / 1000
        words = [
            {
                "word": f"w{int(offset + second)}",
                "start": second + 0.1,
                "end": second + 0.7,
                "speaker_id": str((int(offset + second) // 3 % 2) ^ (len(calls) % 2)),
            }
            for second in range(int(duration))
        ]
        if token is not None:
            token.request()
        return {
            "language": "pl",
            "text": " ".join(x["word"] for x in words),
            "words": words,
            "usage": {"cost": "0.0001"},
        }

    return request


def test_mixed_input_above_24mb_splits_merges_and_remaps_permuted_speakers(tmp_path):
    source = wav(tmp_path / "large.wav", 800)
    assert source.stat().st_size > 24_000_000
    calls = []
    holder = []
    session = CloudSpeechSession(
        SpeechConfig(model="elevenlabs/scribe-v2", chunk_seconds=15),
        "fake-key",
        transport=transport_for(holder, calls),
        rate=Decimal("0.000001"),
    )
    holder.append(session)
    result = session.transcribe(source, "pl", diarize=True)
    assert len(calls) > 1 and all(len(body) <= 24_000_000 for body in calls)
    assert [segment.text for segment in result.aligned.segments] == [f"w{i}" for i in range(800)]
    assert [segment.start_ms for segment in result.aligned.segments] == [
        i * 1000 + 100 for i in range(800)
    ]
    assert len({turn.speaker_label for turn in result.diarization.turns}) == 2
    assert all(
        a.speaker_label == b.speaker_label
        for a, b in zip(result.diarization.turns, result.diarization.turns[6:], strict=False)
    )
    assert not session.speaker_notes
    assert len(session.calls) == len(calls)
    assert all(
        record["request_bytes"] == len(body)
        for record, body in zip(session.calls, calls, strict=True)
    )


def test_complete_json_size_limit_includes_base64_and_headers(tmp_path, monkeypatch):
    monkeypatch.setattr(cloud_chunks, "MAX_REQUEST_BYTES", 64_000)
    calls = []

    def request(url, headers, body, timeout):
        calls.append(body)
        return {
            "language": "pl",
            "words": [{"word": "Test.", "start": 0.001, "end": 0.002}],
            "usage": {"cost": "0.0001"},
        }

    session = CloudSpeechSession(
        SpeechConfig(chunk_seconds=300), "fake-key", transport=request, rate=Decimal("0.000001")
    )
    session.transcribe(wav(tmp_path / "input.wav", 4), "pl", diarize=False)
    assert len(calls) > 1 and all(len(body) <= 64_000 for body in calls)


def parsed(words):
    return parse_transcript(
        {
            "language": "pl",
            "words": [
                {"word": text, "start": start, "end": end, "speaker_id": speaker}
                for text, start, end, speaker in words
            ],
        },
        duration_ms=40000,
        offset_ms=0,
        language="pl",
    )


@pytest.mark.parametrize("previous_time,current_time", [(14.7, 14.9), (14.9, 14.7)])
def test_cut_jitter_keeps_one_shared_word_and_preserves_real_repeated_words(
    previous_time, current_time
):
    merger = MixedChunkMerger()
    first = parsed(
        [
            ("before", 11, 11.3, "a"),
            ("cut", previous_time, previous_time + 0.4, "a"),
            ("echo", 16, 16.2, "a"),
            ("echo", 16.4, 16.6, "a"),
            ("anchor", 17, 17.3, "a"),
        ]
    )
    second = parsed(
        [
            ("before", 11, 11.3, "swapped"),
            ("cut", current_time, current_time + 0.4, "swapped"),
            ("echo", 16, 16.2, "swapped"),
            ("echo", 16.4, 16.6, "swapped"),
            ("anchor", 17, 17.3, "swapped"),
            ("after", 22, 22.3, "swapped"),
        ]
    )
    merger.add(
        first.aligned,
        first.diarization,
        core_start_ms=0,
        core_end_ms=15000,
        final=False,
        chunk_index=1,
    )
    merger.add(
        second.aligned,
        second.diarization,
        core_start_ms=15000,
        core_end_ms=30000,
        final=True,
        chunk_index=2,
    )
    segments, turns = merger.result()
    assert [s.text for s in segments] == ["before", "cut", "echo", "echo", "anchor", "after"]
    assert len({turn.speaker_label for turn in turns}) == 1
    assert not merger.notes


def test_unmatched_speaker_ids_are_distinct_with_review_warning(tmp_path):
    calls = []

    def request(url, headers, body, timeout):
        calls.append(body)
        # No shared speech in the overlap; do not silently equate request-local "0".
        start = 1 if len(calls) == 1 else 7
        return {
            "language": "pl",
            "words": [{"word": "new", "start": start, "end": start + 0.2, "speaker_id": "0"}],
        }

    session = CloudSpeechSession(
        SpeechConfig(model="elevenlabs/scribe-v2", chunk_seconds=15),
        "fake-key",
        transport=request,
        rate=Decimal("0.000001"),
    )
    engine = CloudAsr(session, True)
    engine.transcribe(wav(tmp_path / "gap.wav", 30), language="pl", batch_size=1)
    assert len(engine.warnings) == 1
    assert engine.warnings[0].code == "CLOUD_SPEAKER_CONTINUITY_UNCERTAIN"
    assert (
        len({turn.speaker_label for turn in session.cached(tmp_path / "gap.wav").diarization.turns})
        == 2
    )


def test_preflight_includes_overlap_and_rounding_before_any_upload(tmp_path):
    chunks = plan_audio_chunks(30 * 16000, rate=16000, frame_bytes=2, seconds=15, diarize=True)
    assert sum(chunk.end - chunk.start for chunk in chunks) == 40 * 16000
    calls = []
    session = CloudSpeechSession(
        SpeechConfig(model="elevenlabs/scribe-v2", chunk_seconds=15, max_cost_usd=0.07),
        "fake-key",
        transport=lambda *args: calls.append(args),
        rate=Decimal(".001"),
    )
    with pytest.raises(SpeechEngineError, match="budget"):
        session.transcribe(wav(tmp_path / "budget.wav", 30), "pl", diarize=True)
    assert calls == []


def test_cancellation_stops_between_cloud_chunks_without_retry(tmp_path):
    token = CancellationToken()
    calls = []
    holder = []
    session = CloudSpeechSession(
        SpeechConfig(model="elevenlabs/scribe-v2", chunk_seconds=15),
        "fake-key",
        cancellation=token,
        transport=transport_for(holder, calls, token=token),
        rate=Decimal("0.000001"),
    )
    holder.append(session)
    with pytest.raises(TranscriptionCancelled):
        session.transcribe(wav(tmp_path / "cancel.wav", 30), "pl", diarize=True)
    assert len(calls) == 1
