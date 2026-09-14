"""Read-only application-service workflows exposed by the local GUI."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, ValidationError

from ewp_transcripts.application import dry_run, inspect_input
from ewp_transcripts.config import load_config
from ewp_transcripts.discovery import normalize_input_path
from ewp_transcripts.domain.canonical import CanonicalResult, load_canonical_result
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.errors import ApplicationError

_LINUX_PROHIBITED_ROOTS = (
    Path("/bin"),
    Path("/boot"),
    Path("/dev"),
    Path("/etc"),
    Path("/lib"),
    Path("/lib64"),
    Path("/proc"),
    Path("/root"),
    Path("/run"),
    Path("/sbin"),
    Path("/snap"),
    Path("/sys"),
    Path("/usr"),
    Path("/var"),
)
_WINDOWS_PROHIBITED_DIRECTORY_NAMES = (
    "$Recycle.Bin",
    "Program Files",
    "Program Files (x86)",
    "ProgramData",
    "Recovery",
    "System Volume Information",
    "Windows",
)


def default_gui_prohibited_roots() -> tuple[Path, ...]:
    """Return resolved system locations the local GUI must never operate on.

    The GUI intentionally permits ordinary user-space paths without a launch-time allowlist.
    These denylisted locations protect against accidental selection of operating-system trees;
    they are not a security boundary against the local user who started the service.
    """

    roots = {path.resolve(strict=False) for path in _LINUX_PROHIBITED_ROOTS}
    mount_root = Path("/mnt")
    try:
        drives = tuple(
            path for path in mount_root.iterdir() if path.is_dir() and not path.is_symlink()
        )
    except OSError:
        drives = ()
    for drive in drives:
        roots.update(
            (drive / name).resolve(strict=False) for name in _WINDOWS_PROHIBITED_DIRECTORY_NAMES
        )
    return tuple(sorted(roots, key=str))


def is_gui_prohibited_path(path: Path, *, prohibited_roots: tuple[Path, ...]) -> bool:
    """Return whether a resolved GUI path is inside a prohibited system location."""

    return any(path == root or path.is_relative_to(root) for root in prohibited_roots)


class GuiOperation(BaseModel):
    """Bounded in-process evidence for one read-only GUI operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation_id: str
    kind: Literal["inspect", "dry-run"]
    status: Literal["completed", "failed"]
    input_path: str
    language: LanguageMode
    speaker_count: Literal["auto"] | int
    created_at: datetime
    result: dict[str, Any] | None = None
    error: dict[str, str] | None = None


Service = Callable[..., BaseModel]


def require_completed_canonical_result(path: Path) -> CanonicalResult:
    """Read one strict canonical result with a GUI-facing input error."""

    if not path.is_file():
        raise ValueError("Canonical result JSON must be one completed result file.")
    if path.suffix.lower() != ".json":
        raise ValueError("Choose a completed canonical result JSON, not an audio or subtitle file.")
    try:
        return load_canonical_result(path)
    except ValidationError as error:
        detail = error.errors(include_input=False)[0]
        location = ".".join(str(part) for part in detail["loc"]) or "document"
        raise ValueError(
            f"Canonical JSON validation failed at {location}: {detail['msg']}"
        ) from error
    except (OSError, ValueError) as error:
        raise ValueError(
            "The selected file is not a readable completed canonical result JSON. "
            "Choose a *_results.json or *_results_vNNN.json file."
        ) from error


