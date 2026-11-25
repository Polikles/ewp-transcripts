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


def _tiny_available_config(tmp_path):
    from ewp_transcripts.config import ModelsConfig

    snapshot = tmp_path / ("a" * 40)
    snapshot.mkdir()
    for name in ["model.bin", "config.json", "tokenizer.json"]:
        (snapshot / name).write_bytes(b"synthetic")
    return ApplicationConfig(
        models=ModelsConfig(asr_snapshot_path=snapshot, asr_revision=snapshot.name)
    )


@pytest.mark.parametrize("missing", [None, "model.bin", "config.json", "tokenizer.json"])
def test_local_availability_checks_required_files_without_loading_models(tmp_path, missing):
    from ewp_transcripts.local_asr import (
        LocalAsrUnavailable,
        local_model_options,
        require_local_asr,
    )

    config = _tiny_available_config(tmp_path)
    if missing:
        (config.models.asr_snapshot_path / missing).unlink()
        with pytest.raises(LocalAsrUnavailable, match="restart the program"):
            require_local_asr(config)
    else:
        require_local_asr(config)
    assert local_model_options(config)[0]["installed"] is (missing is None)
    # Pure cloud choices do not inspect local model files.
    require_local_asr(config.model_copy(update={"speech": SpeechConfig(provider="openrouter")}))


def test_optional_snapshot_with_partial_download_is_not_available(tmp_path, monkeypatch):
    from ewp_transcripts import local_asr

    entry = optional_asr_models()[0].copy()
    entry["path"] = str(tmp_path / entry["revision"])
    entry["files"] = {"model.bin": 9, "config.json": 2, "tokenizer.json": 2}
    monkeypatch.setattr(local_asr, "optional_asr_models", lambda: [entry])
    target = Path(entry["path"])
    target.mkdir()
    for name, size in entry["files"].items():
        (target / name).write_bytes(b"x" * (size - 1))
    config = ApplicationConfig(speech=SpeechConfig(local_model="large-v3"))
    with pytest.raises(local_asr.LocalAsrUnavailable):
        local_asr.require_local_asr(config)
    for name, size in entry["files"].items():
        (target / name).write_bytes(b"x" * size)
    local_asr.require_local_asr(config)


def test_planning_rejects_missing_model_before_calling_application_service(tmp_path, monkeypatch):
    from ewp_transcripts import web_workflows
    from ewp_transcripts.local_asr import require_local_asr

    config = _tiny_available_config(tmp_path)
    (config.models.asr_snapshot_path / "model.bin").unlink()
    monkeypatch.setattr(web_workflows, "load_config", lambda: config)
    source = tmp_path / "source.wav"
    source.write_bytes(b"media")
    plan = Mock()
    controller = web_workflows.GuiWorkflowController(
        dry_run_service=plan, model_validator=require_local_asr
    )
    result = controller.run("dry-run", {"path": str(source), "output_directory": str(tmp_path)})
    assert result.status == "failed" and result.error["code"] == "GUI_LOCAL_ASR_MODEL_REQUIRED"
    plan.assert_not_called()
    assert not controller.has_completed_plan(source, tmp_path)
    with pytest.raises(ValueError, match="selected model is not installed"):
        controller.validate_model(SpeechConfig())


def test_missing_restored_model_blocks_entire_queue_before_any_service_runs(tmp_path):
    from ewp_transcripts.local_asr import LocalAsrUnavailable, require_local_asr

    config = _tiny_available_config(tmp_path)
    service = Mock()
    queue = GuiTranscriptionQueue(config=config, service=service, model_validator=require_local_asr)
    try:
        for name in ["configured", "large-v3-turbo"]:
            queue.stage(
                tmp_path / (name + ".wav"),
                tmp_path,
                planned_job_id=name,
                planned_result_path=str(tmp_path / (name + ".json")),
                speech=SpeechConfig(local_model=name),
            )
        with pytest.raises(LocalAsrUnavailable):
            queue.start()
        assert all(job.status == "staged" for job in queue.jobs())
        service.assert_not_called()
    finally:
        queue.close()


def test_http_start_checks_local_models_before_cloud_checks_or_queue_mutation(tmp_path):
    from email.message import Message
    from io import BytesIO

    from ewp_transcripts.local_asr import require_local_asr
    from ewp_transcripts.web_server import LocalGuiRequestHandler

    config = _tiny_available_config(tmp_path)
    service = Mock()
    queue = GuiTranscriptionQueue(config=config, service=service, model_validator=require_local_asr)
    try:
        queue.stage(
            tmp_path / "source.wav",
            tmp_path,
            planned_job_id="pending",
            planned_result_path=str(tmp_path / "result.json"),
        )
        (config.models.asr_snapshot_path / "model.bin").unlink()
        handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
        handler.path = "/api/v1/transcriptions/start"
        handler.headers = Message()
        for key, value in {
            "Host": "127.0.0.1:8765",
            "Origin": "http://127.0.0.1:8765",
            "Content-Length": "2",
            "X-EWP-CSRF": "expected",
        }.items():
            handler.headers[key] = value
        handler.rfile = BytesIO(b"{}")
        speech = Mock()
        handler.server = SimpleNamespace(
            server_port=8765, gui_csrf_token="expected", gui_transcriptions=queue, gui_speech=speech
        )
        handler._write_response = Mock()
        handler.do_POST()
        response = handler._write_response.call_args.args[0]
        assert response.status == 400
        assert json.loads(response.body)["error"]["code"] == "GUI_LOCAL_ASR_MODEL_REQUIRED"
        assert queue.jobs()[0].status == "staged"
        speech.check_key.assert_not_called()
        service.assert_not_called()
    finally:
        queue.close()
