"""Cloud timing/charge/consent boundaries without network, models or real credentials."""

import json
import time
import wave
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

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
            "data": {
                "endpoints": [
                    {"tag": "deepinfra/us", "pricing": {"prompt": "0.1"}},
                    {"tag": "groq", "pricing": {"prompt": "0.2"}},
                ]
            }
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


def test_automatic_guard_covers_all_tracks_instead_of_arbitrary_two_dollar_input(tmp_path):
    first = audio(tmp_path / "first.wav", 4)
    second = audio(tmp_path / "second.wav", 4)
    calls = []

    def transport(*args):
        calls.append(args)
        return response()

    session = CloudSpeechSession(
        SpeechConfig(cost_mode="estimated"),
        "fake-key",
        transport=transport,
        rate=Decimal("0.5"),
        expected_durations_ms=(4000, 4000),
    )
    session.transcribe(first, "pl", diarize=False)
    session.transcribe(second, "pl", diarize=False)
    assert len(calls) == 2
    assert Decimal(session.provenance["budget_usd"]) > 10
    assert session.provenance["cost_mode"] == "estimated"


def test_automatic_guard_refuses_excessive_workload_before_audio_upload(tmp_path):
    transport = Mock()
    session = CloudSpeechSession(
        SpeechConfig(cost_mode="estimated"),
        "fake-key",
        transport=transport,
        rate=Decimal("1"),
        expected_durations_ms=(3600000,),
    )
    path = audio(tmp_path / "first.wav")
    for _ in range(2):
        with pytest.raises(SpeechEngineError, match="internal safety ceiling"):
            session.transcribe(path, "pl", diarize=False)
    transport.assert_not_called()


def test_missing_shared_key_explains_enter_or_load_and_never_reads_audio_or_calls_provider(
    tmp_path,
):
    transport = Mock()
    session = CloudSpeechSession(SpeechConfig(), "", transport=transport)
    with pytest.raises(SpeechEngineError, match="enter it or load a previously saved key"):
        session.transcribe(tmp_path / "not-opened.wav", "pl", diarize=False)
    transport.assert_not_called()


def test_http_cloud_consent_is_single_use_bound_to_queue_and_revoked_on_restore(tmp_path):
    seen = []
    queue = GuiTranscriptionQueue(
        config=ApplicationConfig(),
        service=lambda path, **kw: (
            seen.append(path) or SimpleNamespace(result_path=tmp_path / "result.json")
        ),
    )
    try:
        first = queue.stage(
            tmp_path / "a.wav",
            tmp_path,
            planned_job_id="a",
            planned_result_path=str(tmp_path / "a_results.json"),
            speech=SpeechConfig(provider="openrouter"),
        )
        for allow, token in [(False, ""), (True, ""), (True, "made-up")]:
            with pytest.raises(ValueError, match="fresh cloud"):
                queue.start(allow_cloud=allow, cloud_consent_token=token)
        assert not seen and queue.jobs()[0].status == "staged"
        token = queue.authorize_cloud_start((first.job_id,))
        assert token not in queue.jobs()[0].model_dump_json()
        queue.revoke_cloud_consent()
        with pytest.raises(ValueError, match="fresh cloud"):
            queue.start(allow_cloud=True, cloud_consent_token=token)
        token = queue.authorize_cloud_start((first.job_id,))
        second = queue.stage(
            tmp_path / "b.wav",
            tmp_path,
            planned_job_id="b",
            planned_result_path=str(tmp_path / "b_results.json"),
            speech=SpeechConfig(provider="openrouter"),
        )
        with pytest.raises(ValueError, match="fresh cloud"):
            queue.start(allow_cloud=True, cloud_consent_token=token)
        assert not seen and all(job.status == "staged" for job in queue.jobs())
        token = queue.authorize_cloud_start((first.job_id, second.job_id))
        assert queue.start(allow_cloud=True, cloud_consent_token=token) == 2
        deadline = time.monotonic() + 2
        while len(seen) < 2 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert len(seen) == 2
        with pytest.raises(ValueError, match="changed"):
            queue.authorize_cloud_start((first.job_id,))
    finally:
        queue.close()


