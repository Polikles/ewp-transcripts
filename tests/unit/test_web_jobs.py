import time
from pathlib import Path
from types import SimpleNamespace

from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.web_jobs import GuiTranscriptionQueue


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
