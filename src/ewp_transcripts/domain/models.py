"""Typed foundational domain models."""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ewp_transcripts.domain.enums import (
    ChannelMode,
    DiagnosticStatus,
    DiscoverySkipReason,
    JobStateStatus,
    LanguageMode,
    PlanDecision,
    WarningCode,
    WarningSeverity,
)


class DiagnosticCheck(BaseModel):
    """One sanitized environment check returned by ``doctor``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1)
    status: DiagnosticStatus
    message: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class DoctorResult(BaseModel):
    """Complete lightweight environment diagnostic result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    application_version: str
    ready: bool
    checks: tuple[DiagnosticCheck, ...]


class DiscoveredFile(BaseModel):
    """Regular file selected for later media inspection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: Path
    filename: str = Field(min_length=1)
    suffix: str


class SkippedPath(BaseModel):
    """Directory entry deliberately omitted during discovery."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: Path
    reason: DiscoverySkipReason


class DiscoveryResult(BaseModel):
    """Deterministic output of file discovery before media probing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_path: Path
    recursive: bool
    files: tuple[DiscoveredFile, ...]
    skipped: tuple[SkippedPath, ...]


class AudioStream(BaseModel):
    """Normalized metadata for one audio stream reported by ffprobe."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int = Field(ge=0)
    codec: str = Field(min_length=1)
    sample_rate_hz: int = Field(gt=0)
    channels: int = Field(gt=0)
    channel_layout: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    language: str | None = None
    title: str | None = None


class MediaProbeResult(BaseModel):
    """Normalized, non-destructive media inspection result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: Path
    format_names: tuple[str, ...]
    duration_ms: int = Field(ge=0)
    audio_streams: tuple[AudioStream, ...]
    has_video: bool = False


class SourceFingerprint(BaseModel):
    """Content identity calculated without modifying the source file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: Path
    filename: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class GroupedSource(BaseModel):
    """Fingerprinted source with an optional filename-derived speaker label."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fingerprint: SourceFingerprint
    speaker_label: str | None = None
    speaker_source: Literal["explicit", "filename", "channel_metadata", "default"] = "default"


class EpisodeCandidate(BaseModel):
    """Filename-derived episode candidate before media compatibility checks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str = Field(min_length=1)
    sources: tuple[GroupedSource, ...] = Field(min_length=1)


class ApplicationWarning(BaseModel):
    """Structured warning that does not modify source media."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: WarningCode
    severity: WarningSeverity = WarningSeverity.WARNING
    message: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class ChannelMetrics(BaseModel):
    """Measured stereo similarity and windowed channel activity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sample_rate_hz: int = Field(gt=0)
    analyzed_samples_per_channel: int = Field(gt=0)
    window_ms: int = Field(gt=0)
    windows: int = Field(gt=0)
    correlation: float = Field(ge=-1.0, le=1.0)
    normalized_difference_rms: float = Field(ge=0.0)
    left_rms_dbfs: float
    right_rms_dbfs: float
    left_peak_dbfs: float
    right_peak_dbfs: float
    clipping_sample_ratio: float = Field(ge=0.0, le=1.0)
    channel_rms_difference_db: float = Field(ge=0.0)
    left_activity_threshold_dbfs: float
    right_activity_threshold_dbfs: float
    left_only_ratio: float = Field(ge=0.0, le=1.0)
    right_only_ratio: float = Field(ge=0.0, le=1.0)
    both_active_ratio: float = Field(ge=0.0, le=1.0)
    neither_active_ratio: float = Field(ge=0.0, le=1.0)


