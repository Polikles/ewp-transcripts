"""Read-only cloud readiness, pricing units and bounded local duration estimates."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ewp_transcripts.web_speech import ASR_MODELS, GuiSpeechController


def source(channels=1):
    return {"duration_ms": 60000, "streams": [{"index": 1, "channels": channels}]}


def test_refresh_prices_without_key_or_audio_upload_and_normalizes_hourly_mai():
    calls = []

    def transport(url, headers, body, timeout):
        calls.append((url, headers, body))
        assert headers == {} and body is None
        if url.endswith("?output_modalities=transcription"):
            return {"data": [{"id": model} for model in ASR_MODELS]}
        rate = "0.36" if "microsoft/" in url else "0.0001"
        return {"data": {"endpoints": [{"tag": "deepinfra/us", "pricing": {"prompt": rate}}]}}

    inputs = SimpleNamespace(probe=Mock(return_value=source()))
    payload = GuiSpeechController(inputs, transport).refresh(
        [{"path": "one.wav", "speaker_count": 1}]
    )
    assert payload["recordings"] == 1 and payload["audio_seconds"] == 60
    assert payload["billable_seconds_minimum"] == 61
    assert len(calls) == 5 and all("/audio/transcriptions" not in call[0] for call in calls)
    for model in payload["models"]:
        assert float(model["minimum_usd_per_hour"]) == pytest.approx(0.36)
        assert float(model["estimated_minimum_usd"]) == pytest.approx(0.0061)
        assert model["status"] == "ok" and "_low" not in model


def test_unavailable_model_and_missing_price_are_explicit():
    def transport(url, *args):
        if "?output_modalities" in url:
            return {"data": [{"id": ASR_MODELS[0]}, {"id": ASR_MODELS[1]}]}
        return {"data": {"endpoints": []}}

    result = GuiSpeechController(SimpleNamespace(), transport).refresh([])
    assert result["recordings"] == 0
    assert [model["status"] for model in result["models"]] == [
        "price-unavailable",
        "price-unavailable",
        "unavailable",
        "unavailable",
    ]


def test_shared_key_check_is_only_authenticated_get_and_never_returns_secret():
    transport = Mock(return_value={"data": {"label": "private account info"}})
    controller = GuiSpeechController(SimpleNamespace(), transport)
    with pytest.raises(ValueError, match="shared OpenRouter key"):
        controller.check_key("")
    transport.assert_not_called()
    result = controller.check_key("fake-test-key")
    assert result == {"status": "ok", "provider": "openrouter"}
    url, headers, body, timeout = transport.call_args.args
    assert url.endswith("/key") and headers == {"Authorization": "Bearer fake-test-key"}
    assert body is None
    transport.return_value = {"data": None}
    with pytest.raises(ValueError, match="invalid response"):
        controller.check_key("fake-test-key")


def test_group_and_stereo_estimates_include_all_sources_and_split_range():
    probe = Mock(return_value=source(2))
    controller = GuiSpeechController(SimpleNamespace(probe=probe))
    seconds, minimum, maximum, count = controller._durations(
        [{"group_paths": ["a.wav", "b.wav"], "speaker_count": 2}]
    )
    assert seconds == 120 and minimum == 122 and maximum == 244 and count == 1
    assert probe.call_count == 2


def test_multistream_estimate_requires_choice_before_network():
    media = source()
    media["streams"].append({"index": 2, "channels": 1})
    transport = Mock()
    controller = GuiSpeechController(SimpleNamespace(probe=Mock(return_value=media)), transport)
    with pytest.raises(ValueError, match="Choose an audio stream"):
        controller.refresh([{"path": "a.mp4"}])
    transport.assert_not_called()
    assert controller._durations([{"path": "a.mp4", "selected_streams": {"a.mp4": 2}}])[0] == 60


@pytest.mark.parametrize(
    "items", [None, [None], [{}], [{"path": "a", "selected_streams": {"b": 0}}], [{}] * 51]
)
def test_malformed_workload_rejected_without_network(items):
    transport = Mock()
    with pytest.raises(ValueError):
        GuiSpeechController(SimpleNamespace(), transport).refresh(items)
    transport.assert_not_called()
