"""Lightweight environment diagnostics with no ML imports."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from ewp_transcripts import __version__
from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain import DiagnosticCheck, DiagnosticStatus, DoctorResult
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.platform_runtime import background_creation_flags

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
ExecutableFinder = Callable[[str], str | None]


def _run_command(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        creationflags=background_creation_flags(),
    )


def _python_check(version_info: tuple[int, int, int]) -> DiagnosticCheck:
    supported = (3, 12) <= version_info[:2] < (3, 13)
    return DiagnosticCheck(
        code="python",
        status=DiagnosticStatus.PASS if supported else DiagnosticStatus.FAIL,
        message="Python version is supported." if supported else "Python 3.12 is required.",
        context={"version": ".".join(map(str, version_info))},
    )


def _wsl_check(kernel_release: str) -> DiagnosticCheck:
    is_wsl = "microsoft" in kernel_release.casefold()
    return DiagnosticCheck(
        code="wsl2",
        status=DiagnosticStatus.PASS if is_wsl else DiagnosticStatus.WARNING,
        message="WSL2 environment detected." if is_wsl else "WSL2 was not detected.",
    )


def _ubuntu_check(os_release: Mapping[str, str]) -> DiagnosticCheck:
    distribution = os_release.get("ID", "unknown")
    version = os_release.get("VERSION_ID", "unknown")
    supported = distribution == "ubuntu" and version in {"24.04", "26.04"}
    return DiagnosticCheck(
        code="distribution",
        status=DiagnosticStatus.PASS if supported else DiagnosticStatus.WARNING,
        message=(
            f"Accepted Ubuntu {version} baseline detected."
            if supported
            else "Environment differs from the accepted Ubuntu 24.04 / 26.04 baselines."
        ),
        context={"distribution": distribution, "version": version},
    )


def _command_check(
    executable: str,
    arguments: Sequence[str],
    finder: ExecutableFinder,
    runner: CommandRunner,
) -> DiagnosticCheck:
    path = finder(executable)
    if path is None:
        return DiagnosticCheck(
            code=executable,
            status=DiagnosticStatus.FAIL,
            message=f"Required executable '{executable}' is missing.",
        )

    try:
        completed = runner([path, *arguments])
    except (OSError, subprocess.SubprocessError) as error:
        return DiagnosticCheck(
            code=executable,
            status=DiagnosticStatus.FAIL,
            message=f"Unable to run '{executable}'.",
            context={"error_type": type(error).__name__},
        )

    return DiagnosticCheck(
        code=executable,
        status=(DiagnosticStatus.PASS if completed.returncode == 0 else DiagnosticStatus.FAIL),
        message=(
            f"Executable '{executable}' is available."
            if completed.returncode == 0
            else f"Executable '{executable}' returned an error."
        ),
        context={"exit_code": completed.returncode},
    )


def _gpu_check(finder: ExecutableFinder, runner: CommandRunner) -> DiagnosticCheck:
    executable = finder("nvidia-smi")
    if executable is None:
        return DiagnosticCheck(
            code="gpu",
            status=DiagnosticStatus.FAIL,
            message="NVIDIA GPU visibility is unavailable: nvidia-smi is missing.",
        )

    try:
        completed = runner(
            [
                executable,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ]
        )
    except (OSError, subprocess.SubprocessError) as error:
        return DiagnosticCheck(
            code="gpu",
            status=DiagnosticStatus.FAIL,
            message="NVIDIA GPU query failed.",
            context={"error_type": type(error).__name__},
        )

    output = completed.stdout.strip()
    if completed.returncode != 0 or not output:
        return DiagnosticCheck(
            code="gpu",
            status=DiagnosticStatus.FAIL,
            message="NVIDIA GPU query returned no usable device.",
            context={"exit_code": completed.returncode},
        )

    return DiagnosticCheck(
        code="gpu",
        status=DiagnosticStatus.PASS,
        message="NVIDIA GPU is visible.",
        context={"device": output.splitlines()[0]},
    )


def _cuda_check(runner: CommandRunner) -> DiagnosticCheck:
    try:
        completed = runner(
            [
                sys.executable,
                "-c",
                (
                    "import torch; "
                    "print(torch.version.cuda or 'none'); "
                    "raise SystemExit(0 if torch.cuda.is_available() else 1)"
                ),
            ]
        )
    except (OSError, subprocess.SubprocessError) as error:
        return DiagnosticCheck(
            code="cuda",
            status=DiagnosticStatus.FAIL,
            message="Unable to verify CUDA availability in PyTorch.",
            context={"error_type": type(error).__name__},
        )

    runtime = completed.stdout.strip().splitlines()
    available = completed.returncode == 0 and bool(runtime)
    return DiagnosticCheck(
        code="cuda",
        status=DiagnosticStatus.PASS if available else DiagnosticStatus.FAIL,
        message=(
            "CUDA is available in PyTorch."
            if available
            else "CUDA is unavailable in PyTorch; verify the locked environment and WSL GPU setup."
        ),
        context={
            "runtime": runtime[-1] if runtime else "unavailable",
            "exit_code": completed.returncode,
        },
    )


def _amd_checks(runner: CommandRunner) -> tuple[DiagnosticCheck, ...]:
    try:
        result = runner(
            [
                sys.executable,
                "-c",
                "from ewp_transcripts.amd_runtime import require_amd_runtime; "
                "print(require_amd_runtime())",
            ]
        )
        ready = result.returncode == 0 and bool(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        ready = False
    return (
        DiagnosticCheck(
            code="gpu",
            status=DiagnosticStatus.PASS if ready else DiagnosticStatus.FAIL,
            message="AMD ROCm ASR (experimental); CPU alignment and diarization."
            if ready
            else "AMD ROCm (experimental) is unavailable. Repair the AMD runtime "
            "and check the supported GPU/driver.",
        ),
        DiagnosticCheck(
            code="cuda",
            status=DiagnosticStatus.PASS if ready else DiagnosticStatus.FAIL,
            message="AMD HIP backend verified; PyTorch stages use CPU."
            if ready
            else "AMD HIP runtime/device check failed; no NVIDIA CUDA or CPU ASR "
            "fallback was used.",
        ),
    )


def _speech_runtime_check(
    runner: CommandRunner, environ: Mapping[str, str], *, amd: bool = False
) -> DiagnosticCheck:
    script = (
        "import os; os.environ['HF_HUB_OFFLINE']='1'; "
        "from ewp_transcripts.engines.ffmpeg_compat import prepare_speech_libraries; "
        "prepare_speech_libraries(); "
        "from torchcodec.decoders import AudioDecoder; "
        "from ewp_transcripts.engines.whisperx import _load_whisperx; _load_whisperx(); "
        "from ewp_transcripts.engines.pyannote import _load_pyannote; _load_pyannote(); "
        "import ctranslate2; print(ctranslate2.get_supported_compute_types('cuda'))"
    )
    if amd:
        # HIP is checked in its own child by _amd_checks; avoid mixing its OpenMP DLLs with torch.
        script = script.replace(
            "import ctranslate2; print(ctranslate2.get_supported_compute_types('cuda'))",
            "print('CPU alignment/diarization libraries loaded; HIP checked separately')",
        )
    try:
        completed = runner([sys.executable, "-c", script])
    except (OSError, subprocess.SubprocessError) as error:
        return DiagnosticCheck(
            code="speech_runtime",
            status=DiagnosticStatus.FAIL,
            message=(
                "Speech dependency test could not finish; repair the locked environment and retry."
            ),
            context={"error_type": type(error).__name__},
        )
    detail = completed.stderr[-6000:] if completed.returncode else completed.stdout[-1000:]
    for key, value in environ.items():
        if value and any(word in key.upper() for word in ("TOKEN", "KEY", "SECRET", "PASSWORD")):
            detail = detail.replace(value, "[redacted]")
    return DiagnosticCheck(
        code="speech_runtime",
        status=DiagnosticStatus.PASS if completed.returncode == 0 else DiagnosticStatus.FAIL,
        message=(
            (
                "Speech libraries, TorchCodec/FFmpeg and AMD HIP load successfully (experimental)."
                if amd
                else "Speech libraries, TorchCodec/FFmpeg and CTranslate2 CUDA load successfully."
            )
            if completed.returncode == 0
            else (
                "Speech dependencies failed to load. Save work, stop the GUI and run "
                "powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Repair. "
                "See Instructions/WINDOWS_NATIVE.md (GUI: /help/windows-native) for native "
                "FFmpeg shared DLL, Visual C++ and CUDA diagnostics."
            )
            if sys.platform == "win32"
            else "Speech dependencies failed to load. For missing FFmpeg 4–7 shared libraries, "
            "stop the GUI and run bash scripts/repair-dependencies.sh from the transcription "
            "checkout. Settings & About provides the repair steps. Check technical details "
            "for other Torch/TorchCodec/CUDA failures. If this started after upgrading from "
            "Ubuntu 24.04 to Ubuntu 26.04, follow WSL config/UBUNTU_UPGRADE.md "
            "(GUI: /help/ubuntu-upgrade)."
        ),
        context={
            "exit_code": completed.returncode,
            "detail": detail,
            **(
                {
                    "help_url": "/help/windows-native"
                    if sys.platform == "win32"
                    else "/help/ubuntu-upgrade",
                    "instructions_file": "Instructions/WINDOWS_NATIVE.md"
                    if sys.platform == "win32"
                    else "WSL config/UBUNTU_UPGRADE.md",
                }
                if completed.returncode
                else {}
            ),
        },
    )


def _model_check(
    code: str,
    role: str,
    path: Path,
    revision: str,
    *,
    required: bool = True,
) -> DiagnosticCheck:
    available = path.is_dir() and path.name == revision
    missing_status = DiagnosticStatus.FAIL if required else DiagnosticStatus.WARNING
    return DiagnosticCheck(
        code=code,
        status=DiagnosticStatus.PASS if available else missing_status,
        message=(
            f"Pinned local {role} model snapshot is available."
            if available
            else (
                f"Pinned local {role} model snapshot is missing; follow WSL config/MODEL_SETUP.md."
            )
        ),
        context={"path": str(path), "revision": revision},
    )


def _token_check(environ: Mapping[str, str]) -> DiagnosticCheck:
    present = bool(environ.get("HF_TOKEN"))
    return DiagnosticCheck(
        code="hf_token",
        status=DiagnosticStatus.PASS,
        message=f"HF_TOKEN is {'present' if present else 'missing'}.",
        context={"present": present},
    )


def _read_os_release(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    values: dict[str, str] = {}
    for line in lines:
        key, separator, value = line.partition("=")
        if separator:
            values[key] = value.strip().strip('"')
    return values


def run_doctor(
    *,
    config: ApplicationConfig | None = None,
    finder: ExecutableFinder = shutil.which,
    runner: CommandRunner = _run_command,
    environ: Mapping[str, str] = os.environ,
    python_version: tuple[int, int, int] = sys.version_info[:3],
    kernel_release: str = platform.release(),
    os_release: Mapping[str, str] | None = None,
    test_speech_runtime: bool = False,
    system: str = platform.system(),
) -> DoctorResult:
    """Run deterministic lightweight checks without importing ML backends."""

    from ewp_transcripts.platform_runtime import prepare_native_environment

    prepare_native_environment()
    release = _read_os_release(Path("/etc/os-release")) if os_release is None else os_release
    effective_config = ApplicationConfig() if config is None else config
    checks = (
        _python_check(python_version),
        *(
            (
                DiagnosticCheck(
                    code="platform",
                    status=DiagnosticStatus.PASS,
                    message="Native Windows environment detected.",
                    context={"system": system, "release": kernel_release},
                ),
            )
            if system == "Windows"
            else (_wsl_check(kernel_release), _ubuntu_check(release))
        ),
        _command_check("ffmpeg", ["-version"], finder, runner),
        _command_check("ffprobe", ["-version"], finder, runner),
        *(
            _amd_checks(runner)
            if effective_config.models.accelerator == "amd"
            else (_gpu_check(finder, runner), _cuda_check(runner))
        ),
        *(
            (
                _speech_runtime_check(
                    runner, environ, amd=effective_config.models.accelerator == "amd"
                ),
            )
            if test_speech_runtime
            else ()
        ),
        _model_check(
            "asr_model",
            "ASR",
            effective_config.models.asr_snapshot_path,
            effective_config.models.asr_revision,
        ),
        _model_check(
            "alignment_model",
            "Polish alignment",
            effective_config.models.alignment_snapshot_path,
            effective_config.models.alignment_revision,
            required=effective_config.general.language is not LanguageMode.ENGLISH,
        ),
        _model_check(
            "english_alignment_model",
            "English alignment",
            effective_config.models.english_alignment_snapshot_path,
            effective_config.models.english_alignment_revision,
            required=effective_config.general.language is not LanguageMode.POLISH,
        ),
        _model_check(
            "diarization_model",
            "diarization",
            effective_config.diarization.local_model_path,
            effective_config.diarization.model_revision,
        ),
        _token_check(environ),
    )
    return DoctorResult(
        application_version=__version__,
        ready=all(check.status is not DiagnosticStatus.FAIL for check in checks),
        checks=checks,
    )
