"""Tests for the marker-verified MVP cleanup command."""

from pathlib import Path
from uuid import UUID

from typer.testing import CliRunner

from ewp_transcripts.cli import app
from ewp_transcripts.workdirs import allocate_work_directory, retain_work_directory

RUN_ID = UUID("123e4567-e89b-12d3-a456-426614174000")


def _config(tmp_path: Path, work_root: Path) -> Path:
    path = tmp_path / "transcriber.toml"
    path.write_text(f'[runtime]\nwork_root = "{work_root}"\n', encoding="utf-8")
    return path


def test_clean_requires_preview_or_explicit_confirmation(tmp_path: Path) -> None:
    config = _config(tmp_path, tmp_path / "work")

    outcome = CliRunner().invoke(
        app,
        ["clean", "all-workdirs", "--config", str(config)],
    )

    assert outcome.exit_code == 2
    assert "CLI_CLEAN_MODE_INVALID" in outcome.stderr


def test_clean_dry_run_then_confirmed_removal_preserves_unknown_sibling(tmp_path: Path) -> None:
    root = tmp_path / "work"
    workspace = allocate_work_directory(root, run_id=RUN_ID, job_id="episode")
    (workspace.path / "private-audio.wav").write_bytes(b"audio")
    retain_work_directory(workspace, "failed")
    sibling = root / "models-must-remain"
    sibling.mkdir()
    (sibling / "model.bin").write_bytes(b"model")
    config = _config(tmp_path, root)
    runner = CliRunner()

    preview = runner.invoke(
        app,
        ["clean", "all-workdirs", "--config", str(config), "--dry-run"],
    )

    assert preview.exit_code == 0
    assert f"WOULD REMOVE {workspace.path}" in preview.stdout
    assert "SUMMARY selected=1 removed=0" in preview.stdout
    assert workspace.path.is_dir()

    removal = runner.invoke(
        app,
        ["clean", "all-workdirs", "--config", str(config), "--yes"],
    )

    assert removal.exit_code == 0
    assert f"REMOVED {workspace.path}" in removal.stdout
    assert "SUMMARY selected=1 removed=1" in removal.stdout
    assert not workspace.path.exists()
    assert (sibling / "model.bin").read_bytes() == b"model"
