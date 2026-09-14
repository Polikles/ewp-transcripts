import json
import subprocess
from email.message import Message
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ewp_transcripts import __version__
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
    monkeypatch.setattr("ewp_transcripts.web_server.shutil.which", lambda _: None)
    with pytest.raises(ValueError, match="Enter the output directory path directly"):
        _select_local_directory()


def test_output_folder_dialog_retries_through_cmd_after_direct_interop_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: name if name in {"powershell.exe", "cmd.exe"} else None,
    )
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        if command[0] == "powershell.exe":
            raise OSError(5, "WSL interop unavailable to direct child")
        return SimpleNamespace(returncode=0, stdout="C:\\Users\\DS\\Desktop\\tezt002")

    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)
    assert _select_local_directory() == "C:\\Users\\DS\\Desktop\\tezt002"
    assert [command[0] for command in calls] == ["powershell.exe", "cmd.exe"]


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
        b"Local-first podcast workflow"
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
    assert b"Apply verified revision" in response.body
    assert b'id="clear-review"' in response.body
    assert b'id="restore-review"' in response.body
    assert b"Review status" in response.body
    help_response = dispatch_get(config, server_port=8765, host="localhost:8765", target="/help")
    assert help_response.status == 200
    assert b"Build and start a queue" in help_response.body
    script_response = dispatch_get(
        config, server_port=8765, host="localhost:8765", target="/assets/app.js"
    )
    assert b"const formElement = event.currentTarget" in script_response.body
    assert b"formElement.elements.confirmed" in script_response.body
    assert b"event.currentTarget.elements" not in script_response.body
    assert b"(auto)" in script_response.body
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
    assert b"Draft and history" in script_response.body
    assert b"Undo applied to the current draft" in script_response.body
    assert b"Remove ${speakerId}" in script_response.body
    assert b"GUI_REVIEW_SPEAKER_IN_USE" in script_response.body
    assert b"Completion:" in script_response.body
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
    assert b"translation-provider" in script_response.body
    assert b"translation-set-openrouter-key" in script_response.body
    assert b"translation-check-provider" in script_response.body
    stylesheet_response = dispatch_get(
        config, server_port=8765, host="localhost:8765", target="/assets/app.css"
    )
    assert b"review-control-groups" in stylesheet_response.body
    assert b"translation-review-navigation" in stylesheet_response.body
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
    assert b"workspace-autosave" in script_response.body
    assert b"restoreWorkspaceReviewIfPresent" in script_response.body
    assert b"60000" in script_response.body
    assert b"no tracked workflow-field changes" in script_response.body
    assert b"Changes pending for auto-save" in script_response.body
    assert b"will retry" in script_response.body
    assert b"active GUI server process" in script_response.body
    assert b"API keys, confirmations, transcript text" in script_response.body
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
    assert run.call_args.kwargs["stderr"] is subprocess.DEVNULL


def test_wsl_browser_open_falls_back_when_windows_bridge_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "read_text", lambda self, encoding: "microsoft-standard-WSL2")
    monkeypatch.setattr(
        "ewp_transcripts.web_server.shutil.which",
        lambda name: name if name in {"cmd.exe", "powershell.exe"} else None,
    )
    run = Mock()
    run.return_value.returncode = 1
    opened = Mock()
    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)
    monkeypatch.setattr("ewp_transcripts.web_server.webbrowser.open", opened)

    _open_browser("http://127.0.0.1:8765/")

    opened.assert_called_once_with("http://127.0.0.1:8765/")


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
        resolve_allowed_path=lambda path, directory=False: Path(path),
        resolve_transcription_options=lambda document: ("pl", "auto"),
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
