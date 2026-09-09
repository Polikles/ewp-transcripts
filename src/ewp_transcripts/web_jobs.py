"""Single-worker transcription queue for the local browser GUI."""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from queue import Queue
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from ewp_transcripts.application import transcribe_one
from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.revision import sha256_file


class GuiTranscriptionJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str
    status: Literal["staged", "queued", "running", "completed", "failed"]
    input_path: str
    output_directory: str
    planned_job_id: str
    planned_result_path: str
    source_sha256: str = ""
    language: LanguageMode
    speaker_count: Literal["auto"] | int
    created_at: datetime
    updated_at: datetime
    result_path: str | None = None
    error: dict[str, str] | None = None


TranscriptionService = Callable[..., Any]


class GuiTranscriptionQueue:
    """Run at most one GPU-intensive transcription at a time."""

    def __init__(
        self,
        *,
        config: ApplicationConfig,
        service: TranscriptionService = transcribe_one,
    ) -> None:
        self._config = config
        self._service = service
        self._pending: Queue[
            tuple[str, Path, Path, str, LanguageMode, Literal["auto"] | int] | None
        ] = Queue()
        self._jobs: dict[str, GuiTranscriptionJob] = {}
        self._order: deque[str] = deque(maxlen=50)
        self._lock = threading.Lock()
        self._worker = threading.Thread(
            target=self._run,
            name="ewp-gui-transcription",
            daemon=False,
        )
        self._worker.start()

    def stage(
        self,
        input_path: Path,
        output_directory: Path,
        *,
        planned_job_id: str,
        planned_result_path: str,
        source_sha256: str = "",
        language: LanguageMode = LanguageMode.POLISH,
        speaker_count: Literal["auto"] | int = "auto",
    ) -> GuiTranscriptionJob:
        now = datetime.now(UTC)
        job = GuiTranscriptionJob(
            job_id=str(uuid4()),
            status="staged",
            input_path=str(input_path),
            output_directory=str(output_directory),
            planned_job_id=planned_job_id,
            planned_result_path=planned_result_path,
            source_sha256=source_sha256,
            language=language,
            speaker_count=speaker_count,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job.job_id] = job
            self._order.appendleft(job.job_id)
        return job

    def start(self) -> int:
        """Queue every staged job in stable insertion order."""

        pending: list[tuple[str, Path, Path, str, LanguageMode, Literal["auto"] | int]] = []
        with self._lock:
            for job_id in reversed(self._order):
                job = self._jobs[job_id]
                if job.status != "staged":
                    continue
                self._jobs[job_id] = job.model_copy(
                    update={"status": "queued", "updated_at": datetime.now(UTC)}
                )
                pending.append(
                    (
                        job_id,
                        Path(job.input_path),
                        Path(job.output_directory),
                        job.source_sha256,
                        job.language,
                        job.speaker_count,
                    )
                )
        for item in pending:
            self._pending.put(item)
        return len(pending)

    def remove(self, job_id: str) -> bool:
        """Remove one staged job; running/history entries remain immutable."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status != "staged":
                return False
            del self._jobs[job_id]
            self._order.remove(job_id)
            return True

    def active_output_directory(self) -> str | None:
        with self._lock:
            return next(
                (
                    self._jobs[job_id].output_directory
                    for job_id in self._order
                    if self._jobs[job_id].status in {"staged", "queued", "running"}
                ),
                None,
            )

    def contains_active_planned_job(self, planned_job_id: str) -> bool:
        with self._lock:
            return any(
                job.planned_job_id == planned_job_id
                and job.status in {"staged", "queued", "running"}
                for job in self._jobs.values()
            )

    def contains_active_input(self, input_path: Path) -> bool:
        with self._lock:
            return any(
                job.input_path == str(input_path) and job.status in {"staged", "queued", "running"}
                for job in self._jobs.values()
            )

    def jobs(self) -> tuple[GuiTranscriptionJob, ...]:
        with self._lock:
            return tuple(self._jobs[job_id] for job_id in self._order)

    def close(self) -> None:
        self._pending.put(None)
        self._worker.join()

    def _replace(self, job_id: str, **updates: Any) -> None:
        with self._lock:
            self._jobs[job_id] = self._jobs[job_id].model_copy(
                update={**updates, "updated_at": datetime.now(UTC)}
            )

    def _run(self) -> None:
        while True:
            item = self._pending.get()
            if item is None:
                return
            job_id, input_path, output_directory, source_sha256, language, speaker_count = item
            if source_sha256 and not _matches_staged_source(input_path, source_sha256):
                self._replace(
                    job_id,
                    status="failed",
                    error={
                        "code": "GUI_SOURCE_FINGERPRINT_MISMATCH",
                        "message": (
                            "The staged source changed after dry-run. Inspect and stage the "
                            "current file again."
                        ),
                    },
                )
                continue
            self._replace(job_id, status="running")
            try:
                config = self._config.model_copy(
                    update={
                        "general": self._config.general.model_copy(update={"language": language}),
                        "diarization": self._config.diarization.model_copy(
                            update={"speaker_count": speaker_count}
                        ),
                    }
                )
                outcome = self._service(
                    input_path,
                    config=config,
                    output_directory=output_directory,
                )
                self._replace(
                    job_id,
                    status="completed",
                    result_path=str(outcome.result_path) if outcome.result_path else None,
                )
            except ApplicationError as error:
                self._replace(
                    job_id,
                    status="failed",
                    error={"code": error.code, "message": str(error)},
                )
            except Exception:
                self._replace(
                    job_id,
                    status="failed",
                    error={
                        "code": "GUI_TRANSCRIPTION_FAILED",
                        "message": "Transcription failed unexpectedly; inspect retained job state.",
                    },
                )


def _matches_staged_source(path: Path, expected_sha256: str) -> bool:
    """Check the dry-run source bytes immediately before opening them for transcription."""

    try:
        return path.is_file() and sha256_file(path) == expected_sha256
    except OSError:
        return False
