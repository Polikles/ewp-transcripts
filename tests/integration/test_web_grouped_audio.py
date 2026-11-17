"""Exercise grouped GUI planning, durable staging and restart without models."""

import json
import wave
from email.message import Message
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.web_jobs import GuiTranscriptionQueue
from ewp_transcripts.web_server import GuiSelectionCache, LocalGuiRequestHandler
from ewp_transcripts.web_source_cleanup import inventory_managed_sources
from ewp_transcripts.web_workflows import GuiWorkflowController
from ewp_transcripts.web_workspaces import GuiWorkspaceController

pytestmark = pytest.mark.integration


def audio(rate=16000, frames=1600) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\0\0" * frames)
    return buffer.getvalue()


def post(server, path, document):
    body = json.dumps(document).encode()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = server
    handler.path = path
    handler.rfile = BytesIO(body)
    handler.headers = Message()
    for name, value in {
        "Host": "127.0.0.1:8765",
        "Origin": "http://127.0.0.1:8765",
        "Content-Length": str(len(body)),
        "X-EWP-CSRF": "expected",
    }.items():
        handler.headers[name] = value
    handler._write_response = Mock()
    handler.do_POST()
    response = handler._write_response.call_args.args[0]
    return response.status, json.loads(response.body)


def test_gui_group_is_one_episode_and_restores_both_durable_sources(tmp_path: Path) -> None:
    cache = GuiSelectionCache()
    cache._root = tmp_path / "selections"
    paths = []
    for name in ("Szymon", "Damian"):
        content = audio()
        paths.append(
            cache.store(
                filename=f"s0e00-{name}.wav", content_length=len(content), source=BytesIO(content)
            )
        )
    queue = GuiTranscriptionQueue(config=ApplicationConfig())
    restored_queue = GuiTranscriptionQueue(config=ApplicationConfig())
    workflows = GuiWorkflowController()
    output = tmp_path / "output"
    server = SimpleNamespace(
        server_port=8765,
        gui_csrf_token="expected",
        gui_selections=cache,
        gui_workflows=workflows,
        gui_transcriptions=queue,
    )
    document = {
        "path": str(paths[0]),
        "output_directory": str(output),
        "group_id": "s0e00",
        "group_paths": [str(path) for path in paths],
    }
    try:
        status, inspection = post(server, "/api/v1/inspect", document)
        assert status == 200, inspection
        assert len(inspection["result"]["episodes"]) == 1
        status, plan = post(server, "/api/v1/dry-run", document)
        assert status == 200, plan
        assert [job["job_id"] for job in plan["result"]["jobs"]] == ["s0e00"]
        status, staged = post(server, "/api/v1/transcriptions", {**document, "confirmed": True})
        assert status == 202, staged
        assert len(staged["group_sources"]) == 2
        cache.close()
        assert all(Path(path).is_file() for path in staged["group_sources"])
        assert all(not path.exists() for path in paths)
        saved_job = {
            key: staged[key]
            for key in (
                "input_path",
                "output_directory",
                "planned_job_id",
                "planned_result_path",
                "source_sha256",
                "language",
                "speaker_count",
                "group_sources",
            )
        }
        workspaces = GuiWorkspaceController(
            state_directory=tmp_path / "workspaces", resolve_path=workflows.resolve_allowed_path
        )
        saved = workspaces.save(
            name="group", current_step="workspace-heading", fields={}, staged_jobs=[saved_job]
        )
        # Both copies stay protected through both reference routes.
        for jobs, spaces in ((queue.jobs(), ()), ((), (saved,))):
            inventory = inventory_managed_sources(output, queue_jobs=jobs, workspaces=spaces)
            assert len(inventory) == 2
            assert all(not item.removable for item in inventory)
        handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
        handler.server = SimpleNamespace(
            gui_workflows=GuiWorkflowController(), gui_transcriptions=restored_queue
        )
        assert handler._restore_workspace_staged_jobs(saved.staged_jobs) == 1
        restored = restored_queue.jobs()[0]
        assert restored.group_sources == staged["group_sources"]
        assert restored.planned_job_id == "s0e00"
        restored_queue.clear_current_state()
        second = Path(list(staged["group_sources"])[1])
        second.write_bytes(b"changed after saving")
        with pytest.raises(ValueError, match="grouped source changed"):
            handler._restore_workspace_staged_jobs(saved.staged_jobs)
    finally:
        cache.close()
        queue.close()
        restored_queue.close()


@pytest.mark.parametrize(("rate", "frames"), [(8000, 800), (16000, 16000)])
def test_gui_group_retains_sample_rate_and_timeline_guards(tmp_path: Path, rate, frames) -> None:
    sources = [tmp_path / f"s0e00-{name}.wav" for name in ("Szymon", "Damian")]
    sources[0].write_bytes(audio())
    sources[1].write_bytes(audio(rate, frames))
    operation = GuiWorkflowController().run(
        "dry-run",
        {
            "path": str(sources[0]),
            "output_directory": str(tmp_path / "output"),
            "group_id": "s0e00",
            "group_paths": [str(path) for path in sources],
        },
    )
    assert operation.status == "failed"
    assert operation.error["code"] in {"SAMPLE_RATE_MISMATCH", "DURATION_MISMATCH"}
