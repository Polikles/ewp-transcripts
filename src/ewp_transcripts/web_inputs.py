"""Read-only, content-based media selection for the local GUI."""

from __future__ import annotations

from collections.abc import Callable
from itertools import islice
from pathlib import Path
from typing import Any

from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.media import probe_media


class GuiInputs:
    def __init__(self, resolve: Callable[..., Path]) -> None:
        self.resolve = resolve

    def probe(self, raw_path: str) -> dict[str, Any]:
        source = self.resolve(raw_path)
        if not source.is_file():
            raise ValueError("Choose one media file to read audio streams")
        media = probe_media(source)
        return {
            "path": str(source),
            "name": source.name,
            "duration_ms": media.duration_ms,
            "streams": [x.model_dump(mode="json") for x in media.audio_streams],
        }

    def discover(self, raw_path: str) -> dict[str, Any]:
        directory = self.resolve(raw_path, directory=True)
        if not directory.is_dir():
            raise ValueError("Media directory is unavailable")
        entries = list(islice(directory.iterdir(), 501))
        files, skipped = [], 0
        for source in sorted(entries[:500], key=lambda x: x.name.casefold()):
            if not source.is_file():
                continue
            try:
                files.append(self.probe(str(source)))
            except (ValueError, OSError, ApplicationError):
                skipped += 1
        return {"files": files, "skipped": skipped, "truncated": len(entries) > 500}
