"""Stable application-facing operations shared by user interfaces."""

from __future__ import annotations

import platform
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from ewp_transcripts import __version__
from ewp_transcripts.automated_translation import build_automated_translation
from ewp_transcripts.config import ApplicationConfig, load_config
from ewp_transcripts.correction import (
    CorrectionChunkConfig,
    build_correction_revision,
)
from ewp_transcripts.correction_consent import (
    ConsentChoice,
    CorrectionConsentScope,
    authorize_correction_api,
    load_correction_consents,
    persist_correction_consent,
)
from ewp_transcripts.correction_dictionary import ProjectCorrectionDictionary
from ewp_transcripts.correction_execution import (
    CorrectionExecutionPolicy,
)
from ewp_transcripts.discovery import (
    discover_explicit_group,
    discover_input,
    group_discovered_files,
    group_explicit_files,
    normalize_input_path,
)
from ewp_transcripts.doctor import run_doctor
from ewp_transcripts.domain import (
    DiscoveryResult,
    DoctorResult,
    DryRunResult,
    EpisodeCandidate,
    EpisodeInspection,
    InspectionResult,
    JobReservation,
    TranscriptReview,
    TranscriptRevision,
)
from ewp_transcripts.domain.automated_translation import AutomatedTranslationProvider
from ewp_transcripts.domain.canonical import (
    CanonicalEnvironment,
    CanonicalResult,
    load_canonical_result,
)
from ewp_transcripts.domain.correction import CorrectionProvider
from ewp_transcripts.domain.enums import ChannelMode, JobStateStatus, PlanDecision
from ewp_transcripts.domain.errors import (
    AmbiguousJobIdError,
    ApplicationError,
    InvalidReviewError,
    UnsupportedPipelineScopeError,
)
from ewp_transcripts.domain.revision import load_transcript_revision, sha256_file
from ewp_transcripts.domain.translation import Language, TranscriptTranslation, TranslationStyle
from ewp_transcripts.domain.translation_review import TranslationReview
from ewp_transcripts.engines import AlignmentEngine, AsrEngine, DiarizationEngine
from ewp_transcripts.engines.pyannote import PyannoteDiarizationEngine
from ewp_transcripts.engines.whisperx import WhisperXAlignmentEngine, WhisperXAsrEngine

# Re-exported here to keep user interfaces on the application boundary.
from ewp_transcripts.export_service import (
    BatchExportOutcome,
    ExportFormat,
    ExportOutcome,
    export_batch,
    export_result,
)
from ewp_transcripts.inspection import apply_explicit_speaker_labels, inspect_episode
from ewp_transcripts.media import measure_file_channels
from ewp_transcripts.pipeline import (
    run_diarization_pipeline,
    run_single_speaker_pipeline,
    run_source_speaker_pipeline,
)
from ewp_transcripts.review_discovery import discover_review_files, discover_review_results
from ewp_transcripts.review_format import load_review
from ewp_transcripts.review_service import prepare_review
from ewp_transcripts.review_storage import publish_review
from ewp_transcripts.revision_audit import build_revision_audit, publish_revision_audit
from ewp_transcripts.revision_service import build_revision
from ewp_transcripts.revision_storage import publish_next_revision, revision_filename
from ewp_transcripts.state import finalize_job_result, reserve_job, transition_job_state
from ewp_transcripts.storage import (
    find_existing_results,
    plan_job_outputs,
    resolve_output_directory,
)
from ewp_transcripts.translation_audit import (
    build_translation_audit,
    publish_translation_audit,
)
from ewp_transcripts.translation_consent import (
    TranslationConsentScope,
    authorize_translation_api,
    load_translation_consents,
    persist_translation_consent,
)
from ewp_transcripts.translation_dictionary import ProjectTranslationDictionary
from ewp_transcripts.translation_discovery import (
    discover_translation_reviews,
    discover_translations,
    latest_compatible_revision_path,
    resolve_translation_review_sources,
)
from ewp_transcripts.translation_export import (
    TranslationExportFormat,
    TranslationExportOutcome,
)
from ewp_transcripts.translation_export import (
    export_translation as export_translation_artifact,
)
from ewp_transcripts.translation_review_format import load_translation_review
from ewp_transcripts.translation_review_service import (
    prepare_translation_review,
    validate_translation_review_source,
)
from ewp_transcripts.translation_service import build_manual_translation
from ewp_transcripts.translation_storage import (
    publish_next_translation,
    publish_translation_review,
)
from ewp_transcripts.workdirs import (
    allocate_work_directory,
    cleanup_work_directory,
    find_work_directories,
)

__all__ = [
    "ExportFormat",
    "ExportOutcome",
    "BatchExportOutcome",
    "application_version",
    "clean_all_workdirs",
    "discover",
    "doctor",
    "dry_run",
    "export_result",
    "export_batch",
    "inspect_input",
    "prepare_review_file",
    "prepare_review_batch",
    "preview_review_file",
    "apply_review_file",
    "process_review_batch",
    "prepare_translation_review_file",
    "preview_translation_review_file",
    "apply_translation_review_file",
    "preview_automated_translation",
    "apply_automated_translation",
    "process_automated_translation_batch",
    "prepare_translation_review_batch",
    "process_translation_review_batch",
    "export_translation",
    "export_translation_batch",
    "TranslationExportFormat",
    "audit_translation_file",
    "audit_revision_file",
    "preview_mock_correction",
    "apply_mock_correction",
    "process_mock_correction_batch",
    "preview_correction",
    "apply_correction",
    "transcribe_batch",
    "transcribe_one",
]

AsrFactory = Callable[[ApplicationConfig], AsrEngine]
AlignmentFactory = Callable[[ApplicationConfig], AlignmentEngine]
DiarizationFactory = Callable[[ApplicationConfig], DiarizationEngine]


@dataclass(frozen=True, slots=True)
class TranscriptionOutcome:
    """User-facing outcome of one complete transcription lifecycle."""

    decision: PlanDecision
    job_id: str
    result_path: Path
    exports: ExportOutcome | None = None
    run_id: UUID | None = None
    elapsed_ms: int | None = None


@dataclass(frozen=True, slots=True)
class BatchJobOutcome:
    """Stable summary entry for one episode in a sequential batch."""

    job_id: str
    status: Literal["completed", "skipped", "failed", "cancelled"]
    result_path: Path | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    run_id: UUID | None = None
    elapsed_ms: int | None = None


@dataclass(frozen=True, slots=True)
class BatchTranscriptionOutcome:
    """Deterministically ordered summary of one sequential batch."""

    output_directory: Path
    jobs: tuple[BatchJobOutcome, ...]
    stopped_early: bool = False

    @property
    def completed(self) -> int:
        return sum(job.status == "completed" for job in self.jobs)

    @property
    def skipped(self) -> int:
        return sum(job.status == "skipped" for job in self.jobs)

    @property
    def failed(self) -> int:
        return sum(job.status == "failed" for job in self.jobs)

    @property
    def cancelled(self) -> int:
        return sum(job.status == "cancelled" for job in self.jobs)