class ChannelClassification(BaseModel):
    """Detected topology and safe processing decision for one audio stream."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    original_channels: int = Field(gt=0)
    detected_mode: ChannelMode
    processing_mode: ChannelMode
    selected_channel_index: int | None = Field(default=None, ge=0)
    warnings: tuple[ApplicationWarning, ...] = ()


class InspectedSource(BaseModel):
    """Fingerprinted source paired with one selected audio stream."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fingerprint: SourceFingerprint
    media_type: Literal["audio", "video"] = "audio"
    stream: AudioStream
    duration_ms: int = Field(ge=0)
    channel_mode: ChannelMode
    channel_metrics: ChannelMetrics | None = None
    channel_classification: ChannelClassification
    speaker_id: str = Field(pattern=r"^speaker_[0-9]{3,}$")
    speaker_label: str | None = None
    speaker_source: Literal["explicit", "filename", "channel_metadata", "default"] = "default"


class EpisodeInspection(BaseModel):
    """Validated grouped-source metadata and channel-processing decisions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str = Field(min_length=1)
    episode_signature_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    duration_ms: int = Field(ge=0)
    sample_rate_hz: int = Field(gt=0)
    sources: tuple[InspectedSource, ...] = Field(min_length=1)
    warnings: tuple[ApplicationWarning, ...] = ()


class InspectionResult(BaseModel):
    """Complete non-destructive inspection of one file or directory input."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    discovery: DiscoveryResult
    episodes: tuple[EpisodeInspection, ...]


class PlannedOutputPaths(BaseModel):
    """Complete immutable filename set for one planned result version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    output_directory: Path
    result_version: int = Field(ge=1)
    results: Path
    partial_results: Path
    failed_results: Path
    transcript: Path | None = None
    subtitles_srt: Path | None = None
    subtitles_vtt: Path | None = None
    segments: Path | None = None


class ExistingResult(BaseModel):
    """Minimal trusted metadata read from one completed canonical result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: Path
    job_id: str = Field(min_length=1)
    episode_signature_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_version: int = Field(ge=1)


class JobOutputPlan(BaseModel):
    """Read-only process/skip and version decision for one inspected episode."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str = Field(min_length=1)
    episode_signature_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: PlanDecision
    outputs: PlannedOutputPaths | None = None
    existing_result: ExistingResult | None = None
    warnings: tuple[ApplicationWarning, ...] = ()

    @model_validator(mode="after")
    def validate_decision_payload(self) -> Self:
        if self.decision is PlanDecision.PROCESS and self.outputs is None:
            raise ValueError("process decisions require planned outputs")
        if self.decision is PlanDecision.SKIP and self.existing_result is None:
            raise ValueError("skip decisions require an existing result")
        return self


class DryRunResult(BaseModel):
    """Complete non-mutating execution plan for one input batch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    inspection: InspectionResult
    output_directory: Path
    language: LanguageMode
    jobs: tuple[JobOutputPlan, ...]


class JobStateRecord(BaseModel):
    """Small persistent envelope for a non-completed job state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state_schema_version: Literal["1.0"] = "1.0"
    application_version: str = Field(min_length=1)
    run_id: UUID
    job_id: str = Field(min_length=1)
    episode_signature_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_version: int = Field(ge=1)
    status: JobStateStatus
    created_at: datetime
    updated_at: datetime
    failure_code: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]*$")
    failure_message: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_failure_details(self) -> Self:
        has_details = self.failure_code is not None and self.failure_message is not None
        if self.status is JobStateStatus.RUNNING and (
            self.failure_code is not None or self.failure_message is not None
        ):
            raise ValueError("running state cannot contain failure details")
        if self.status is not JobStateStatus.RUNNING and not has_details:
            raise ValueError("failed and cancelled states require code and message")
        return self


class JobReservation(BaseModel):
    """Locked planning result and optional atomically published running state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plan: JobOutputPlan
    state: JobStateRecord | None = None
    state_path: Path | None = None

    @model_validator(mode="after")
    def validate_reservation_payload(self) -> Self:
        processing = self.plan.decision is PlanDecision.PROCESS
        if processing != (self.state is not None and self.state_path is not None):
            raise ValueError("only process decisions may contain a state reservation")
        return self


class WorkDirectory(BaseModel):
    """Owned isolated workspace for one job inside one run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_root: Path
    run_id: UUID
    job_id: str = Field(min_length=1)
    path: Path
    marker_path: Path
