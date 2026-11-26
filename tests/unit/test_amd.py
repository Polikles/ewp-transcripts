"""AMD adapter boundaries without downloading speech models or claiming GPU inference."""

from types import SimpleNamespace

import pytest

from ewp_transcripts import amd_runtime
from ewp_transcripts.application import (
    _pyannote_diarization,
    _runtime_environment,
    _whisperx_alignment,
)
from ewp_transcripts.config import ApplicationConfig, load_config
from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines.amd import AmdAsrEngine, _HipAsrEngine


def amd_config():
    return ApplicationConfig.model_validate({"models": {"accelerator": "amd"}})


def test_amd_profile_keeps_pytorch_stages_on_cpu_and_reports_asr_hardware():
    config = amd_config()
    assert _whisperx_alignment(config)._device == "cpu"
    assert _pyannote_diarization(config)._device == "cpu"
    environment = _runtime_environment(config)
    assert "amd-rocm" in environment.device and "experimental" in environment.device
    assert environment.batch_size == 1
    original = ApplicationConfig()
    assert _whisperx_alignment(original)._device == "cuda"
    assert _pyannote_diarization(original)._device == "cuda"


def test_managed_amd_profile_can_be_overridden_by_explicit_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("EWP_LOCAL_ACCELERATOR", "amd")
    assert load_config(home=tmp_path, cwd=tmp_path).models.accelerator == "amd"
    assert (
        load_config(
            home=tmp_path, cwd=tmp_path, cli_overrides={"models": {"accelerator": "nvidia"}}
        ).models.accelerator
        == "nvidia"
    )


def engine(tmp_path, monkeypatch, *, bad=False, failure=False):
    snapshot = tmp_path / "revision"
    snapshot.mkdir()
    calls = []
    monkeypatch.setattr(amd_runtime, "require_amd_runtime", lambda: 1)

    class Model:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

        def transcribe(self, *args, **kwargs):
            calls.append((args, kwargs))
            if failure:
                raise RuntimeError("unavailable HIP device")
            segment = SimpleNamespace(text=" test", start=float("nan") if bad else 1.125, end=2.25)
            return iter([segment]), SimpleNamespace(language="pl")

    adapter = _HipAsrEngine(
        snapshot,
        revision="revision",
        name="large-v2",
        module_loader=lambda name: SimpleNamespace(WhisperModel=Model),
    )
    return adapter, calls


def test_amd_asr_is_offline_transcribe_only_and_preserves_timestamps(tmp_path, monkeypatch):
    adapter, calls = engine(tmp_path, monkeypatch)
    draft = adapter.transcribe(tmp_path / "audio.wav", language="auto", batch_size=4)
    assert draft.language == "pl" and draft.segments[0].start_ms == 1125
    assert draft.segments[0].end_ms == 2250 and draft.segments[0].text == " test"
    assert calls[0][1] == {"device": "cuda", "compute_type": "float16", "local_files_only": True}
    assert calls[1][1] == {
        "language": None,
        "task": "transcribe",
        "vad_filter": False,
        "word_timestamps": False,
    }
    adapter.close()
    assert adapter._model is None


@pytest.mark.parametrize("bad,failure", [(True, False), (False, True)])
def test_amd_does_not_fall_back_or_publish_invalid_results(tmp_path, monkeypatch, bad, failure):
    adapter, calls = engine(tmp_path, monkeypatch, bad=bad, failure=failure)
    with pytest.raises(SpeechEngineError, match="AMD ROCm"):
        adapter.transcribe(tmp_path / "audio.wav", language="pl", batch_size=1)
    assert len(calls) == 2


def test_amd_asr_rejects_missing_runtime_before_loading_model(tmp_path, monkeypatch):
    adapter, calls = engine(tmp_path, monkeypatch)

    def unavailable():
        raise SpeechEngineError("AMD runtime is missing")

    monkeypatch.setattr(amd_runtime, "require_amd_runtime", unavailable)
    with pytest.raises(SpeechEngineError, match="runtime is missing"):
        adapter.transcribe(tmp_path / "audio.wav", language="en", batch_size=1)
    assert not calls


def test_amd_adapter_rejects_non_windows_before_importing_ml(monkeypatch):
    monkeypatch.setattr(amd_runtime.sys, "platform", "linux")
    with pytest.raises(SpeechEngineError, match="Windows"):
        amd_runtime.require_amd_runtime()


@pytest.mark.parametrize("returncode,payload", [(0, '{"language":"pl","segments":[]}'), (2, "")])
def test_amd_worker_uses_local_pipe_and_preserves_failures(
    tmp_path, monkeypatch, returncode, payload
):
    import json
    import subprocess

    from ewp_transcripts.engines import amd

    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, returncode, payload, "technical details")

    monkeypatch.setattr(amd.subprocess, "run", run)
    adapter = AmdAsrEngine(tmp_path / "revision", revision="revision", name="large-v2")
    if returncode:
        with pytest.raises(SpeechEngineError, match="no CPU ASR fallback"):
            adapter.transcribe(tmp_path / "audio.wav", language="pl", batch_size=4)
    else:
        assert (
            adapter.transcribe(tmp_path / "audio.wav", language="pl", batch_size=4).language == "pl"
        )
    command, kwargs = calls[0]
    assert command[1:] == ["-m", "ewp_transcripts.engines.amd"]
    assert json.loads(kwargs["input"])["audio"] == str(tmp_path / "audio.wav")
    assert kwargs["env"]["HF_HUB_OFFLINE"] == "1" and kwargs["capture_output"] is True


@pytest.mark.parametrize("payload", [b"BAD!", b"short"])
def test_amd_setup_rejects_changed_archive_before_package_install(tmp_path, monkeypatch, payload):
    import hashlib
    import importlib.util
    from io import BytesIO
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "scripts/setup-amd.py"
    spec = importlib.util.spec_from_file_location("amd_setup_test", path)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    monkeypatch.setattr(script.urllib.request, "urlopen", lambda *args, **kwargs: BytesIO(payload))
    with pytest.raises(ValueError, match="pinned size/SHA-256"):
        script.download(
            {
                "file": "library.whl",
                "url": "https://example.invalid/library",
                "size": 4,
                "sha256": hashlib.sha256(b"GOOD").hexdigest(),
            },
            tmp_path,
        )
