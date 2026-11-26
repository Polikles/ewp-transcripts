import json
import subprocess
from datetime import UTC, datetime
from email.message import Message
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ewp_transcripts import __version__
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.storage import preserve_gui_selected_source
from ewp_transcripts.web_jobs import GuiTranscriptionJob
from ewp_transcripts.web_server import (
    SECURITY_HEADERS,
    GuiSelectionCache,
    LocalGuiRequestHandler,
    WebConfiguration,
    WebResponse,
    _is_canonical_result_filename,
    _open_browser,
    _select_local_directory,
    dispatch_get,
)
from ewp_transcripts.web_workflows import GuiWorkflowController


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("s0e00_results.json", True),
        ("S0E02_mono_normalized_results_v003.json", True),
        ("episode_results_v002.json", True),
        ("episode_segments.json", False),
        ("episode_results_v3.json", False),
    ],
)
def test_canonical_picker_filename_gate(filename: str, expected: bool) -> None:
    assert _is_canonical_result_filename(filename) is expected


def test_output_folder_dialog_uses_local_os_picker_without_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ewp_transcripts.web_server._is_wsl_environment", lambda: True)
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: name if name == "powershell.exe" else None,
    )
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        assert kwargs["timeout"] == 600
        return SimpleNamespace(returncode=0, stdout="C:\\Users\\DS\\Desktop\\tezt001")

    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)
    assert _select_local_directory() == "C:\\Users\\DS\\Desktop\\tezt001"
    assert calls[0][:4] == ["powershell.exe", "-NoProfile", "-STA", "-EncodedCommand"]


def test_output_folder_dialog_reports_missing_desktop_picker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ewp_transcripts.web_server._is_wsl_environment", lambda: False)
    monkeypatch.setattr("ewp_transcripts.web_server.shutil.which", lambda _: None)
    with pytest.raises(ValueError, match="Enter the output directory path directly"):
        _select_local_directory()


def test_output_folder_dialog_retries_through_wsl_init_after_direct_interop_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ewp_transcripts.web_server._is_wsl_environment", lambda: True)
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: name if name in {"powershell.exe", "cmd.exe"} else None,
    )
    monkeypatch.setattr(Path, "is_file", lambda self: str(self) == "/init")
    calls: list[tuple[list[str], object]] = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append((command, kwargs["executable"]))
        if kwargs["executable"] is None:
            raise OSError(5, "WSL interop unavailable to direct child")
        return SimpleNamespace(returncode=0, stdout="C:\\Users\\DS\\Desktop\\tezt002")

    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)
    assert _select_local_directory() == "C:\\Users\\DS\\Desktop\\tezt002"
    assert [executable for _, executable in calls] == [None, "/init"]
    assert calls[1][0][0] == "powershell.exe"


def test_output_folder_dialog_uses_linux_desktop_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ewp_transcripts.web_server._is_wsl_environment", lambda: False)
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: "/usr/bin/kdialog" if name == "kdialog" else None,
    )
    run = Mock(return_value=SimpleNamespace(returncode=0, stdout="/home/user/output\n"))
    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)

    assert _select_local_directory() == "/home/user/output"
    assert run.call_args.args[0][:2] == ["/usr/bin/kdialog", "--getexistingdirectory"]
    assert run.call_args.kwargs["executable"] is None


def test_health_is_versioned_and_hardened(tmp_path: Path) -> None:
    config = WebConfiguration.create(port=8765)
    response = dispatch_get(
        config, server_port=8765, host="127.0.0.1:8765", target="/api/v1/health"
    )
    assert response.status == 200
    assert json.loads(response.body) == {
        "status": "ok",
        "api_version": "1.0",
        "application_version": __version__,
    }
    assert "default-src 'none'" in SECURITY_HEADERS["Content-Security-Policy"]
    assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"


