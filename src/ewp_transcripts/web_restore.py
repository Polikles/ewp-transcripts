"""Bounded process-local progress for one explicit saved-work restoration."""

from __future__ import annotations

import re
import threading
from typing import Any


class GuiRestoreProgress:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._identity = ""
        self._state = "idle"
        self._loaded = 0
        self._total = 0

    def start(self, identity: str) -> None:
        if re.fullmatch(r"[A-Za-z0-9_-]{16,80}", identity) is None:
            raise ValueError("Saved-work restore identity is invalid")
        with self._lock:
            if self._state == "loading":
                raise ValueError("Saved work is already being restored")
            self._identity = identity
            self._state = "loading"
            self._loaded = self._total = 0

    def total(self, value: int) -> None:
        with self._lock:
            self._total = max(0, value)

    def advance(self, value: int) -> None:
        with self._lock:
            self._loaded = min(self._total, self._loaded + max(0, value))

    def finish(self, identity: str, *, succeeded: bool) -> None:
        with self._lock:
            if self._identity == identity:
                self._state = "complete" if succeeded else "failed"

    def snapshot(self, identity: str) -> dict[str, Any]:
        with self._lock:
            if identity != self._identity:
                return {"state": "pending", "loaded": 0, "total": None}
            return {"state": self._state, "loaded": self._loaded, "total": self._total}
