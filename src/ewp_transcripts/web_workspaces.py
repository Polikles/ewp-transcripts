"""Versioned non-secret GUI workspace field persistence."""

from __future__ import annotations

import json
import os
import tempfile
from builtins import list as builtin_list
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from ewp_transcripts.config import SpeechConfig
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.input_options import recording_identity, stream_choices
from ewp_transcripts.storage import is_preserved_gui_result
from ewp_transcripts.web_jobs import GuiTranscriptionJob

_FIELD_NAMES = frozenset(
    {
        "gui-translation-applied-path",
        "gui-translation-review-path",
        "gui-translation-result-path",
        "gui-translation-revision-path",
        "gui-translation-parent-path",
        "gui-translation-target",
        "gui-speaker-colors",
        "gui-palette-profile",
        "cloud-asr-provider",
        "cloud-asr-model",
        "cloud-asr-budget",
        "input-path",
        "output-path",
        "workflow-language",
        "workflow-speaker-count",
        "workflow-speaker-auto",
        "correction-result-path",
        "correction-output-root",
        "correction-provider",
        "correction-model",
        "correction-endpoint",
        "correction-reasoning",
        "correction-allow-remote",
        "correction-dictionary",
        "review-result-path",
        "review-project-path",
        "custom-review-paths",
        "review-output-path",
        "revision-output-path",
        "export-output-path",
        "translation-result-path",
        "translation-revision-path",
        "translation-output-root",
        "translation-target",
        "translation-model",
        "translation-endpoint",
        "translation-allow-remote",
        "translation-output-mode",
        "translation-dictionary",
        "translation-provider",
        "translation-reasoning",
        "dictionary-canonical-directory",
        "dictionary-revision-directory",
        "dictionary-output-root",
        "dictionary-project-id",
        "dictionary-minimum",
        "dictionary-previous",
    }
)
_PATH_FIELDS = frozenset(
    {
        "gui-translation-applied-path",
        "gui-translation-review-path",
        "gui-translation-result-path",
        "gui-translation-revision-path",
        "gui-translation-parent-path",
        "input-path",
        "output-path",
        "correction-result-path",
        "correction-output-root",
        "correction-dictionary",
        "review-result-path",
        "review-project-path",
        "review-output-path",
        "revision-output-path",
        "export-output-path",
        "translation-result-path",
        "translation-revision-path",
        "translation-output-root",
        "translation-dictionary",
        "dictionary-canonical-directory",
        "dictionary-revision-directory",
        "dictionary-output-root",
        "dictionary-previous",
    }
)
_FILE_FIELDS = frozenset(
    {
        "gui-translation-applied-path",
        "gui-translation-review-path",
        "gui-translation-result-path",
        "gui-translation-revision-path",
        "gui-translation-parent-path",
        "input-path",
        "correction-result-path",
        "correction-dictionary",
        "review-result-path",
        "translation-result-path",
        "translation-revision-path",
        "translation-dictionary",
        "dictionary-previous",
    }
)


class GuiWorkspaceSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_id: str
    name: str
    saved_at: datetime
    field_count: int = Field(ge=0)
    available: bool
    queue_count: int = Field(default=0, ge=0)


class GuiWorkspaceDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_version: Literal[1, 2] = 2
    workspace_id: str
    name: str
    saved_at: datetime
    current_step: str
    fields: dict[str, str | bool | int]
    staged_jobs: tuple[dict[str, Any], ...] = ()
    terminal_jobs: tuple[GuiTranscriptionJob, ...] = ()


ResolvePath = Callable[..., Path]


def resolve_optional_workspace_file(raw: str, resolve_path: ResolvePath) -> Path:
    """Validate a saved file location without confusing a future result with a directory."""
    candidate = Path(raw.strip()).expanduser()
    if not candidate.name or candidate.name in {".", ".."}:
        raise ValueError("Saved file reference is invalid")
    try:
        resolved = resolve_path(raw)
    except FileNotFoundError:
        if candidate.is_symlink():
            raise ValueError("Symbolic-link paths are not allowed") from None
        return resolve_path(str(candidate.parent), directory=True) / candidate.name
    if resolved.is_dir():
        raise ValueError("Saved file reference must not be a directory")
    return resolved