def test_shell_is_served(tmp_path: Path) -> None:
    config = WebConfiguration.create(port=8765)
    response = dispatch_get(config, server_port=8765, host="localhost:8765", target="/")
    assert response.status == 200
    assert b"EWP Transcriber" in response.body
    assert response.body.index(b"EWP Transcriber") < response.body.index(
        b"Local-first transcript workflow"
    )
    assert b"Status: connecting" in response.body
    assert b'id="clear-workflow"' in response.body
    assert b"Add to queue" in response.body
    assert b'id="clear-browser-state"' in response.body
    assert b"Start queue" in response.body
    assert b"Review and export" in response.body
    assert b"LLM-assisted transcript correction" in response.body
    assert b'id="generate-correction"' in response.body
    assert b'id="generate-translation"' in response.body
    assert b"LLM-assisted translation" in response.body
    assert b"Semantic translation review" in response.body
    assert b'id="review-translation"' in response.body
    assert b'id="proceed-next-output"' in response.body
    assert b"Project correction dictionary" in response.body
    assert b'id="propose-dictionary"' in response.body
    assert b'id="review-correction"' in response.body
    assert b"Save and prepare for export" in response.body
    assert b'id="clear-review"' in response.body
    assert b'id="restore-review"' in response.body
    assert b"Review status" in response.body
    help_response = dispatch_get(config, server_port=8765, host="localhost:8765", target="/help")
    assert help_response.status == 200
    assert b"User manual" in help_response.body
    assert b"/help/installation?lang=en" in help_response.body
    script_response = dispatch_get(
        config, server_port=8765, host="localhost:8765", target="/assets/app.js"
    )
    assert b"const formElement = event.currentTarget" in script_response.body
    assert b"formElement.elements.confirmed" in script_response.body
    assert b"event.currentTarget.elements" not in script_response.body
    assert b"Auto-detect" in script_response.body
    assert b"GUI_REVIEW_ACTIVE" in script_response.body
    assert b"GUI_REVIEW_RESTORE_FAILED" in script_response.body
    assert b"None \xe2\x80\x94 validation only" in script_response.body
    assert b"ewp-review-layout" in script_response.body
    assert b"ewp-active-review-v1" in script_response.body
    assert b"beforeunload" in script_response.body
    assert b"not manually verified" in script_response.body
    assert b"Separate selected text" in script_response.body
    assert b"Merge entire block with previous" in script_response.body
    assert b"Speaker names for this revision" in response.body
    assert b"review-speaker-labels" in response.body
    assert b"Add revision-only speaker" in script_response.body
    assert b"reviewSpeakerNamesPanel" in script_response.body
    assert b"Restore saved draft" in response.body
    assert b"Undo applied to the current draft" in script_response.body
    assert b"Preview the current draft before applying." in script_response.body
    assert b"if (reviewDirty) await saveReviewDraft();" in script_response.body
    assert b"Remove ${speakerId}" in script_response.body
    assert b"GUI_REVIEW_SPEAKER_IN_USE" in script_response.body
    assert b"Completion:" in script_response.body
    assert b'circle.textContent = state === "complete"' in script_response.body
    assert b"workflow-error" in script_response.body
    assert b"Existing non-final correction candidate found" in script_response.body
    assert b"review-bottom-navigation" in script_response.body
    assert b"translation-review-navigation" in script_response.body
    assert b"ewp-active-translation-review-v1" in script_response.body
    assert (
        b"translationReviewDirty && !(await saveEnhancedTranslationReview())"
        in script_response.body
    )
    assert b"clearEwpBrowserState" in script_response.body
    assert b"Choose audio file" in script_response.body
    assert b"selected-media/upload" in script_response.body
    assert b"Remove selected work state" in script_response.body
    assert b"workspace-directory" in script_response.body
    assert b"managed-sources/inventory" in script_response.body
    assert b"Delete selected unreferenced copies" in script_response.body
    assert b"translation-provider" in script_response.body
    assert (
        b'<option value="openrouter">OpenRouter (cloud)</option><option value="lm-studio">'
        in script_response.body
    )
    assert b"bielik-11b-v3.0-instruct" in script_response.body
    assert b"translation-set-openrouter-key" in script_response.body
    assert b"translation-check-provider" in script_response.body
    stylesheet_response = dispatch_get(
        config, server_port=8765, host="localhost:8765", target="/assets/app.css"
    )
    assert b"review-control-groups" in stylesheet_response.body
    assert b"translation-review-navigation" in stylesheet_response.body
    assert b".workflow-failed .workflow-circle" in stylesheet_response.body
    assert b"translate(-50%, -50%) rotate(45deg)" in stylesheet_response.body
    assert b"GUI_REVIEW_SELECTION_REQUIRED" in script_response.body
    assert b"speaker_labels: reviewDocument.speaker_labels" in script_response.body
    assert b"startsWithTerminalPunctuation" in script_response.body
    assert b"Draft saved before merge" in script_response.body
    assert b"mergeReviewBlock" in script_response.body
    assert b"separatedByPointer" in script_response.body
    assert b"/\\\\s" not in script_response.body
    assert b"/\\s" in script_response.body
    assert b"Only pending" in script_response.body
    assert b"Previous occurrence" in script_response.body
    assert b"Versioned project dictionary published" in script_response.body
    assert b"Refresh dictionary list" in script_response.body
    assert b"Available ${kind} dictionaries" in script_response.body
    assert b"item.open = !item.hidden" in script_response.body
    assert b"Proceed to translation" in script_response.body
    assert b"Verified transcript source loaded" in script_response.body
    assert b'behavior: "smooth"' in script_response.body
    assert b"installConfirmationHighlight" in script_response.body
    assert b"confirmation is required" in script_response.body
    assert b"Next step: correction" in script_response.body
    assert b"stage-queue-${definition.id}" in script_response.body
    assert b'id: "correction"' in script_response.body
    assert b'id: "review"' in script_response.body
    assert b'id: "translation"' in script_response.body
    assert b'id: "semantic-review"' in script_response.body
    assert b"Select all actionable items" in script_response.body
    assert b'workflowIndicator("not started"' in script_response.body
    assert b"Reopen correction" in script_response.body
    assert b"Reopen review / export" in script_response.body
    assert b"Reopen translation" in script_response.body
    assert b"Reopen semantic review" in script_response.body
    assert b'correctionForm.elements.namedItem("confirmed").checked = false' in script_response.body
    assert (
        b'translationForm.elements.namedItem("confirmed").checked = false' in script_response.body
    )
    assert b"Skip LLM-assisted correction" in script_response.body
    assert b"Skip LLM-assisted translation" in script_response.body
    assert (
        b"LLM-assisted translation skipped. An editable manual translation review is open below"
        in script_response.body
    )
    assert b"translationReviewSourceKey" in script_response.body
    assert b"installFeedbackSlots();" in script_response.body
    assert b"Clear current translation review" in response.body
    assert b"this output is now open in manual review" in script_response.body
    assert b"Completed canonical transcription loaded" in script_response.body
    assert b"Provider settings" in script_response.body
    assert b"Set an OpenRouter API key" in script_response.body
    assert b"Check connection" in script_response.body
    assert b"API OK" in script_response.body
    assert b"GUI_[A-Z_]*CONFIRMATION_REQUIRED" in script_response.body
    assert b"GUI_OUTPUT_REQUIRED" in script_response.body
    assert b"API check" in script_response.body
    assert b"not saved in the project or workspace" in script_response.body
    assert b"Gemini 2.5 Flash Lite" in script_response.body
    assert b"Gemini 2.5 Pro" in script_response.body
    assert b"Enter ID manually" in script_response.body
    assert b"Check models and pricing" in script_response.body
    assert b"does not send transcript text" in script_response.body
    assert b"server-session-only" not in script_response.body
    assert b"#operation-status" in script_response.body
    assert b"Save current work state" in script_response.body
    assert b"/api/v1/workspaces/save" in script_response.body
    assert b"if (reviewDocument && reviewDirty) await saveReviewDraft()" in script_response.body
    assert b"workspace-autosave" in script_response.body
    assert b"restoreWorkspaceReviewIfPresent" in script_response.body
    assert b"60000" in script_response.body
    assert b"no tracked workflow-field changes" in script_response.body
    assert b"Changes pending for auto-save" in script_response.body
    assert b"will retry" in script_response.body
    assert b"active GUI server process" in script_response.body
    assert b"workspace JSON does not embed transcript text, API keys" in script_response.body
    style_response = dispatch_get(
        config, server_port=8765, host="localhost:8765", target="/assets/app.css"
    )
    assert b".workspace-autosave" in style_response.body
    assert b".stage-queue" in style_response.body
    assert b"[hidden]" in style_response.body
    assert b'postReview("load"' in script_response.body
    assert b'postReview("session/restore"' in script_response.body


def test_untrusted_host_and_unknown_route_have_codes(tmp_path: Path) -> None:
    config = WebConfiguration.create(port=8765)
    response = dispatch_get(config, server_port=8765, host="attacker.example", target="/")
    assert response.status == 421
    assert json.loads(response.body)["error"]["code"] == "GUI_HOST_REJECTED"
    response = dispatch_get(config, server_port=8765, host="[::1]:8765", target="/missing")
    assert response.status == 404
    assert json.loads(response.body)["error"]["code"] == "GUI_ROUTE_NOT_FOUND"


def test_web_configuration_rejects_invalid_port() -> None:
    with pytest.raises(ValueError, match="port"):
        WebConfiguration.create(port=65536)


def test_wsl_browser_open_uses_windows_bridge_without_terminal_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "read_text", lambda self, encoding: "microsoft-standard-WSL2")
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: name if name in {"cmd.exe", "powershell.exe"} else None,
    )
    run = Mock()
    run.return_value.returncode = 0
    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)

    _open_browser("http://127.0.0.1:8765/")

    assert run.call_args.args[0] == ["cmd.exe", "/C", "start", "", "http://127.0.0.1:8765/"]
    assert run.call_args.kwargs["stderr"] is subprocess.PIPE


def test_wsl_browser_open_uses_init_after_exec_format_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "read_text", lambda self, encoding: "microsoft-standard-WSL2")
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: name if name in {"cmd.exe", "powershell.exe"} else None,
    )
    monkeypatch.setattr(Path, "is_file", lambda self: str(self) == "/init")
    calls: list[tuple[list[str], object]] = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append((command, kwargs["executable"]))
        if kwargs["executable"] is None:
            raise OSError(8, "Exec format error")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)
    _open_browser("http://127.0.0.1:8765/")
    assert [executable for _, executable in calls] == [None, "/init"]
    assert calls[1][0] == ["cmd.exe", "/C", "start", "", "http://127.0.0.1:8765/"]


