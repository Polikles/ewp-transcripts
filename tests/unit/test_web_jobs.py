import time
from pathlib import Path
from types import SimpleNamespace

from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.web_jobs import GuiTranscriptionQueue, workflow_progress


def wait_for_terminal(queue: GuiTranscriptionQueue, timeout: float = 1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = queue.jobs()[0]
        if job.status in {"completed", "failed"}:
            return job
        time.sleep(0.005)
    raise AssertionError("job did not finish")


def test_queue_stages_then_runs_application_service_and_records_result(tmp_path: Path) -> None:
    source = tmp_path / "episode.wav"
    output = tmp_path / "output"
    calls = []

    def transcribe(path, **kwargs):
        calls.append((path, kwargs))
        return SimpleNamespace(result_path=output / "episode_results.json")

    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=transcribe)
    try:
        submitted = queue.stage(
            source,
            output,
            planned_job_id="episode",
            planned_result_path=str(output / "episode_results.json"),
        )
        assert calls == []
        assert queue.start() == 1
        completed = wait_for_terminal(queue)
    finally:
        queue.close()

    assert submitted.status == "staged"
    assert completed.status == "completed"
    assert completed.result_path == str(output / "episode_results.json")
    assert calls[0][0] == source
    assert calls[0][1]["output_directory"] == output


def test_queue_applies_staged_language_and_speaker_count(tmp_path: Path) -> None:
    source = tmp_path / "episode.wav"
    output = tmp_path / "output"
    seen = []

    def transcribe(path, **kwargs):
        seen.append(kwargs["config"])
        return SimpleNamespace(result_path=output / "episode_results.json")

    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=transcribe)
    try:
        staged = queue.stage(
            source,
            output,
            planned_job_id="episode",
            planned_result_path=str(output / "episode_results.json"),
            language=LanguageMode.ENGLISH,
            speaker_count=4,
        )
        queue.start()
        wait_for_terminal(queue)
    finally:
        queue.close()

    assert staged.language == LanguageMode.ENGLISH
    assert staged.speaker_count == 4
    assert seen[0].general.language == LanguageMode.ENGLISH
    assert seen[0].diarization.speaker_count == 4


def test_queue_sanitizes_unexpected_failure(tmp_path: Path) -> None:
    def fail(*args, **kwargs):
        raise RuntimeError("secret backend detail")

    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=fail)
    try:
        queue.stage(
            tmp_path / "episode.wav",
            tmp_path / "output",
            planned_job_id="episode",
            planned_result_path=str(tmp_path / "output/episode_results.json"),
        )
        queue.start()
        failed = wait_for_terminal(queue)
    finally:
        queue.close()

    assert failed.status == "failed"
    assert failed.error is not None
    assert failed.error["code"] == "GUI_TRANSCRIPTION_FAILED"
    assert "secret" not in failed.error["message"]


def test_staged_job_can_be_removed_before_start(tmp_path: Path) -> None:
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        job = queue.stage(
            tmp_path / "episode.wav",
            tmp_path / "output",
            planned_job_id="episode",
            planned_result_path=str(tmp_path / "output/episode_results.json"),
        )
        assert queue.remove(job.job_id)
        assert queue.jobs() == ()
        assert queue.start() == 0
    finally:
        queue.close()