@dataclass(frozen=True, slots=True)
class CleanupOutcome:
    """Marker-verified workspaces selected or removed by one cleanup operation."""

    paths: tuple[Path, ...]
    dry_run: bool


@dataclass(frozen=True, slots=True)
class ReviewPreparationOutcome:
    """One prepared and safely published human-editable review."""

    review: TranscriptReview
    path: Path


@dataclass(frozen=True, slots=True)
class BatchReviewJobOutcome:
    """One deterministic review-preparation batch item."""

    result_path: Path
    status: Literal["prepared", "failed"]
    review_path: Path | None = None
    failure_code: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchReviewPreparationOutcome:
    """Summary of isolated sequential review preparation."""

    output_directory: Path
    jobs: tuple[BatchReviewJobOutcome, ...]
    stopped_early: bool = False

    @property
    def prepared(self) -> int:
        return sum(job.status == "prepared" for job in self.jobs)

    @property
    def failed(self) -> int:
        return sum(job.status == "failed" for job in self.jobs)


@dataclass(frozen=True, slots=True)
class RevisionPreviewOutcome:
    """Validated unpublished revision and its exact base result."""

    review_path: Path
    base_result_path: Path
    revision: TranscriptRevision


@dataclass(frozen=True, slots=True)
class RevisionApplyOutcome:
    """Atomically published immutable revision."""

    review_path: Path
    base_result_path: Path
    revision: TranscriptRevision
    revision_path: Path


@dataclass(frozen=True, slots=True)
class TranslationReviewPreparationOutcome:
    """One safely published human-editable translation review."""

    review: TranslationReview
    path: Path


@dataclass(frozen=True, slots=True)
class TranslationPreviewOutcome:
    """One validated unpublished complete translation snapshot."""

    review_path: Path
    result_path: Path
    translation: TranscriptTranslation


@dataclass(frozen=True, slots=True)
class TranslationApplyOutcome:
    """One atomically published complete translation snapshot."""

    review_path: Path
    result_path: Path
    translation: TranscriptTranslation
    translation_path: Path


@dataclass(frozen=True, slots=True)
class AutomatedTranslationOutcome:
    """One unpublished or atomically published automated translation candidate."""

    result_path: Path
    translation: TranscriptTranslation
    translation_path: Path | None = None


@dataclass(frozen=True, slots=True)
class BatchAutomatedTranslationJobOutcome:
    result_path: Path
    status: Literal["previewed", "published", "failed"]
    translation: TranscriptTranslation | None = None
    translation_path: Path | None = None
    failure_code: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchAutomatedTranslationOutcome:
    jobs: tuple[BatchAutomatedTranslationJobOutcome, ...]
    stopped_early: bool

    def count(self, status: str) -> int:
        return sum(job.status == status for job in self.jobs)


@dataclass(frozen=True, slots=True)
class BatchTranslationJobOutcome:
    """One isolated manual translation batch operation."""

    input_path: Path
    status: Literal["prepared", "previewed", "applied", "failed"]
    review_path: Path | None = None
    translation: TranscriptTranslation | None = None
    translation_path: Path | None = None
    failure_code: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchTranslationOutcome:
    """Deterministically ordered translation batch summary."""

    jobs: tuple[BatchTranslationJobOutcome, ...]
    stopped_early: bool = False

    def count(self, status: str) -> int:
        return sum(job.status == status for job in self.jobs)


@dataclass(frozen=True, slots=True)
class BatchTranslationExportJobOutcome:
    translation_path: Path
    status: Literal["exported", "failed"]
    outcome: TranslationExportOutcome | None = None
    failure_code: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchTranslationExportOutcome:
    jobs: tuple[BatchTranslationExportJobOutcome, ...]
    stopped_early: bool = False

    @property
    def exported(self) -> int:
        return sum(job.status == "exported" for job in self.jobs)

    @property
    def failed(self) -> int:
        return sum(job.status == "failed" for job in self.jobs)


@dataclass(frozen=True, slots=True)
class TranslationAuditOutcome:
    translation_path: Path
    audit: dict[str, object]
    audit_path: Path | None = None
    written: bool = False


@dataclass(frozen=True, slots=True)
class CorrectionPreviewOutcome:
    """Validated unpublished automated-correction revision."""

    base_result_path: Path
    revision: TranscriptRevision


@dataclass(frozen=True, slots=True)
class CorrectionApplyOutcome:
    """Atomically published automated-correction revision."""

    base_result_path: Path
    revision: TranscriptRevision
    revision_path: Path


@dataclass(frozen=True, slots=True)
class BatchCorrectionJobOutcome:
    """One isolated automated-correction batch result."""

    result_path: Path
    status: Literal["previewed", "applied", "failed"]
    revision: TranscriptRevision | None = None
    revision_path: Path | None = None
    failure_code: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchCorrectionOutcome:
    """Deterministically ordered automated-correction batch summary."""

    jobs: tuple[BatchCorrectionJobOutcome, ...]
    stopped_early: bool = False

    @property
    def previewed(self) -> int:
        return sum(job.status == "previewed" for job in self.jobs)

    @property
    def applied(self) -> int:
        return sum(job.status == "applied" for job in self.jobs)

    @property
    def failed(self) -> int:
        return sum(job.status == "failed" for job in self.jobs)


@dataclass(frozen=True, slots=True)
class RevisionAuditOutcome:
    """Reconstructed audit and optional published diagnostic path."""

    revision_path: Path
    base_result_path: Path
    audit: dict[str, object]
    audit_path: Path | None = None


@dataclass(frozen=True, slots=True)
class BatchRevisionJobOutcome:
    """One isolated review preview/apply outcome."""

    review_path: Path
    status: Literal["previewed", "applied", "failed"]
    revision: TranscriptRevision | None = None
    revision_path: Path | None = None
    failure_code: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchRevisionOutcome:
    """Deterministically ordered batch revision summary."""

    jobs: tuple[BatchRevisionJobOutcome, ...]
    stopped_early: bool = False

    @property
    def previewed(self) -> int:
        return sum(job.status == "previewed" for job in self.jobs)

    @property
    def applied(self) -> int:
        return sum(job.status == "applied" for job in self.jobs)

    @property
    def failed(self) -> int:
        return sum(job.status == "failed" for job in self.jobs)


def _review_base_path(review_path: Path, *, results_directory: Path | None) -> Path:
    review = load_review(review_path)
    filename = review.header.base_result_file
    candidates = (
        (results_directory / filename,)
        if results_directory is not None
        else (review_path.parent / filename, review_path.parent.parent / filename)
    )
    existing = [candidate for candidate in candidates if candidate.is_file()]
    if not existing:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Cannot locate the review's canonical base result; use --results-dir",
        )
    matching = [
        candidate
        for candidate in existing
        if sha256_file(candidate) == review.header.base_result_sha256
    ]
    if not matching:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Located canonical result does not match the review SHA-256",
        )
    return matching[0]