def test_wsl_browser_open_reports_windows_failure_without_gio(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(Path, "read_text", lambda self, encoding: "microsoft-standard-WSL2")
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: name if name in {"cmd.exe", "powershell.exe"} else None,
    )
    run = Mock()
    run.return_value.returncode = 1
    run.return_value.stderr = "interop failed"
    opened = Mock()
    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)
    monkeypatch.setattr("ewp_transcripts.web_server.webbrowser.open", opened)

    _open_browser("http://127.0.0.1:8765/")

    opened.assert_not_called()
    assert "GUI_BROWSER_OPEN_FAILED" in capsys.readouterr().err


def test_selection_cache_copies_and_cleans_an_explicitly_selected_file(tmp_path: Path) -> None:
    cache = GuiSelectionCache()
    cache._root = tmp_path / "cache"  # noqa: SLF001 - assert owned-workdir cleanup behavior

    selected = cache.store(filename="episode.wav", content_length=5, source=BytesIO(b"audio"))

    assert selected.read_bytes() == b"audio"
    cache.close()
    assert not selected.exists()


def test_native_media_picker_upload_route_returns_a_session_copy(tmp_path: Path) -> None:
    cache = GuiSelectionCache()
    cache._root = tmp_path / "cache"  # noqa: SLF001 - isolate the owned temporary workdir
    body = b"audio"
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    headers["X-EWP-Filename"] = "episode.wav"
    handler.headers = headers
    handler.path = "/api/v1/selected-media/upload"
    handler.rfile = BytesIO(body)
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_selections=cache,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    copied = Path(json.loads(response.body)["path"])
    assert response.status == 200
    assert copied.read_bytes() == body
    cache.close()


def test_canonical_picker_import_remains_after_selection_cache_closes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = b'{"canonical":"validated by fake"}'
    output = tmp_path / "output"
    cache = GuiSelectionCache()
    cache._root = tmp_path / "cache"  # noqa: SLF001 - isolate this request's cache
    monkeypatch.setattr(
        "ewp_transcripts.web_server.require_completed_canonical_result",
        lambda _: SimpleNamespace(
            job_id="episode",
            episode=SimpleNamespace(language="pl"),
            processing=SimpleNamespace(models=[SimpleNamespace(role="asr", name="large-v2")]),
        ),
    )
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    headers["X-EWP-Filename"] = "episode_results.json"
    headers["X-EWP-Output-Directory"] = str(output)
    handler.headers = headers
    handler.path = "/api/v1/import-canonical-file"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    transcriptions.register_completed_result.return_value = (
        SimpleNamespace(model_dump=lambda mode: {"status": "completed"}),
        True,
    )
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_selections=cache,
        gui_workflows=GuiWorkflowController(),
        gui_transcriptions=transcriptions,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()
    cache.close()

    response = write_response.call_args.args[0]
    assert response.status == 200
    preserved = transcriptions.register_completed_result.call_args.args[0]
    assert preserved.read_bytes() == body
    assert preserved.is_relative_to(output / ".ewp-gui-sources" / "canonical")
    assert len(transcriptions.register_completed_result.call_args.kwargs["source_sha256"]) == 64
    assert transcriptions.register_completed_result.call_args.kwargs["asr_model_name"] == "large-v2"


def test_staged_browser_audio_remains_after_selection_cache_closes(tmp_path: Path) -> None:
    cache = GuiSelectionCache()
    cache._root = tmp_path / "cache"  # noqa: SLF001 - isolate this request's cache
    selected = cache.store(filename="episode.wav", content_length=5, source=BytesIO(b"audio"))
    output = tmp_path / "output"
    base_workflows = GuiWorkflowController()
    plan = {
        "jobs": [
            {
                "job_id": "episode",
                "decision": "process",
                "outputs": {"results": str(output / "episode_results.json")},
            }
        ],
        "inspection": {
            "episodes": [{"sources": [{"fingerprint": {"sha256": sha256_file(selected)}}]}]
        },
    }
    body = json.dumps(
        {
            "path": str(selected),
            "output_directory": str(output),
            "language": "pl",
            "speaker_count": "auto",
            "confirmed": True,
        }
    ).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/transcriptions"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    transcriptions.active_output_directory.return_value = None
    transcriptions.contains_active_input.return_value = False
    transcriptions.contains_active_planned_job.return_value = False
    transcriptions.stage.return_value = SimpleNamespace(
        model_dump=lambda mode: {"status": "staged"}
    )
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_selections=cache,
        gui_workflows=SimpleNamespace(
            resolve_allowed_path=base_workflows.resolve_allowed_path,
            resolve_transcription_options=base_workflows.resolve_transcription_options,
            resolve_group_options=base_workflows.resolve_group_options,
            validate_model=lambda speech: None,
            completed_plan=Mock(return_value=plan),
        ),
        gui_transcriptions=transcriptions,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()
    cache.close()

    assert write_response.call_args.args[0].status == 202
    preserved = transcriptions.stage.call_args.args[0]
    assert preserved.read_bytes() == b"audio"
    assert preserved.is_relative_to(output / ".ewp-gui-sources" / "media")


def test_write_response_ignores_abandoned_browser_connection() -> None:
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.wfile = Mock()
    handler.wfile.write.side_effect = BrokenPipeError()

    handler._write_response(WebResponse(HTTPStatus.OK, "text/plain", b"ok"))

    handler.send_response.assert_called_once_with(HTTPStatus.OK)
    handler.end_headers.assert_called_once_with()
    handler.wfile.write.assert_called_once_with(b"ok")


def test_post_rejects_cross_origin_before_reading_body() -> None:
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "https://attacker.example"
    handler.headers = headers
    handler.path = "/api/v1/inspect"
    handler.rfile = BytesIO(b"")
    handler.server = SimpleNamespace(server_port=8765)
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 403
    assert json.loads(response.body)["error"]["code"] == "GUI_ORIGIN_REJECTED"


def test_transcription_post_requires_active_csrf_token() -> None:
    body = b'{"path":"/tmp/source.wav","confirmed":true}'
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    handler.headers = headers
    handler.path = "/api/v1/transcriptions"
    handler.rfile = BytesIO(body)
    handler.server = SimpleNamespace(server_port=8765, gui_csrf_token="expected")
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 403
    assert json.loads(response.body)["error"]["code"] == "GUI_CSRF_REJECTED"


def test_output_folder_route_returns_validated_local_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("ewp_transcripts.web_server._select_local_directory", lambda: str(tmp_path))
    body = b"{}"
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/select-output-directory"
    handler.rfile = BytesIO(body)
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_workflows=GuiWorkflowController(),
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 200
    assert json.loads(response.body)["path"] == str(tmp_path)


def test_clear_current_queue_requires_confirmation() -> None:
    body = b"{}"
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/transcriptions/clear-current"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    handler.server = SimpleNamespace(
        server_port=8765, gui_csrf_token="expected", gui_transcriptions=transcriptions
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 400
    assert json.loads(response.body)["error"]["code"] == "GUI_CLEAR_CONFIRMATION_REQUIRED"
    transcriptions.clear_current_state.assert_not_called()