@dataclass
class GuiWorkflowController:
    """Reject unsafe system paths and invoke existing application services directly."""

    # Retained as an ignored constructor argument so saved integrations using the old
    # controller signature keep starting while the server migrates from allowlists.
    allowed_roots: tuple[Path, ...] = ()
    prohibited_roots: tuple[Path, ...] = field(default_factory=default_gui_prohibited_roots)
    inspect_service: Service = inspect_input
    dry_run_service: Service = dry_run
    _operations: deque[GuiOperation] = field(default_factory=lambda: deque(maxlen=50))

    def run(self, kind: Literal["inspect", "dry-run"], document: dict[str, Any]) -> GuiOperation:
        raw_path = document.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return self._failure(kind, "", "GUI_REQUEST_INVALID", "A non-empty path is required.")
        input_path: Path | None = None
        try:
            language, speaker_count = self.resolve_transcription_options(document)
        except ValueError as error:
            return self._failure(
                kind,
                raw_path,
                "GUI_TRANSCRIPTION_OPTIONS_INVALID",
                str(error),
            )
        try:
            input_path = self.resolve_allowed_path(raw_path)
            config = load_config()
            config = config.model_copy(
                update={
                    "general": config.general.model_copy(update={"language": language}),
                    "diarization": config.diarization.model_copy(
                        update={"speaker_count": speaker_count}
                    ),
                }
            )
            if kind == "inspect":
                result = self.inspect_service(input_path, config=config)
            else:
                raw_output = document.get("output_directory")
                if not isinstance(raw_output, str) or not raw_output.strip():
                    return self._failure(
                        kind,
                        raw_path,
                        "GUI_OUTPUT_REQUIRED",
                        "Enter a shared output directory before running dry-run.",
                    )
                output = (
                    self.resolve_allowed_path(raw_output, directory=True)
                    if isinstance(raw_output, str) and raw_output.strip()
                    else None
                )
                result = self.dry_run_service(input_path, config=config, output_directory=output)
            operation = GuiOperation(
                operation_id=str(uuid4()),
                kind=kind,
                status="completed",
                input_path=str(input_path),
                language=language,
                speaker_count=speaker_count,
                created_at=datetime.now(UTC),
                result=result.model_dump(mode="json"),
            )
        except ApplicationError as error:
            operation = self._new_failure(
                kind,
                raw_path,
                error.code,
                self._user_facing_error_message(
                    error,
                    input_path,
                ),
            )
        except (FileNotFoundError, OSError, ValueError) as error:
            operation = self._new_failure(kind, raw_path, "GUI_PATH_REJECTED", str(error))
        self._operations.appendleft(operation)
        return operation

    @staticmethod
    def _user_facing_error_message(error: ApplicationError, input_path: Path | None) -> str:
        """Turn low-level media-probe failures into a useful local GUI instruction."""

        if error.code != "MEDIA_PROBE_FAILED":
            return str(error)
        if input_path is not None and input_path.suffix.lower() == ".json":
            return (
                "This input is a transcript or result JSON document, not media. "
                "Use it in Review and export; Inspect and plan accepts supported audio files."
            )
        return (
            "This file could not be read as supported audio. "
            "Choose a readable audio file such as WAV or MP3, then inspect it again."
        )

    def operations(self) -> tuple[GuiOperation, ...]:
        return tuple(self._operations)

    def completed_plan(
        self,
        input_path: Path,
        output_directory: Path,
        *,
        language: LanguageMode = LanguageMode.POLISH,
        speaker_count: Literal["auto"] | int = "auto",
    ) -> dict[str, Any] | None:
        """Return the newest exact dry-run produced by this server session."""

        return next(
            (
                operation.result
                for operation in self._operations
                if operation.kind == "dry-run"
                and operation.status == "completed"
                and operation.input_path == str(input_path)
                and operation.language == language
                and operation.speaker_count == speaker_count
                and operation.result is not None
                and operation.result.get("output_directory") == str(output_directory)
            ),
            None,
        )

    def has_completed_plan(
        self,
        input_path: Path,
        output_directory: Path,
        *,
        language: LanguageMode = LanguageMode.POLISH,
        speaker_count: Literal["auto"] | int = "auto",
    ) -> bool:
        """Confirm this server session produced the exact dry-run being authorized."""

        return (
            self.completed_plan(
                input_path,
                output_directory,
                language=language,
                speaker_count=speaker_count,
            )
            is not None
        )

    @staticmethod
    def resolve_transcription_options(
        document: dict[str, Any],
    ) -> tuple[LanguageMode, Literal["auto"] | int]:
        """Validate GUI transcription controls without accepting arbitrary config."""

        try:
            language = LanguageMode(document.get("language", LanguageMode.POLISH))
        except ValueError as error:
            raise ValueError("Language must be pl, en, or auto") from error
        raw_speakers = document.get("speaker_count", "auto")
        if raw_speakers == "auto":
            speaker_count: Literal["auto"] | int = "auto"
        elif isinstance(raw_speakers, int) and not isinstance(raw_speakers, bool):
            if not 1 <= raw_speakers <= 6:
                raise ValueError("Speaker count must be auto or an integer from 1 to 6")
            speaker_count = raw_speakers
        else:
            raise ValueError("Speaker count must be auto or an integer from 1 to 6")
        return language, speaker_count

    def resolve_allowed_path(self, raw_path: str, *, directory: bool = False) -> Path:
        # Browser copy/paste commonly carries an accidental outer space. Trim only the GUI
        # field boundary: whitespace within a path and filesystem names remains significant.
        candidate = normalize_input_path(raw_path.strip())
        if candidate.is_symlink():
            raise ValueError("Symbolic-link paths are not allowed")
        resolved = candidate.resolve(strict=not directory)
        if is_gui_prohibited_path(resolved, prohibited_roots=self.prohibited_roots):
            raise ValueError("Path is inside a prohibited operating-system directory")
        if directory and resolved.exists() and not resolved.is_dir():
            raise ValueError("Output path must be a directory")
        return resolved

    def _failure(
        self, kind: Literal["inspect", "dry-run"], path: str, code: str, message: str
    ) -> GuiOperation:
        operation = self._new_failure(kind, path, code, message)
        self._operations.appendleft(operation)
        return operation

    @staticmethod
    def _new_failure(
        kind: Literal["inspect", "dry-run"], path: str, code: str, message: str
    ) -> GuiOperation:
        return GuiOperation(
            operation_id=str(uuid4()),
            kind=kind,
            status="failed",
            input_path=path,
            language=LanguageMode.POLISH,
            speaker_count="auto",
            created_at=datetime.now(UTC),
            error={"code": code, "message": message},
        )