def default_workspace_directory() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME", "").strip()
    base = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return base / "ewp-transcripts" / "gui-workspaces"


class GuiWorkspaceController:
    """Store a bounded catalog of non-secret form values outside project artifacts."""

    def __init__(
        self,
        *,
        state_directory: Path,
        resolve_path: ResolvePath,
        temporary_selection_root: Path | None = None,
    ) -> None:
        self._state_directory = state_directory
        self._resolve_path = resolve_path
        self._temporary_selection_root = temporary_selection_root

    @property
    def state_directory(self) -> Path:
        """Return this catalog's normalized storage directory for catalog deduplication."""

        return self._state_directory.resolve(strict=False)

    def is_temporary_selection(self, value: str) -> bool:
        """Identify exact GUI-owned picker copies, including expired sessions."""

        path = Path(value.strip())
        return bool(
            self._temporary_selection_root
            and path.is_absolute()
            and path.is_relative_to(self._temporary_selection_root)
        )

    def documents(self) -> tuple[GuiWorkspaceDocument, ...]:
        """Return readable workspace records without requiring every referenced path to exist."""

        if not self._state_directory.is_dir() or self._state_directory.is_symlink():
            return ()
        documents: list[GuiWorkspaceDocument] = []
        for path in sorted(self._state_directory.glob("*.json")):
            try:
                documents.append(self._read(path))
            except ValueError:
                continue
        return tuple(documents)

    def save(
        self,
        *,
        name: str,
        current_step: str,
        fields: dict[str, Any],
        staged_jobs: builtin_list[dict[str, Any]] | None = None,
        terminal_jobs: builtin_list[dict[str, Any]] | None = None,
        workspace_id: str = "",
        omit_unavailable: bool = False,
    ) -> GuiWorkspaceDocument:
        clean_name = name.strip()
        if not clean_name or len(clean_name) > 100:
            raise ValueError("Workspace name must contain 1 to 100 characters")
        clean_fields = self._validate_fields(fields, omit_unavailable=omit_unavailable)
        clean_staged_jobs = self._validate_staged_jobs(
            staged_jobs or [], omit_unavailable=omit_unavailable
        )
        clean_terminal_jobs = self._validate_terminal_jobs(
            terminal_jobs or [], omit_unavailable=omit_unavailable
        )
        identifier = (
            self._normalize_workspace_id(workspace_id) if workspace_id.strip() else str(uuid4())
        )
        document = GuiWorkspaceDocument(
            workspace_id=identifier,
            name=clean_name,
            saved_at=datetime.now(UTC),
            current_step=current_step[:100],
            fields=clean_fields,
            staged_jobs=clean_staged_jobs,
            terminal_jobs=clean_terminal_jobs,
        )
        self._state_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination = self._state_directory / f"{identifier}.json"
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".workspace-", dir=self._state_directory
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(document.model_dump(mode="json"), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, destination)
        finally:
            Path(temporary_name).unlink(missing_ok=True)
        return document

    def list(self) -> tuple[GuiWorkspaceSummary, ...]:
        if not self._state_directory.exists():
            return ()
        summaries: list[GuiWorkspaceSummary] = []
        for path in self._state_directory.glob("*.json"):
            try:
                document = self._read(path)
                available = self._paths_available(
                    document.fields, document.staged_jobs, document.terminal_jobs
                )
                summaries.append(
                    GuiWorkspaceSummary(
                        workspace_id=document.workspace_id,
                        name=document.name,
                        saved_at=document.saved_at,
                        field_count=len(document.fields),
                        available=available,
                        queue_count=len(document.staged_jobs) + len(document.terminal_jobs),
                    )
                )
            except (OSError, ValueError):
                continue
        summaries.sort(key=lambda item: item.saved_at, reverse=True)
        return tuple(summaries[:20])

    def load(
        self, workspace_id: str, *, on_read: Callable[[int], None] | None = None
    ) -> GuiWorkspaceDocument:
        path = self._workspace_path(workspace_id)
        document = self._read(path)
        if on_read is not None:
            on_read(len(document.staged_jobs) + len(document.terminal_jobs))
        self._validate_fields(document.fields)
        self._validate_staged_jobs(list(document.staged_jobs))
        self._validate_terminal_jobs(
            [job.model_dump(mode="json") for job in document.terminal_jobs]
        )
        return document

    def delete(self, workspace_id: str) -> None:
        """Delete one exact workspace record without touching its referenced artifacts."""

        path = self._workspace_path(workspace_id)
        if path.is_symlink() or not path.is_file():
            raise ValueError("Saved workspace does not exist")
        path.unlink()

    def import_file(self, path: Path) -> GuiWorkspaceDocument:
        """Validate one selected workspace document and save it in this workspace catalog."""

        document = self._read(path)
        return self.save(
            name=document.name,
            current_step=document.current_step,
            fields=document.fields,
            staged_jobs=list(document.staged_jobs),
            terminal_jobs=[item.model_dump(mode="json") for item in document.terminal_jobs],
            workspace_id=document.workspace_id,
        )

    def _validate_fields(
        self, fields: dict[str, Any], *, omit_unavailable: bool = False
    ) -> dict[str, str | bool | int]:
        if not isinstance(fields, dict):
            raise ValueError("Workspace fields must be an object")
        clean: dict[str, str | bool | int] = {}
        for name, value in fields.items():
            if name not in _FIELD_NAMES:
                raise ValueError(f"Workspace contains an unsupported field: {str(name)[:80]}")
            if not isinstance(value, (str, bool, int)):
                raise ValueError(f"Workspace field has an invalid value: {name}")
            if isinstance(value, str) and len(value) > 4096:
                raise ValueError("Workspace field is too long")
            if name in _PATH_FIELDS and isinstance(value, str) and value.strip():
                if self.is_temporary_selection(value):
                    clean[name] = ""
                    continue
                try:
                    self._resolve_path(value, directory=name not in _FILE_FIELDS)
                except FileNotFoundError:
                    if not omit_unavailable:
                        raise
                    clean[name] = ""
                    continue
            clean[name] = value
        return clean

    def _validate_staged_jobs(
        self,
        staged_jobs: builtin_list[dict[str, Any]],
        *,
        omit_unavailable: bool = False,
    ) -> tuple[dict[str, Any], ...]:
        if not isinstance(staged_jobs, builtin_list) or len(staged_jobs) > 50:
            raise ValueError("Workspace staged jobs are invalid")
        required = {
            "input_path",
            "output_directory",
            "planned_job_id",
            "planned_result_path",
            "source_sha256",
            "language",
            "speaker_count",
        }
        clean: builtin_list[dict[str, Any]] = []
        for item in staged_jobs:
            if (
                not isinstance(item, dict)
                or not required.issubset(item)
                or set(item)
                - required
                - {"group_sources", "selected_streams", "recording_id", "speech"}
            ):
                raise ValueError("Workspace staged job is invalid")
            speaker_count = item["speaker_count"]
            if (
                not isinstance(speaker_count, int) or isinstance(speaker_count, bool)
            ) and speaker_count != "auto":
                raise ValueError("Workspace staged job is invalid")
            if any(not isinstance(item[key], str) for key in required - {"speaker_count"}):
                raise ValueError("Workspace staged job is invalid")
            if item["language"] not in {"pl", "en", "auto"} or len(item["source_sha256"]) != 64:
                raise ValueError("Workspace staged job is invalid")
            try:
                SpeechConfig.model_validate(item.get("speech", {}))
                recording_identity(item.get("recording_id"))
                self._resolve_path(item["input_path"])
                group_sources = item.get("group_sources", {})
                selected_streams = stream_choices(
                    item.get("selected_streams", {}),
                    [
                        item["input_path"],
                        *(group_sources if isinstance(group_sources, dict) else {}),
                    ],
                )
                if not isinstance(group_sources, dict) or (
                    group_sources and not 2 <= len(group_sources) <= 6
                ):
                    raise ValueError("Workspace grouped sources are invalid")
                for path, digest in group_sources.items():
                    if (
                        not isinstance(path, str)
                        or not isinstance(digest, str)
                        or len(digest) != 64
                    ):
                        raise ValueError("Workspace grouped source is invalid")
                    self._resolve_path(path)
                if group_sources and group_sources.get(item["input_path"]) != item["source_sha256"]:
                    raise ValueError("Workspace group primary source is invalid")
            except FileNotFoundError:
                if omit_unavailable:
                    continue
                raise
            self._resolve_path(item["output_directory"], directory=True)
            clean.append(
                {
                    **{key: item[key] for key in required},
                    **(
                        {
                            "speech": SpeechConfig.model_validate(item["speech"]).model_dump(
                                mode="json"
                            )
                        }
                        if item.get("speech")
                        else {}
                    ),
                    **({"group_sources": group_sources} if group_sources else {}),
                    **({"selected_streams": selected_streams} if selected_streams else {}),
                    **({"recording_id": item["recording_id"]} if item.get("recording_id") else {}),
                }
            )
        return tuple(clean)

    def _validate_terminal_jobs(
        self,
        terminal_jobs: builtin_list[dict[str, Any]],
        *,
        omit_unavailable: bool = False,
    ) -> tuple[GuiTranscriptionJob, ...]:
        if not isinstance(terminal_jobs, builtin_list) or len(terminal_jobs) > 50:
            raise ValueError("Workspace completed jobs are invalid")
        clean: builtin_list[GuiTranscriptionJob] = []
        seen_job_ids: set[str] = set()
        for item in terminal_jobs:
            try:
                job = GuiTranscriptionJob.model_validate(item)
            except ValueError:
                raise ValueError("Workspace completed job is invalid") from None
            if job.status not in {"completed", "failed", "cancelled"} or job.job_id in seen_job_ids:
                raise ValueError("Workspace completed job is invalid")
            if not job.source_sha256 or len(job.source_sha256) != 64:
                raise ValueError("Workspace completed job is invalid")
            try:
                if job.status in {"failed", "cancelled"}:
                    resolve_optional_workspace_file(job.input_path, self._resolve_path)
                output = self._resolve_path(job.output_directory, directory=True)
                planned = (
                    resolve_optional_workspace_file(job.planned_result_path, self._resolve_path)
                    if job.status in {"failed", "cancelled"}
                    else self._resolve_path(job.planned_result_path)
                )
            except FileNotFoundError:
                if omit_unavailable:
                    continue
                raise
            imported = (
                job.status == "completed"
                and job.input_path == job.result_path == job.planned_result_path
                and is_preserved_gui_result(planned, output, job.source_sha256)
            )
            if planned.parent != output and not imported:
                raise ValueError("Workspace completed job has an invalid result location")
            if job.status == "completed":
                if not job.result_path or self._resolve_path(job.result_path) != planned:
                    raise ValueError("Workspace completed job has an invalid result")
                if imported:
                    try:
                        unchanged = sha256_file(planned) == job.source_sha256
                    except FileNotFoundError:
                        if omit_unavailable:
                            continue
                        raise
                    if not unchanged:
                        raise ValueError("Saved imported canonical result changed on disk")
            elif job.result_path is not None:
                raise ValueError("Workspace failed job cannot have a result")
            clean.append(job)
            seen_job_ids.add(job.job_id)
        return tuple(clean)

    def _paths_available(
        self,
        fields: dict[str, str | bool | int],
        staged_jobs: tuple[dict[str, Any], ...],
        terminal_jobs: tuple[GuiTranscriptionJob, ...],
    ) -> bool:
        try:
            self._validate_fields(fields)
            self._validate_staged_jobs(list(staged_jobs))
            self._validate_terminal_jobs([job.model_dump(mode="json") for job in terminal_jobs])
        except (FileNotFoundError, OSError, ValueError):
            return False
        return True

    def _workspace_path(self, workspace_id: str) -> Path:
        return self._state_directory / f"{self._normalize_workspace_id(workspace_id)}.json"

    @staticmethod
    def _normalize_workspace_id(workspace_id: str) -> str:
        try:
            return str(UUID(workspace_id))
        except (ValueError, AttributeError):
            raise ValueError("Workspace ID is invalid") from None

    @staticmethod
    def _read(path: Path) -> GuiWorkspaceDocument:
        try:
            return GuiWorkspaceDocument.model_validate_json(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ValueError("Saved workspace does not exist") from None
        except (OSError, ValueError):
            raise ValueError("Saved workspace is invalid") from None
