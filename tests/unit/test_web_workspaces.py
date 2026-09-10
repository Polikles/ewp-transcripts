from datetime import UTC, datetime
from pathlib import Path

import pytest

from ewp_transcripts.web_workflows import GuiWorkflowController
from ewp_transcripts.web_workspaces import GuiWorkspaceController


def controller(tmp_path: Path) -> tuple[GuiWorkspaceController, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    workflows = GuiWorkflowController((allowed.resolve(),))
    return (
        GuiWorkspaceController(
            state_directory=tmp_path / "state",
            resolve_path=workflows.resolve_allowed_path,
        ),
        allowed,
    )


def test_workspace_round_trip_contains_only_allowlisted_non_secret_fields(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")

    saved = workspaces.save(
        name="Episode work",
        current_step="correction-heading",
        fields={
            "input-path": str(media),
            "output-path": str(allowed / "output"),
            "workflow-language": "pl",
            "workflow-speaker-auto": True,
        },
    )
    loaded = workspaces.load(saved.workspace_id)
    listed = workspaces.list()

    assert loaded == saved
    assert loaded.fields["input-path"] == str(media)
    assert listed[0].workspace_id == saved.workspace_id
    assert listed[0].available is True
    assert (tmp_path / "state" / f"{saved.workspace_id}.json").stat().st_mode & 0o777 == 0o600


def test_workspace_rejects_unknown_fields_and_outside_paths(tmp_path: Path) -> None:
    workspaces, _ = controller(tmp_path)

    with pytest.raises(ValueError, match="unsupported field"):
        workspaces.save(name="Bad", current_step="", fields={"api_key": "secret"})
    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"audio")
    with pytest.raises(ValueError, match="outside"):
        workspaces.save(
            name="Bad path",
            current_step="",
            fields={"input-path": str(outside)},
        )


def test_missing_saved_path_marks_summary_unavailable(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    saved = workspaces.save(
        name="Temporary",
        current_step="workspace-heading",
        fields={"input-path": str(media)},
    )
    media.unlink()

    assert workspaces.list()[0].available is False
    with pytest.raises(FileNotFoundError):
        workspaces.load(saved.workspace_id)


def test_workspace_retains_only_hash_bound_staged_queue_identity(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    output = allowed / "output"
    saved = workspaces.save(
        name="Queued episode",
        current_step="workspace-heading",
        fields={"input-path": str(media), "output-path": str(output)},
        staged_jobs=[
            {
                "input_path": str(media),
                "output_directory": str(output),
                "planned_job_id": "episode",
                "planned_result_path": str(output / "episode_results.json"),
                "source_sha256": "a" * 64,
                "language": "pl",
                "speaker_count": "auto",
            }
        ],
    )

    assert saved.staged_jobs[0]["planned_job_id"] == "episode"
    assert workspaces.load(saved.workspace_id).staged_jobs == saved.staged_jobs


def test_workspace_retains_terminal_queue_history_without_credentials(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    output = allowed / "output"
    output.mkdir()
    result = output / "episode_results.json"
    result.write_text("{}", encoding="utf-8")
    now = datetime.now(UTC)
    saved = workspaces.save(
        name="Completed episode",
        current_step="translation-heading",
        fields={"input-path": str(media), "output-path": str(output)},
        terminal_jobs=[
            {
                "job_id": "ec6d26a5-709a-487b-b459-87f85d64a81d",
                "status": "completed",
                "input_path": str(media),
                "output_directory": str(output),
                "planned_job_id": "episode",
                "planned_result_path": str(result),
                "source_sha256": "a" * 64,
                "language": "pl",
                "speaker_count": "auto",
                "created_at": now,
                "updated_at": now,
                "result_path": str(result),
                "error": None,
                "workflow_errors": {"translation": "INVALID_TRANSLATION_RESPONSE"},
                "workflow_skips": ["correction"],
            },
            {
                "job_id": "f2a7fdd3-4bdb-4c84-9156-b4177df5670f",
                "status": "failed",
                "input_path": str(media),
                "output_directory": str(output),
                "planned_job_id": "failed-episode",
                "planned_result_path": str(output / "failed-episode_results.json"),
                "source_sha256": "b" * 64,
                "language": "pl",
                "speaker_count": "auto",
                "created_at": now,
                "updated_at": now,
                "result_path": None,
                "error": {"code": "GUI_TRANSCRIPTION_FAILED", "message": "Retained failure."},
                "workflow_errors": {},
                "workflow_skips": [],
            },
        ],
    )

    restored = workspaces.load(saved.workspace_id)

    assert restored.workspace_version == 2
    assert len(restored.terminal_jobs) == 2
    assert restored.terminal_jobs[0].workflow_skips == {"correction"}
    assert restored.terminal_jobs[0].workflow_errors == {
        "translation": "INVALID_TRANSLATION_RESPONSE"
    }
    assert restored.terminal_jobs[1].status == "failed"
