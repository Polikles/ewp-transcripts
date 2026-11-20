"""Tests for strict work-directory allocation and cleanup."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ewp_transcripts.domain.errors import UnsafeWorkDirectoryError
from ewp_transcripts.workdirs import (
    MARKER_FILENAME,
    allocate_work_directory,
    cleanup_work_directory,
    find_work_directories,
)

RUN_ID = UUID("123e4567-e89b-12d3-a456-426614174000")


def test_allocate_creates_isolated_marked_workspace(tmp_path: Path) -> None:
    workspace = allocate_work_directory(tmp_path / "work", run_id=RUN_ID, job_id="episode")

    assert workspace.path == tmp_path / "work" / str(RUN_ID) / "episode"
    marker = json.loads(workspace.marker_path.read_text(encoding="utf-8"))
    assert marker["marker_version"] == "2.0"
    assert marker["retention_reason"] == "active"
    assert marker["owner_pid"] == os.getpid()
    assert datetime.fromisoformat(marker["created_at"]).tzinfo is not None
    assert marker["run_id"] == str(RUN_ID)
    assert marker["job_id"] == "episode"


def test_existing_workspace_is_never_reused(tmp_path: Path) -> None:
    root = tmp_path / "work"
    allocate_work_directory(root, run_id=RUN_ID, job_id="episode")

    with pytest.raises(UnsafeWorkDirectoryError, match="already exists"):
        allocate_work_directory(root, run_id=RUN_ID, job_id="episode")


def test_cleanup_removes_only_verified_workspace(tmp_path: Path) -> None:
    root = tmp_path / "work"
    workspace = allocate_work_directory(root, run_id=RUN_ID, job_id="episode")
    sibling = root / "models-must-remain"
    sibling.mkdir()
    (sibling / "model.bin").write_bytes(b"model")
    (workspace.path / "temporary.wav").write_bytes(b"audio")

    cleanup_work_directory(workspace)

    assert not workspace.path.exists()
    assert (sibling / "model.bin").read_bytes() == b"model"


def test_cleanup_removes_empty_run_parent_but_not_work_root(tmp_path: Path) -> None:
    root = tmp_path / "work"
    workspace = allocate_work_directory(root, run_id=RUN_ID, job_id="episode")

    cleanup_work_directory(workspace)

    assert root.is_dir()
    assert not workspace.path.parent.exists()


def test_tampered_marker_blocks_cleanup(tmp_path: Path) -> None:
    workspace = allocate_work_directory(tmp_path / "work", run_id=RUN_ID, job_id="episode")
    workspace.marker_path.write_text("{}", encoding="utf-8")

    with pytest.raises(UnsafeWorkDirectoryError, match="does not match"):
        cleanup_work_directory(workspace)

    assert workspace.path.is_dir()


@pytest.mark.parametrize("job_id", ["", ".", "..", "../escape", "dir/escape"])
def test_unsafe_job_id_is_rejected(tmp_path: Path, job_id: str) -> None:
    with pytest.raises(UnsafeWorkDirectoryError, match="Unsafe job ID"):
        allocate_work_directory(tmp_path / "work", run_id=RUN_ID, job_id=job_id)


def test_symlink_work_root_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "work"
    link.symlink_to(target, target_is_directory=True)

    with pytest.raises(UnsafeWorkDirectoryError, match="symbolic link"):
        allocate_work_directory(link, run_id=RUN_ID, job_id="episode")


def test_find_work_directories_filters_by_marker_age_and_ignores_unknown_paths(
    tmp_path: Path,
) -> None:
    root = tmp_path / "work"
    old = allocate_work_directory(root, run_id=RUN_ID, job_id="old")
    recent_run = UUID("223e4567-e89b-12d3-a456-426614174000")
    recent = allocate_work_directory(root, run_id=recent_run, job_id="recent")
    unknown = root / "models-must-remain"
    unknown.mkdir()
    (unknown / "model.bin").write_bytes(b"model")
    invalid = root / str(UUID("323e4567-e89b-12d3-a456-426614174000")) / "invalid"
    invalid.mkdir(parents=True)
    (invalid / MARKER_FILENAME).write_text("{}", encoding="utf-8")
    now = datetime(2026, 8, 4, tzinfo=UTC)
    old_time = (now - timedelta(days=10)).timestamp()
    recent_time = (now - timedelta(days=1)).timestamp()
    old.marker_path.write_text(
        json.dumps({"marker_version": "1.0", "run_id": str(RUN_ID), "job_id": "old"})
    )
    recent.marker_path.write_text(
        json.dumps({"marker_version": "1.0", "run_id": str(recent_run), "job_id": "recent"})
    )
    os.utime(old.marker_path, (old_time, old_time))
    os.utime(recent.marker_path, (recent_time, recent_time))

    found = find_work_directories(root, older_than_days=5, now=now)

    assert [workspace.path for workspace in found] == [old.path]
    assert (unknown / "model.bin").read_bytes() == b"model"
    assert invalid.is_dir()