def preview_review_file(
    review_path: str | Path,
    *,
    results_directory: Path | None = None,
    revisions_directory: Path | None = None,
    parent_revision_path: Path | None = None,
    long_gap_warning_ms: int = 2000,
) -> RevisionPreviewOutcome:
    """Run the complete review parse, base verification, and alignment path without writes."""

    normalized_review = normalize_input_path(review_path)
    review = load_review(normalized_review)
    base_path = _review_base_path(normalized_review, results_directory=results_directory)
    base = load_canonical_result(base_path)
    parent_revision = None
    parent_path = None
    if review.header.source_revision_number is not None:
        parent_path = parent_revision_path
        if parent_path is None:
            parent_name = revision_filename(
                job_id=base.job_id,
                result_version=base.result_version,
                revision_number=review.header.source_revision_number,
            )
            parent_directory = revisions_directory or results_directory or base_path.parent
            parent_path = parent_directory / parent_name
        if not parent_path.is_file():
            raise InvalidReviewError(
                "REVISION_BASE_HASH_MISMATCH",
                "Cannot locate the review parent revision",
            )
        parent_revision = load_transcript_revision(parent_path)
    revision = build_revision(
        review,
        base,
        base_path=base_path,
        long_gap_warning_ms=long_gap_warning_ms,
        parent_revision=parent_revision,
        parent_path=parent_path,
    )
    return RevisionPreviewOutcome(normalized_review, base_path, revision)


def apply_review_file(
    review_path: str | Path,
    *,
    config: ApplicationConfig,
    results_directory: Path | None = None,
    revisions_directory: Path | None = None,
    parent_revision_path: Path | None = None,
    output_directory: Path | None = None,
) -> RevisionApplyOutcome:
    """Validate one review through preview and atomically publish its full snapshot."""

    preview = preview_review_file(
        review_path,
        results_directory=results_directory,
        revisions_directory=revisions_directory,
        parent_revision_path=parent_revision_path,
        long_gap_warning_ms=config.revision.long_gap_warning_ms,
    )
    revision, path = publish_next_revision(
        preview.revision,
        output_directory=output_directory or preview.base_result_path.parent,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
    )
    return RevisionApplyOutcome(
        preview.review_path,
        preview.base_result_path,
        revision,
        path,
    )


def preview_mock_correction(
    result_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: CorrectionProvider,
    prompt_id: str = "faithful-correction-v1",
    resume_directory: Path | None = None,
) -> CorrectionPreviewOutcome:
    """Run the complete network-free correction path without publishing a revision."""

    return preview_correction(
        result_path,
        config=config,
        provider=provider,
        prompt_id=prompt_id,
        resume_directory=resume_directory,
    )


def preview_correction(
    result_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: CorrectionProvider,
    source_revision_path: str | Path | None = None,
    consent_choice: ConsentChoice | None = None,
    prompt_id: str | None = None,
    resume_directory: Path | None = None,
    dictionary: ProjectCorrectionDictionary | None = None,
    dictionary_sha256: str | None = None,
    dictionary_project_id: str | None = None,
) -> CorrectionPreviewOutcome:
    """Authorize and build one correction revision without publishing it."""

    _authorize_correction_provider(config, provider, consent_choice)

    normalized = normalize_input_path(result_path)
    normalized_revision = (
        normalize_input_path(source_revision_path) if source_revision_path is not None else None
    )
    revision = build_correction_revision(
        normalized,
        provider,
        source_revision_path=normalized_revision,
        config=CorrectionChunkConfig(
            target_tokens=config.correction.target_tokens,
            max_tokens=config.correction.max_tokens,
            context_tokens=config.correction.context_tokens,
        ),
        prompt_id=prompt_id or config.correction.prompt_id,
        resume_directory=resume_directory,
        execution_policy=CorrectionExecutionPolicy(
            timeout_seconds=config.correction.timeout_seconds,
            max_attempts=config.correction.max_attempts,
            retry_delay_seconds=config.correction.retry_delay_seconds,
        ),
        dictionary=dictionary,
        dictionary_sha256=dictionary_sha256,
        dictionary_project_id=dictionary_project_id,
    )
    return CorrectionPreviewOutcome(normalized, revision)


def _authorize_correction_provider(
    config: ApplicationConfig,
    provider: CorrectionProvider,
    choice: ConsentChoice | None,
) -> None:
    scope = CorrectionConsentScope(
        provider_id=provider.provider_id,
        endpoint_kind=provider.endpoint_kind,
        endpoint_identity=provider.endpoint_identity,
    )
    records = load_correction_consents(config.correction.consent_store)
    decision = authorize_correction_api(
        scope,
        offline=config.general.offline,
        interactive=config.general.interactive,
        choice=choice,
        stored_records=records,
    )
    if decision.persist_scope is not None:
        persist_correction_consent(config.correction.consent_store, decision.persist_scope)


def apply_mock_correction(
    result_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: CorrectionProvider,
    output_directory: Path | None = None,
    prompt_id: str = "faithful-correction-v1",
    resume_directory: Path | None = None,
) -> CorrectionApplyOutcome:
    """Validate and atomically publish one network-free mock correction revision."""

    preview = preview_mock_correction(
        result_path,
        config=config,
        provider=provider,
        prompt_id=prompt_id,
        resume_directory=resume_directory,
    )
    revision, path = publish_next_revision(
        preview.revision,
        output_directory=output_directory or preview.base_result_path.parent,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
    )
    return CorrectionApplyOutcome(preview.base_result_path, revision, path)


def apply_correction(
    result_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: CorrectionProvider,
    source_revision_path: str | Path | None = None,
    consent_choice: ConsentChoice | None = None,
    output_directory: Path | None = None,
    prompt_id: str | None = None,
    resume_directory: Path | None = None,
    dictionary: ProjectCorrectionDictionary | None = None,
    dictionary_sha256: str | None = None,
    dictionary_project_id: str | None = None,
) -> CorrectionApplyOutcome:
    """Authorize, validate, and atomically publish one correction revision."""

    preview = preview_correction(
        result_path,
        config=config,
        provider=provider,
        source_revision_path=source_revision_path,
        consent_choice=consent_choice,
        prompt_id=prompt_id,
        resume_directory=resume_directory,
        dictionary=dictionary,
        dictionary_sha256=dictionary_sha256,
        dictionary_project_id=dictionary_project_id,
    )
    revision, path = publish_next_revision(
        preview.revision,
        output_directory=output_directory or preview.base_result_path.parent,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
    )
    return CorrectionApplyOutcome(preview.base_result_path, revision, path)


