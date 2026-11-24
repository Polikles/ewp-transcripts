"""Last active workspace and queue checkpoints across GUI/browser restarts."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from ewp_transcripts.web_jobs import GuiTranscriptionJob
from ewp_transcripts.web_workspaces import GuiWorkspaceController, _write_private_json


class GuiStartupRecovery:
    """Keep a local reference; credentials, approvals and transcript text never enter it."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.RLock()
        self.armed = False
        self.queue_signature = ""

    def reference(self) -> dict[str, str] | None:
        with self.lock:
            if not self.path.exists():
                return None
            if self.path.is_symlink() or self.path.stat().st_size > 16384:
                raise ValueError("Automatic recovery reference is invalid")
            try:
                record = json.loads(self.path.read_text(encoding="utf-8"))
                return {
                    "workspace_id": str(UUID(record["workspace_id"])),
                    "storage_directory": str(record["storage_directory"]),
                }
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError("Automatic recovery reference is invalid") from error

    def remember(self, workspace_id: str, storage_directory: str, *, enabled: bool = True) -> None:
        with self.lock:
            _write_private_json(
                self.path,
                {"workspace_id": str(UUID(workspace_id)), "storage_directory": storage_directory},
            )
            self.armed = enabled
            self.queue_signature = ""

    def forget(self) -> None:
        with self.lock:
            self.armed = False
            self.path.unlink(missing_ok=True)

    def checkpoint(
        self,
        jobs: tuple[GuiTranscriptionJob, ...],
        controller: Callable[[str], GuiWorkspaceController],
    ) -> None:
        with self.lock, GuiWorkspaceController._publication_lock:
            if not self.armed or not (reference := self.reference()):
                return
            signature = "|".join(f"{job.job_id}:{job.updated_at.isoformat()}" for job in jobs)
            if signature == self.queue_signature:
                return
            workspaces = controller(reference["storage_directory"])
            previous = workspaces.load(reference["workspace_id"])
            staged = []
            terminal = []
            for job in jobs:
                if not job.source_sha256 or workspaces.is_temporary_selection(job.input_path):
                    continue
                if job.status in {"staged", "queued", "running", "cancel_requested"}:
                    staged.append(
                        {
                            key: value
                            for key, value in job.model_dump(mode="json").items()
                            if key
                            in {
                                "input_path",
                                "output_directory",
                                "planned_job_id",
                                "planned_result_path",
                                "source_sha256",
                                "language",
                                "speaker_count",
                                "speech",
                                "group_sources",
                                "selected_streams",
                                "recording_id",
                            }
                        }
                    )
                elif job.status in {"completed", "failed", "cancelled"}:
                    terminal.append(job.model_dump(mode="json"))
            workspaces.save(
                workspace_id=previous.workspace_id,
                name=previous.name,
                current_step=previous.current_step,
                fields=dict(previous.fields),
                staged_jobs=staged,
                terminal_jobs=terminal,
                pending_media=[m.model_dump(mode="json") for m in previous.pending_media],
                omit_unavailable=True,
            )
            self.queue_signature = signature
