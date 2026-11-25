"""Optional local ASR choices preserve pins, offline operation and per-job identity."""

import json
import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ewp_transcripts.config import ApplicationConfig, SpeechConfig
from ewp_transcripts.local_asr import optional_asr_models, resolve_local_asr
from ewp_transcripts.web_jobs import GuiTranscriptionQueue

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["large-v3", "large-v3-turbo"])
def test_local_selection_uses_exact_pinned_snapshot_without_changing_other_models(name):
    config = ApplicationConfig(speech=SpeechConfig(local_model=name))
    selected = resolve_local_asr(config)
    entry = next(m for m in optional_asr_models() if m["name"] == name)
    assert selected.models.asr_model == name
    assert selected.models.asr_repository == entry["repository"]
    assert selected.models.asr_revision == entry["revision"]
    assert selected.models.asr_snapshot_path.name == entry["revision"]
    assert selected.models.alignment_snapshot_path == config.models.alignment_snapshot_path
    assert selected.models.device == config.models.device
    assert config.models.asr_model == "large-v2"
    assert entry in json.loads((ROOT / "installer/models.json").read_text())["models"]
    assert len(entry["revision"]) == 40
    assert entry["bytes"] == sum(entry["files"].values())
    assert set(entry["files"]) == set(entry["hashes"])


def test_configured_custom_snapshot_and_cloud_selection_are_preserved(tmp_path):
    config = ApplicationConfig()
    assert resolve_local_asr(config).models is config.models
    cloud = config.model_copy(
        update={"speech": SpeechConfig(provider="openrouter", local_model="large-v3")}
    )
    assert resolve_local_asr(cloud).models is config.models
    with pytest.raises(ValueError):
        SpeechConfig(local_model="elevenlabs/scribe-v2")


@pytest.mark.parametrize("code", [None, "asr_v3", "asr_v3_turbo"])
def test_setup_downloads_optional_model_only_when_explicitly_selected(monkeypatch, code):
    import huggingface_hub

    setup = runpy.run_path(str(ROOT / "scripts/setup-models.py"))
    main = setup["main"]
    main.__globals__["prepare_language_data"] = lambda: None
    download = Mock()
    monkeypatch.setattr(huggingface_hub, "snapshot_download", download)
    monkeypatch.setattr(
        "sys.argv",
        ["setup-models.py", "--yes", "--public-only"] + (["--model", code] if code else []),
    )
    main()
    if code:
        entry = next(m for m in optional_asr_models() if m["code"] == code)
        assert download.call_count == 1
        assert download.call_args.kwargs["repo_id"] == entry["repository"]
        assert download.call_args.kwargs["revision"] == entry["revision"]
    else:
        assert download.call_count == 3
        assert all(
            call.kwargs["repo_id"] not in {m["repository"] for m in optional_asr_models()}
            for call in download.call_args_list
        )


def test_queue_retains_distinct_local_models_and_passes_selected_config_to_service(tmp_path):
    import time

    calls = []

    def transcribe(path, **kwargs):
        calls.append(kwargs["config"])
        return SimpleNamespace(result_path=tmp_path / "result.json")

    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=transcribe)
    try:
        jobs = [
            queue.stage(
                tmp_path / "source.wav",
                tmp_path,
                planned_job_id=name,
                planned_result_path=str(tmp_path / (name + ".json")),
                speech=SpeechConfig(local_model=name),
            )
            for name in ["large-v3", "large-v3-turbo"]
        ]
        assert [j.asr_model_name for j in jobs] == ["large-v3", "large-v3-turbo"]
        assert calls == []
        queue.start()
        deadline = time.monotonic() + 2
        while (
            any(j.status not in {"completed", "failed"} for j in queue.jobs())
            and time.monotonic() < deadline
        ):
            time.sleep(0.005)
        assert all(j.status == "completed" for j in queue.jobs())
        assert {c.models.asr_model for c in calls} == {"large-v3", "large-v3-turbo"}
    finally:
        queue.close()


def test_windows_user_ui_language_is_exposed_in_initial_page(monkeypatch):
    from ewp_transcripts import web_runtime
    from ewp_transcripts.web_server import WebConfiguration, dispatch_get

    monkeypatch.setattr(web_runtime, "system_ui_language", lambda: "pl")
    response = dispatch_get(
        WebConfiguration.create(port=8765), server_port=8765, host="127.0.0.1:8765", target="/"
    )
    assert b'data-system-language="pl"' in response.body


@pytest.mark.parametrize("code,expected", [(0x0415, "pl"), (0x0409, "en"), (0x0407, "en")])
def test_system_ui_language_reads_windows_user_setting(monkeypatch, code, expected):
    import ctypes
    import sys

    from ewp_transcripts.web_runtime import system_ui_language

    monkeypatch.setattr(
        ctypes,
        "windll",
        SimpleNamespace(kernel32=SimpleNamespace(GetUserDefaultUILanguage=lambda: code)),
        raising=False,
    )
    monkeypatch.setattr(sys, "platform", "win32")
    assert system_ui_language() == expected


def test_completed_import_retains_canonical_asr_name_without_using_current_default(tmp_path):
    queue = GuiTranscriptionQueue(config=ApplicationConfig())
    try:
        job, added = queue.register_completed_result(
            tmp_path / "result.json",
            output_directory=tmp_path,
            planned_job_id="imported",
            language="pl",
            asr_model_name="large-v3-turbo",
        )
        assert added and job.status == "completed" and job.asr_model_name == "large-v3-turbo"
    finally:
        queue.close()
