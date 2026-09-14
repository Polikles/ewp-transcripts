"""Tests for lightweight CLI entry points."""

import subprocess
import sys

from typer.testing import CliRunner

from ewp_transcripts import __version__
from ewp_transcripts.cli import app

runner = CliRunner()


def test_help_succeeds_without_importing_ml_backends() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Local-first transcription" in result.stdout
    assert "transcriber COMMAND --help" in result.stdout
    assert "torch" not in sys.modules
    assert "whisperx" not in sys.modules
    assert "pyannote.audio" not in sys.modules


def test_command_help_exposes_command_specific_options() -> None:
    result = runner.invoke(app, ["inspect", "--help"])

    assert result.exit_code == 0
    assert "--speaker-count" in result.stdout
    assert "--channel-mode" in result.stdout

    gui = runner.invoke(app, ["gui", "--help"])
    assert gui.exit_code == 0
    assert "--open-browser" in gui.stdout


def test_root_and_revision_help_explain_command_specific_discovery() -> None:
    root = runner.invoke(app, ["--help"])
    revise = runner.invoke(app, ["revise", "--help"])

    assert "transcriber COMMAND --help" in root.stdout
    assert "transcriber revise COMMAND --help" in revise.stdout


def test_batch_capable_help_names_file_or_directory_inputs() -> None:
    for arguments in (
        ["export", "--help"],
        ["revise", "preview", "--help"],
        ["revise", "apply", "--help"],
    ):
        result = runner.invoke(app, arguments)
        assert result.exit_code == 0
        assert "directory" in result.stdout


def test_version_reports_installed_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_framework_usage_errors_have_a_stable_code() -> None:
    result = runner.invoke(app, ["translate", "audit", "missing.json"])

    assert result.exit_code == 2
    assert "CLI_USAGE_ERROR" in result.stderr


def test_module_entry_point_reports_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ewp_transcripts", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == __version__
    assert result.stderr == ""