def process_mock_correction_batch(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: CorrectionProvider,
    output_directory: Path | None = None,
    recursive: bool = False,
    apply: bool = True,
    prompt_id: str = "faithful-correction-v1",
    resume_directory: Path | None = None,
) -> BatchCorrectionOutcome:
    """Preview or publish mock corrections with deterministic per-result isolation."""

    result_paths = discover_review_results(input_path, recursive=recursive)
    jobs: list[BatchCorrectionJobOutcome] = []
    stopped_early = False
    for result_path in result_paths:
        try:
            if apply:
                applied = apply_mock_correction(
                    result_path,
                    config=config,
                    provider=provider,
                    output_directory=output_directory,
                    prompt_id=prompt_id,
                    resume_directory=resume_directory,
                )
                jobs.append(
                    BatchCorrectionJobOutcome(
                        result_path=result_path,
                        status="applied",
                        revision=applied.revision,
                        revision_path=applied.revision_path,
                    )
                )
            else:
                previewed = preview_mock_correction(
                    result_path,
                    config=config,
                    provider=provider,
                    prompt_id=prompt_id,
                    resume_directory=resume_directory,
                )
                jobs.append(
                    BatchCorrectionJobOutcome(
                        result_path=result_path,
                        status="previewed",
                        revision=previewed.revision,
                    )
                )
        except Exception as error:
            jobs.append(
                BatchCorrectionJobOutcome(
                    result_path=result_path,
                    status="failed",
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
    return BatchCorrectionOutcome(tuple(jobs), stopped_early=stopped_early)


def audit_revision_file(
    revision_path: str | Path,
    *,
    config: ApplicationConfig,
    results_directory: Path | None = None,
    output_directory: Path | None = None,
    publish: bool = True,
) -> RevisionAuditOutcome:
    """Reconstruct and optionally publish a detailed base-relative revision audit."""

    normalized_revision = normalize_input_path(revision_path)
    revision = load_transcript_revision(normalized_revision)
    filename = revision.base_result.filename
    if filename is None:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Revision does not contain a canonical base filename",
        )
    candidates = (
        (results_directory / filename,)
        if results_directory is not None
        else (normalized_revision.parent / filename,)
    )
    matching = [
        candidate
        for candidate in candidates
        if candidate.is_file() and sha256_file(candidate) == revision.base_result.sha256
    ]
    if not matching:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Cannot locate the exact revision base result; use --results-dir",
        )
    base_path = matching[0]
    base = load_canonical_result(base_path)
    audit = build_revision_audit(
        base,
        revision,
        base_path=base_path,
        revision_path=normalized_revision,
    )
    audit_path = None
    if publish:
        audit_path = publish_revision_audit(
            audit,
            output_directory=output_directory or normalized_revision.parent,
            job_id=revision.job_id,
            revision_number=revision.revision_number,
            lock_timeout_seconds=config.runtime.lock_timeout_seconds,
        )
    return RevisionAuditOutcome(normalized_revision, base_path, audit, audit_path)