def test_cloud_retry_cannot_reuse_a_consumed_http_grant(tmp_path):
    calls = []

    def fail(path, **kw):
        calls.append(path)
        raise SpeechEngineError("synthetic failure")

    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=fail)
    try:
        job = queue.stage(
            tmp_path / "a.wav",
            tmp_path,
            planned_job_id="a",
            planned_result_path=str(tmp_path / "a_results.json"),
            speech=SpeechConfig(provider="openrouter"),
        )
        token = queue.authorize_cloud_start((job.job_id,))
        queue.start(allow_cloud=True, cloud_consent_token=token)
        deadline = time.monotonic() + 2
        while queue.jobs()[0].status != "failed" and time.monotonic() < deadline:
            time.sleep(0.005)
        retry = queue.retry(job.job_id)
        with pytest.raises(ValueError, match="fresh cloud"):
            queue.start(allow_cloud=True, cloud_consent_token=token)
        assert queue.jobs()[0].status == "staged" and len(calls) == 1
        fresh = queue.authorize_cloud_start((retry.job_id,))
        assert queue.start(allow_cloud=True, cloud_consent_token=fresh) == 1
    finally:
        queue.close()


@pytest.mark.parametrize("words", [None, []])
def test_empty_speech_without_word_array_is_not_a_capability_failure(words):
    payload = {"text": " \n", "language": "pol", "words": words, "segments": []}
    parsed = parse_transcript(payload, duration_ms=1000, offset_ms=2000, language="auto")
    assert parsed.aligned.language == "pl" and not parsed.aligned.segments
    with pytest.raises(SpeechEngineError, match="word timestamps"):
        parse_transcript(
            {**payload, "segments": [{"text": "Real speech"}]},
            duration_ms=1000,
            offset_ms=0,
            language="pl",
        )


def test_whisper_routes_and_prices_only_word_timing_providers(tmp_path):
    def prices(*args):
        return {
            "data": {
                "endpoints": [
                    {"tag": "deepinfra/us", "pricing": {"prompt": "0.00001"}},
                    {"tag": "groq", "pricing": {"prompt": "0.00002"}},
                    {"tag": "together", "pricing": {"prompt": "1"}},
                ]
            }
        }

    assert maximum_rate("openai/whisper-large-v3", prices) == Decimal("0.00002")
    seen = []

    def transport(url, headers, body, timeout):
        seen.append(json.loads(body))
        return response()

    session = CloudSpeechSession(
        SpeechConfig(model="openai/whisper-large-v3"),
        "fake-key",
        transport=transport,
        rate=Decimal("0.00001"),
    )
    session.transcribe(audio(tmp_path / "audio.wav"), "pl", diarize=False)
    assert seen[0]["provider"] == {"only": ["deepinfra", "groq"], "allow_fallbacks": False}
    assert seen[0]["response_format"] == "verbose_json"
    assert "word" in seen[0]["timestamp_granularities"]


def test_missing_timing_retains_only_noncontent_diagnostics_and_never_retries(tmp_path):
    from ewp_transcripts.engines.openrouter import CloudResponseError
    from ewp_transcripts.web_jobs import _backend_failure_detail

    transport = Mock(
        return_value={
            "text": "private words",
            "segments": [{"text": "private words"}],
            "words": [],
            "usage": {"cost": "0.001"},
        }
    )
    session = CloudSpeechSession(
        SpeechConfig(), "secret-test-key", transport=transport, rate=Decimal("0.00001")
    )
    with pytest.raises(CloudResponseError) as caught:
        session.transcribe(audio(tmp_path / "audio.wav"), "pl", diarize=False)
    assert transport.call_count == 1
    details = _backend_failure_detail(caught.value)
    assert json.loads(details["cloud_response"])["word_count"] == "0"
    ledger = (tmp_path / "cloud-asr-usage.json").read_text()
    assert json.loads(ledger)["calls"][0]["status"] == "invalid-response"
    assert "private words" not in ledger + json.dumps(details)
    assert "secret-test-key" not in ledger + json.dumps(details)
    with pytest.raises(SpeechEngineError, match="provider error response"):
        parse_transcript(
            {"error": {"code": 402}, "words": []}, duration_ms=1000, offset_ms=0, language="pl"
        )