def test_managed_source_inventory_exposes_only_audited_copy(tmp_path: Path) -> None:
    output = tmp_path / "output"
    source = tmp_path / "episode.wav"
    source.write_bytes(b"audio")
    preserved, _ = preserve_gui_selected_source(source, output_directory=output, category="media")
    body = json.dumps({"output_directory": str(output), "storage_directory": ""}).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/managed-sources/inventory"
    handler.rfile = BytesIO(body)
    workspaces = Mock()
    workspaces.documents.return_value = ()
    transcriptions = Mock()
    transcriptions.jobs.return_value = ()
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_workflows=GuiWorkflowController(),
        gui_workspaces=workspaces,
        workspace_controller=Mock(return_value=workspaces),
        workspace_catalogs=Mock(return_value=(("", "Default", workspaces),)),
        gui_transcriptions=transcriptions,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    payload = json.loads(response.body)
    assert response.status == 200
    assert payload["workspace_count"] == 0
    assert payload["sources"] == [
        {
            "relative_path": preserved.relative_to(output / ".ewp-gui-sources").as_posix(),
            "path": str(preserved),
            "category": "media",
            "filename": "episode.wav",
            "sha256": sha256_file(preserved),
            "size_bytes": 5,
            "removable": True,
            "references": [],
        }
    ]


def test_workspace_list_combines_default_and_selected_catalogs(tmp_path: Path) -> None:
    body = json.dumps({"storage_directory": str(tmp_path / "custom")}).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/workspaces/list"
    handler.rfile = BytesIO(body)
    default_summary = Mock(workspace_id="default-id")
    default_summary.model_dump.return_value = {"workspace_id": "default-id", "name": "Default"}
    custom_summary = Mock(workspace_id="custom-id")
    custom_summary.model_dump.return_value = {"workspace_id": "custom-id", "name": "Custom"}
    default_catalog = Mock(state_directory=tmp_path / "default")
    default_catalog.list.return_value = (default_summary,)
    custom_catalog = Mock(state_directory=tmp_path / "custom")
    custom_catalog.list.return_value = (custom_summary,)
    default_catalog.document_path.return_value = tmp_path / "default/default-id.json"
    custom_catalog.document_path.return_value = tmp_path / "custom/custom-id.json"
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        workspace_controller=Mock(return_value=custom_catalog),
        workspace_catalogs=Mock(
            return_value=(
                ("", "Default", default_catalog),
                (str(tmp_path / "custom"), "Custom", custom_catalog),
            )
        ),
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 200
    assert json.loads(response.body)["workspaces"] == [
        {
            "workspace_id": "default-id",
            "name": "Default",
            "storage_directory": "",
            "catalog": "Default",
            "workspace_file": str(tmp_path / "default/default-id.json"),
        },
        {
            "workspace_id": "custom-id",
            "name": "Custom",
            "storage_directory": str(tmp_path / "custom"),
            "catalog": "Custom",
            "workspace_file": str(tmp_path / "custom/custom-id.json"),
        },
    ]


def test_remove_selected_queue_items_requires_confirmation() -> None:
    body = json.dumps({"job_ids": ["job-a"]}).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/transcriptions/remove-batch"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    handler.server = SimpleNamespace(
        server_port=8765, gui_csrf_token="expected", gui_transcriptions=transcriptions
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 400
    assert json.loads(response.body)["error"]["code"] == "GUI_QUEUE_REMOVE_INVALID"
    transcriptions.remove_inactive.assert_not_called()


def test_remove_selected_queue_items_returns_per_item_outcome() -> None:
    body = json.dumps({"job_ids": ["job-a", "job-b"], "confirmed": True}).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/transcriptions/remove-batch"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    transcriptions.remove_inactive.return_value = (("job-a",), ("job-b",))
    handler.server = SimpleNamespace(
        server_port=8765, gui_csrf_token="expected", gui_transcriptions=transcriptions
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 200
    assert json.loads(response.body) == {"removed": ["job-a"], "not_found": ["job-b"]}
    transcriptions.remove_inactive.assert_called_once_with(("job-a", "job-b"))


def test_workflow_skip_rejects_audio_instead_of_a_canonical_result(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"not a canonical result")
    body = json.dumps({"result_path": str(media), "stage": "correction"}).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/transcriptions/workflow-skip"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_workflows=GuiWorkflowController((tmp_path.resolve(),)),
        gui_transcriptions=transcriptions,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 400
    assert json.loads(response.body)["error"]["code"] == "GUI_WORKFLOW_RESULT_INVALID"
    transcriptions.skip_workflow_stage.assert_not_called()


def test_workflow_skip_batch_updates_both_selected_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    results = [tmp_path / f"episode-{number}_results.json" for number in (1, 2)]
    for result in results:
        result.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "ewp_transcripts.web_server.require_completed_canonical_result", lambda _: None
    )
    result_paths = [str(result) for result in results]
    body = json.dumps({"result_paths": result_paths, "stage": "correction"}).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/transcriptions/workflow-skip-batch"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    transcriptions.skip_workflow_stages.return_value = tuple(result_paths)
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_workflows=GuiWorkflowController(),
        gui_transcriptions=transcriptions,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 200
    assert json.loads(response.body) == {"skipped": result_paths, "not_found": []}
    transcriptions.skip_workflow_stages.assert_called_once_with(tuple(result_paths), "correction")


def test_translation_review_prepare_accepts_a_manual_target_language(tmp_path: Path) -> None:
    result = tmp_path / "episode_results.json"
    result.write_text("{}", encoding="utf-8")
    review_directory = tmp_path / "translation-reviews"
    body = json.dumps(
        {
            "result_path": str(result),
            "revision_path": "",
            "parent_translation_path": "",
            "review_output_directory": str(review_directory),
            "target_language": "pl",
        }
    ).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/translation-reviews/prepare"
    handler.rfile = BytesIO(body)
    reviews = Mock()
    reviews.prepare.return_value = {"review_path": str(review_directory / "review.txt")}
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_translation_reviews=reviews,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    reviews.prepare.assert_called_once_with(
        result=str(result),
        revision="",
        parent="",
        output=str(review_directory),
        target_language="pl",
    )
    assert write_response.call_args.args[0].status == 200


def test_translation_review_preview_forwards_explicit_empty_unit_permission(
    tmp_path: Path,
) -> None:
    body = json.dumps(
        {
            "review_path": str(tmp_path / "review.txt"),
            "result_path": str(tmp_path / "episode_results.json"),
            "revision_path": "",
            "parent_translation_path": "",
            "allow_empty_units": True,
        }
    ).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/translation-reviews/preview"
    handler.rfile = BytesIO(body)
    reviews = Mock()
    reviews.preview.return_value = {"statistics": {"intentionally_empty_units": 1}}
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_translation_reviews=reviews,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    reviews.preview.assert_called_once_with(
        review=str(tmp_path / "review.txt"),
        result=str(tmp_path / "episode_results.json"),
        revision="",
        parent="",
        allow_empty_units=True,
    )
    assert write_response.call_args.args[0].status == 200


def test_review_reports_missing_source_with_reimport_instruction(tmp_path: Path) -> None:
    missing = tmp_path / ".ewp-gui-sources" / "episode_results.json"
    body = json.dumps(
        {"result_path": str(missing), "review_output_directory": str(tmp_path / "reviews")}
    ).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/reviews/prepare"
    handler.rfile = BytesIO(body)
    reviews = Mock()
    reviews.prepare.side_effect = FileNotFoundError(2, "No such file", str(missing))
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_reviews=reviews,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    payload = json.loads(response.body)
    assert response.status == 400
    assert payload["error"]["code"] == "GUI_REVIEW_FILE_MISSING"
    assert str(missing) in payload["error"]["message"]
    assert "Add the original canonical *_results.json" in payload["error"]["message"]


