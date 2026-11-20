"""Preview-bound maintenance of temporary workdirs; never a general filesystem browser."""

from __future__ import annotations

import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.workdirs import (
    cleanup_identity,
    cleanup_work_directory,
    find_work_directories,
    work_directory_metadata,
)


class GuiWorkdirController:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._lock = threading.Lock()
        self._previews: dict[str, tuple[float, dict[str, str]]] = {}

    def inventory(
        self, references: tuple[Path, ...], *, older_than_days: int = 0, reason: str = ""
    ) -> dict[str, Any]:
        entries = []
        for workspace in find_work_directories(self.root, older_than_days=older_than_days):
            marker = work_directory_metadata(workspace)
            fingerprint, size, blocker = cleanup_identity(workspace, references)
            retention = marker.get("retention_reason", "legacy-unknown")
            if retention == "active" and blocker != "active":
                # The owner may still be live but a stronger blocker won; don't mislabel it.
                try:
                    os.kill(marker["owner_pid"], 0)
                except ProcessLookupError:
                    retention = "interrupted"
                except (OSError, ApplicationError):
                    pass
            if reason and retention != reason:
                continue
            entries.append(
                dict(
                    id=f"{workspace.run_id}/{workspace.job_id}",
                    path=str(workspace.path),
                    job_id=workspace.job_id,
                    created_at=marker.get("created_at"),
                    reason=retention,
                    size_bytes=size,
                    blocker=blocker,
                    removable=not blocker,
                    fingerprint=fingerprint,
                )
            )
        return {"root": str(self.root), "entries": entries}

    def preview(self, identities: list[str], references: tuple[Path, ...]) -> dict[str, Any]:
        if not identities or len(identities) > 100 or len(set(identities)) != len(identities):
            raise ValueError("Select temporary work directories to preview")
        with self._lock:
            inventory = self.inventory(references)["entries"]
            entries = {entry["id"]: entry for entry in inventory}
            candidates = {
                f"{item.run_id}/{item.job_id}": item for item in find_work_directories(self.root)
            }
            fingerprints = {}
            selected = []
            for identity in identities:
                if identity not in entries or not entries[identity]["removable"]:
                    raise ValueError("Selected work directory is unavailable or protected")
                fingerprint, _size, blocker = cleanup_identity(candidates[identity], references)
                if blocker:
                    raise ValueError("Selected work directory became protected")
                fingerprints[identity] = fingerprint
                selected.append(entries[identity])
            now = time.monotonic()
            self._previews = {
                key: value for key, value in self._previews.items() if now - value[0] < 300
            }
            if len(self._previews) >= 20:
                self._previews.clear()
            token = secrets.token_urlsafe(24)
            self._previews[token] = (now, fingerprints)
            return {
                "preview_token": token,
                "entries": selected,
                "size_bytes": sum(item["size_bytes"] for item in selected),
            }

    def cleanup(self, token: str, references: tuple[Path, ...]) -> dict[str, Any]:
        with self._lock:
            preview = self._previews.pop(token, None)
            if preview is None or time.monotonic() - preview[0] >= 300:
                raise ValueError("Cleanup preview expired; preview the selection again")
            candidates = {
                f"{item.run_id}/{item.job_id}": item for item in find_work_directories(self.root)
            }
            # Revalidate the whole selection before deleting any of it.
            for identity, fingerprint in preview[1].items():
                workspace = candidates.get(identity)
                if workspace is None:
                    raise ValueError(
                        "A work directory changed after preview; refresh and preview again"
                    )
                current, _size, blocker = cleanup_identity(workspace, references)
                if blocker or current != fingerprint:
                    raise ValueError("A work directory changed or became protected after preview")
            removed = []
            for identity in preview[1]:
                try:
                    cleanup_work_directory(candidates[identity])
                    removed.append(identity)
                except (OSError, ApplicationError):
                    return {"removed": removed, "failed": identity}
            return {"removed": removed, "failed": None}
