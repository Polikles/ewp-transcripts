"""Single-worker transcription queue for the local browser GUI."""

from __future__ import annotations

import os
import re
import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from queue import Queue
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from ewp_transcripts.application import transcribe_one
from ewp_transcripts.cancellation import CancellationToken, TranscriptionCancelled
from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.progress import ProgressHistory, RuntimeProgress, runtime_profile

WorkflowStageName = Literal[
    "correction",
    "review",
    "original_export",
    "assisted_translation",
    "translation",
    "translated_export",
]


class GuiRuntimeProgress(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    phase: str
    percent: int = Field(ge=0, le=100)
    estimated: bool
    elapsed_seconds: int = Field(ge=0)
    phase_elapsed_seconds: int = Field(ge=0)
    eta_seconds: int | None = None
    eta_min_seconds: int | None = None
    eta_max_seconds: int | None = None
    calibrated: bool
    calibration_runs: int = Field(default=0, ge=0)
    calibration_required: int = Field(default=3, ge=1)
    overdue: bool
    stream_index: int = Field(ge=1)
    stream_count: int = Field(ge=1)


class GuiTranscriptionJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str
    status: Literal[
        "staged", "queued", "running", "cancel_requested", "cancelled", "completed", "failed"
    ]
    input_path: str
    output_directory: str
    planned_job_id: str
    planned_result_path: str
    source_sha256: str = ""
    group_sources: dict[str, str] = Field(default_factory=dict)
    language: LanguageMode
    speaker_count: Literal["auto"] | int
    created_at: datetime
    updated_at: datetime
    result_path: str | None = None
    error: dict[str, str] | None = None
    workflow_errors: dict[WorkflowStageName, str] = Field(default_factory=dict)
    workflow_skips: set[WorkflowStageName] = Field(default_factory=set)
    runtime_progress: GuiRuntimeProgress | None = None


class GuiWorkflowStage(BaseModel):
    """One artifact-derived stage in the GUI's per-job workflow tracker."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: Literal["pending", "complete", "failed", "skipped"]
    path: str | None = None
    candidate_path: str | None = None


class GuiWorkflowProgress(BaseModel):
    """Compact, durable workflow progress inferred from published artifacts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    transcription: GuiWorkflowStage
    correction: GuiWorkflowStage
    review: GuiWorkflowStage
    original_export: GuiWorkflowStage
    assisted_translation: GuiWorkflowStage
    translation: GuiWorkflowStage
    translated_export: GuiWorkflowStage


TranscriptionService = Callable[..., Any]


class GuiTranscriptionQueue:
    """Run at most one GPU-intensive transcription at a time."""

    def __init__(
        self,
        *,
        config: ApplicationConfig,
        service: TranscriptionService = transcribe_one,
        history_path: Path | None = None,
    ) -> None:
        self._config = config
        self._service = service
        self._history = ProgressHistory(history_path)
        self._cancellations: dict[str, CancellationToken] = {}
        self._live_progress: dict[str, RuntimeProgress] = {}
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
        group_sources: dict[str, str] | None = None,
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
            group_sources=group_sources or {},
            language=language,
            speaker_count=speaker_count,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job.job_id] = job
            self._order.appendleft(job.job_id)
        return job

    def register_completed_result(
        self,
        result_path: Path,
        *,
        output_directory: Path,
        planned_job_id: str,
        language: LanguageMode,
        source_sha256: str = "",
    ) -> tuple[GuiTranscriptionJob, bool]:
        """Expose an existing canonical result to the local GUI workflow queues.

        The caller has already validated the immutable result through the GUI path-safety policy.
        This is terminal queue history, never a request to rerun ASR.
        """

        normalized = str(result_path)
        with self._lock:
            for job in self._jobs.values():
                if job.result_path == normalized:
                    return job, False
            now = datetime.now(UTC)
            job = GuiTranscriptionJob(
                job_id=str(uuid4()),
                status="completed",
                input_path=normalized,
                output_directory=str(output_directory),
                planned_job_id=planned_job_id,
                planned_result_path=normalized,
                language=language,
                speaker_count="auto",
                created_at=now,
                updated_at=now,
                result_path=normalized,
                source_sha256=source_sha256,
            )
            self._jobs[job.job_id] = job
            self._order.appendleft(job.job_id)
            return job, True

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

    def cancel(self, job_id: str) -> GuiTranscriptionJob:
        """Cancel waiting work immediately or request a safe checkpoint from its worker."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise ValueError("Queue job does not exist")
            if job.status in {"staged", "queued"}:
                status = "cancelled"
            elif job.status in {"running", "cancel_requested"}:
                if not self._cancellations[job_id].request():
                    raise ValueError(
                        "Final publication has started; this job can no longer be cancelled"
                    )
                status = "cancel_requested"
            else:
                raise ValueError("Only waiting or running jobs can be cancelled")
            job = job.model_copy(update={"status": status, "updated_at": datetime.now(UTC)})
            self._jobs[job_id] = job
            return job

    def retry(self, job_id: str) -> GuiTranscriptionJob:
        """Stage a new attempt; the worker rechecks hashes and restarts the application pipeline."""
        with self._lock:
            previous = self._jobs.get(job_id)
            if previous is None or previous.status not in {"failed", "cancelled"}:
                raise ValueError("Only failed or cancelled jobs can be retried")
            previous_sources = {previous.input_path, *previous.group_sources}
            if any(
                (
                    job.planned_job_id == previous.planned_job_id
                    or previous_sources.intersection({job.input_path, *job.group_sources})
                )
                and job.status in {"staged", "queued", "running", "cancel_requested"}
                for job in self._jobs.values()
            ):
                raise ValueError("This recording already has an active attempt")
            now = datetime.now(UTC)
            job = previous.model_copy(
                update={
                    "job_id": str(uuid4()),
                    "status": "staged",
                    "created_at": now,
                    "updated_at": now,
                    "error": None,
                    "runtime_progress": None,
                    "result_path": None,
                    "workflow_errors": {},
                    "workflow_skips": set(),
                }
            )
            self._order.remove(previous.job_id)
            del self._jobs[previous.job_id]
            self._live_progress.pop(previous.job_id, None)
            self._cancellations.pop(previous.job_id, None)
            self._jobs[job.job_id] = job
            self._order.appendleft(job.job_id)
            return job

    def remove(self, job_id: str) -> bool:
        """Remove one staged job; running/history entries remain immutable."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status != "staged":
                return False
            del self._jobs[job_id]
            self._order.remove(job_id)
            return True

    def remove_completed(self) -> tuple[str, ...]:
        """Forget fully finished workflows, preserving unfinished/failed and active entries."""
        with self._lock:
            finished = tuple(
                job_id
                for job_id in self._order
                if self._jobs[job_id].status == "completed"
                and all(
                    stage["state"] in {"complete", "skipped"}
                    for stage in workflow_progress(self._jobs[job_id]).model_dump().values()
                )
            )
            for job_id in finished:
                del self._jobs[job_id]
                self._order.remove(job_id)
            return finished

    def remove_inactive(self, job_ids: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Forget selected inactive jobs without deleting any referenced files."""

        with self._lock:
            active = tuple(
                job_id
                for job_id in job_ids
                if (job := self._jobs.get(job_id)) is not None
                and job.status in {"queued", "running", "cancel_requested"}
            )
            if active:
                raise ValueError("Queued or running transcription jobs cannot be removed")
            removed: list[str] = []
            missing: list[str] = []
            for job_id in job_ids:
                if job_id not in self._jobs:
                    missing.append(job_id)
                    continue
                del self._jobs[job_id]
                self._order.remove(job_id)
                removed.append(job_id)
            return tuple(removed), tuple(missing)

    def active_output_directory(self) -> str | None:
        with self._lock:
            return next(
                (
                    self._jobs[job_id].output_directory
                    for job_id in self._order
                    if self._jobs[job_id].status
                    in {"staged", "queued", "running", "cancel_requested"}
                ),
                None,
            )

    def contains_active_planned_job(self, planned_job_id: str) -> bool:
        with self._lock:
            return any(
                job.planned_job_id == planned_job_id
                and job.status in {"staged", "queued", "running", "cancel_requested"}
                for job in self._jobs.values()
            )

    def contains_active_input(self, input_path: Path) -> bool:
        with self._lock:
            return any(
                (job.input_path == str(input_path) or str(input_path) in job.group_sources)
                and job.status in {"staged", "queued", "running", "cancel_requested"}
                for job in self._jobs.values()
            )

    def jobs(self) -> tuple[GuiTranscriptionJob, ...]:
        with self._lock:
            jobs = []
            for job_id in self._order:
                job = self._jobs[job_id]
                if job_id in self._live_progress:
                    snapshot = self._live_progress[job_id].snapshot()
                    if job.status != "completed":
                        snapshot["percent"] = min(99, snapshot["percent"])
                    job = job.model_copy(
                        update={"runtime_progress": GuiRuntimeProgress.model_validate(snapshot)}
                    )
                jobs.append(job)
            return tuple(jobs)

    def record_workflow_error(self, result_path: str, stage: WorkflowStageName, code: str) -> bool:
        """Record one non-secret later-stage error against its queue job for this GUI process."""

        with self._lock:
            for job_id, job in self._jobs.items():
                if result_path not in {job.result_path, job.planned_result_path}:
                    continue
                errors = {**job.workflow_errors, stage: code}
                self._jobs[job_id] = job.model_copy(
                    update={"workflow_errors": errors, "updated_at": datetime.now(UTC)}
                )
                return True
        return False

    def clear_workflow_error(self, result_path: str, stage: WorkflowStageName) -> bool:
        """Clear a resolved later-stage error from its matching queue job."""

        with self._lock:
            for job_id, job in self._jobs.items():
                if result_path not in {job.result_path, job.planned_result_path}:
                    continue
                self._jobs[job_id] = job.model_copy(
                    update={
                        "workflow_errors": {
                            key: value for key, value in job.workflow_errors.items() if key != stage
                        },
                        "updated_at": datetime.now(UTC),
                    }
                )
                return True
        return False

    def skip_workflow_stage(self, result_path: str, stage: WorkflowStageName) -> bool:
        """Mark one optional workflow stage skipped for the active GUI process."""

        return bool(self.skip_workflow_stages((result_path,), stage))

    def skip_workflow_stages(
        self, result_paths: tuple[str, ...], stage: WorkflowStageName
    ) -> tuple[str, ...]:
        """Mark a selected set in one queue mutation, before the browser refreshes."""

        changed: list[str] = []
        with self._lock:
            for result_path in result_paths:
                for job_id, job in self._jobs.items():
                    if result_path not in {job.result_path, job.planned_result_path}:
                        continue
                    skips = {*job.workflow_skips, stage}
                    self._jobs[job_id] = job.model_copy(
                        update={"workflow_skips": skips, "updated_at": datetime.now(UTC)}
                    )
                    changed.append(result_path)
                    break
        return tuple(changed)

    def reopen_workflow_stage(self, result_path: str, stage: WorkflowStageName) -> bool:
        """Make one previously skipped optional stage actionable again."""

        with self._lock:
            for job_id, job in self._jobs.items():
                if result_path not in {job.result_path, job.planned_result_path}:
                    continue
                self._jobs[job_id] = job.model_copy(
                    update={
                        "workflow_skips": job.workflow_skips - {stage},
                        "workflow_errors": {
                            key: value for key, value in job.workflow_errors.items() if key != stage
                        },
                        "updated_at": datetime.now(UTC),
                    }
                )
                return True
        return False

    def replace_terminal_jobs(self, jobs: tuple[GuiTranscriptionJob, ...]) -> int:
        """Replace inactive queue history from a validated saved workspace.

        Only terminal entries can cross a GUI-process boundary.  Never revive an interrupted
        GPU operation: staged, queued, and running entries require their separate hash-bound
        restoration path.
        """

        if any(job.status not in {"completed", "failed", "cancelled"} for job in jobs):
            raise ValueError("Only completed or failed jobs can be restored as queue history")
        with self._lock:
            if len({job.job_id for job in jobs}) != len(jobs):
                raise ValueError("Saved queue history contains duplicate job IDs")
            active = tuple(
                self._jobs[job_id]
                for job_id in self._order
                if self._jobs[job_id].status in {"staged", "queued", "running", "cancel_requested"}
            )
            if {job.job_id for job in active} & {job.job_id for job in jobs}:
                raise ValueError("Saved queue history conflicts with an active job")
            self._jobs = {job.job_id: job for job in (*active, *jobs)}
            self._order = deque((job.job_id for job in (*active, *jobs)), maxlen=50)
        return len(jobs)

    def clear_current_state(self) -> int:
        """Forget only inactive queue entries; never interrupt active GPU work."""

        with self._lock:
            if any(
                job.status in {"queued", "running", "cancel_requested"}
                for job in self._jobs.values()
            ):
                raise ValueError("Stop or finish active transcription jobs before clearing state")
            count = len(self._jobs)
            self._jobs.clear()
            self._order.clear()
            return count

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
            with self._lock:
                job = self._jobs.get(job_id)
                if job is None or job.status != "queued":
                    continue
                token = CancellationToken()
                self._cancellations[job_id] = token
                self._jobs[job_id] = job.model_copy(
                    update={"status": "running", "updated_at": datetime.now(UTC)}
                )
            fingerprints = job.group_sources or {str(input_path): source_sha256}
            if any(
                digest and not _matches_staged_source(Path(path), digest)
                for path, digest in fingerprints.items()
            ):
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
            tracker: RuntimeProgress | None = None
            try:
                config = self._config.model_copy(
                    update={
                        "general": self._config.general.model_copy(update={"language": language}),
                        "diarization": self._config.diarization.model_copy(
                            update={"speaker_count": speaker_count}
                        ),
                    }
                )
                group_options = (
                    {
                        "explicit_group_paths": tuple(Path(path) for path in job.group_sources),
                        "explicit_group_id": job.planned_job_id,
                    }
                    if job.group_sources
                    else {}
                )
                tracker = RuntimeProgress(
                    self._history,
                    runtime_profile(
                        config,
                        len(job.group_sources) or 1,
                        "group" if job.group_sources else "single",
                    ),
                )
                with self._lock:
                    self._live_progress[job_id] = tracker
                outcome = self._service(
                    input_path,
                    config=config,
                    output_directory=output_directory,
                    progress=tracker,
                    cancellation=token,
                    **group_options,
                )
                tracker.finish(True)
                self._replace(
                    job_id,
                    status="completed",
                    result_path=str(outcome.result_path) if outcome.result_path else None,
                )
            except TranscriptionCancelled:
                if tracker is not None:
                    tracker.finish(False)
                self._replace(job_id, status="cancelled", error=None)
            except ApplicationError as error:
                if tracker is not None:
                    tracker.finish(False)
                self._replace(
                    job_id,
                    status="failed",
                    error={
                        "code": error.code,
                        "message": str(error),
                        **_backend_failure_detail(error),
                        "exception_type": type(error).__name__,
                        "cause_type": type(error.__cause__).__name__ if error.__cause__ else "",
                        "action": (
                            "Transcription failed. Open Settings & About and use "
                            "Test local dependencies, "
                            "then retry after fixing failed checks."
                        ),
                    },
                )
            except Exception:
                if tracker is not None:
                    tracker.finish(False)
                self._replace(
                    job_id,
                    status="failed",
                    error={
                        "code": "GUI_TRANSCRIPTION_FAILED",
                        "message": (
                            "Transcription failed unexpectedly. Use Test local dependencies "
                            "and inspect retained job state."
                        ),
                    },
                )


def _backend_failure_detail(error: ApplicationError) -> dict[str, str]:
    # Backend exception text is only shown in the local technical-details disclosure.
    # Do not expose arbitrary unexpected exceptions or environment credentials.
    if error.code != "SPEECH_ENGINE_ERROR" or error.__cause__ is None:
        return {}
    cause = error.__cause__
    while cause.__cause__ is not None:
        cause = cause.__cause__
    detail = f"{type(cause).__name__}: {cause}"
    for name, value in os.environ.items():
        if value and any(word in name.upper() for word in ("TOKEN", "KEY", "SECRET", "PASSWORD")):
            detail = detail.replace(value, "[redacted]")
    instructions = (
        {
            "help_url": "/help/ubuntu-upgrade",
            "upgrade_guidance": "If this error started after upgrading Ubuntu 24.04 to Ubuntu "
            "26.04, follow WSL config/UBUNTU_UPGRADE.md.",
        }
        if any(word in detail.casefold() for word in ("torchcodec", "libavutil", "ffmpeg"))
        else {}
    )
    return {"backend_detail": detail[:4000], **instructions}


def _matches_staged_source(path: Path, expected_sha256: str) -> bool:
    """Check the dry-run source bytes immediately before opening them for transcription."""

    try:
        return path.is_file() and sha256_file(path) == expected_sha256
    except OSError:
        return False


def workflow_progress(job: GuiTranscriptionJob) -> GuiWorkflowProgress:
    """Infer completed workflow stages from immutable files below a job's output root.

    This deliberately does not treat a transient browser message as progress.  A green
    indicator always corresponds to an artifact that survives a GUI restart. Errors from
    the transcription queue are likewise durable in the queue entry itself. Later workflow
    failures are retained for the active GUI process without storing request contents or
    credentials; a general cross-process operation journal remains deliberately out of scope.
    """

    root = Path(job.output_directory)
    prefix = f"{job.planned_job_id}_"
    result_name = Path(job.result_path or job.planned_result_path).name
    version_match = re.fullmatch(
        rf"{re.escape(job.planned_job_id)}_results(?P<suffix>_v[0-9]{{3}})?\.json",
        result_name,
    )
    revision_prefix = (
        f"{job.planned_job_id}{version_match.group('suffix') or ''}_" if version_match else prefix
    )

    def first(directory: str, pattern: str) -> str | None:
        candidate_root = root / directory
        if not candidate_root.is_dir():
            return None
        matches = sorted(candidate_root.glob(pattern))
        return str(matches[-1]) if matches else None

    if job.status == "cancelled":
        transcription = GuiWorkflowStage(state="skipped")
    elif job.status == "failed":
        transcription = GuiWorkflowStage(state="failed")
    elif job.status == "completed":
        transcription = GuiWorkflowStage(state="complete", path=job.result_path)
    else:
        transcription = GuiWorkflowStage(state="pending")

    correction_path = first("correction-candidates", f"{revision_prefix}revision_*.json")
    review_path = first("revisions", f"{revision_prefix}revision_*.json")
    original_export_path = first("exports", f"{revision_prefix}transcript_revision_*.txt")
    translation_path = first("accepted-translations", f"{prefix}*_translation_*.json")
    translation_candidate_path = first("translation-candidates", f"{prefix}*_translation_*.json")
    translated_export_path = first(
        "translation-exports", f"{prefix}*_translation_*.provenance.json"
    )

    def stage(
        name: WorkflowStageName, path: str | None, candidate_path: str | None = None
    ) -> GuiWorkflowStage:
        if path:
            return GuiWorkflowStage(state="complete", path=path, candidate_path=candidate_path)
        if name in job.workflow_skips:
            return GuiWorkflowStage(state="skipped")
        return GuiWorkflowStage(state="failed" if name in job.workflow_errors else "pending")

    return GuiWorkflowProgress(
        transcription=transcription,
        correction=(
            GuiWorkflowStage(state="skipped")
            if not correction_path
            and any((review_path, original_export_path, translation_path, translated_export_path))
            else stage("correction", correction_path)
        ),
        review=stage("review", review_path),
        original_export=stage("original_export", original_export_path),
        assisted_translation=stage(
            "assisted_translation", translation_candidate_path, translation_candidate_path
        ),
        translation=stage("translation", translation_path),
        translated_export=stage("translated_export", translated_export_path),
    )