def test_transcription_queue_explains_an_existing_result(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    output = tmp_path / "output"
    output.mkdir()
    existing = output / "episode_results.json"
    existing.write_text("{}", encoding="utf-8")
    body = json.dumps(
        {
            "path": str(media),
            "output_directory": str(output),
            "language": "pl",
            "speaker_count": "auto",
            "confirmed": True,
        }
    ).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/transcriptions"
    handler.rfile = BytesIO(body)
    transcriptions = Mock()
    transcriptions.active_output_directory.return_value = None
    transcriptions.contains_active_input.return_value = False
    workflow = SimpleNamespace(
        validate_model=lambda speech: None,
        resolve_allowed_path=lambda path, directory=False: Path(path),
        resolve_transcription_options=lambda document: ("pl", "auto"),
        resolve_group_options=GuiWorkflowController().resolve_group_options,
        completed_plan=lambda *args, **kwargs: {
            "jobs": [
                {
                    "decision": "skip",
                    "existing_result": {"path": str(existing)},
                }
            ]
        },
    )
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_workflows=workflow,
        gui_transcriptions=transcriptions,
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 409
    payload = json.loads(response.body)
    assert payload["error"]["code"] == "GUI_TRANSCRIPTION_ALREADY_EXISTS"
    assert str(existing) in payload["error"]["message"]


def test_preview_resources_are_fixed_local_routes() -> None:
    assert "font-src 'self'" in SECURITY_HEADERS["Content-Security-Policy"]
    config = WebConfiguration.create(port=8765)
    for asset, expected in [
        ("brand/logo.svg", b"<svg"),
        ("brand/gear.svg", b"gear--gear-ring"),
        ("brand/montserrat.woff2", b"wOF2"),
        ("brand/mono.woff2", b"wOF2"),
        ("brand/NOTICE.txt", b"Cyryl"),
        ("brand/NOTICE_PL.txt", "Właściciel praw".encode()),
        ("brand/LICENSE-ASSETS_PL.txt", b"warunki dystrybucji"),
    ]:
        response = dispatch_get(
            config, server_port=8765, host="localhost:8765", target="/assets/" + asset
        )
        assert response.status == 200
        assert expected in response.body
    for path in ["/assets/brand/../../config.py", "/assets/brand/unknown.svg"]:
        assert (
            dispatch_get(config, server_port=8765, host="localhost:8765", target=path).status == 404
        )


@pytest.mark.parametrize("token", ["expected", "wrong"])
def test_dependency_test_is_explicit_and_requires_csrf(monkeypatch, token) -> None:
    body = b"{}"
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(server_port=8765, gui_csrf_token="expected")
    handler.path = "/api/v1/dependencies/test"
    handler.headers = Message()
    for name, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": token,
    }.items():
        handler.headers[name] = value
    handler.rfile = BytesIO(body)
    handler._write_response = Mock()
    doctor = Mock(return_value=SimpleNamespace(model_dump=lambda mode: {"ready": False}))
    monkeypatch.setattr("ewp_transcripts.web_server.doctor", doctor)
    handler.do_POST()
    response = handler._write_response.call_args.args[0]
    if token == "expected":
        assert response.status == 200
        assert json.loads(response.body) == {"ready": False}
        assert doctor.call_args.kwargs["test_speech_runtime"] is True
    else:
        assert response.status == 403
        doctor.assert_not_called()


@pytest.mark.parametrize("tested", [False, True])
def test_gui_doctor_requires_a_completed_dependency_test(monkeypatch, tested) -> None:
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(
        server_port=8765, gui_csrf_token="expected", gui_dependencies_tested=tested
    )
    handler.path = "/api/v1/dependencies/doctor"
    handler.headers = Message()
    for name, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": "2",
        "X-EWP-CSRF": "expected",
    }.items():
        handler.headers[name] = value
    handler.rfile = BytesIO(b"{}")
    handler._write_response = Mock()
    doctor = Mock(return_value=SimpleNamespace(model_dump=lambda mode: {"ready": False}))
    monkeypatch.setattr("ewp_transcripts.web_server.doctor", doctor)
    handler.do_POST()
    response = handler._write_response.call_args.args[0]
    if tested:
        assert response.status == 200
        assert doctor.call_args.kwargs["test_speech_runtime"] is False
    else:
        assert response.status == 409
        assert json.loads(response.body)["error"]["code"] == "GUI_DEPENDENCY_TEST_REQUIRED"
        doctor.assert_not_called()


@pytest.mark.parametrize("token", ["expected", "wrong"])
@pytest.mark.parametrize(
    "route", ["profiles", "profile-save", "view", "visibility", "edition", "export", "import"]
)
def test_library_routes_require_active_session_before_access(route: str, token: str) -> None:
    """Even profile reads and library metadata remain inside the local session boundary."""
    request = {
        "name": "My profile",
        "colors": ["#123456"],
        "path": "dictionary.json",
        "sha256": "0" * 64,
        "visible": False,
        "document": {},
        "payload": "{}",
        "directory": "dictionaries",
    }
    body = json.dumps(request).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    service = Mock()
    for method in (
        "profiles",
        "save_profile",
        "view",
        "visibility",
        "edition",
        "export_dictionary",
        "import_dictionary",
    ):
        getattr(service, method).return_value = {"ok": True}
    handler.server = SimpleNamespace(
        server_port=8765, gui_csrf_token="expected", gui_library=service
    )
    handler.path = f"/api/v1/dictionaries/{route}"
    handler.headers = Message()
    for name, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": token,
    }.items():
        handler.headers[name] = value
    handler.rfile = BytesIO(body)
    handler._write_response = Mock()
    handler.do_POST()
    response = handler._write_response.call_args.args[0]
    assert response.status == (200 if token == "expected" else 403)
    if token == "wrong":
        assert not service.mock_calls


def test_supplied_gear_animation_has_a_pinned_style_permission() -> None:
    """Allow the owner's exact animated SVG CSS without enabling arbitrary inline styles."""
    import base64
    import hashlib
    import xml.etree.ElementTree as ET

    response = dispatch_get(
        WebConfiguration.create(port=8765),
        server_port=8765,
        host="localhost:8765",
        target="/assets/brand/gear.svg",
    )
    assert response.status == 200 and response.content_type == "image/svg+xml"
    root = ET.fromstring(response.body)
    style = next(node.text for node in root.iter() if node.tag.endswith("style"))
    assert style is not None and "prefers-reduced-motion" in style
    digest = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    policy = SECURITY_HEADERS["Content-Security-Policy"]
    assert f"'sha256-{digest}'" in policy
    assert "'unsafe-inline'" not in policy
    assert not any(node.tag.endswith("script") for node in root.iter())


@pytest.mark.parametrize("token", ["expected", "wrong"])
@pytest.mark.parametrize("route", ["load", "import"])
def test_user_profile_routes_require_active_session(route: str, token: str) -> None:
    request = {"profile": {}}
    body = json.dumps(request).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    profiles = Mock()
    profiles.load.return_value = profiles.restore.return_value = {"profile": {}}
    handler.server = SimpleNamespace(
        server_port=8765, gui_csrf_token="expected", gui_profiles=profiles
    )
    handler.path = f"/api/v1/profile/{route}"
    handler.headers = Message()
    for name, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": token,
    }.items():
        handler.headers[name] = value
    handler.rfile = BytesIO(body)
    handler._write_response = Mock()
    handler.do_POST()
    assert handler._write_response.call_args.args[0].status == (200 if token == "expected" else 403)
    if token == "wrong":
        assert not profiles.mock_calls


