"""Hash-bound, session-private audio previews with bounded byte-range streaming."""

from __future__ import annotations

import re
import secrets
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4

from ewp_transcripts.domain import WorkDirectory
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.media.ffmpeg import prepare_working_audio
from ewp_transcripts.web_workflows import require_completed_canonical_result
from ewp_transcripts.workdirs import allocate_work_directory, cleanup_work_directory


def media_byte_range(value: str | None, size: int) -> tuple[int, int]:
    """Return inclusive bounds; reject malformed, multipart and unsatisfiable ranges."""
    if value is None:
        return 0, size - 1
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
    if match is None or size <= 0:
        raise ValueError("Unsatisfiable audio byte range")
    first, last = match.groups()
    if not first:
        if not last or int(last) == 0:
            raise ValueError("Unsatisfiable audio byte range")
        return max(0, size - int(last)), size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start > end:
        raise ValueError("Unsatisfiable audio byte range")
    return start, end


class GuiMediaController:
    """Keep one decoded preview, never expose a browser-supplied filesystem URL."""

    def __init__(self, *, resolve_path: Callable[..., Path]) -> None:
        self._resolve_path = resolve_path
        self._temporary = tempfile.TemporaryDirectory(prefix="ewp-gui-playback-")
        self._lock = threading.RLock()
        self._workspace: WorkDirectory | None = None
        self._key: tuple[str, str, str] | None = None
        self._token = ""
        self._audio: Path | None = None

    def prepare(self, result: str, source_id: str) -> dict[str, Any]:
        """Explicitly verify original bytes and decode the canonical selected stream/channel."""
        with self._lock:
            result_path = self._resolve_path(result)
            base = require_completed_canonical_result(result_path)
            source = next((item for item in base.sources if item.source_id == source_id), None)
            if source is None:
                raise ValueError("Choose an audio source from the current recording.")
            try:
                path = self._resolve_path(source.normalized_path)
            except FileNotFoundError as error:
                raise ValueError(
                    "The original recording is unavailable. Restore it at its original location, "
                    "then reload recording audio. Transcript editing remains available."
                ) from error
            key = (str(result_path), sha256_file(result_path), source_id)
            if self._key != key:
                if path.stat().st_size != source.size_bytes or sha256_file(path) != source.sha256:
                    raise ValueError(
                        "The recording source differs from its transcription. "
                        "Restore the original file before playback."
                    )
                self._clear()
                workspace = allocate_work_directory(
                    Path(self._temporary.name), run_id=uuid4(), job_id="playback"
                )
                try:
                    audio = prepare_working_audio(
                        path,
                        workspace.path / "preview.wav",
                        stream_index=source.stream_index,
                        channel_index=source.channel_selection
                        if isinstance(source.channel_selection, int)
                        else None,
                    )
                    if sha256_file(path) != source.sha256:
                        raise ValueError("The recording source changed while preparing playback.")
                except (ApplicationError, OSError, ValueError):
                    cleanup_work_directory(workspace)
                    raise
                self._workspace, self._audio, self._key = workspace, audio, key
                self._token = secrets.token_urlsafe(32)
            return {"url": f"/api/v1/review-audio/{self._token}", "source_id": source_id}

    def open(self, token: str) -> BinaryIO:
        """Open before cache replacement, so an in-flight stream retains its own descriptor."""
        with self._lock:
            if (
                not self._token
                or not secrets.compare_digest(token, self._token)
                or self._audio is None
            ):
                raise FileNotFoundError("No audio preview exists for this session.")
            return self._audio.open("rb")

    def _clear(self) -> None:
        if self._workspace is not None:
            cleanup_work_directory(self._workspace)
        self._workspace, self._audio, self._key, self._token = None, None, None, ""

    def close(self) -> None:
        with self._lock:
            self._clear()
            self._temporary.cleanup()
