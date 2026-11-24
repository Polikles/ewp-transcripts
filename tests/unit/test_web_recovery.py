from datetime import UTC, datetime

import pytest

from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.web_jobs import GuiTranscriptionJob
from ewp_transcripts.web_recovery import GuiStartupRecovery
from ewp_transcripts.web_workflows import GuiWorkflowController
from ewp_transcripts.web_workspaces import GuiWorkspaceController, default_workspace_directory


def test_automatic_queue_checkpoint_survives_restart_without_restoring_permissions(tmp_path):
    controller = GuiWorkspaceController(
        state_directory=tmp_path / "state",
        resolve_path=GuiWorkflowController().resolve_allowed_path,
    )
    saved = controller.save(name="Recovery", current_step="workspace-heading", fields={})
    recovery = GuiStartupRecovery(tmp_path / "startup.json")
    recovery.remember(saved.workspace_id, "")
    source = tmp_path / "input.wav"
    source.write_bytes(b"synthetic source")
    now = datetime.now(UTC)
    job = GuiTranscriptionJob(
        job_id="test",
        status="running",
        input_path=str(source),
        output_directory=str(tmp_path),
        planned_job_id="test",
        planned_result_path=str(tmp_path / "test_results.json"),
        source_sha256=sha256_file(source),
        language="pl",
        speaker_count=1,
        created_at=now,
        updated_at=now,
    )
    recovery.checkpoint((job,), lambda _: controller)
    loaded = controller.load(saved.workspace_id)
    assert len(loaded.staged_jobs) == 1  # Interrupted work is staged, never started automatically.
    assert "status" not in loaded.staged_jobs[0]
    after_restart = GuiStartupRecovery(recovery.path)
    assert after_restart.reference() == {
        "workspace_id": saved.workspace_id,
        "storage_directory": "",
    }
    assert not after_restart.armed  # Loading finishes before background checkpoints can replace it.
    result = tmp_path / "test_results.json"
    result.write_text("{}")
    finished = job.model_copy(
        update={"status": "completed", "result_path": str(result), "updated_at": datetime.now(UTC)}
    )
    recovery.checkpoint((finished,), lambda _: controller)
    loaded = controller.load(saved.workspace_id)
    assert not loaded.staged_jobs and len(loaded.terminal_jobs) == 1
    after_restart.forget()
    assert after_restart.reference() is None


def test_unavailable_recovery_is_not_overwritten_with_empty_work(tmp_path):
    recovery = GuiStartupRecovery(tmp_path / "startup.json")
    controller = GuiWorkspaceController(
        state_directory=tmp_path / "state",
        resolve_path=GuiWorkflowController().resolve_allowed_path,
    )
    saved = controller.save(name="Recovery", current_step="workspace-heading", fields={})
    recovery.remember(saved.workspace_id, "")
    path = controller.document_path(saved.workspace_id)
    path.write_text("damaged checkpoint")
    recovery.queue_signature = "previous"
    with pytest.raises(ValueError):
        recovery.checkpoint((), lambda _: controller)
    assert path.read_text() == "damaged checkpoint"


def test_managed_workspace_directory_uses_launch_selected_state(tmp_path, monkeypatch):
    monkeypatch.setenv("EWP_GUI_STATE_DIR", str(tmp_path / "work-state"))
    assert default_workspace_directory() == tmp_path / "work-state/gui-workspaces"