def test_completed_workspace_history_recovers_without_original_media(tmp_path: Path) -> None:
    result = tmp_path / "episode_results.json"
    result.write_text("{}")
    now = datetime.now(UTC)
    job = GuiTranscriptionJob(
        job_id="saved",
        status="completed",
        input_path=str(tmp_path / "moved.wav"),
        output_directory=str(tmp_path),
        planned_job_id="episode",
        planned_result_path=str(result),
        result_path=str(result),
        language="pl",
        speaker_count=1,
        created_at=now,
        updated_at=now,
    )
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    queue = Mock()
    queue.replace_terminal_jobs.return_value = 1
    resolver = Mock()

    def resolve(path, **kwargs):
        if path == job.input_path:
            raise FileNotFoundError(path)
        return Path(path)

    resolver.resolve_allowed_path.side_effect = resolve
    handler.server = SimpleNamespace(gui_workflows=resolver, gui_transcriptions=queue)
    assert handler._restore_workspace_terminal_jobs((job,)) == 1
    queue.replace_terminal_jobs.assert_called_once_with((job,))


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "evil.invalid"},
        {"Host": "127.0.0.1:8765", "Origin": "https://evil.invalid"},
        {"Host": "127.0.0.1:8765", "Sec-Fetch-Site": "cross-site"},
    ],
)
def test_export_attachment_rejects_foreign_requests(headers) -> None:
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.path = "/api/v1/export-downloads/opaque"
    handler.headers = Message()
    for key, value in headers.items():
        handler.headers[key] = value
    downloads = Mock()
    handler.server = SimpleNamespace(server_port=8765, gui_downloads=downloads)
    handler.send_error = Mock()
    handler.do_GET()
    handler.send_error.assert_called_once_with(HTTPStatus.FORBIDDEN)
    downloads.open.assert_not_called()


def test_export_attachment_is_exact_and_preserves_unicode_filename() -> None:
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.path = "/api/v1/export-downloads/opaque"
    handler.headers = Message()
    handler.headers["Host"] = "127.0.0.1:8765"
    downloads = Mock()
    downloads.open.return_value = ("Żółć_revision_002.srt", b"published bytes\r\n")
    handler.server = SimpleNamespace(server_port=8765, gui_downloads=downloads)
    handler.send_response = Mock()
    handler._headers = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.wfile = BytesIO()
    handler.do_GET()
    assert handler.wfile.getvalue() == b"published bytes\r\n"
    handler._headers.assert_called_once_with(
        content_type="application/octet-stream", content_length=17
    )
    disposition = handler.send_header.call_args.args[1]
    assert disposition.startswith("attachment; filename=export; filename*=UTF-8''%C5%BB")
    assert disposition.endswith("_revision_002.srt")


@pytest.mark.parametrize("token, expected", [("expected", 200), ("", 403)])
def test_existing_exports_list_requires_session_token(token: str, expected: int) -> None:
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    body = json.dumps(
        {"result_path": "result", "revision_path": "revision", "export_output_directory": "exports"}
    ).encode()
    handler.path = "/api/v1/exports/list"
    handler.headers = Message()
    for key, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": token,
    }.items():
        handler.headers[key] = value
    handler.rfile = BytesIO(body)
    downloads = Mock()
    downloads.list.return_value = {"exports": [], "unavailable": []}
    handler.server = SimpleNamespace(
        server_port=8765, gui_csrf_token="expected", gui_downloads=downloads
    )
    handler._write_response = Mock()
    handler.do_POST()
    assert handler._write_response.call_args.args[0].status == expected
    if expected == 403:
        downloads.list.assert_not_called()
    else:
        downloads.list.assert_called_once_with(
            result="result", revision="revision", translation="", directory="exports"
        )


@pytest.mark.parametrize("action", ["check", "estimate"])
@pytest.mark.parametrize("token,expected", [("expected", 200), ("", 403)])
def test_cloud_read_only_checks_require_csrf_and_use_shared_session_key(action, token, expected):
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    body = json.dumps({"items": [{"path": "selected.wav"}]}).encode()
    handler.path = f"/api/v1/speech/{action}"
    handler.headers = Message()
    for key, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": token,
    }.items():
        handler.headers[key] = value
    handler.rfile = BytesIO(body)
    speech = Mock()
    speech.check_key.return_value = {"status": "ok"}
    speech.refresh.return_value = {"recordings": 1, "models": []}
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_speech=speech,
        gui_openrouter_api_key="shared-fake-key",
        gui_openrouter_api_key_env="EWP_TEST_UNUSED_KEY",
    )
    handler._write_response = Mock()
    handler.do_POST()
    response = handler._write_response.call_args.args[0]
    assert response.status == expected
    assert b"shared-fake-key" not in response.body
    if expected == 403:
        assert not speech.method_calls
    elif action == "check":
        speech.check_key.assert_called_once_with("shared-fake-key")
        speech.refresh.assert_not_called()
    else:
        speech.refresh.assert_called_once_with([{"path": "selected.wav"}])
        speech.check_key.assert_not_called()


@pytest.mark.parametrize("failure", [BrokenPipeError, ConnectionResetError, ConnectionAbortedError])
@pytest.mark.parametrize("at_headers", [False, True])
def test_review_audio_browser_disconnect_closes_file_without_stack(tmp_path, failure, at_headers):
    path = tmp_path / "preview.wav"
    path.write_bytes(b"audio" * 20000)
    audio = path.open("rb")
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.path = "/api/v1/review-audio/preview"
    handler.headers = Message()
    handler.headers["Host"] = "127.0.0.1:8765"
    handler.server = SimpleNamespace(
        server_port=8765, gui_media=Mock(open=Mock(return_value=audio))
    )
    handler.send_response = Mock()
    handler._headers = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock(side_effect=failure() if at_headers else None)
    handler.wfile = Mock()
    if not at_headers:
        handler.wfile.write.side_effect = failure()
    handler._stream_review_audio()
    assert audio.closed


def test_review_audio_does_not_hide_other_stream_failures(tmp_path):
    path = tmp_path / "preview.wav"
    path.write_bytes(b"audio")
    audio = path.open("rb")
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.path = "/api/v1/review-audio/preview"
    handler.headers = Message()
    handler.headers["Host"] = "127.0.0.1:8765"
    handler.server = SimpleNamespace(
        server_port=8765, gui_media=Mock(open=Mock(return_value=audio))
    )
    handler.send_response = Mock()
    handler._headers = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.wfile = Mock(write=Mock(side_effect=OSError("genuine I/O error")))
    with pytest.raises(OSError, match="genuine I/O"):
        handler._stream_review_audio()
    assert audio.closed


