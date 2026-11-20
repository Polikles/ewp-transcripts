"""Real event boundaries, elapsed heartbeat, calibration and safe ETA failure modes."""

from pathlib import Path

from ewp_transcripts.progress import ProgressEvent, ProgressHistory, RuntimeProgress, emit_progress


def test_progress_uses_events_then_calibrates_with_local_successful_timings(tmp_path: Path) -> None:
    now = [0.0]
    history = ProgressHistory(tmp_path / "timings.json")
    phases = ("inspect", "transcribe:1", "publish", "cleanup")

    def tracker():
        progress = RuntimeProgress(history, "a" * 64, clock=lambda: now[0])
        progress(ProgressEvent("plan", "planned", media_duration_ms=10000, phases=phases))
        return progress

    first = tracker()
    first(ProgressEvent("inspect", "started"))
    now[0] = 2
    assert first.snapshot()["elapsed_seconds"] == 2
    assert first.snapshot()["eta_seconds"] is None
    for phase, elapsed in [("inspect", 1), ("transcribe", 20), ("publish", 1), ("cleanup", 0)]:
        first(ProgressEvent(phase, "started"))
        now[0] += elapsed
        first(ProgressEvent(phase, "completed", duration_ms=elapsed * 1000))
    assert first.snapshot()["percent"] < 100
    first.finish(True)
    assert first.snapshot()["percent"] == 100
    assert history.path.is_file()
    assert history.completed_runs(first.profile) == 1
    # Independent complete jobs, not per-track observations, calibrate ETA.
    history.record(first.profile, history.samples(first.profile))
    history.record(first.profile, history.samples(first.profile))
    second = RuntimeProgress(ProgressHistory(history.path), "a" * 64, clock=lambda: now[0])
    second(ProgressEvent("plan", "planned", media_duration_ms=10000, phases=phases))
    second(ProgressEvent("inspect", "completed", duration_ms=1000))
    second(ProgressEvent("transcribe", "started"))
    now[0] += 5
    predicted = second.snapshot()
    assert predicted["calibrated"] and predicted["eta_seconds"] > 0
    assert predicted["eta_min_seconds"] <= predicted["eta_seconds"] <= predicted["eta_max_seconds"]
    now[0] += 20
    late = second.snapshot()
    assert late["eta_seconds"] > 0 and late["eta_min_seconds"] > 0
    now[0] += 100
    overdue = second.snapshot()
    assert overdue["overdue"] and overdue["eta_seconds"] is None
    assert overdue["percent"] < 100 and overdue["percent"] >= predicted["percent"]
    second.finish(False)
    frozen = second.snapshot()
    now[0] += 100
    assert second.snapshot() == frozen
    assert second.snapshot()["percent"] < 100


def test_unknown_profile_and_corrupt_history_have_no_eta(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text("broken")
    progress = RuntimeProgress(ProgressHistory(path), "b" * 64)
    progress(ProgressEvent("plan", "planned", phases=("transcribe:1",), media_duration_ms=1000))
    assert not progress.snapshot()["calibrated"]
    assert progress.snapshot()["eta_seconds"] is None


def test_progress_observer_failure_is_isolated() -> None:
    def failing(event):
        raise RuntimeError("observer failure")

    emit_progress(failing, "transcribe", "started")


def test_eta_requires_three_complete_jobs_not_three_source_tracks() -> None:
    history = ProgressHistory()
    phases = ("transcribe:1", "transcribe:2", "transcribe:3", "publish")
    for index in range(3):
        progress = RuntimeProgress(history, "c" * 64, clock=lambda: 0)
        progress(ProgressEvent("plan", "planned", phases=phases, media_duration_ms=1000))
        assert progress.snapshot()["calibration_runs"] == index
        assert progress.snapshot()["eta_seconds"] is None
        for stream in range(1, 4):
            progress(
                ProgressEvent(
                    "transcribe", "completed", stream_index=stream, stream_count=3, duration_ms=1000
                )
            )
        progress(ProgressEvent("publish", "completed", duration_ms=100))
        progress.finish(True)
    probe = RuntimeProgress(history, "c" * 64, clock=lambda: 0)
    probe(ProgressEvent("plan", "planned", phases=phases, media_duration_ms=1000))
    assert probe.snapshot()["calibration_runs"] == probe.snapshot()["calibration_required"] == 3
    assert probe.snapshot()["eta_seconds"] > 0
    probe.finish(False)
    assert history.completed_runs(probe.profile) == 3
