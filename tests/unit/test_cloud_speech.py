"""Cloud timing/charge/consent boundaries without network, models or real credentials."""

import json
import time
import wave
from decimal import Decimal
from types import SimpleNamespace

import pytest

from ewp_transcripts.config import ApplicationConfig, SpeechConfig
from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines.openrouter import CloudSpeechSession, maximum_rate, parse_transcript
from ewp_transcripts.web_jobs import GuiTranscriptionQueue


def audio(path, seconds=1):
    with wave.open(str(path), "wb") as out:
        out.setparams((1, 2, 16000, 0, "NONE", ""))
        out.writeframes(b"\0\0" * 16000 * seconds)
    return path


def response(language="pl"):
    return {
        "language": language,
        "words": [{"word": "Test.", "start": 0.1, "end": 0.8}],
        "usage": {"cost": "0.001"},
    }


@pytest.mark.parametrize("language", ["pl", "en"])
def test_provider_times_are_preserved_with_chunk_offset(language):
    payload = response(language)
    payload["words"][0]["speaker_id"] = "speaker-1"
    result = parse_transcript(payload, duration_ms=1000, offset_ms=15000, language="auto")
    assert result.aligned.language == language
    assert result.aligned.segments[0].words[0].start_ms == 15100
    assert result.diarization.turns[0].speaker_label == "speaker-1"


@pytest.mark.parametrize(
    "payload", [{}, {"words": []}, {"words": [{"word": "x", "start": 2, "end": 1}]}]
)
def test_rejects_missing_or_invalid_word_alignment(payload):
    with pytest.raises(SpeechEngineError):
        parse_transcript(payload, duration_ms=1000, offset_ms=0, language="pl")


def test_cost_guard_no_upload_and_uncertain_call_is_not_retried(tmp_path):
    source = audio(tmp_path / "work.wav")
    calls = []

    def transport(*args):
        calls.append(args)
        raise SpeechEngineError("sanitized upstream failure")

    session = CloudSpeechSession(
        SpeechConfig(max_cost_usd=0.01), "fake-key", transport=transport, rate=Decimal("0.01")
    )
    with pytest.raises(SpeechEngineError, match="budget"):
        session.transcribe(source, "pl", diarize=False)
    assert calls == []
    session = CloudSpeechSession(
        SpeechConfig(), "fake-key", transport=transport, rate=Decimal("0.001")
    )
    with pytest.raises(SpeechEngineError, match="upstream"):
        session.transcribe(source, "pl", diarize=False)
    assert len(calls) == 1
    ledger = (tmp_path / "cloud-asr-usage.json").read_text()
    assert "fake-key" not in ledger and "Test." not in ledger
    assert json.loads(ledger)["calls"][0]["status"] == "uncertain"


def test_chunking_accounts_usage_and_carries_real_offsets(tmp_path):
    source = audio(tmp_path / "work.wav", 16)
    calls = []

    def transport(url, headers, body, timeout):
        calls.append(json.loads(body))
        return response("en")

    session = CloudSpeechSession(
        SpeechConfig(chunk_seconds=15), "fake-key", transport=transport, rate=Decimal("0.0001")
    )
    result = session.transcribe(source, "en", diarize=False)
    assert len(calls) == 2
    assert result.aligned.segments[1].start_ms == 15100
    assert session.provenance["accounted_cost_usd"] == "0.0020"
    assert calls[0]["input_audio"]["format"] == "wav"


def test_diarization_requires_capable_model_and_labels(tmp_path):
    source = audio(tmp_path / "work.wav")

    def transport(*args):
        return response()

    session = CloudSpeechSession(
        SpeechConfig(), "fake-key", transport=transport, rate=Decimal("0.0001")
    )
    with pytest.raises(SpeechEngineError, match="separate speaker tracks"):
        session.transcribe(source, "pl", diarize=True)
    session = CloudSpeechSession(
        SpeechConfig(model="elevenlabs/scribe-v2"),
        "fake-key",
        transport=transport,
        rate=Decimal("0.0001"),
    )
    with pytest.raises(SpeechEngineError, match="speaker labels"):
        session.transcribe(source, "pl", diarize=True)


def test_pricing_uses_worst_endpoint_and_explicit_duration_unit():
    def transport(*args):
        return {
            "data": {"endpoints": [{"pricing": {"prompt": "0.1"}}, {"pricing": {"prompt": "0.2"}}]}
        }

    assert maximum_rate("microsoft/mai-transcribe-2", transport) == Decimal("0.2") / 3600
    assert maximum_rate("openai/whisper-large-v3", transport) == Decimal("0.2")


