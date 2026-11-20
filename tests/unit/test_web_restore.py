import pytest

from ewp_transcripts.web_restore import GuiRestoreProgress


def test_progress_tracks_partial_queue_and_keeps_restore_owners_separate():
    progress = GuiRestoreProgress()
    first, second = "a" * 24, "b" * 24
    assert progress.snapshot(first)["state"] == "pending"
    progress.start(first)
    progress.total(3)
    progress.advance(1)
    assert progress.snapshot(first) == dict(state="loading", loaded=1, total=3)
    with pytest.raises(ValueError, match="already"):
        progress.start(second)
    progress.advance(1)
    assert progress.snapshot(first)["loaded"] == 2
    progress.finish(first, succeeded=False)
    assert progress.snapshot(first)["state"] == "failed"
    progress.start(second)
    progress.finish(first, succeeded=True)
    assert progress.snapshot(second)["state"] == "loading"
    assert progress.snapshot(first)["state"] == "pending"
    progress.finish(second, succeeded=True)
    assert progress.snapshot(second)["state"] == "complete"
