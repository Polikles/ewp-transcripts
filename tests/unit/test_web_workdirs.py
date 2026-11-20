import json
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from ewp_transcripts.web_workdirs import GuiWorkdirController
from ewp_transcripts.workdirs import (
    allocate_work_directory,
    find_work_directories,
    retain_work_directory,
    work_directory_metadata,
)


def retained(root: Path, reason="failed"):
    workspace = allocate_work_directory(root, run_id=uuid4(), job_id="episode")
    (workspace.path / "working.wav").write_bytes(b"audio")
    retain_work_directory(workspace, reason)
    return workspace


def test_inventory_protects_active_referenced_legacy_and_final_artifacts(tmp_path: Path):
    active = allocate_work_directory(tmp_path, run_id=uuid4(), job_id="active")
    reference = retained(tmp_path)
    final = retained(tmp_path)
    (final.path / "episode_results.json").write_text("{}")
    legacy = retained(tmp_path)
    legacy.marker_path.write_text(
        json.dumps(dict(marker_version="1.0", run_id=str(legacy.run_id), job_id=legacy.job_id))
    )
    controller = GuiWorkdirController(tmp_path)
    entries = {
        item["path"]: item
        for item in controller.inventory((reference.path / "working.wav",))["entries"]
    }
    assert entries[str(active.path)]["blocker"] == "active"
    assert entries[str(reference.path)]["blocker"] == "referenced"
    assert entries[str(final.path)]["blocker"] == "unknown-artifact"
    assert entries[str(legacy.path)]["blocker"] == "legacy-unknown"
    assert not any(item["removable"] for item in entries.values())


def test_cleanup_requires_current_preview_and_rechecks_all_references(tmp_path: Path):
    first, second = retained(tmp_path), retained(tmp_path)
    controller = GuiWorkdirController(tmp_path)
    ids = [item["id"] for item in controller.inventory(())["entries"]]
    token = controller.preview(ids, ())["preview_token"]
    with pytest.raises(ValueError, match="protected"):
        controller.cleanup(token, (second.path / "working.wav",))
    assert first.path.exists() and second.path.exists()
    token = controller.preview(ids, ())["preview_token"]
    (first.path / "working.wav").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        controller.cleanup(token, ())
    token = controller.preview(ids, ())["preview_token"]
    assert len(controller.cleanup(token, ())["removed"]) == 2
    assert not first.path.exists() and not second.path.exists()
    with pytest.raises(ValueError, match="expired"):
        controller.cleanup(token, ())


def test_creation_time_survives_retention_and_age_uses_creation(tmp_path: Path):
    workspace = allocate_work_directory(tmp_path, run_id=uuid4(), job_id="episode")
    created = work_directory_metadata(workspace)["created_at"]
    retain_work_directory(workspace, "cancelled")
    assert work_directory_metadata(workspace)["created_at"] == created
    assert find_work_directories(
        tmp_path, older_than_days=2, now=datetime.fromisoformat(created) + timedelta(days=3)
    ) == (workspace,)
    assert not find_work_directories(
        tmp_path, older_than_days=2, now=datetime.fromisoformat(created) + timedelta(days=1)
    )
    assert (
        GuiWorkdirController(tmp_path).inventory((), reason="cancelled")["entries"][0]["reason"]
        == "cancelled"
    )
