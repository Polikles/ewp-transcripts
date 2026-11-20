"""Cooperative cancellation with an atomic boundary before final publication."""

from __future__ import annotations

import threading

from ewp_transcripts.domain.errors import ApplicationError


class TranscriptionCancelled(ApplicationError):
    """An explicit user request reached a safe transcription checkpoint."""

    code = "USER_CANCELLED"


class CancellationToken:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requested = False
        self._publishing = False

    def request(self) -> bool:
        """Accept requests only before publication; never promise to undo a published result."""
        with self._lock:
            if self._publishing:
                return False
            self._requested = True
            return True

    def check(self) -> None:
        with self._lock:
            if self._requested:
                raise TranscriptionCancelled("Transcription cancelled by user")

    def begin_publication(self) -> None:
        with self._lock:
            if self._requested:
                raise TranscriptionCancelled("Transcription cancelled by user")
            self._publishing = True


def check_cancellation(token: CancellationToken | None) -> None:
    if token is not None:
        token.check()
