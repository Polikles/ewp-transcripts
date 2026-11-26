"""Small authenticated lifecycle state for the owned Windows desktop host."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterator


class DesktopLifecycle:
    """Track active requests without persisting content, credentials or queued-work consent."""

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled
        self._lock = threading.Lock()
        self._requests = 0
        self._close_requested = False
        self._close_refused = False

    @contextlib.contextmanager
    def request(self, path: str) -> Iterator[None]:
        # Autosave, status and draft saves must remain usable while closing.
        tracked = (
            self.enabled
            and path.startswith("/api/v1/")
            and not path.startswith(
                (
                    "/api/v1/runtime-control",
                    "/api/v1/workspaces/",
                    "/api/v1/reviews/save",
                    "/api/v1/reviews/session/",
                    "/api/v1/transcriptions/cancel",
                    "/api/v1/translation-reviews/save",
                )
            )
        )
        if tracked:
            with self._lock:
                self._requests += 1
        try:
            yield
        finally:
            if tracked:
                with self._lock:
                    self._requests -= 1

    def request_close(self) -> None:
        with self._lock:
            self._close_requested = True
            self._close_refused = False

    def refuse_close(self) -> None:
        with self._lock:
            self._close_requested = False
            self._close_refused = True

    def status(self, *, running_jobs: int) -> dict[str, object]:
        with self._lock:
            return {
                "desktop": self.enabled,
                "busy": running_jobs > 0 or self._requests > 0,
                "running_jobs": running_jobs,
                "active_requests": self._requests,
                "close_requested": self._close_requested,
                "close_refused": self._close_refused,
            }