def test_queue_rejects_source_changed_after_dry_run_before_transcription(tmp_path: Path) -> None:
    source = tmp_path / "episode.wav"
    source.write_bytes(b"dry-run bytes")
    calls = []
    queue = GuiTranscriptionQueue(
        config=ApplicationConfig(),
        service=lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    try:
        queue.stage(
            source,
            tmp_path / "output",
            planned_job_id="episode",
            planned_result_path=str(tmp_path / "output/episode_results.json"),
            source_sha256=sha256_file(source),
        )
        source.write_bytes(b"changed after dry-run")
        queue.start()
        failed = wait_for_terminal(queue)
    finally:
        queue.close()

    assert failed.status == "failed"
    assert failed.error == {
        "code": "GUI_SOURCE_FINGERPRINT_MISMATCH",
        "message": (
            "The staged source changed after dry-run. Inspect and stage the current file again."
        ),
    }
    assert calls == []


def test_active_queue_exposes_shared_output_and_rejectable_job_identity(tmp_path: Path) -> None:
    output = tmp_path / "output"
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        queue.stage(
            tmp_path / "episode.wav",
            output,
            planned_job_id="episode",
            planned_result_path=str(output / "episode_results.json"),
        )
        assert queue.active_output_directory() == str(output)
        assert queue.contains_active_planned_job("episode")
        assert not queue.contains_active_planned_job("different")
    finally:
        queue.close()


def test_workflow_progress_is_derived_from_immutable_output_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        staged = queue.stage(
            tmp_path / "episode.wav",
            output,
            planned_job_id="episode",
            planned_result_path=str(output / "episode_results.json"),
        )
        completed = staged.model_copy(
            update={"status": "completed", "result_path": str(output / "episode_results.json")}
        )
        assert workflow_progress(completed).model_dump() == {
            "transcription": {
                "state": "complete",
                "path": str(output / "episode_results.json"),
                "candidate_path": None,
            },
            "correction": {"state": "pending", "path": None, "candidate_path": None},
            "review": {"state": "pending", "path": None, "candidate_path": None},
            "original_export": {"state": "pending", "path": None, "candidate_path": None},
            "translation": {"state": "pending", "path": None, "candidate_path": None},
            "translated_export": {
                "state": "pending",
                "path": None,
                "candidate_path": None,
            },
        }
        for directory, filename in [
            ("correction-candidates", "episode_revision_001.json"),
            ("revisions", "episode_revision_001.json"),
            ("exports", "episode_transcript_revision_001.txt"),
            ("accepted-translations", "episode_en_translation_001.json"),
            ("translation-exports", "episode_en_translation_001.provenance.json"),
        ]:
            destination = output / directory
            destination.mkdir()
            (destination / filename).write_text("{}", encoding="utf-8")
        progress = workflow_progress(completed)
    finally:
        queue.close()

    assert progress.transcription.state == "complete"
    assert progress.correction.state == "complete"
    assert progress.review.state == "complete"
    assert progress.original_export.state == "complete"
    assert progress.translation.state == "complete"
    assert progress.translated_export.state == "complete"


def test_workflow_progress_marks_failed_transcription_red(tmp_path: Path) -> None:
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        job = queue.stage(
            tmp_path / "episode.wav",
            tmp_path / "output",
            planned_job_id="episode",
            planned_result_path=str(tmp_path / "output/episode_results.json"),
        ).model_copy(update={"status": "failed"})
        assert workflow_progress(job).transcription.state == "failed"
    finally:
        queue.close()


def test_queue_records_later_workflow_error_for_its_matching_result(tmp_path: Path) -> None:
    output = tmp_path / "output"
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        staged = queue.stage(
            tmp_path / "episode.wav",
            output,
            planned_job_id="episode",
            planned_result_path=str(output / "episode_results.json"),
        )
        queue._replace(  # noqa: SLF001 - assert the queue's immutable public job view
            staged.job_id,
            status="completed",
            result_path=str(output / "episode_results.json"),
        )
        assert queue.record_workflow_error(
            str(output / "episode_results.json"), "translation", "INVALID_TRANSLATION_RESPONSE"
        )
        assert workflow_progress(queue.jobs()[0]).translation.state == "failed"
        assert not queue.record_workflow_error(
            str(output / "other_results.json"), "translation", "INVALID_TRANSLATION_RESPONSE"
        )
    finally:
        queue.close()


def test_queue_marks_optional_stages_skipped_for_its_matching_result(tmp_path: Path) -> None:
    output = tmp_path / "output"
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        staged = queue.stage(
            tmp_path / "episode.wav",
            output,
            planned_job_id="episode",
            planned_result_path=str(output / "episode_results.json"),
        )
        queue._replace(  # noqa: SLF001 - assert the queue's immutable public job view
            staged.job_id,
            status="completed",
            result_path=str(output / "episode_results.json"),
        )
        assert queue.skip_workflow_stage(str(output / "episode_results.json"), "correction")
        assert queue.skip_workflow_stage(str(output / "episode_results.json"), "translation")
        progress = workflow_progress(queue.jobs()[0])
    finally:
        queue.close()

    assert progress.correction.state == "skipped"
    assert progress.translation.state == "skipped"
    assert progress.translated_export.state == "skipped"


def test_queue_restores_only_terminal_history_from_saved_workspace(tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = output / "episode_results.json"
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    restored_queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        staged = queue.stage(
            tmp_path / "episode.wav",
            output,
            planned_job_id="episode",
            planned_result_path=str(result),
            source_sha256="a" * 64,
        )
        terminal = staged.model_copy(
            update={
                "status": "completed",
                "result_path": str(result),
                "workflow_skips": {"correction"},
                "workflow_errors": {"translation": "INVALID_TRANSLATION_RESPONSE"},
            }
        )
        assert restored_queue.replace_terminal_jobs((terminal,)) == 1
        restored = restored_queue.jobs()
    finally:
        queue.close()
        restored_queue.close()

    assert restored == (terminal,)
    progress = workflow_progress(restored[0])
    assert progress.correction.state == "skipped"
    assert progress.translation.state == "failed"


def test_restoring_terminal_history_preserves_active_staged_jobs(tmp_path: Path) -> None:
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=lambda *a, **k: None)
    try:
        active = queue.stage(
            tmp_path / "active.wav",
            tmp_path / "output",
            planned_job_id="active",
            planned_result_path=str(tmp_path / "output/active_results.json"),
            source_sha256="a" * 64,
        )
        terminal = active.model_copy(
            update={
                "job_id": "7d927d4e-96e0-439e-a3d7-1626d1ee89cc",
                "status": "completed",
                "planned_job_id": "finished",
                "planned_result_path": str(tmp_path / "output/finished_results.json"),
                "result_path": str(tmp_path / "output/finished_results.json"),
            }
        )
        queue.replace_terminal_jobs((terminal,))
        restored = queue.jobs()
    finally:
        queue.close()

    assert [job.job_id for job in restored] == [active.job_id, terminal.job_id]
