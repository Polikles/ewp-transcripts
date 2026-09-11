import json
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self

import pytest

from ewp_transcripts.application import apply_correction
from ewp_transcripts.config import ApplicationConfig, RuntimeConfig
from ewp_transcripts.correction import DeterministicMockCorrectionProvider
from ewp_transcripts.web_corrections import (
    GuiCorrectionController,
    GuiCorrectionError,
    _preflight_provider,
)
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/results.example.json"


def mock_runner(result_path: Path, **kwargs: Any) -> Any:
    return apply_correction(
        result_path,
        config=kwargs["config"],
        provider=DeterministicMockCorrectionProvider(),
        output_directory=kwargs["output_directory"],
        resume_directory=kwargs["resume_directory"],
        dictionary=kwargs["dictionary"],
        dictionary_sha256=kwargs["dictionary_sha256"],
        dictionary_project_id=kwargs["dictionary_project_id"],
    )


def controller(tmp_path: Path) -> GuiCorrectionController:
    paths = GuiWorkflowController((tmp_path.resolve(),))
    return GuiCorrectionController(
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        resolve_path=paths.resolve_allowed_path,
        runner=mock_runner,
        preflight=lambda provider, config, environment: None,
    )


def test_gui_correction_publishes_explicit_non_final_candidate(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())

    outcome = controller(tmp_path).generate(
        result=str(result),
        output_directory=str(tmp_path / "candidates"),
        resume_directory=str(tmp_path / "state"),
        provider_name="openrouter",
        model="google/gemini-2.5-flash",
        endpoint="https://openrouter.ai/api/v1",
        allow_remote_endpoint=False,
        allow_cloud=True,
        reasoning_max_tokens=0,
        dictionary_path="",
        project_id="",
        confirmed=True,
    )

    assert outcome["final"] is False
    assert outcome["provider"] == "openrouter"
    assert outcome["model"] == "google/gemini-2.5-flash"
    assert Path(outcome["candidate_path"]).is_file()