@pytest.mark.parametrize("failure", [BrokenPipeError, ConnectionResetError, ConnectionAbortedError])
@pytest.mark.parametrize("at_headers", [False, True])
def test_json_response_browser_disconnect_is_not_an_application_failure(failure, at_headers):
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.send_response = Mock()
    handler._headers = Mock()
    handler.end_headers = Mock(side_effect=failure() if at_headers else None)
    handler.wfile = Mock()
    if not at_headers:
        handler.wfile.write.side_effect = failure()
    handler._write_response(WebResponse(HTTPStatus.OK, "application/json", b"{}"))


def test_read_only_key_check_can_check_typed_key_without_setting_or_saving_it():
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    body = json.dumps({"api_key": "typed-fake-key"}).encode()
    handler.path = "/api/v1/speech/check"
    handler.headers = Message()
    for key, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": "expected",
    }.items():
        handler.headers[key] = value
    handler.rfile = BytesIO(body)
    speech = Mock(check_key=Mock(return_value={"status": "ok"}))
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_speech=speech,
        gui_openrouter_api_key="existing-fake-key",
        gui_openrouter_api_key_env="EWP_TEST_UNUSED_KEY",
        gui_credentials=Mock(),
    )
    handler._write_response = Mock()
    handler.do_POST()
    response = handler._write_response.call_args.args[0]
    assert response.status == 200 and b"typed-fake-key" not in response.body
    speech.check_key.assert_called_once_with("typed-fake-key")
    assert handler.server.gui_openrouter_api_key == "existing-fake-key"
    assert not handler.server.gui_credentials.method_calls


def test_restored_cloud_job_requires_fresh_http_consent_even_if_start_boolean_is_true(tmp_path):
    import time

    from ewp_transcripts.config import ApplicationConfig, SpeechConfig
    from ewp_transcripts.web_jobs import GuiTranscriptionQueue

    source = tmp_path / "episode.wav"
    source.write_bytes(b"synthetic media")
    result = tmp_path / "episode_results.json"
    workflows = GuiWorkflowController()
    seen = []
    active_key = {"value": ""}
    key_check = Mock(return_value={"status": "ok"})
    queue = GuiTranscriptionQueue(
        config=ApplicationConfig(),
        api_key_provider=lambda: active_key["value"],
        service=lambda path, **kw: seen.append(kw) or SimpleNamespace(result_path=result),
    )
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_transcriptions=queue,
        gui_speech=SimpleNamespace(check_key=key_check),
        gui_workflows=SimpleNamespace(
            resolve_allowed_path=workflows.resolve_allowed_path,
            resolve_transcription_options=workflows.resolve_transcription_options,
            run=Mock(
                return_value=SimpleNamespace(
                    status="completed",
                    result={"jobs": [{"job_id": "episode", "outputs": {"results": str(result)}}]},
                )
            ),
        ),
    )

    def post(action, body):
        raw = json.dumps(body).encode()
        handler.path = "/api/v1/transcriptions/" + action
        handler.headers = Message()
        for key, value in {
            "Host": "127.0.0.1:8765",
            "Origin": "http://127.0.0.1:8765",
            "Content-Length": str(len(raw)),
            "X-EWP-CSRF": "expected",
        }.items():
            handler.headers[key] = value
        handler.rfile = BytesIO(raw)
        handler._write_response = Mock()
        handler.do_POST()
        response = handler._write_response.call_args.args[0]
        return response.status, json.loads(response.body)

    try:
        speech = SpeechConfig(provider="openrouter", model="openai/whisper-large-v3")
        assert (
            handler._restore_workspace_staged_jobs(
                (
                    {
                        "input_path": str(source),
                        "output_directory": str(tmp_path),
                        "planned_job_id": "episode",
                        "planned_result_path": str(result),
                        "source_sha256": sha256_file(source),
                        "language": "pl",
                        "speaker_count": 1,
                        "speech": speech.model_dump(mode="json"),
                    },
                )
            )
            == 1
        )
        job = queue.jobs()[0]
        assert job.speech == speech
        for body in (
            {},
            {"cloud_confirmed": False},
            {"cloud_confirmed": True},
            {"cloud_confirmed": True, "cloud_consent_token": None},
        ):
            status, payload = post("start", body)
            assert status == 400 and payload["error"]["code"] == "GUI_CLOUD_CONSENT_REQUIRED"
            assert not seen and queue.jobs()[0].status == "staged"
        status, payload = post(
            "cloud-consent", {"cloud_confirmed": True, "cloud_job_ids": [job.job_id]}
        )
        assert status == 200
        token = payload["cloud_consent_token"]
        queue.revoke_cloud_consent()
        assert post("start", {"cloud_confirmed": True, "cloud_consent_token": token})[0] == 400
        token = post("cloud-consent", {"cloud_confirmed": True, "cloud_job_ids": [job.job_id]})[1][
            "cloud_consent_token"
        ]
        status, payload = post("start", {"cloud_confirmed": True, "cloud_consent_token": token})
        assert status == 400 and payload["error"]["code"] == "GUI_OPENROUTER_KEY_REQUIRED"
        key_check.assert_not_called()
        assert not seen and queue.jobs()[0].status == "staged" and not result.exists()
        active_key["value"] = "fake-key"
        token = post("cloud-consent", {"cloud_confirmed": True, "cloud_job_ids": [job.job_id]})[1][
            "cloud_consent_token"
        ]
        key_check.side_effect = ValueError("synthetic invalid key")
        status, payload = post("start", {"cloud_confirmed": True, "cloud_consent_token": token})
        assert status == 400 and payload["error"]["code"] == "GUI_OPENROUTER_PREFLIGHT_FAILED"
        assert not seen and queue.jobs()[0].status == "staged" and not result.exists()
        key_check.side_effect = None
        token = post("cloud-consent", {"cloud_confirmed": True, "cloud_job_ids": [job.job_id]})[1][
            "cloud_consent_token"
        ]
        assert post("start", {"cloud_confirmed": True, "cloud_consent_token": token})[0] == 202
        assert key_check.call_count == 2
        deadline = time.monotonic() + 2
        while not seen and time.monotonic() < deadline:
            time.sleep(0.005)
        assert (
            len(seen) == 1 and seen[0]["allow_cloud"] is True and seen[0]["config"].speech == speech
        )
    finally:
        queue.close()


