import json
import subprocess
from email.message import Message
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ewp_transcripts import __version__
from ewp_transcripts.web_filesystem import GuiFilesystemController
from ewp_transcripts.web_server import (
    SECURITY_HEADERS,
    LocalGuiRequestHandler,
    WebConfiguration,
    _open_browser,
    dispatch_get,
)


def test_health_is_versioned_and_hardened(tmp_path: Path) -> None:
    config = WebConfiguration.create(port=8765, allowed_roots=[tmp_path])
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


def test_shell_and_allowed_roots_are_served(tmp_path: Path) -> None:
    config = WebConfiguration.create(port=8765, allowed_roots=[tmp_path])
    response = dispatch_get(config, server_port=8765, host="localhost:8765", target="/")
    assert response.status == 200
    assert b"EWP Transcriber" in response.body
    assert response.body.index(b"EWP Transcriber") < response.body.index(
        b"Local-first podcast workflow"
    )
    assert b"Status: connecting" in response.body
    assert b'id="clear-workflow"' in response.body
    assert b"Add to queue" in response.body
    assert b"Start queue" in response.body
    assert b"Review and export" in response.body
    assert b"LLM-assisted transcript correction" in response.body
    assert b'id="generate-correction"' in response.body
    assert b'id="generate-translation"' in response.body
    assert b"LLM-assisted translation" in response.body
    assert b"Semantic translation review" in response.body
    assert b'id="review-translation"' in response.body
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
    assert b"GUI_REVIEW_SELECTION_REQUIRED" in script_response.body
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
    assert b"Continue to correction" in script_response.body
    assert b"Continue to manual review" in script_response.body
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
    assert b"/api/v1/filesystem/list" in script_response.body
    assert b"Browse\xe2\x80\xa6" in script_response.body
    assert b"filesystemDialog.showModal" in script_response.body
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
    assert b"[hidden]" in style_response.body
    assert b'postReview("load"' in script_response.body
    assert b'postReview("session/restore"' in script_response.body
    response = dispatch_get(config, server_port=8765, host="localhost:8765", target="/api/v1/roots")
    assert json.loads(response.body) == {"roots": [str(tmp_path.resolve())]}


def test_untrusted_host_and_unknown_route_have_codes(tmp_path: Path) -> None:
    config = WebConfiguration.create(port=8765, allowed_roots=[tmp_path])
    response = dispatch_get(config, server_port=8765, host="attacker.example", target="/")
    assert response.status == 421
    assert json.loads(response.body)["error"]["code"] == "GUI_HOST_REJECTED"
    response = dispatch_get(config, server_port=8765, host="[::1]:8765", target="/missing")
    assert response.status == 404
    assert json.loads(response.body)["error"]["code"] == "GUI_ROUTE_NOT_FOUND"


def test_web_configuration_rejects_files_and_missing_roots(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    source.write_bytes(b"")
    with pytest.raises(ValueError, match="not a directory"):
        WebConfiguration.create(port=8765, allowed_roots=[source])
    with pytest.raises(FileNotFoundError):
        WebConfiguration.create(port=8765, allowed_roots=[tmp_path / "missing"])


def test_wsl_browser_open_uses_windows_bridge_without_terminal_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "read_text", lambda self, encoding: "microsoft-standard-WSL2")
    run = Mock()
    monkeypatch.setattr("ewp_transcripts.web_server.subprocess.run", run)

    _open_browser("http://127.0.0.1:8765/")

    assert run.call_args.args[0] == [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        "Start-Process",
        "http://127.0.0.1:8765/",
    ]
    assert run.call_args.kwargs["stderr"] is subprocess.DEVNULL


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


def test_filesystem_listing_requires_csrf_and_returns_filtered_entries(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / "result.json").write_text("{}", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")
    document = {
        "path": str(tmp_path),
        "select": "file",
        "extensions": ["json"],
    }
    body = json.dumps(document).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    headers = Message()
    headers["Host"] = "127.0.0.1:8765"
    headers["Origin"] = "http://127.0.0.1:8765"
    headers["Content-Length"] = str(len(body))
    headers["X-EWP-CSRF"] = "expected"
    handler.headers = headers
    handler.path = "/api/v1/filesystem/list"
    handler.rfile = BytesIO(body)
    handler.server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_filesystem=GuiFilesystemController((tmp_path.resolve(),)),
    )
    write_response = Mock()
    handler._write_response = write_response

    handler.do_POST()

    response = write_response.call_args.args[0]
    assert response.status == 200
    payload = json.loads(response.body)
    assert [(item["name"], item["kind"]) for item in payload["entries"]] == [
        ("nested", "directory"),
        ("result.json", "file"),
    ]
