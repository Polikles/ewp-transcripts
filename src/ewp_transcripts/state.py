"""Atomic non-completed job-state reservation and persistence."""

from __future__ import annotations

import os
import stat
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from ewp_transcripts import __version__
from ewp_transcripts.config import OutputsConfig
from ewp_transcripts.domain import (
    EpisodeInspection,
    JobReservation,
    JobStateRecord,
)
from ewp_transcripts.domain.canonical import CanonicalResult
from ewp_transcripts.domain.enums import JobStateStatus, PlanDecision
from ewp_transcripts.domain.errors import InvalidJobStateError, OutputReservationError
from ewp_transcripts.output_lock import output_directory_lock
from ewp_transcripts.platform_runtime import fsync_directory
from ewp_transcripts.storage import find_existing_results, plan_job_outputs


def _write_all(descriptor: int, payload: bytes) -> None:
    remaining = memoryview(payload)
    while remaining:
        remaining = remaining[os.write(descriptor, remaining) :]


def _read_state(path: Path, *, maximum_bytes: int = 1024 * 1024) -> JobStateRecord:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum_bytes:
                raise InvalidJobStateError(f"Job state is not a safe regular file: {path}")
            payload = bytearray()
            while chunk := os.read(descriptor, 64 * 1024):
                payload.extend(chunk)
        finally:
            os.close(descriptor)
        return JobStateRecord.model_validate_json(payload)
    except InvalidJobStateError:
        raise
    except (OSError, ValueError) as error:
        raise InvalidJobStateError(f"Cannot read trusted job state: {path}") from error


def _publish_exclusive_json(path: Path, payload: str, *, run_id: UUID) -> None:
    temporary = path.parent / f".{path.name}.{run_id}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        created = True
        try:
            _write_all(descriptor, payload.encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.link(temporary, path)
        fsync_directory(path.parent)
    except FileExistsError as error:
        raise OutputReservationError(f"Output state already exists: {path}") from error
    except OSError as error:
        raise OutputReservationError(f"Cannot reserve output state: {path}") from error
    finally:
        if created:
            with suppress(FileNotFoundError):
                temporary.unlink()
            with suppress(OSError):
                fsync_directory(path.parent)


def reserve_job(
    inspection: EpisodeInspection,
    *,
    output_directory: Path,
    run_id: UUID,
    force: bool,
    config: OutputsConfig,
    lock_timeout_seconds: float = 0,
) -> JobReservation:
    """Re-plan under lock and atomically publish a running state for PROCESS."""

    with output_directory_lock(
        output_directory,
        timeout_seconds=lock_timeout_seconds,
    ):
        existing = find_existing_results(output_directory)
        plan = plan_job_outputs(
            inspection,
            output_directory=output_directory,
            existing_results=existing,
            force=force,
            config=config,
        )
        if plan.decision is PlanDecision.SKIP:
            return JobReservation(plan=plan)
        if plan.outputs is None:  # Defensive; JobOutputPlan also enforces this invariant.
            raise OutputReservationError("Process plan has no output paths")

        now = datetime.now(UTC)
        state = JobStateRecord(
            application_version=__version__,
            run_id=run_id,
            job_id=inspection.job_id,
            episode_signature_sha256=inspection.episode_signature_sha256,
            result_version=plan.outputs.result_version,
            status=JobStateStatus.RUNNING,
            created_at=now,
            updated_at=now,
        )
        _publish_exclusive_json(
            plan.outputs.partial_results,
            state.model_dump_json(indent=2) + "\n",
            run_id=run_id,
        )
        return JobReservation(
            plan=plan,
            state=state,
            state_path=plan.outputs.partial_results,
        )


def transition_job_state(
    reservation: JobReservation,
    *,
    status: JobStateStatus,
    failure_code: str,
    failure_message: str,
    lock_timeout_seconds: float = 0,
) -> JobStateRecord:
    """Atomically publish failed/cancelled state after verifying reservation ownership."""

    if status not in {JobStateStatus.FAILED, JobStateStatus.CANCELLED}:
        raise ValueError("transition target must be failed or cancelled")
    if reservation.state is None or reservation.state_path is None:
        raise InvalidJobStateError("Only a processing reservation can transition state")
    outputs = reservation.plan.outputs
    if outputs is None:
        raise InvalidJobStateError("Reservation has no output paths")

    with output_directory_lock(
        outputs.output_directory,
        timeout_seconds=lock_timeout_seconds,
    ):
        persisted = _read_state(reservation.state_path)
        expected = reservation.state
        identity = (
            persisted.run_id,
            persisted.job_id,
            persisted.episode_signature_sha256,
            persisted.result_version,
        )
        expected_identity = (
            expected.run_id,
            expected.job_id,
            expected.episode_signature_sha256,
            expected.result_version,
        )
        if identity != expected_identity or persisted.status is not JobStateStatus.RUNNING:
            raise InvalidJobStateError("Persisted running state does not match reservation")

        transitioned = JobStateRecord.model_validate(
            persisted.model_copy(
                update={
                    "status": status,
                    "updated_at": datetime.now(UTC),
                    "failure_code": failure_code,
                    "failure_message": failure_message,
                }
            ).model_dump()
        )
        _publish_exclusive_json(
            outputs.failed_results,
            transitioned.model_dump_json(indent=2) + "\n",
            run_id=persisted.run_id,
        )
        try:
            reservation.state_path.unlink()
            fsync_directory(outputs.output_directory)
        except OSError as error:
            raise InvalidJobStateError(
                f"Failed state was published but running state could not be removed: "
                f"{reservation.state_path}"
            ) from error
        return transitioned


def finalize_job_result(
    reservation: JobReservation,
    result: CanonicalResult,
    *,
    lock_timeout_seconds: float = 0,
) -> Path:
    """Publish one completed canonical result and retire its running state under lock."""

    if reservation.state is None or reservation.state_path is None:
        raise InvalidJobStateError("Only a processing reservation can be finalized")
    outputs = reservation.plan.outputs
    if outputs is None:
        raise InvalidJobStateError("Reservation has no output paths")
    expected = reservation.state
    result_identity = (
        result.run_id,
        result.job_id,
        result.episode.episode_signature_sha256,
        result.result_version,
    )
    expected_identity = (
        expected.run_id,
        expected.job_id,
        expected.episode_signature_sha256,
        expected.result_version,
    )
    if result.status != "completed" or result_identity != expected_identity:
        raise InvalidJobStateError("Completed result does not match its reservation")

    with output_directory_lock(
        outputs.output_directory,
        timeout_seconds=lock_timeout_seconds,
    ):
        persisted = _read_state(reservation.state_path)
        persisted_identity = (
            persisted.run_id,
            persisted.job_id,
            persisted.episode_signature_sha256,
            persisted.result_version,
        )
        if (
            persisted_identity != expected_identity
            or persisted.status is not JobStateStatus.RUNNING
        ):
            raise InvalidJobStateError("Persisted running state does not match reservation")
        _publish_exclusive_json(
            outputs.results,
            result.model_dump_json(indent=2) + "\n",
            run_id=result.run_id,
        )
        try:
            reservation.state_path.unlink()
            fsync_directory(outputs.output_directory)
        except OSError as error:
            raise InvalidJobStateError(
                f"Final result was published but running state could not be removed: "
                f"{reservation.state_path}"
            ) from error
        return outputs.results