@pytest.mark.parametrize("terminal_status", ["failed", "cancelled"])
def test_restore_staged_snapshot_recovers_later_terminal_state(tmp_path, terminal_status):
    from datetime import UTC, datetime
    from uuid import uuid4

    from ewp_transcripts.config import ApplicationConfig
    from ewp_transcripts.domain.models import JobStateRecord
    from ewp_transcripts.web_jobs import GuiTranscriptionQueue

    source = tmp_path / "source.wav"
    source.write_bytes(b"fixed source")
    result = tmp_path / "episode_results.json"
    failed = result.with_suffix(".failed.json")
    now = datetime.now(UTC)
    code = "USER_CANCELLED" if terminal_status == "cancelled" else "SPEECH_ENGINE_ERROR"
    state = JobStateRecord(
        application_version="0.20.0",
        run_id=uuid4(),
        job_id="episode",
        episode_signature_sha256="a" * 64,
        result_version=1,
        status=terminal_status,
        created_at=now,
        updated_at=now,
        failure_code=code,
        failure_message="Retained failure",
    )
    failed.write_text(state.model_dump_json())
    service = Mock()
    queue = GuiTranscriptionQueue(config=ApplicationConfig(), service=service)
    workflows = GuiWorkflowController()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(
        gui_transcriptions=queue,
        gui_workflows=SimpleNamespace(
            resolve_allowed_path=workflows.resolve_allowed_path,
            resolve_transcription_options=workflows.resolve_transcription_options,
            run=Mock(
                return_value=SimpleNamespace(
                    status="completed",
                    result={
                        "jobs": [
                            {
                                "job_id": "episode",
                                "episode_signature_sha256": "a" * 64,
                                "outputs": {"results": str(tmp_path / "episode_results_v002.json")},
                            }
                        ]
                    },
                )
            ),
        ),
    )
    progress = Mock()
    try:
        item = dict(
            input_path=str(source),
            output_directory=str(tmp_path),
            planned_job_id="episode",
            planned_result_path=str(result),
            source_sha256=sha256_file(source),
            language="pl",
            speaker_count=1,
            speech={"provider": "openrouter", "model": "openai/whisper-large-v3"},
        )
        assert handler._restore_workspace_staged_jobs((item,), progress=progress) == 1
        job = queue.jobs()[0]
        assert job.status == terminal_status and job.error["code"] == code
        assert job.speech.provider == "openrouter" and job.result_path is None
        assert job.planned_result_path == str(result) and failed.exists()
        progress.assert_called_once_with(1)
        service.assert_not_called()
        assert handler._restore_workspace_staged_jobs((item,)) == 1
        assert len(queue.jobs()) == 1  # Loading the same retained attempt never duplicates history.
    finally:
        queue.close()


def test_save_preserves_pending_media_before_clearing_temporary_picker(tmp_path):
    from ewp_transcripts.web_workspaces import GuiWorkspaceController

    selection = tmp_path / "picked"
    selection.mkdir()
    source = selection / "episode.wav"
    source.write_bytes(b"selected source bytes")
    output = tmp_path / "output"
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(
        gui_workflows=GuiWorkflowController(), gui_selections=SimpleNamespace(root=selection)
    )
    fields = {"input-path": str(source), "output-path": str(output)}
    media = handler._preserve_workspace_media(
        [{"path": str(source), "name": source.name, "language": "en", "speaker_count": 1}], fields
    )
    assert fields["input-path"] == media[0]["path"] != str(source)
    source.unlink()
    controller = GuiWorkspaceController(
        state_directory=output,
        resolve_path=GuiWorkflowController().resolve_allowed_path,
        temporary_selection_root=selection,
    )
    saved = controller.save(
        name="Pending source", current_step="workspace-heading", fields=fields, pending_media=media
    )
    loaded = controller.load(saved.workspace_id)
    assert loaded.workspace_version == 3 and len(loaded.pending_media) == 1
    assert loaded.pending_media[0].language == "en"
    assert Path(loaded.pending_media[0].path).read_bytes() == b"selected source bytes"
    assert not loaded.staged_jobs and not loaded.terminal_jobs
    Path(loaded.pending_media[0].path).write_bytes(b"changed")
    with pytest.raises(ValueError, match="pending source changed"):
        controller.load(saved.workspace_id)


def test_pending_group_is_preserved_before_output_directory_selection(tmp_path):
    from ewp_transcripts.web_workspaces import GuiWorkspaceController

    selection = tmp_path / "picker"
    selection.mkdir()
    fields = {}
    pending = []
    for speaker in ("left", "right"):
        source = selection / f"episode-{speaker}.wav"
        source.write_bytes(f"selected {speaker}".encode())
        pending.append({"path": str(source), "name": source.name})
    controller = GuiWorkspaceController(
        state_directory=tmp_path / "program/work-state/gui-workspaces",
        resolve_path=GuiWorkflowController().resolve_allowed_path,
        temporary_selection_root=selection,
    )
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(
        gui_workflows=GuiWorkflowController(),
        gui_selections=SimpleNamespace(root=selection),
        gui_workspaces=controller,
    )
    media = handler._preserve_workspace_media(pending, fields)
    for source in selection.iterdir():
        source.unlink()
    saved = controller.save(
        name="task", current_step="workspace-heading", fields=fields, pending_media=media
    )
    loaded = controller.load(saved.workspace_id)
    assert len(loaded.pending_media) == 2
    assert all(Path(item.path).is_file() for item in loaded.pending_media)
    assert not loaded.staged_jobs and not fields


def test_runtime_control_requires_private_token_and_matching_host(monkeypatch):
    from ewp_transcripts.web_runtime import runtime_authorized

    assert not runtime_authorized("", "")
    assert not runtime_authorized("foreign-token", "x" * 64)
    assert runtime_authorized("x" * 64, "x" * 64)
    monkeypatch.setenv("EWP_RUNTIME_TOKEN", "x" * 64)
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(server_port=8765)
    responses = []
    handler._write_response = responses.append
    for headers in (
        {"Host": "evil.example", "X-EWP-Runtime-Token": "x" * 64},
        {"Host": "127.0.0.1:8765"},
    ):
        handler.headers = headers
        handler._runtime_control(stop=False)
        assert responses[-1].status == 403


@pytest.mark.parametrize(
    "source", ["stored", "session", "environment", "typed", "absent", "failed-check", "csrf"]
)
def test_explicit_key_check_loads_saved_key_only_when_needed_and_after_success(monkeypatch, source):
    from ewp_transcripts.credentials import CredentialStoreError

    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    body = json.dumps({"api_key": "typed-fake-key"} if source == "typed" else {}).encode()
    handler.path = "/api/v1/speech/check"
    handler.headers = Message()
    for key, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": "wrong" if source == "csrf" else "expected",
    }.items():
        handler.headers[key] = value
    handler.rfile = BytesIO(body)
    store = Mock()
    store.perform.return_value = "stored-fake-key"
    if source == "absent":
        store.perform.side_effect = CredentialStoreError(
            "No OpenRouter key is saved in the OS store."
        )
    speech = Mock(check_key=Mock(return_value={"status": "ok", "audio_uploaded": False}))
    if source == "failed-check":
        speech.check_key.side_effect = ValueError("Connection failed")
    monkeypatch.setenv("EWP_TEST_ONLY_KEY", "env-fake-key" if source == "environment" else "")
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_speech=speech,
        gui_openrouter_api_key="session-fake-key" if source == "session" else "",
        gui_openrouter_api_key_env="EWP_TEST_ONLY_KEY",
        gui_credentials=store,
    )
    handler._write_response = Mock()
    handler.do_POST()
    response = handler._write_response.call_args.args[0]
    assert not any(
        key.encode() in response.body
        for key in ["stored-fake-key", "env-fake-key", "typed-fake-key", "session-fake-key"]
    )
    if source in {"absent", "failed-check", "csrf"}:
        assert response.status in {400, 403}
        assert not handler.server.gui_openrouter_api_key
    else:
        assert response.status == 200
        assert json.loads(response.body)["loaded_saved_key"] is (source == "stored")
        expected = {
            "session": "session-fake-key",
            "environment": "env-fake-key",
            "typed": "typed-fake-key",
            "stored": "stored-fake-key",
        }[source]
        speech.check_key.assert_called_once_with(expected)
    if source in {"session", "environment", "typed", "csrf"}:
        store.perform.assert_not_called()
    else:
        store.perform.assert_called_once_with("use")
    if source == "stored":
        assert handler.server.gui_openrouter_api_key == "stored-fake-key"
