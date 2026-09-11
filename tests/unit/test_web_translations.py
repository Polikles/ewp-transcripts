from pathlib import Path
from typing import Any

import pytest

from ewp_transcripts.application import apply_automated_translation
from ewp_transcripts.automated_translation import DeterministicMockTranslationProvider
from ewp_transcripts.config import ApplicationConfig, RuntimeConfig
from ewp_transcripts.web_translations import GuiTranslationController, GuiTranslationError
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/results.example.json"


def mock_runner(result_path: Path, **kwargs: Any) -> Any:
    assert kwargs["context_units"] == 0
    return apply_automated_translation(
        result_path,
        config=kwargs["config"],
        provider=DeterministicMockTranslationProvider(),
        target_language=kwargs["target_language"],
        revision_path=kwargs["revision_path"],
        style=kwargs["style"],
        output_directory=kwargs["output_directory"],
        resume_directory=kwargs["resume_directory"],
        dictionary=kwargs["dictionary"],
        dictionary_sha256=kwargs["dictionary_sha256"],
    )


def controller(tmp_path: Path) -> GuiTranslationController:
    paths = GuiWorkflowController((tmp_path.resolve(),))
    return GuiTranslationController(
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        resolve_path=paths.resolve_allowed_path,
        runner=mock_runner,
        preflight=lambda provider, environment: None,
    )


def request(tmp_path: Path, result: Path) -> dict[str, Any]:
    return {
        "result": str(result),
        "source_revision": "",
        "output_directory": str(tmp_path / "candidates"),
        "resume_directory": str(tmp_path / "state"),
        "target_language": "pl",
        "provider_name": "lm-studio",
        "model": "bielik-test",
        "endpoint": "http://127.0.0.1:1234/v1",
        "allow_remote_endpoint": False,
        "allow_cloud": False,
        "reasoning_max_tokens": None,
        "output_mode": "plain-text",
        "dictionary_path": "",
    }


def test_gui_translation_publishes_explicit_non_final_candidate(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())

    outcome = controller(tmp_path).generate(**request(tmp_path, result), confirmed=True)

    assert outcome["final"] is False
    assert outcome["source_verification"] == "raw"
    assert outcome["model"] == "deterministic-unit-map-v1"
    assert Path(outcome["candidate_path"]).is_file()


def test_gui_translation_requires_confirmation(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())

    with pytest.raises(GuiTranslationError) as missing:
        controller(tmp_path).generate(**request(tmp_path, result), confirmed=False)

    assert missing.value.code == "GUI_TRANSLATION_CONFIRMATION_REQUIRED"


def test_gui_translation_rejects_audio_instead_of_a_canonical_result(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"not a canonical result")

    with pytest.raises(GuiTranslationError) as invalid:
        controller(tmp_path).generate(**request(tmp_path, media), confirmed=True)

    assert invalid.value.code == "GUI_TRANSLATION_RESULT_INVALID"
    assert "not an audio" in str(invalid.value)


def test_gui_translation_allows_explicit_cloud_candidate_with_session_key(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    seen: list[object] = []
    paths = GuiWorkflowController((tmp_path.resolve(),))
    service = GuiTranslationController(
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        resolve_path=paths.resolve_allowed_path,
        runner=mock_runner,
        preflight=lambda provider, environment: seen.append((provider.provider_id, environment)),
    )

    outcome = service.generate(
        **{
            **request(tmp_path, result),
            "provider_name": "openrouter",
            "model": "google/gemini-2.5-flash",
            "endpoint": "https://openrouter.ai/api/v1",
            "allow_cloud": True,
            "reasoning_max_tokens": 0,
        },
        confirmed=True,
        api_key="session-secret",
    )

    assert outcome["final"] is False
    assert seen == [("openrouter", {"OPENROUTER_API_KEY": "session-secret"})]


def test_gui_translation_checks_exact_cloud_provider_without_source_text(tmp_path: Path) -> None:
    seen: list[object] = []
    paths = GuiWorkflowController((tmp_path.resolve(),))
    service = GuiTranslationController(
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        resolve_path=paths.resolve_allowed_path,
        preflight=lambda provider, environment: seen.append((provider.provider_id, environment)),
    )

    outcome = service.check_provider(
        provider_name="openrouter",
        model="google/gemini-2.5-flash",
        endpoint="https://openrouter.ai/api/v1",
        allow_remote_endpoint=False,
        reasoning_max_tokens=0,
        api_key="session-secret",
    )

    assert outcome == {
        "status": "ok",
        "provider": "openrouter",
        "model": "google/gemini-2.5-flash",
        "endpoint_kind": "cloud",
    }
    assert seen == [("openrouter", {"OPENROUTER_API_KEY": "session-secret"})]
