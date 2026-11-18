"""Tests for lightweight environment diagnostics."""

import subprocess
import sys
from collections.abc import Sequence

import pytest
from typer.testing import CliRunner

from ewp_transcripts.cli import app
from ewp_transcripts.config import ApplicationConfig, DiarizationConfig, ModelsConfig
from ewp_transcripts.doctor import run_doctor
from ewp_transcripts.domain import DiagnosticStatus


def _successful_runner(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    if "nvidia-smi" in arguments[0]:
        stdout = "NVIDIA GeForce RTX 3090, 24576\n"
    elif arguments[0] == sys.executable:
        stdout = "12.8\n"
    else:
        stdout = "ok\n"
    return subprocess.CompletedProcess(arguments, 0, stdout=stdout, stderr="")


def _all_executables(name: str) -> str:
    return f"/usr/bin/{name}"


def _config_with_models(tmp_path) -> ApplicationConfig:
    revisions = {
        "asr": "asr-revision",
        "alignment": "alignment-revision",
        "diarization": "diarization-revision",
        "english_alignment": "english-alignment-revision",
    }
    paths = {name: tmp_path / revision for name, revision in revisions.items()}
    for path in paths.values():
        path.mkdir()
    return ApplicationConfig(
        models=ModelsConfig(
            asr_revision=revisions["asr"],
            asr_snapshot_path=paths["asr"],
            alignment_revision=revisions["alignment"],
            alignment_snapshot_path=paths["alignment"],
            english_alignment_revision=revisions["english_alignment"],
            english_alignment_snapshot_path=paths["english_alignment"],
        ),
        diarization=DiarizationConfig(
            model_revision=revisions["diarization"],
            local_model_path=paths["diarization"],
        ),
    )


@pytest.mark.parametrize("ubuntu_version", ["24.04", "26.04"])
def test_doctor_passes_on_validated_baseline_without_importing_ml(tmp_path, ubuntu_version) -> None:
    result = run_doctor(
        config=_config_with_models(tmp_path),
        finder=_all_executables,
        runner=_successful_runner,
        environ={},
        python_version=(3, 12, 3),
        kernel_release="6.18.0-microsoft-standard-WSL2",
        os_release={"ID": "ubuntu", "VERSION_ID": ubuntu_version},
    )

    assert result.ready is True
    assert all(check.status is DiagnosticStatus.PASS for check in result.checks)
    assert "torch" not in sys.modules
    assert "whisperx" not in sys.modules
    assert "pyannote.audio" not in sys.modules


def test_doctor_fails_when_gpu_is_missing(tmp_path) -> None:
    def finder(name: str) -> str | None:
        return None if name == "nvidia-smi" else f"/usr/bin/{name}"

    result = run_doctor(
        config=_config_with_models(tmp_path),
        finder=finder,
        runner=_successful_runner,
        python_version=(3, 12, 3),
        kernel_release="6.18.0-microsoft-standard-WSL2",
        os_release={"ID": "ubuntu", "VERSION_ID": "24.04"},
    )

    assert result.ready is False
    gpu_check = next(check for check in result.checks if check.code == "gpu")
    assert gpu_check.status is DiagnosticStatus.FAIL


def test_doctor_fails_when_ffmpeg_is_missing(tmp_path) -> None:
    def finder(name: str) -> str | None:
        return None if name == "ffmpeg" else f"/usr/bin/{name}"

    result = run_doctor(
        config=_config_with_models(tmp_path),
        finder=finder,
        runner=_successful_runner,
        python_version=(3, 12, 3),
        kernel_release="6.18.0-microsoft-standard-WSL2",
        os_release={"ID": "ubuntu", "VERSION_ID": "24.04"},
    )

    assert result.ready is False
    check = next(item for item in result.checks if item.code == "ffmpeg")
    assert check.status is DiagnosticStatus.FAIL


def test_doctor_json_returns_environment_exit_code_without_secrets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    secret = "test-secret-that-must-not-be-printed"
    diagnostic = run_doctor(
        config=_config_with_models(tmp_path),
        finder=lambda name: None if name == "nvidia-smi" else f"/usr/bin/{name}",
        runner=_successful_runner,
        environ={"HF_TOKEN": secret},
        python_version=(3, 12, 3),
        kernel_release="6.18.0-microsoft-standard-WSL2",
        os_release={"ID": "ubuntu", "VERSION_ID": "24.04"},
    )
    monkeypatch.setattr("ewp_transcripts.cli.doctor", lambda **_kwargs: diagnostic)
    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "--json-output"])

    assert result.exit_code == 3
    assert '"ready": false' in result.stdout
    assert "HF_TOKEN is present" in result.stdout
    assert secret not in result.stdout