def test_gui_correction_requires_consent_and_cloud_opt_in(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    request = {
        "result": str(result),
        "output_directory": str(tmp_path / "candidates"),
        "resume_directory": str(tmp_path / "state"),
        "provider_name": "openrouter",
        "model": "google/gemini-2.5-flash",
        "endpoint": "https://openrouter.ai/api/v1",
        "allow_remote_endpoint": False,
        "allow_cloud": True,
        "reasoning_max_tokens": 0,
        "dictionary_path": "",
        "project_id": "",
    }

    with pytest.raises(GuiCorrectionError) as missing_consent:
        service.generate(**request, confirmed=False)
    assert missing_consent.value.code == "GUI_CORRECTION_CONFIRMATION_REQUIRED"

    with pytest.raises(GuiCorrectionError) as missing_cloud:
        service.generate(**{**request, "allow_cloud": False}, confirmed=True)
    assert missing_cloud.value.code == "GUI_CORRECTION_CLOUD_OPT_IN_REQUIRED"


def test_gui_correction_rejects_audio_instead_of_a_canonical_result(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"not a canonical result")

    with pytest.raises(GuiCorrectionError) as invalid:
        controller(tmp_path).generate(
            result=str(media),
            output_directory=str(tmp_path / "candidates"),
            resume_directory=str(tmp_path / "state"),
            provider_name="openrouter",
            model="google/gemini-2.5-flash",
            endpoint="https://openrouter.ai/api/v1",
            allow_remote_endpoint=False,
            allow_cloud=True,
            reasoning_max_tokens=0,
            dictionary_path="",
            project_id="",
            confirmed=True,
        )

    assert invalid.value.code == "GUI_CORRECTION_RESULT_INVALID"
    assert "not an audio" in str(invalid.value)


def test_gui_correction_passes_session_key_only_to_provider_boundary(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    seen: list[object] = []
    paths = GuiWorkflowController((tmp_path.resolve(),))
    service = GuiCorrectionController(
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        resolve_path=paths.resolve_allowed_path,
        runner=mock_runner,
        preflight=lambda provider, config, environment: seen.append(environment),
    )

    service.generate(
        result=str(result),
        output_directory=str(tmp_path / "candidates"),
        resume_directory=str(tmp_path / "state"),
        provider_name="openrouter",
        model="google/gemini-2.5-flash",
        endpoint="https://openrouter.ai/api/v1",
        allow_remote_endpoint=False,
        allow_cloud=True,
        reasoning_max_tokens=0,
        dictionary_path="",
        project_id="",
        confirmed=True,
        api_key="session-secret",
    )

    assert seen == [{"OPENROUTER_API_KEY": "session-secret"}]


def test_gui_provider_check_sends_no_transcript_and_reports_exact_model(tmp_path: Path) -> None:
    seen: list[object] = []
    paths = GuiWorkflowController((tmp_path.resolve(),))
    service = GuiCorrectionController(
        config=ApplicationConfig(),
        resolve_path=paths.resolve_allowed_path,
        preflight=lambda provider, config, environment: seen.append(environment),
    )

    result = service.check_provider(
        provider_name="openrouter",
        model="google/gemini-2.5-flash",
        endpoint="https://openrouter.ai/api/v1",
        allow_remote_endpoint=False,
        reasoning_max_tokens=0,
        api_key="session-secret",
    )

    assert result == {
        "status": "ok",
        "provider": "openrouter",
        "model": "google/gemini-2.5-flash",
        "endpoint_kind": "cloud",
    }
    assert seen == [{"OPENROUTER_API_KEY": "session-secret"}]


def test_gui_model_pricing_is_bounded_to_requested_presets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = GuiWorkflowController((tmp_path.resolve(),))
    service = GuiCorrectionController(
        config=ApplicationConfig(), resolve_path=paths.resolve_allowed_path
    )
    monkeypatch.setattr(
        "ewp_transcripts.web_corrections._read_provider_document",
        lambda url, headers: {
            "data": [
                {
                    "id": "google/gemini-2.5-flash",
                    "name": "Gemini 2.5 Flash",
                    "pricing": {"prompt": "0.0000003", "completion": "0.0000025"},
                },
                {"id": "unrequested/model", "pricing": {"prompt": "1"}},
            ]
        },
    )

    result = service.model_pricing(
        endpoint="https://openrouter.ai/api/v1",
        model_ids=["google/gemini-2.5-flash", "missing/model"],
    )

    assert result["items"] == [
        {
            "id": "google/gemini-2.5-flash",
            "available": True,
            "name": "Gemini 2.5 Flash",
            "input": {"usd_per_million": 0.3, "tokens_per_usd": 3_333_333},
            "output": {"usd_per_million": 2.5, "tokens_per_usd": 400_000},
        },
        {
            "id": "missing/model",
            "available": False,
            "name": None,
            "input": None,
            "output": None,
        },
    ]


def test_gui_correction_preflight_rejects_missing_cloud_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    provider = SimpleNamespace(
        provider_id="openrouter",
        endpoint_identity="https://openrouter.ai/api/v1",
        model_id="google/gemini-2.5-flash",
    )

    with pytest.raises(GuiCorrectionError) as missing:
        _preflight_provider(provider, ApplicationConfig())

    assert missing.value.code == "GUI_CORRECTION_CREDENTIAL_MISSING"


def test_gui_correction_preflight_distinguishes_rejected_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = SimpleNamespace(
        provider_id="openrouter",
        endpoint_identity="https://openrouter.ai/api/v1",
        model_id="google/gemini-2.5-flash",
    )
    rejected = urllib.error.HTTPError("https://openrouter.ai/api/v1/models", 401, "", {}, None)

    def reject(*args: object, **kwargs: object) -> None:
        raise rejected

    monkeypatch.setattr("ewp_transcripts.web_corrections.urllib.request.urlopen", reject)

    with pytest.raises(GuiCorrectionError) as error:
        _preflight_provider(provider, ApplicationConfig(), {"OPENROUTER_API_KEY": "bad"})

    assert error.value.code == "GUI_CORRECTION_CREDENTIAL_REJECTED"


def test_gui_correction_preflight_validates_key_before_exact_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = SimpleNamespace(
        provider_id="openrouter",
        endpoint_identity="https://openrouter.ai/api/v1",
        model_id="google/gemini-2.5-flash",
    )
    requested: list[str] = []

    class Response:
        def __init__(self, document: dict[str, object]) -> None:
            self.payload = json.dumps(document).encode()

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self, limit: int) -> bytes:
            return self.payload

    def respond(request: Any, **kwargs: object) -> Response:
        url = request.full_url
        requested.append(url)
        if url.endswith("/key"):
            return Response({"data": {"label": "configured"}})
        return Response({"data": [{"id": "google/gemini-2.5-flash"}]})

    monkeypatch.setattr("ewp_transcripts.web_corrections.urllib.request.urlopen", respond)

    _preflight_provider(provider, ApplicationConfig(), {"OPENROUTER_API_KEY": "valid"})

    assert requested == [
        "https://openrouter.ai/api/v1/key",
        "https://openrouter.ai/api/v1/models",
    ]


def test_gui_correction_derives_project_id_from_dictionary(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    source_dictionary = (
        ROOT / "dictionaries/ethics-in-the-loop/correction/pl/ethics-in-the-loop-pl-v1.json"
    )
    dictionary = tmp_path / source_dictionary.name
    dictionary.write_bytes(source_dictionary.read_bytes())

    outcome = controller(tmp_path).generate(
        result=str(result),
        output_directory=str(tmp_path / "candidates"),
        resume_directory=str(tmp_path / "state"),
        provider_name="openrouter",
        model="google/gemini-2.5-flash",
        endpoint="https://openrouter.ai/api/v1",
        allow_remote_endpoint=False,
        allow_cloud=True,
        reasoning_max_tokens=0,
        dictionary_path=str(dictionary),
        project_id="",
        confirmed=True,
    )

    assert outcome["dictionary"]["project_id"] == "ethics-in-the-loop"