def process_review_batch(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    results_directory: Path | None = None,
    revisions_directory: Path | None = None,
    output_directory: Path | None = None,
    recursive: bool = False,
    apply: bool = True,
) -> BatchRevisionOutcome:
    """Preview or apply discovered reviews sequentially with per-item isolation."""

    review_paths = discover_review_files(input_path, recursive=recursive)
    jobs: list[BatchRevisionJobOutcome] = []
    stopped_early = False
    for review_path in review_paths:
        try:
            if apply:
                applied = apply_review_file(
                    review_path,
                    config=config,
                    results_directory=results_directory,
                    revisions_directory=revisions_directory,
                    output_directory=output_directory,
                )
                jobs.append(
                    BatchRevisionJobOutcome(
                        review_path=review_path,
                        status="applied",
                        revision=applied.revision,
                        revision_path=applied.revision_path,
                    )
                )
            else:
                previewed = preview_review_file(
                    review_path,
                    results_directory=results_directory,
                    revisions_directory=revisions_directory,
                    long_gap_warning_ms=config.revision.long_gap_warning_ms,
                )
                jobs.append(
                    BatchRevisionJobOutcome(
                        review_path=review_path,
                        status="previewed",
                        revision=previewed.revision,
                    )
                )
        except Exception as error:
            jobs.append(
                BatchRevisionJobOutcome(
                    review_path=review_path,
                    status="failed",
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
    return BatchRevisionOutcome(tuple(jobs), stopped_early=stopped_early)


def prepare_review_file(
    result_path: Path,
    *,
    output_directory: Path | None = None,
    source_revision_path: Path | None = None,
    anchor_target_words: int = 200,
    lock_timeout_seconds: float = 0,
) -> ReviewPreparationOutcome:
    """Prepare and non-destructively publish one review without loading models or audio."""

    review = prepare_review(
        result_path,
        source_revision_path=source_revision_path,
        anchor_target_words=anchor_target_words,
    )
    path = publish_review(
        review,
        output_directory=result_path.parent if output_directory is None else output_directory,
        lock_timeout_seconds=lock_timeout_seconds,
    )
    return ReviewPreparationOutcome(review=review, path=path)


def prepare_translation_review_file(
    result_path: str | Path,
    *,
    target_language: Language,
    config: ApplicationConfig,
    revision_path: str | Path | None = None,
    parent_translation_path: str | Path | None = None,
    output_directory: Path | None = None,
    style: TranslationStyle | None = None,
) -> TranslationReviewPreparationOutcome:
    """Prepare and non-destructively publish one exact-lineage translation review."""

    normalized_result = normalize_input_path(result_path)
    normalized_revision = normalize_input_path(revision_path) if revision_path is not None else None
    normalized_parent = (
        normalize_input_path(parent_translation_path)
        if parent_translation_path is not None
        else None
    )
    review = prepare_translation_review(
        normalized_result,
        target_language=target_language,
        revision_path=normalized_revision,
        parent_translation_path=normalized_parent,
        style=style,
    )
    path = publish_translation_review(
        review,
        output_directory=output_directory or normalized_result.parent,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
    )
    return TranslationReviewPreparationOutcome(review=review, path=path)


def preview_translation_review_file(
    review_path: str | Path,
    *,
    result_path: str | Path,
    revision_path: str | Path | None = None,
    parent_translation_path: str | Path | None = None,
) -> TranslationPreviewOutcome:
    """Validate exact source lineage and build a complete translation without writes."""

    normalized_review = normalize_input_path(review_path)
    normalized_result = normalize_input_path(result_path)
    normalized_revision = normalize_input_path(revision_path) if revision_path is not None else None
    normalized_parent = (
        normalize_input_path(parent_translation_path)
        if parent_translation_path is not None
        else None
    )
    review = load_translation_review(normalized_review)
    validate_translation_review_source(
        review,
        normalized_result,
        revision_path=normalized_revision,
        parent_translation_path=normalized_parent,
    )
    translation = build_manual_translation(review)
    return TranslationPreviewOutcome(normalized_review, normalized_result, translation)


def apply_translation_review_file(
    review_path: str | Path,
    *,
    result_path: str | Path,
    config: ApplicationConfig,
    revision_path: str | Path | None = None,
    parent_translation_path: str | Path | None = None,
    output_directory: Path | None = None,
) -> TranslationApplyOutcome:
    """Validate through preview and atomically publish one translation snapshot."""

    preview = preview_translation_review_file(
        review_path,
        result_path=result_path,
        revision_path=revision_path,
        parent_translation_path=parent_translation_path,
    )
    translation, path = publish_next_translation(
        preview.translation,
        output_directory=output_directory or preview.result_path.parent,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
    )
    return TranslationApplyOutcome(
        preview.review_path,
        preview.result_path,
        translation,
        path,
    )


def preview_automated_translation(
    result_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: AutomatedTranslationProvider,
    target_language: Language,
    revision_path: str | Path | None = None,
    style: TranslationStyle | None = None,
    resume_directory: Path | None = None,
    consent_choice: ConsentChoice | None = None,
    context_units: int = 1,
    dictionary: ProjectTranslationDictionary | None = None,
    dictionary_sha256: str | None = None,
) -> AutomatedTranslationOutcome:
    """Build a validated non-final provider candidate without publishing it."""

    normalized_result = normalize_input_path(result_path)
    normalized_revision = normalize_input_path(revision_path) if revision_path else None
    _authorize_translation_provider(config, provider, consent_choice)
    translation = build_automated_translation(
        normalized_result,
        provider,
        target_language=target_language,
        revision_path=normalized_revision,
        style=style,
        resume_directory=resume_directory,
        context_units=context_units,
        dictionary=dictionary,
        dictionary_sha256=dictionary_sha256,
    )
    return AutomatedTranslationOutcome(normalized_result, translation)


def apply_automated_translation(
    result_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: AutomatedTranslationProvider,
    target_language: Language,
    revision_path: str | Path | None = None,
    style: TranslationStyle | None = None,
    resume_directory: Path | None = None,
    output_directory: Path | None = None,
    consent_choice: ConsentChoice | None = None,
    context_units: int = 1,
    dictionary: ProjectTranslationDictionary | None = None,
    dictionary_sha256: str | None = None,
) -> AutomatedTranslationOutcome:
    """Build and atomically publish a non-final automated translation candidate."""

    preview = preview_automated_translation(
        result_path,
        config=config,
        provider=provider,
        target_language=target_language,
        revision_path=revision_path,
        style=style,
        resume_directory=resume_directory,
        consent_choice=consent_choice,
        context_units=context_units,
        dictionary=dictionary,
        dictionary_sha256=dictionary_sha256,
    )
    translation, path = publish_next_translation(
        preview.translation,
        output_directory=output_directory or preview.result_path.parent,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
    )
    return AutomatedTranslationOutcome(preview.result_path, translation, path)


def _authorize_translation_provider(
    config: ApplicationConfig,
    provider: AutomatedTranslationProvider,
    choice: ConsentChoice | None,
) -> None:
    scope = TranslationConsentScope(
        provider_id=provider.provider_id,
        endpoint_kind=provider.endpoint_kind,
        endpoint_identity=provider.endpoint_identity,
    )
    store = config.correction.consent_store.with_name("translation-consent.json")
    decision = authorize_translation_api(
        scope,
        offline=config.general.offline,
        interactive=config.general.interactive,
        choice=choice,
        stored_records=load_translation_consents(store),
    )
    if decision.persist_scope is not None:
        persist_translation_consent(store, decision.persist_scope)


def process_automated_translation_batch(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    provider: AutomatedTranslationProvider,
    target_language: Language,
    revision: str | Path | None = None,
    style: TranslationStyle | None = None,
    resume_directory: Path | None = None,
    output_directory: Path | None = None,
    recursive: bool = False,
    preview: bool = False,
    consent_choice: ConsentChoice | None = None,
    context_units: int = 1,
    dictionary: ProjectTranslationDictionary | None = None,
    dictionary_sha256: str | None = None,
) -> BatchAutomatedTranslationOutcome:
    """Build automated candidates sequentially with per-result failure isolation."""

    results = discover_review_results(input_path, recursive=recursive)
    revision_selection = normalize_input_path(revision) if revision is not None else None
    jobs: list[BatchAutomatedTranslationJobOutcome] = []
    stopped_early = False
    for result_path in results:
        try:
            selected_revision = revision_selection
            if revision_selection is not None and revision_selection.is_dir():
                selected_revision = latest_compatible_revision_path(
                    revision_selection,
                    result_path=result_path,
                    result=load_canonical_result(result_path),
                )
            state = resume_directory / result_path.stem if resume_directory is not None else None
            if preview:
                outcome = preview_automated_translation(
                    result_path,
                    config=config,
                    provider=provider,
                    target_language=target_language,
                    revision_path=selected_revision,
                    style=style,
                    resume_directory=state,
                    consent_choice=consent_choice,
                    context_units=context_units,
                    dictionary=dictionary,
                    dictionary_sha256=dictionary_sha256,
                )
                status: Literal["previewed", "published"] = "previewed"
            else:
                outcome = apply_automated_translation(
                    result_path,
                    config=config,
                    provider=provider,
                    target_language=target_language,
                    revision_path=selected_revision,
                    style=style,
                    resume_directory=state,
                    output_directory=output_directory,
                    consent_choice=consent_choice,
                    context_units=context_units,
                    dictionary=dictionary,
                    dictionary_sha256=dictionary_sha256,
                )
                status = "published"
            jobs.append(
                BatchAutomatedTranslationJobOutcome(
                    result_path=result_path,
                    status=status,
                    translation=outcome.translation,
                    translation_path=outcome.translation_path,
                )
            )
        except Exception as error:
            jobs.append(
                BatchAutomatedTranslationJobOutcome(
                    result_path=result_path,
                    status="failed",
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
    return BatchAutomatedTranslationOutcome(tuple(jobs), stopped_early)


def prepare_translation_review_batch(
    input_path: str | Path,
    *,
    target_language: Language,
    config: ApplicationConfig,
    revision: str | Path | None = None,
    output_directory: Path | None = None,
    recursive: bool = False,
    style: TranslationStyle | None = None,
) -> BatchTranslationOutcome:
    """Prepare translation reviews sequentially with per-result failure isolation."""

    results = discover_review_results(input_path, recursive=recursive)
    normalized_input = normalize_input_path(input_path)
    destination = output_directory or (
        normalized_input.parent
        if normalized_input.is_file()
        else normalized_input / "translation-reviews"
    )
    revision_selection = normalize_input_path(revision) if revision is not None else None
    jobs: list[BatchTranslationJobOutcome] = []
    stopped_early = False
    for result_path in results:
        try:
            selected_revision = revision_selection
            if revision_selection is not None and revision_selection.is_dir():
                selected_revision = latest_compatible_revision_path(
                    revision_selection,
                    result_path=result_path,
                    result=load_canonical_result(result_path),
                )
            prepared = prepare_translation_review_file(
                result_path,
                target_language=target_language,
                config=config,
                revision_path=selected_revision,
                output_directory=destination,
                style=style,
            )
            jobs.append(
                BatchTranslationJobOutcome(
                    input_path=result_path,
                    status="prepared",
                    review_path=prepared.path,
                )
            )
        except Exception as error:
            jobs.append(
                BatchTranslationJobOutcome(
                    input_path=result_path,
                    status="failed",
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
    return BatchTranslationOutcome(tuple(jobs), stopped_early=stopped_early)


def process_translation_review_batch(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    results_directory: Path,
    revisions_directory: Path | None = None,
    output_directory: Path | None = None,
    recursive: bool = False,
    apply: bool = True,
) -> BatchTranslationOutcome:
    """Preview or apply translation reviews with exact-source resolution and isolation."""

    reviews = discover_translation_reviews(input_path, recursive=recursive)
    jobs: list[BatchTranslationJobOutcome] = []
    stopped_early = False
    for review_path in reviews:
        try:
            review = load_translation_review(review_path)
            result_path, revision_path = resolve_translation_review_sources(
                review,
                results_directory=results_directory,
                revisions_directory=revisions_directory,
            )
            if apply:
                outcome = apply_translation_review_file(
                    review_path,
                    result_path=result_path,
                    revision_path=revision_path,
                    config=config,
                    output_directory=output_directory,
                )
                jobs.append(
                    BatchTranslationJobOutcome(
                        input_path=review_path,
                        status="applied",
                        review_path=review_path,
                        translation=outcome.translation,
                        translation_path=outcome.translation_path,
                    )
                )
            else:
                outcome_preview = preview_translation_review_file(
                    review_path,
                    result_path=result_path,
                    revision_path=revision_path,
                )
                jobs.append(
                    BatchTranslationJobOutcome(
                        input_path=review_path,
                        status="previewed",
                        review_path=review_path,
                        translation=outcome_preview.translation,
                    )
                )
        except Exception as error:
            jobs.append(
                BatchTranslationJobOutcome(
                    input_path=review_path,
                    status="failed",
                    review_path=review_path,
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
    return BatchTranslationOutcome(tuple(jobs), stopped_early=stopped_early)


def export_translation(
    translation_path: str | Path,
    *,
    config: ApplicationConfig,
    formats: tuple[TranslationExportFormat, ...] = (TranslationExportFormat.TXT,),
    output_directory: Path | None = None,
) -> TranslationExportOutcome:
    """Export deterministic translation text through the application boundary."""

    return export_translation_artifact(
        normalize_input_path(translation_path),
        formats=formats,
        output_directory=output_directory,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
        subtitles_config=config.subtitles,
    )


def export_translation_batch(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    formats: tuple[TranslationExportFormat, ...],
    output_directory: Path | None = None,
    recursive: bool = False,
) -> BatchTranslationExportOutcome:
    """Export discovered translations deterministically with per-file isolation."""

    translations = discover_translations(input_path, recursive=recursive)
    normalized_input = normalize_input_path(input_path)
    destination = output_directory or (
        normalized_input.parent if normalized_input.is_file() else normalized_input / "exports"
    )
    jobs: list[BatchTranslationExportJobOutcome] = []
    stopped_early = False
    for translation_path in translations:
        try:
            outcome = export_translation(
                translation_path,
                config=config,
                formats=formats,
                output_directory=destination,
            )
            jobs.append(
                BatchTranslationExportJobOutcome(
                    translation_path=translation_path,
                    status="exported",
                    outcome=outcome,
                )
            )
        except Exception as error:
            jobs.append(
                BatchTranslationExportJobOutcome(
                    translation_path=translation_path,
                    status="failed",
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
    return BatchTranslationExportOutcome(tuple(jobs), stopped_early=stopped_early)


def audit_translation_file(
    translation_path: str | Path,
    *,
    config: ApplicationConfig,
    results_directory: Path,
    revisions_directory: Path | None = None,
    output_directory: Path | None = None,
    publish: bool = True,
) -> TranslationAuditOutcome:
    """Reconstruct and optionally publish one exact-source translation audit."""

    normalized = normalize_input_path(translation_path)
    audit = build_translation_audit(
        normalized,
        results_directory=results_directory,
        revisions_directory=revisions_directory,
    )
    audit_path = None
    written = False
    if publish:
        audit_path, written = publish_translation_audit(
            audit,
            output_directory=output_directory or normalized.parent,
            lock_timeout_seconds=config.runtime.lock_timeout_seconds,
        )
    return TranslationAuditOutcome(normalized, audit, audit_path, written)


def prepare_review_batch(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    output_directory: Path | None = None,
    source_revision_path: Path | None = None,
    recursive: bool = False,
    anchor_target_words: int = 200,
) -> BatchReviewPreparationOutcome:
    """Prepare discovered canonical results sequentially with per-file failure isolation."""

    results = discover_review_results(input_path, recursive=recursive)
    normalized_input = normalize_input_path(input_path)
    if source_revision_path is not None and len(results) != 1:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "--revision requires exactly one canonical result",
        )
    destination = output_directory or (
        normalized_input.parent
        if normalized_input.is_file()
        else normalized_input / "review-ewp-transcripts"
    )
    jobs: list[BatchReviewJobOutcome] = []
    stopped_early = False
    for result_path in results:
        try:
            prepared = prepare_review_file(
                result_path,
                output_directory=destination,
                source_revision_path=source_revision_path,
                anchor_target_words=anchor_target_words,
                lock_timeout_seconds=config.runtime.lock_timeout_seconds,
            )
            jobs.append(
                BatchReviewJobOutcome(
                    result_path=result_path,
                    status="prepared",
                    review_path=prepared.path,
                )
            )
        except Exception as error:
            jobs.append(
                BatchReviewJobOutcome(
                    result_path=result_path,
                    status="failed",
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
    return BatchReviewPreparationOutcome(
        output_directory=destination,
        jobs=tuple(jobs),
        stopped_early=stopped_early,
    )


def clean_all_workdirs(
    *,
    config: ApplicationConfig,
    older_than_days: int = 0,
    dry_run: bool,
) -> CleanupOutcome:
    """Preview or remove every eligible owned workspace below the configured root."""

    workspaces = find_work_directories(
        config.runtime.work_root,
        older_than_days=older_than_days,
    )
    if not dry_run:
        for workspace in workspaces:
            cleanup_work_directory(workspace)
    return CleanupOutcome(
        paths=tuple(workspace.path for workspace in workspaces),
        dry_run=dry_run,
    )


def application_version() -> str:
    """Return the installed EWP-transcripts version without loading ML backends."""

    return __version__


def doctor(*, config: ApplicationConfig | None = None) -> DoctorResult:
    """Return lightweight, sanitized environment diagnostics."""

    return run_doctor(config=config)


def discover(
    input_path: str | Path,
    *,
    config: ApplicationConfig | None = None,
) -> DiscoveryResult:
    """Discover candidate media paths using the resolved application configuration."""

    effective_config = load_config() if config is None else config
    return discover_input(
        input_path,
        recursive=effective_config.input.recursive,
        supported_extensions=effective_config.input.supported_audio,
    )


def inspect_input(
    input_path: str | Path,
    *,
    config: ApplicationConfig | None = None,
    allow_duration_mismatch: bool = False,
    explicit_group_paths: tuple[Path, ...] | None = None,
    explicit_group_id: str | None = None,
) -> InspectionResult:
    """Discover, group, probe, and classify input without loading ML models."""

    effective_config = load_config() if config is None else config
    episodes: tuple[EpisodeCandidate, ...]
    if explicit_group_paths is not None:
        if explicit_group_id is None:
            raise UnsupportedPipelineScopeError("An explicit group requires a group ID")
        discovery = discover_explicit_group(explicit_group_paths)
        episodes = (
            group_explicit_files(
                discovery.files,
                job_id=explicit_group_id,
                separator=effective_config.grouping.speaker_suffix_separator,
            ),
        )
    else:
        if explicit_group_id is not None:
            raise UnsupportedPipelineScopeError("A group ID requires explicit group sources")
        discovery = discover(input_path, config=effective_config)
        episodes = group_discovered_files(
            discovery.files,
            separator=effective_config.grouping.speaker_suffix_separator,
            speaker_count=effective_config.diarization.speaker_count,
        )
    inspections = tuple(
        inspect_episode(
            episode,
            channel_analyzer=measure_file_channels,
            channels_config=effective_config.channels,
            quality_config=effective_config.quality,
            duration_warning_ms=effective_config.grouping.duration_warning_ms,
            duration_error_ms=effective_config.grouping.duration_error_ms,
            allow_duration_mismatch=allow_duration_mismatch,
        )
        for episode in episodes
    )
    return InspectionResult(discovery=discovery, episodes=inspections)


def dry_run(
    input_path: str | Path,
    *,
    config: ApplicationConfig | None = None,
    output_directory: Path | None = None,
    force: bool = False,
    allow_duration_mismatch: bool = False,
    explicit_group_paths: tuple[Path, ...] | None = None,
    explicit_group_id: str | None = None,
) -> DryRunResult:
    """Build a complete batch execution plan without creating outputs or workdirs."""

    effective_config = load_config() if config is None else config
    inspection = inspect_input(
        input_path,
        config=effective_config,
        allow_duration_mismatch=allow_duration_mismatch,
        explicit_group_paths=explicit_group_paths,
        explicit_group_id=explicit_group_id,
    )
    _require_unique_job_ids(inspection)
    destination = resolve_output_directory(
        inspection.discovery,
        config=effective_config.outputs,
        explicit_directory=output_directory,
    )
    existing = find_existing_results(destination)
    jobs = tuple(
        plan_job_outputs(
            episode,
            output_directory=destination,
            existing_results=existing,
            force=force,
            config=effective_config.outputs,
        )
        for episode in inspection.episodes
    )
    return DryRunResult(
        inspection=inspection,
        output_directory=destination,
        language=effective_config.general.language,
        jobs=jobs,
    )


def _require_unique_job_ids(inspection: InspectionResult) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for episode in inspection.episodes:
        if episode.job_id in seen:
            duplicates.add(episode.job_id)
        seen.add(episode.job_id)
    if duplicates:
        names = ", ".join(sorted(duplicates))
        raise AmbiguousJobIdError(
            "Separate discovered episodes share a job ID: "
            f"{names}. Select one source directly or rename/relocate inputs explicitly."
        )


def transcribe_one(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    output_directory: Path | None = None,
    force: bool = False,
    allow_duration_mismatch: bool = False,
    run_id: UUID | None = None,
    asr_factory: AsrFactory | None = None,
    alignment_factory: AlignmentFactory | None = None,
    diarization_factory: DiarizationFactory | None = None,
    speaker_label: str | None = None,
    speaker_map: dict[str, str] | None = None,
    explicit_group_paths: tuple[Path, ...] | None = None,
    explicit_group_id: str | None = None,
) -> TranscriptionOutcome:
    """Run one inspected episode through safe publication."""
    started = time.perf_counter()
    inspected = inspect_input(
        input_path,
        config=config,
        allow_duration_mismatch=allow_duration_mismatch,
        explicit_group_paths=explicit_group_paths,
        explicit_group_id=explicit_group_id,
    )
    inspected = apply_explicit_speaker_labels(
        inspected,
        speaker_label=speaker_label,
        speaker_map=speaker_map,
    )
    if len(inspected.episodes) != 1:
        raise UnsupportedPipelineScopeError("Single-file transcribe requires exactly one episode")
    episode = inspected.episodes[0]
    destination = resolve_output_directory(
        inspected.discovery,
        config=config.outputs,
        explicit_directory=output_directory,
    )
    outcome = _transcribe_episode(
        episode,
        destination=destination,
        config=config,
        force=force,
        run_id=run_id or uuid4(),
        asr_factory=asr_factory or _whisperx_asr,
        alignment_factory=alignment_factory or _whisperx_alignment,
        diarization_factory=diarization_factory or _pyannote_diarization,
    )
    return replace(outcome, elapsed_ms=max(0, round((time.perf_counter() - started) * 1000)))


def transcribe_batch(
    input_path: str | Path,
    *,
    config: ApplicationConfig,
    output_directory: Path | None = None,
    force: bool = False,
    allow_duration_mismatch: bool = False,
    asr_factory: AsrFactory | None = None,
    alignment_factory: AlignmentFactory | None = None,
    diarization_factory: DiarizationFactory | None = None,
    speaker_map: dict[str, str] | None = None,
) -> BatchTranscriptionOutcome:
    """Process inspected episodes sequentially and isolate per-job failures."""

    inspected = inspect_input(
        input_path,
        config=config,
        allow_duration_mismatch=allow_duration_mismatch,
    )
    _require_unique_job_ids(inspected)
    inspected = apply_explicit_speaker_labels(inspected, speaker_map=speaker_map)
    destination = resolve_output_directory(
        inspected.discovery,
        config=config.outputs,
        explicit_directory=output_directory,
    )
    jobs: list[BatchJobOutcome] = []
    stopped_early = False
    for episode in inspected.episodes:
        job_run_id = uuid4()
        started = time.perf_counter()
        try:
            outcome = _transcribe_episode(
                episode,
                destination=destination,
                config=config,
                force=force,
                run_id=job_run_id,
                asr_factory=asr_factory or _whisperx_asr,
                alignment_factory=alignment_factory or _whisperx_alignment,
                diarization_factory=diarization_factory or _pyannote_diarization,
            )
            jobs.append(
                BatchJobOutcome(
                    job_id=outcome.job_id,
                    status=("skipped" if outcome.decision is PlanDecision.SKIP else "completed"),
                    result_path=outcome.result_path,
                    run_id=outcome.run_id,
                    elapsed_ms=max(0, round((time.perf_counter() - started) * 1000)),
                )
            )
        except Exception as error:
            jobs.append(
                BatchJobOutcome(
                    job_id=episode.job_id,
                    status="failed",
                    failure_code=_failure_code(error),
                    failure_message=_failure_message(error),
                    run_id=job_run_id,
                    elapsed_ms=max(0, round((time.perf_counter() - started) * 1000)),
                )
            )
            if not config.runtime.continue_batch_after_error:
                stopped_early = True
                break
        except KeyboardInterrupt:
            jobs.append(
                BatchJobOutcome(
                    job_id=episode.job_id,
                    status="cancelled",
                    failure_code="USER_CANCELLED",
                    failure_message="Transcription cancelled by user",
                    run_id=job_run_id,
                    elapsed_ms=max(0, round((time.perf_counter() - started) * 1000)),
                )
            )
            stopped_early = True
            break
    return BatchTranscriptionOutcome(
        output_directory=destination,
        jobs=tuple(jobs),
        stopped_early=stopped_early,
    )


def _transcribe_episode(
    episode: EpisodeInspection,
    *,
    destination: Path,
    config: ApplicationConfig,
    force: bool,
    run_id: UUID,
    asr_factory: AsrFactory,
    alignment_factory: AlignmentFactory,
    diarization_factory: DiarizationFactory,
) -> TranscriptionOutcome:
    reservation = reserve_job(
        episode,
        output_directory=destination,
        run_id=run_id,
        force=force,
        config=config.outputs,
        lock_timeout_seconds=config.runtime.lock_timeout_seconds,
    )
    if reservation.plan.decision is PlanDecision.SKIP:
        existing = reservation.plan.existing_result
        assert existing is not None
        formats = _configured_export_formats(config)
        exports = (
            export_result(
                existing.path,
                formats=formats,
                subtitles_config=config.subtitles,
            )
            if formats
            else None
        )
        return TranscriptionOutcome(
            decision=PlanDecision.SKIP,
            job_id=episode.job_id,
            result_path=existing.path,
            exports=exports,
            run_id=run_id,
        )

    return _process_reservation(
        episode,
        reservation,
        config=config,
        asr_factory=asr_factory,
        alignment_factory=alignment_factory,
        diarization_factory=diarization_factory,
    )


def _process_reservation(
    episode: EpisodeInspection,
    reservation: JobReservation,
    *,
    config: ApplicationConfig,
    asr_factory: AsrFactory,
    alignment_factory: AlignmentFactory,
    diarization_factory: DiarizationFactory,
) -> TranscriptionOutcome:
    state = reservation.state
    assert state is not None
    workspace = None
    published = False
    succeeded = False
    try:
        workspace = allocate_work_directory(
            config.runtime.work_root,
            run_id=state.run_id,
            job_id=episode.job_id,
        )
        environment = _runtime_environment(config)
        source_speakers = len(episode.sources) > 1 or (
            len(episode.sources) == 1
            and episode.sources[0].channel_classification.processing_mode
            is ChannelMode.SPLIT_SPEAKERS
        )
        if source_speakers:
            result = run_source_speaker_pipeline(
                episode,
                reservation,
                workspace,
                config=config,
                environment=environment,
                asr_engine_factory=lambda: asr_factory(config),
                alignment_engine_factory=lambda: alignment_factory(config),
            )
        elif config.diarization.speaker_count == 1:
            result = run_single_speaker_pipeline(
                episode,
                reservation,
                workspace,
                config=config,
                environment=environment,
                asr_engine=asr_factory(config),
                alignment_engine=alignment_factory(config),
            )
        else:
            result = run_diarization_pipeline(
                episode,
                reservation,
                workspace,
                config=config,
                environment=environment,
                asr_engine=asr_factory(config),
                alignment_engine=alignment_factory(config),
                diarization_engine=diarization_factory(config),
            )
        result = _record_peak_vram(result)
        result_path = finalize_job_result(
            reservation,
            result,
            lock_timeout_seconds=config.runtime.lock_timeout_seconds,
        )
        published = True
        formats = _configured_export_formats(config)
        exports = (
            export_result(
                result_path,
                formats=formats,
                subtitles_config=config.subtitles,
            )
            if formats
            else None
        )
        outcome = TranscriptionOutcome(
            decision=PlanDecision.PROCESS,
            job_id=episode.job_id,
            result_path=result_path,
            exports=exports,
            run_id=state.run_id,
        )
        succeeded = True
        return outcome
    except KeyboardInterrupt:
        if not published:
            transition_job_state(
                reservation,
                status=JobStateStatus.CANCELLED,
                failure_code="USER_CANCELLED",
                failure_message="Transcription cancelled by user",
                lock_timeout_seconds=config.runtime.lock_timeout_seconds,
            )
        raise
    except Exception as error:
        if not published:
            transition_job_state(
                reservation,
                status=JobStateStatus.FAILED,
                failure_code=_failure_code(error),
                failure_message=_failure_message(error),
                lock_timeout_seconds=config.runtime.lock_timeout_seconds,
            )
        raise
    finally:
        retain = (
            config.runtime.keep_temp_on_success if succeeded else config.runtime.keep_temp_on_error
        )
        if workspace is not None and not retain:
            cleanup_work_directory(workspace)


def _configured_export_formats(config: ApplicationConfig) -> tuple[ExportFormat, ...]:
    return tuple(
        format_
        for enabled, format_ in (
            (config.outputs.generate_txt, ExportFormat.TXT),
            (config.outputs.generate_srt, ExportFormat.SRT),
            (config.outputs.generate_vtt, ExportFormat.VTT),
            (config.outputs.generate_segments_json, ExportFormat.SEGMENTS),
        )
        if enabled
    )


def _whisperx_asr(config: ApplicationConfig) -> AsrEngine:
    return WhisperXAsrEngine(
        config.models.asr_snapshot_path,
        revision=config.models.asr_revision,
        device=config.models.device,
        compute_type=config.models.compute_type,
    )


def _whisperx_alignment(config: ApplicationConfig) -> AlignmentEngine:
    return WhisperXAlignmentEngine(
        config.models.alignment_snapshot_path,
        revision=config.models.alignment_revision,
        english_snapshot=config.models.english_alignment_snapshot_path,
        english_revision=config.models.english_alignment_revision,
        device=config.models.device,
    )


def _pyannote_diarization(config: ApplicationConfig) -> DiarizationEngine:
    return PyannoteDiarizationEngine(
        config.diarization.local_model_path,
        revision=config.diarization.model_revision,
        device=config.models.device,
    )


def _runtime_environment(config: ApplicationConfig) -> CanonicalEnvironment:
    return CanonicalEnvironment(
        os=platform.platform(),
        wsl_distribution=None,
        python=platform.python_version(),
        whisperx=_distribution_version("whisperx"),
        pytorch=_distribution_version("torch"),
        device=config.models.device,
        compute_type=config.models.compute_type,
        batch_size=config.models.batch_size,
    )


def _record_peak_vram(result: CanonicalResult) -> CanonicalResult:
    """Record the process CUDA allocation peak when the ML runtime exposed it."""

    torch = sys.modules.get("torch")
    cuda = getattr(torch, "cuda", None)
    if cuda is None:
        return result
    try:
        peak_vram_bytes = int(cuda.max_memory_allocated())
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return result
    if peak_vram_bytes < 0:
        return result
    environment = result.processing.environment.model_copy(
        update={"peak_vram_bytes": peak_vram_bytes}
    )
    processing = result.processing.model_copy(update={"environment": environment})
    return result.model_copy(update={"processing": processing})


def _distribution_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _failure_code(error: Exception) -> str:
    if isinstance(error, ApplicationError):
        return error.code
    return "TRANSCRIPTION_FAILED"


def _failure_message(error: Exception) -> str:
    if isinstance(error, ApplicationError) and str(error):
        return str(error)[:1000]
    return "Unexpected transcription failure"
