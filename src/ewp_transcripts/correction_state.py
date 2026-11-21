"""Private immutable cache of validated correction chunk responses."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ewp_transcripts.correction import validate_correction_response
from ewp_transcripts.correction_execution import (
    CorrectionExecutionMetrics,
    CorrectionExecutionPolicy,
    execute_correction_call,
)
from ewp_transcripts.domain.correction import (
    CorrectionProvider,
    CorrectionRequest,
    CorrectionResponse,
)
from ewp_transcripts.domain.errors import InvalidCorrectionResponseError
from ewp_transcripts.platform_runtime import private_descriptor_mode


class CorrectionResumeEntry(BaseModel):
    """Strict persisted response bound to one complete operation identity."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    schema_version: str = Field(pattern=r"^1\.0$")
    operation_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    response: CorrectionResponse
    execution_metrics: dict[str, int | None] | None = None


@dataclass(frozen=True, slots=True)
class CorrectionCallOutcome:
    response: CorrectionResponse
    resumed: bool
    state_path: Path
    metrics: CorrectionExecutionMetrics


def call_correction_resumable(
    provider: CorrectionProvider,
    request: CorrectionRequest,
    *,
    state_directory: Path,
    execution_policy: CorrectionExecutionPolicy | None = None,
) -> CorrectionCallOutcome:
    """Reuse only an exactly bound validated response or publish one new response."""

    state_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(state_directory, 0o700)
    state_path = state_directory / f"{request.operation_id}.json"
    if state_path.exists():
        entry = _load_entry(state_path, provider, request)
        return CorrectionCallOutcome(
            entry.response,
            True,
            state_path,
            CorrectionExecutionMetrics(
                attempts=0,
                retries=0,
                elapsed_ms=0,
                request_count=0,
                input_tokens=0,
                output_tokens=0,
                cost_usd_micros=0,
            ),
        )

    execution = execute_correction_call(provider, request, policy=execution_policy)
    response = execution.response
    entry = CorrectionResumeEntry(
        schema_version="1.0",
        operation_id=request.operation_id,
        provider_id=provider.provider_id,
        model_id=provider.model_id,
        prompt_id=request.prompt_id,
        prompt_sha256=request.prompt_sha256,
        response=response,
        execution_metrics={
            "attempts": execution.metrics.attempts,
            "retries": execution.metrics.retries,
            "elapsed_ms": execution.metrics.elapsed_ms,
            "request_count": execution.metrics.request_count,
            "input_tokens": execution.metrics.input_tokens,
            "output_tokens": execution.metrics.output_tokens,
            "cost_usd_micros": execution.metrics.cost_usd_micros,
        },
    )
    payload = (entry.model_dump_json(indent=2) + "\n").encode()
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=".correction-", dir=state_directory)
        temporary_path = Path(temporary_name)
        private_descriptor_mode(descriptor)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, state_path)
        except FileExistsError:
            entry = _load_entry(state_path, provider, request)
            return CorrectionCallOutcome(
                entry.response,
                True,
                state_path,
                CorrectionExecutionMetrics(
                    attempts=0,
                    retries=0,
                    elapsed_ms=0,
                    request_count=0,
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd_micros=0,
                ),
            )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return CorrectionCallOutcome(response, False, state_path, execution.metrics)


def summarize_correction_resume_state(state_directory: Path) -> dict[str, int]:
    """Aggregate content-free provider evidence from validated resume entries."""

    totals = {
        "chunks": 0,
        "attempts": 0,
        "retries": 0,
        "elapsed_ms": 0,
        "request_count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd_micros": 0,
        "entries_without_execution_metrics": 0,
    }
    for path in sorted(state_directory.glob("*.json")):
        try:
            entry = CorrectionResumeEntry.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            raise InvalidCorrectionResponseError(
                f"Cannot read valid correction resume state: {path}"
            ) from error
        totals["chunks"] += 1
        metrics = entry.execution_metrics
        if metrics is None:
            totals["entries_without_execution_metrics"] += 1
            usage = entry.response.usage
            if usage is not None:
                totals["input_tokens"] += usage.input_tokens or 0
                totals["output_tokens"] += usage.output_tokens or 0
                totals["cost_usd_micros"] += usage.cost_usd_micros or 0
            continue
        for name in (
            "attempts",
            "retries",
            "elapsed_ms",
            "request_count",
            "input_tokens",
            "output_tokens",
            "cost_usd_micros",
        ):
            totals[name] += metrics.get(name) or 0
    return totals


def _load_entry(
    path: Path,
    provider: CorrectionProvider,
    request: CorrectionRequest,
) -> CorrectionResumeEntry:
    try:
        entry = CorrectionResumeEntry.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise InvalidCorrectionResponseError(
            f"Cannot read valid correction resume state: {path}"
        ) from error
    if (
        entry.operation_id != request.operation_id
        or entry.provider_id != provider.provider_id
        or entry.model_id != provider.model_id
        or entry.prompt_id != request.prompt_id
        or entry.prompt_sha256 != request.prompt_sha256
    ):
        raise InvalidCorrectionResponseError("Correction resume state identity does not match")
    validate_correction_response(request, entry.response)
    return entry
