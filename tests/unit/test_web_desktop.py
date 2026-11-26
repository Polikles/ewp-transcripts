"""Desktop shutdown is authenticated, saves before commit, and never starts queued work."""

from __future__ import annotations

import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ewp_transcripts.web_desktop import DesktopLifecycle
from ewp_transcripts.web_server import LocalGuiRequestHandler


def test_activity_tracks_failures_and_leaves_save_available() -> None:
    lifecycle = DesktopLifecycle(enabled=True)
    assert not lifecycle.status(running_jobs=0)["busy"]
    with pytest.raises(ValueError), lifecycle.request("/api/v1/corrections/generate"):
        assert lifecycle.status(running_jobs=0)["busy"]
        raise ValueError("worker failed")
    assert not lifecycle.status(running_jobs=0)["busy"]
    for path in ["/api/v1/workspaces/save", "/api/v1/reviews/save", "/api/v1/runtime-control"]:
        with lifecycle.request(path):
            assert not lifecycle.status(running_jobs=0)["busy"]
    assert lifecycle.status(running_jobs=1)["busy"]
    ordinary = DesktopLifecycle()
    with ordinary.request("/api/v1/corrections/generate"):
        assert not ordinary.status(running_jobs=0)["busy"]


def test_native_stop_requests_save_then_waits_for_explicit_commit(monkeypatch) -> None:
    token = "private-native-management-" + "x" * 40
    monkeypatch.setenv("EWP_RUNTIME_TOKEN", token)
    stopped = threading.Event()
    lifecycle = DesktopLifecycle(enabled=True)
    server = SimpleNamespace(
        server_port=8765,
        gui_desktop=lifecycle,
        gui_transcriptions=SimpleNamespace(
            jobs=lambda: [SimpleNamespace(status="staged"), SimpleNamespace(status="queued")]
        ),
        checkpoint_recovery=Mock(),
        shutdown=stopped.set,
    )
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = server
    handler.path = "/api/v1/runtime-control"
    handler.headers = {"Host": "127.0.0.1:8765", "X-EWP-Runtime-Token": token}
    responses = []
    handler._write_response = responses.append
    handler._runtime_control(stop=True)
    payload = json.loads(responses[-1].body)
    assert payload["close_requested"] and payload["busy"]
    assert token.encode() not in responses[-1].body
    assert not stopped.is_set()
    server.checkpoint_recovery.assert_not_called()
    handler.path += "?close=refuse"
    handler._runtime_control(stop=True)
    payload = json.loads(responses[-1].body)
    assert payload["close_refused"] and not payload["close_requested"]
    assert not stopped.is_set()
    handler.path = "/api/v1/runtime-control?close=commit"
    handler._runtime_control(stop=True)
    payload = json.loads(responses[-1].body)
    assert not payload["close_refused"]
    assert stopped.wait(1)
    server.checkpoint_recovery.assert_called_once()


def test_native_commit_rejects_foreign_origin_and_wrong_token(monkeypatch) -> None:
    monkeypatch.setenv("EWP_RUNTIME_TOKEN", "x" * 64)
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(server_port=8765, gui_desktop=DesktopLifecycle(enabled=True))
    handler.path = "/api/v1/runtime-control?close=commit"
    responses = []
    handler._write_response = responses.append
    handler.headers = {
        "Host": "127.0.0.1:8765",
        "Origin": "https://foreign.example",
        "X-EWP-Runtime-Token": "x" * 64,
    }
    handler.do_POST()
    assert responses[-1].status == 403
    handler.headers = {"Host": "127.0.0.1:8765", "X-EWP-Runtime-Token": "not-authorized"}
    handler._runtime_control(stop=True)
    assert responses[-1].status == 403
    assert not handler.server.gui_desktop.status(running_jobs=0)["close_requested"]
