"""Private playback cache, byte ranges and actual canonical-source identity."""

import json
from pathlib import Path

import pytest

from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.web_media import GuiMediaController, media_byte_range
from ewp_transcripts.web_workflows import GuiWorkflowController

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/results.example.json"


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, (0, 99)),
        ("bytes=0-9", (0, 9)),
        ("bytes=90-", (90, 99)),
        ("bytes=-20", (80, 99)),
        ("bytes=0-500", (0, 99)),
        ("bytes=-500", (0, 99)),
    ],
)
def test_playback_ranges(header, expected) -> None:
    assert media_byte_range(header, 100) == expected


@pytest.mark.parametrize(
    "header",
    ["bytes=100-", "bytes=9-3", "bytes=-0", "bytes=-", "bytes=1-2,4-5", "bytes=abc", "items=0-1"],
)
def test_invalid_playback_range_is_rejected(header) -> None:
    with pytest.raises(ValueError):
        media_byte_range(header, 100)


def playback_result(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "recording.mp4"
    source.write_bytes(b"original video bytes")
    base = json.loads(EXAMPLE.read_text())
    base["sources"][0] = {
        **base["sources"][0],
        "normalized_path": str(source),
        "input_path": str(source),
        "filename": source.name,
        "media_type": "video",
        "sha256": sha256_file(source),
        "size_bytes": source.stat().st_size,
        "stream_index": 1,
        "channel_selection": 0,
    }
    result = tmp_path / "recording_results.json"
    result.write_text(json.dumps(base))
    return result, source


def test_preview_uses_canonical_stream_channel_and_revokes_old_token(
    tmp_path: Path, monkeypatch
) -> None:
    result, source = playback_result(tmp_path)
    calls = []

    def prepare(path, destination, **kwargs):
        calls.append((path, kwargs))
        destination.write_bytes(b"wave preview")
        return destination

    monkeypatch.setattr("ewp_transcripts.web_media.prepare_working_audio", prepare)
    media = GuiMediaController(resolve_path=GuiWorkflowController().resolve_allowed_path)
    try:
        preview = media.prepare(str(result), "source_001")
        token = preview["url"].rsplit("/", 1)[1]
        assert calls == [(source, {"stream_index": 1, "channel_index": 0})]
        assert media.prepare(str(result), "source_001") == preview
        assert len(calls) == 1
        with media.open(token) as audio:
            assert audio.read() == b"wave preview"
        another_result = tmp_path / "another_results.json"
        another_result.write_bytes(result.read_bytes())
        with media.open(token) as in_flight:
            replacement = media.prepare(str(another_result), "source_001")
            assert replacement["url"] != preview["url"]
            assert in_flight.read() == b"wave preview"
        with pytest.raises(FileNotFoundError):
            media.open(token)
        with pytest.raises(FileNotFoundError):
            media.open("unrecognized")
        media.close()
        with pytest.raises(FileNotFoundError):
            media.open(token)
        assert source.read_bytes() == b"original video bytes"
    finally:
        media.close()


def test_preview_rejects_changed_source_unknown_source_and_prohibited_path(tmp_path: Path) -> None:
    result, source = playback_result(tmp_path)
    media = GuiMediaController(resolve_path=GuiWorkflowController().resolve_allowed_path)
    try:
        with pytest.raises(ValueError, match="current recording"):
            media.prepare(str(result), "source_999")
        source.write_bytes(b"changed bytes")
        with pytest.raises(ValueError, match="differs from its transcription"):
            media.prepare(str(result), "source_001")
        source.unlink()
        with pytest.raises(ValueError, match="original recording is unavailable"):
            media.prepare(str(result), "source_001")
        with pytest.raises(ValueError):
            media.prepare("/etc/passwd", "source_001")
    finally:
        media.close()


@pytest.mark.parametrize(
    ("header", "head", "expected_status", "expected_body"),
    [
        ("bytes=2-5", False, 206, b"2345"),
        ("bytes=-3", False, 206, b"789"),
        (None, True, 200, b""),
        ("bytes=100-", False, 416, b""),
    ],
)
def test_http_audio_streams_ranges_and_head(
    tmp_path: Path, header, head, expected_status, expected_body
) -> None:
    from email.message import Message
    from io import BytesIO
    from types import SimpleNamespace
    from unittest.mock import Mock

    from ewp_transcripts.web_server import LocalGuiRequestHandler

    source = tmp_path / "preview.wav"
    source.write_bytes(b"0123456789")
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(
        server_port=8765, gui_media=SimpleNamespace(open=lambda token: source.open("rb"))
    )
    handler.path = "/api/v1/review-audio/private-token"
    handler.headers = Message()
    handler.headers["Host"] = "127.0.0.1:8765"
    if header:
        handler.headers["Range"] = header
    handler.wfile = BytesIO()
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler._stream_review_audio(head=head)
    assert handler.send_response.call_args.args[0] == expected_status
    assert handler.wfile.getvalue() == expected_body
    headers = dict(call.args for call in handler.send_header.call_args_list)
    assert headers["Cache-Control"] == "no-store"
    assert headers["Content-Length"] == str(len(expected_body) if not head else 10)
    if expected_status == 416:
        assert headers["Content-Range"] == "bytes */10"
    else:
        assert headers["Accept-Ranges"] == "bytes"


@pytest.mark.parametrize(
    ("host", "site"), [("evil.example", "same-origin"), ("localhost:8765", "cross-site")]
)
def test_http_audio_rejects_foreign_request_before_opening(host, site) -> None:
    from email.message import Message
    from types import SimpleNamespace
    from unittest.mock import Mock

    from ewp_transcripts.web_server import LocalGuiRequestHandler

    media = Mock()
    handler = LocalGuiRequestHandler.__new__(LocalGuiRequestHandler)
    handler.server = SimpleNamespace(server_port=8765, gui_media=media)
    handler.headers = Message()
    handler.headers["Host"], handler.headers["Sec-Fetch-Site"] = host, site
    handler._write_response = Mock()
    handler._stream_review_audio()
    assert handler._write_response.call_args.args[0].status == 403
    media.open.assert_not_called()
