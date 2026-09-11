from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.errors import MediaProbeError
from ewp_transcripts.web_workflows import GuiWorkflowController


class StubResult(BaseModel):
    selected: str
    mode: str
    output_directory: str | None = None


def test_inspect_calls_injected_application_service_and_records_result(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    calls: list[tuple[Path, dict[str, Any]]] = []

    def inspect(path: Path, **kwargs: Any) -> BaseModel:
        calls.append((path, kwargs))
        return StubResult(selected=str(path), mode="inspect")

    controller = GuiWorkflowController((tmp_path.resolve(),), inspect_service=inspect)
    operation = controller.run("inspect", {"path": str(media)})

    assert operation.status == "completed"
    assert operation.result == {
        "selected": str(media),
        "mode": "inspect",
        "output_directory": None,
    }
    assert calls[0][0] == media
    assert "config" in calls[0][1]
    assert controller.operations() == (operation,)


def test_gui_paths_trim_accidental_outer_whitespace(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    seen: list[Path] = []

    def inspect(path: Path, **kwargs: Any) -> BaseModel:
        seen.append(path)
        return StubResult(selected=str(path), mode="inspect")

    controller = GuiWorkflowController((tmp_path.resolve(),), inspect_service=inspect)
    operation = controller.run("inspect", {"path": f"  {media}  "})

    assert operation.status == "completed"
    assert seen == [media]


def test_dry_run_passes_allowed_output_directory(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    output = tmp_path / "exports"
    captured: dict[str, Any] = {}

    def plan(path: Path, **kwargs: Any) -> BaseModel:
        captured.update(kwargs)
        return StubResult(
            selected=str(path),
            mode="dry-run",
            output_directory=str(kwargs["output_directory"]),
        )

    controller = GuiWorkflowController((tmp_path.resolve(),), dry_run_service=plan)
    operation = controller.run("dry-run", {"path": str(media), "output_directory": str(output)})

    assert operation.status == "completed"
    assert captured["output_directory"] == output
    assert controller.has_completed_plan(media, output)
    assert controller.completed_plan(media, output) == operation.result
    assert not controller.has_completed_plan(media, tmp_path / "other")


def test_dry_run_identity_includes_language_and_speaker_count(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    output = tmp_path / "exports"
    captured: dict[str, Any] = {}

    def plan(path: Path, **kwargs: Any) -> BaseModel:
        captured.update(kwargs)
        return StubResult(selected=str(path), mode="dry-run", output_directory=str(output))

    controller = GuiWorkflowController((tmp_path.resolve(),), dry_run_service=plan)
    operation = controller.run(
        "dry-run",
        {
            "path": str(media),
            "output_directory": str(output),
            "language": "en",
            "speaker_count": 3,
        },
    )

    assert operation.language == LanguageMode.ENGLISH
    assert operation.speaker_count == 3
    assert captured["config"].general.language == LanguageMode.ENGLISH
    assert captured["config"].diarization.speaker_count == 3
    assert controller.has_completed_plan(
        media, output, language=LanguageMode.ENGLISH, speaker_count=3
    )
    assert not controller.has_completed_plan(
        media, output, language=LanguageMode.ENGLISH, speaker_count=2
    )


def test_invalid_transcription_controls_are_coded_failures(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    controller = GuiWorkflowController((tmp_path.resolve(),))

    language = controller.run("inspect", {"path": str(media), "language": "xx"})
    speakers = controller.run("inspect", {"path": str(media), "speaker_count": 0})

    assert language.error == {
        "code": "GUI_TRANSCRIPTION_OPTIONS_INVALID",
        "message": "Language must be pl, en, or auto",
    }
    assert speakers.error == {
        "code": "GUI_TRANSCRIPTION_OPTIONS_INVALID",
        "message": "Speaker count must be auto or an integer from 1 to 6",
    }


def test_dry_run_requires_explicit_output_directory(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    controller = GuiWorkflowController((tmp_path.resolve(),))

    operation = controller.run("dry-run", {"path": str(media), "output_directory": ""})

    assert operation.status == "failed"
    assert operation.error == {
        "code": "GUI_OUTPUT_REQUIRED",
        "message": "Enter a shared output directory before running dry-run.",
    }


def test_paths_outside_roots_and_symlinks_are_rejected(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"audio")
    link = allowed / "link.wav"
    link.symlink_to(outside)
    controller = GuiWorkflowController((allowed.resolve(),))

    outside_result = controller.run("inspect", {"path": str(outside)})
    link_result = controller.run("inspect", {"path": str(link)})

    assert outside_result.error is not None
    assert outside_result.error["code"] == "GUI_PATH_REJECTED"
    assert link_result.error is not None
    assert link_result.error["code"] == "GUI_PATH_REJECTED"


def test_windows_drive_path_is_normalized_before_root_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    seen: list[Path] = []

    def inspect(path: Path, **kwargs: Any) -> BaseModel:
        seen.append(path)
        return StubResult(selected=str(path), mode="inspect")

    monkeypatch.setattr(
        "ewp_transcripts.web_workflows.normalize_input_path", lambda supplied: media
    )
    controller = GuiWorkflowController((tmp_path.resolve(),), inspect_service=inspect)

    operation = controller.run("inspect", {"path": r"D:\recordings\episode.wav"})

    assert operation.status == "completed"
    assert seen == [media]


def test_missing_path_is_a_coded_failure(tmp_path: Path) -> None:
    controller = GuiWorkflowController((tmp_path.resolve(),))

    operation = controller.run("inspect", {})

    assert operation.status == "failed"
    assert operation.error == {
        "code": "GUI_REQUEST_INVALID",
        "message": "A non-empty path is required.",
    }


def test_json_input_explains_that_inspection_requires_media(tmp_path: Path) -> None:
    result = tmp_path / "results.example.json"
    result.write_text("{}", encoding="utf-8")

    def inspect(path: Path, **kwargs: Any) -> BaseModel:
        raise MediaProbeError("ffprobe rejected the input with exit code 1")

    controller = GuiWorkflowController((tmp_path.resolve(),), inspect_service=inspect)
    operation = controller.run("inspect", {"path": str(result)})

    assert operation.error == {
        "code": "MEDIA_PROBE_FAILED",
        "message": (
            "This input is a transcript or result JSON document, not media. "
            "Use it in Review and export; Inspect and plan accepts supported audio files."
        ),
    }
