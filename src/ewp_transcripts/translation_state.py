"""Private immutable resume state for validated automated translations."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ewp_transcripts.automated_translation import validate_automated_translation_response
from ewp_transcripts.domain.automated_translation import (
    AutomatedTranslationProvider,
    AutomatedTranslationRequest,
    AutomatedTranslationResponse,
)
from ewp_transcripts.domain.errors import InvalidTranslationResponseError
from ewp_transcripts.platform_runtime import private_descriptor_mode
from ewp_transcripts.translation_execution import (
    TranslationExecutionMetrics,
    TranslationExecutionPolicy,
    execute_translation_call,
)


class TranslationResumeEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    schema_version: str = Field(pattern=r"^1\.0$")
    operation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response: AutomatedTranslationResponse
    execution_metrics: dict[str, int | None]


@dataclass(frozen=True, slots=True)
class TranslationCallOutcome:
    response: AutomatedTranslationResponse
    resumed: bool
    state_path: Path
    metrics: TranslationExecutionMetrics


def call_translation_resumable(
    provider: AutomatedTranslationProvider,
    request: AutomatedTranslationRequest,
    *,
    state_directory: Path,
    execution_policy: TranslationExecutionPolicy | None = None,
) -> TranslationCallOutcome:
    """Reuse only an exactly identified and locally revalidated response."""

    state_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(state_directory, 0o700)
    state_path = state_directory / f"{request.operation_id}.json"
    if state_path.exists():
        entry = _load_entry(state_path, provider, request)
        return TranslationCallOutcome(entry.response, True, state_path, _zero_metrics())
    execution = execute_translation_call(provider, request, policy=execution_policy)
    entry = TranslationResumeEntry(
        schema_version="1.0",
        operation_id=request.operation_id,
        provider_id=provider.provider_id,
        model_id=provider.model_id,
        prompt_id=request.prompt_id,
        prompt_sha256=request.prompt_sha256,
        response=execution.response,
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
        descriptor, temporary_name = tempfile.mkstemp(prefix=".translation-", dir=state_directory)
        temporary_path = Path(temporary_name)
        private_descriptor_mode(descriptor)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, state_path)
        except FileExistsError:
            existing = _load_entry(state_path, provider, request)
            return TranslationCallOutcome(existing.response, True, state_path, _zero_metrics())
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return TranslationCallOutcome(execution.response, False, state_path, execution.metrics)


def summarize_translation_resume_state(state_directory: Path) -> dict[str, int]:
    """Aggregate content-free execution evidence from strict resume entries."""

    totals = {
        "units": 0,
        "attempts": 0,
        "retries": 0,
        "elapsed_ms": 0,
        "request_count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd_micros": 0,
    }
    for path in sorted(state_directory.glob("*.json")):
        try:
            entry = TranslationResumeEntry.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            raise InvalidTranslationResponseError(
                f"Cannot read valid translation resume state: {path}"
            ) from error
        totals["units"] += 1
        for name in tuple(totals)[1:]:
            totals[name] += entry.execution_metrics.get(name) or 0
    return totals


def _load_entry(
    path: Path,
    provider: AutomatedTranslationProvider,
    request: AutomatedTranslationRequest,
) -> TranslationResumeEntry:
    try:
        entry = TranslationResumeEntry.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise InvalidTranslationResponseError(
            f"Cannot read valid translation resume state: {path}"
        ) from error
    if (
        entry.operation_id != request.operation_id
        or entry.provider_id != provider.provider_id
        or entry.model_id != provider.model_id
        or entry.prompt_id != request.prompt_id
        or entry.prompt_sha256 != request.prompt_sha256
    ):
        raise InvalidTranslationResponseError("Translation resume state identity does not match")
    validate_automated_translation_response(request, entry.response)
    return entry


def _zero_metrics() -> TranslationExecutionMetrics:
    return TranslationExecutionMetrics(0, 0, 0, 0, 0, 0, 0)
