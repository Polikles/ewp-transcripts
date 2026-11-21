"""Simulate the Windows CRT directory-open failure across immutable publication families."""

import errno
import os
from pathlib import Path
from uuid import uuid4

from ewp_transcripts import (
    export_service,
    platform_runtime,
    review_storage,
    revision_storage,
    state,
    translation_export,
    translation_storage,
)


class WindowsCRT:
    def __init__(self):
        self.file_flushes = 0
        self.directory_attempts = 0

    def __getattr__(self, name):
        return getattr(os, name)

    def open(self, path, flags, *args, **kwargs):
        if Path(path).is_dir():
            self.directory_attempts += 1
            raise PermissionError(errno.EACCES, "Windows CRT directory handles are unsupported")
        return os.open(path, flags, *args, **kwargs)

    def fsync(self, descriptor):
        self.file_flushes += 1
        return os.fsync(descriptor)


def test_windows_publication_keeps_file_flushes_without_directory_opens(tmp_path, monkeypatch):
    monkeypatch.setattr(platform_runtime, "WINDOWS", True)
    crt = WindowsCRT()
    for module in [
        state,
        review_storage,
        revision_storage,
        translation_storage,
        export_service,
        translation_export,
    ]:
        monkeypatch.setattr(module, "os", crt)
    state._publish_exclusive_json(tmp_path / "state.json", "{}", run_id=uuid4())
    review_storage._publish_exclusive(tmp_path / "review.txt", b"review")
    revision_storage._publish_exclusive(tmp_path / "revision.json", b"{}", revision_id=str(uuid4()))
    translation_storage._publish_exclusive(tmp_path / "translation.json", b"{}")
    export_service._publish_exclusive(tmp_path / "subtitles.srt", "subtitle")
    translation_export._publish_or_skip(tmp_path / "translated.srt", b"translated")
    assert crt.directory_attempts == 0
    assert crt.file_flushes >= 6
    assert len(list(tmp_path.iterdir())) == 6