def test_cloud_start_requires_new_consent_and_uses_shared_key_provider(tmp_path):
    seen = []

    def service(path, **kwargs):
        seen.append(kwargs)
        return SimpleNamespace(result_path=tmp_path / "results.json")

    queue = GuiTranscriptionQueue(
        config=ApplicationConfig(), service=service, api_key_provider=lambda: "fake-key"
    )
    try:
        job = queue.stage(
            tmp_path / "input.wav",
            tmp_path,
            planned_job_id="episode",
            planned_result_path=str(tmp_path / "results.json"),
            speech=SpeechConfig(provider="openrouter"),
        )
        with pytest.raises(ValueError, match="Confirm sending"):
            queue.start()
        assert queue.jobs()[0].status == "staged" and not seen
        assert queue.start(allow_cloud=True) == 1
        deadline = time.monotonic() + 2
        while queue.jobs()[0].status not in {"completed", "failed"} and time.monotonic() < deadline:
            time.sleep(0.01)
        assert queue.jobs()[0].status == "completed"
        assert seen[0]["api_key"] == "fake-key" and seen[0]["allow_cloud"] is True
        assert seen[0]["config"].speech == job.speech
        assert "fake-key" not in job.model_dump_json()
    finally:
        queue.close()


def test_silent_chunk_and_iso6393_language_codes_are_supported():
    silent = parse_transcript(
        {"words": [], "text": ""}, duration_ms=1000, offset_ms=0, language="pl"
    )
    assert silent.aligned.segments == ()
    assert (
        parse_transcript(
            response("pol"), duration_ms=1000, offset_ms=0, language="auto"
        ).aligned.language
        == "pl"
    )
    assert (
        parse_transcript(
            response("eng"), duration_ms=1000, offset_ms=0, language="auto"
        ).aligned.language
        == "en"
    )


def test_cloud_plan_identity_includes_provider_model_and_cost_guard(tmp_path):
    from pydantic import BaseModel

    from ewp_transcripts.web_workflows import GuiWorkflowController

    class Plan(BaseModel):
        output_directory: str

    source = tmp_path / "source.wav"
    source.write_bytes(b"fake")
    controller = GuiWorkflowController(
        dry_run_service=lambda path, **kwargs: Plan(output_directory=str(tmp_path))
    )
    speech = SpeechConfig(provider="openrouter")
    operation = controller.run(
        "dry-run",
        {
            "path": str(source),
            "output_directory": str(tmp_path),
            "speech": speech.model_dump(mode="json"),
        },
    )
    assert operation.status == "completed"
    assert controller.completed_plan(source, tmp_path, speech=speech)
    assert controller.completed_plan(source, tmp_path) is None
    assert (
        controller.completed_plan(
            source, tmp_path, speech=speech.model_copy(update={"max_cost_usd": 1})
        )
        is None
    )
    assert (
        controller.completed_plan(
            source, tmp_path, speech=speech.model_copy(update={"model": "elevenlabs/scribe-v2"})
        )
        is None
    )


def test_saved_cloud_job_preserves_model_id_and_streams_without_authorization(tmp_path):
    from ewp_transcripts.domain.revision import sha256_file
    from ewp_transcripts.web_profiles import _portable_workspace
    from ewp_transcripts.web_workflows import GuiWorkflowController
    from ewp_transcripts.web_workspaces import GuiWorkspaceController

    source = tmp_path / "source.wav"
    source.write_bytes(b"fake")
    service = GuiWorkspaceController(
        state_directory=tmp_path / "state",
        resolve_path=GuiWorkflowController().resolve_allowed_path,
    )
    staged = {
        "input_path": str(source),
        "output_directory": str(tmp_path),
        "planned_job_id": "one",
        "planned_result_path": str(tmp_path / "one_results.json"),
        "source_sha256": sha256_file(source),
        "language": "pl",
        "speaker_count": 1,
        "recording_id": "one",
        "selected_streams": {str(source): 2},
        "speech": SpeechConfig(provider="openrouter", model="elevenlabs/scribe-v2").model_dump(
            mode="json"
        ),
    }
    saved = service.save(
        name="Cloud draft", current_step="workspace-heading", fields={}, staged_jobs=[staged]
    )
    _portable_workspace(saved)
    assert saved.staged_jobs[0]["speech"]["provider"] == "openrouter"
    assert saved.staged_jobs[0]["recording_id"] == "one"
    assert "cloud_confirmed" not in saved.model_dump_json()
    with pytest.raises(ValueError):
        service.save(
            name="Bad consent",
            current_step="workspace-heading",
            fields={"cloud-asr-confirmed": True},
        )


def test_per_stream_provenance_counts_each_paid_call_once(tmp_path):
    from ewp_transcripts.engines.openrouter import CloudAsr

    session = CloudSpeechSession(
        SpeechConfig(), "fake-key", rate=Decimal("0.0001"), transport=lambda *args: response()
    )
    first = CloudAsr(session, False)
    first.transcribe(audio(tmp_path / "one.wav"), language="pl", batch_size=1)
    second = CloudAsr(session, False)
    second.transcribe(audio(tmp_path / "two.wav"), language="pl", batch_size=1)
    assert len(first.provenance["calls"]) == len(second.provenance["calls"]) == 1
    assert first.provenance["accounting_scope"] == second.provenance["accounting_scope"] == "stream"
    assert Decimal(first.provenance["accounted_cost_usd"]) + Decimal(
        second.provenance["accounted_cost_usd"]
    ) == Decimal(session.provenance["accounted_cost_usd"])