def test_doctor_fails_with_setup_guidance_when_a_model_is_missing(tmp_path) -> None:
    config = _config_with_models(tmp_path)
    config.models.asr_snapshot_path.rmdir()

    result = run_doctor(
        config=config,
        finder=_all_executables,
        runner=_successful_runner,
        environ={},
        python_version=(3, 12, 3),
        kernel_release="6.18.0-microsoft-standard-WSL2",
        os_release={"ID": "ubuntu", "VERSION_ID": "24.04"},
    )

    assert result.ready is False
    check = next(item for item in result.checks if item.code == "asr_model")
    assert check.status is DiagnosticStatus.FAIL
    assert "WSL config/MODEL_SETUP.md" in check.message


def test_explicit_speech_test_reports_native_failure_without_leaking_tokens(tmp_path) -> None:
    secret = "hf-private-test-value"

    def runner(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if arguments[0] == sys.executable and "torchcodec" in arguments[-1]:
            return subprocess.CompletedProcess(
                arguments, 1, stdout="", stderr=f"libavutil.so.58 missing; token={secret}"
            )
        return _successful_runner(arguments)

    result = run_doctor(
        config=_config_with_models(tmp_path),
        finder=_all_executables,
        runner=runner,
        environ={"HF_TOKEN": secret},
        python_version=(3, 12, 3),
        kernel_release="microsoft",
        os_release={"ID": "ubuntu", "VERSION_ID": "24.04"},
        test_speech_runtime=True,
    )
    check = next(check for check in result.checks if check.code == "speech_runtime")
    assert not result.ready
    assert check.status is DiagnosticStatus.FAIL
    assert "libavutil.so.58" in check.context["detail"]
    assert "after upgrading from Ubuntu 24.04 to Ubuntu 26.04" in check.message
    assert check.context["help_url"] == "/help/ubuntu-upgrade"
    assert check.context["instructions_file"] == "WSL config/UBUNTU_UPGRADE.md"
    assert secret not in result.model_dump_json()
    assert "torchcodec" not in sys.modules


def test_speech_test_timeout_is_a_failed_check(tmp_path) -> None:
    def runner(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if arguments[0] == sys.executable and "torchcodec" in arguments[-1]:
            raise subprocess.TimeoutExpired(arguments, 60)
        return _successful_runner(arguments)

    result = run_doctor(
        config=_config_with_models(tmp_path),
        finder=_all_executables,
        runner=runner,
        test_speech_runtime=True,
    )
    check = next(check for check in result.checks if check.code == "speech_runtime")
    assert check.status is DiagnosticStatus.FAIL
    assert check.context["error_type"] == "TimeoutExpired"


def test_unaccepted_distribution_still_warns(tmp_path) -> None:
    result = run_doctor(
        config=_config_with_models(tmp_path),
        finder=_all_executables,
        runner=_successful_runner,
        os_release={"ID": "ubuntu", "VERSION_ID": "25.10"},
    )
    assert (
        next(check for check in result.checks if check.code == "distribution").status
        is DiagnosticStatus.WARNING
    )


def test_cli_native_check_is_explicit(monkeypatch, tmp_path) -> None:
    calls = []
    result = run_doctor(config=_config_with_models(tmp_path), runner=_successful_runner)

    def doctor(**kwargs):
        calls.append(kwargs["test_speech_runtime"])
        return result

    monkeypatch.setattr("ewp_transcripts.cli.doctor", doctor)
    runner = CliRunner()
    runner.invoke(app, ["doctor"])
    runner.invoke(app, ["doctor", "--test-speech-runtime"])
    assert calls == [False, True]
