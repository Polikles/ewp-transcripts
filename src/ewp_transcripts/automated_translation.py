"""Automated translation planning, validation, and candidate construction."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from ewp_transcripts import __version__
from ewp_transcripts.domain.automated_translation import (
    AutomatedTranslationProvider,
    AutomatedTranslationRequest,
    AutomatedTranslationResponse,
    AutomatedTranslationUsage,
    TranslationContextUnit,
    TranslationDictionaryTerm,
)
from ewp_transcripts.domain.errors import InvalidTranslationResponseError
from ewp_transcripts.domain.translation import (
    Language,
    TranscriptTranslation,
    TranslationDictionaryProvenance,
    TranslationDirection,
    TranslationLlmProvenance,
    TranslationProvenance,
    TranslationStatistics,
    TranslationStyle,
    TranslationUnit,
    TranslationWarning,
)
from ewp_transcripts.domain.translation_review import TranslationReview, TranslationReviewUnit
from ewp_transcripts.translation_dictionary import ProjectTranslationDictionary
from ewp_transcripts.translation_review_service import prepare_translation_review

DEFAULT_TRANSLATION_PROMPT_ID = "faithful-translation-v1"
DICTIONARY_SELECTION_CONTRACT = "owned-source-unicode-phrase-v2"


def build_automated_translation_request(
    review: TranslationReview,
    unit_index: int,
    *,
    provider: AutomatedTranslationProvider,
    prompt_id: str = DEFAULT_TRANSLATION_PROMPT_ID,
    context_units: int = 1,
    dictionary: ProjectTranslationDictionary | None = None,
    dictionary_sha256: str | None = None,
) -> AutomatedTranslationRequest:
    """Build one single-owner request with bounded read-only context."""

    if context_units < 0:
        raise ValueError("translation context_units must not be negative")
    if not 0 <= unit_index < len(review.units):
        raise ValueError("translation unit index is outside the review")

    def context(unit: TranslationReviewUnit) -> TranslationContextUnit:
        return TranslationContextUnit(
            unit_id=unit.unit_id,
            speaker_id=unit.speaker_id,
            source_text=unit.source_text,
        )

    prompt_sha256 = provider.prompt_sha256(prompt_id)
    unit = review.units[unit_index]
    applicable_entries = tuple(
        entry
        for entry in (dictionary.entries if dictionary is not None else ())
        if _dictionary_source_occurs(entry.source, unit.source_text)
    )
    context_start = max(0, unit_index - context_units)
    context_end = min(len(review.units), unit_index + context_units + 1)
    identity = "\0".join(
        (
            provider.provider_id,
            provider.model_id,
            prompt_id,
            prompt_sha256,
            review.header.source_language,
            review.header.target_language,
            review.header.style.register_mode,
            review.header.style.discourse,
            str(context_units),
            dictionary.dictionary_id if dictionary is not None else "",
            dictionary_sha256 or "",
            DICTIONARY_SELECTION_CONTRACT,
            unit.unit_id,
            unit.source_text_sha256,
            *(
                review.units[index].source_text_sha256
                for index in range(context_start, context_end)
            ),
        )
    )
    return AutomatedTranslationRequest(
        operation_id=hashlib.sha256(identity.encode()).hexdigest(),
        prompt_id=prompt_id,
        prompt_sha256=prompt_sha256,
        source_language=review.header.source_language,
        target_language=review.header.target_language,
        style=review.header.style,
        dictionary_id=dictionary.dictionary_id if dictionary is not None else None,
        dictionary_sha256=dictionary_sha256,
        dictionary_terms=tuple(
            TranslationDictionaryTerm(source=entry.source, target=entry.target)
            for entry in applicable_entries
        ),
        preceding_context=tuple(
            context(review.units[index]) for index in range(context_start, unit_index)
        ),
        unit=context(unit),
        following_context=tuple(
            context(review.units[index]) for index in range(unit_index + 1, context_end)
        ),
    )


def _dictionary_source_occurs(source: str, owned_text: str) -> bool:
    """Match one source term as a Unicode word/phrase, never as an inner substring."""

    folded_source = source.casefold()
    folded_text = owned_text.casefold()
    return re.search(rf"(?<!\w){re.escape(folded_source)}(?!\w)", folded_text) is not None


def validate_automated_translation_response(
    request: AutomatedTranslationRequest,
    response: AutomatedTranslationResponse,
) -> str:
    """Bind provider output to the exact owned unit and normalize its target text."""

    if response.operation_id != request.operation_id:
        raise InvalidTranslationResponseError("Translation response operation ID does not match")
    if response.unit_id != request.unit.unit_id:
        raise InvalidTranslationResponseError("Translation response unit ID does not match")
    normalized = " ".join(response.target_text.split())
    if not normalized:
        raise InvalidTranslationResponseError("Translation response target text is empty")
    return normalized


class DeterministicMockTranslationProvider:
    """In-process provider for tests without network or model access."""

    def __init__(self, translations: dict[str, str] | None = None) -> None:
        self._translations = translations or {}

    @property
    def provider_id(self) -> str:
        return "ewp-mock-translation"

    @property
    def model_id(self) -> str:
        return "deterministic-unit-map-v1"

    @property
    def endpoint_kind(self) -> Literal["mock"]:
        return "mock"

    @property
    def endpoint_identity(self) -> str:
        return "in-process"

    @property
    def provenance_parameters(self) -> dict[str, str | int | float | bool | None]:
        return {"request_contract": "single-owner-unit-v1"}

    def prompt_sha256(self, prompt_id: str) -> str:
        return hashlib.sha256(f"ewp-translation-mock-v1\0{prompt_id}".encode()).hexdigest()

    def translate(
        self,
        request: AutomatedTranslationRequest,
        *,
        timeout_seconds: float | None = None,
    ) -> AutomatedTranslationResponse:
        del timeout_seconds
        target = self._translations.get(
            request.unit.unit_id,
            f"[{request.target_language}] {request.unit.source_text}",
        )
        context = (*request.preceding_context, request.unit, *request.following_context)
        return AutomatedTranslationResponse(
            operation_id=request.operation_id,
            unit_id=request.unit.unit_id,
            target_text=target,
            usage=AutomatedTranslationUsage(
                input_tokens=sum(len(unit.source_text.split()) for unit in context),
                output_tokens=len(target.split()),
                cost_usd_micros=0,
            ),
        )


def build_automated_translation(
    result_path: Path,
    provider: AutomatedTranslationProvider,
    *,
    target_language: Language,
    revision_path: Path | None = None,
    style: TranslationStyle | None = None,
    prompt_id: str = DEFAULT_TRANSLATION_PROMPT_ID,
    context_units: int = 1,
    resume_directory: Path | None = None,
    execution_policy: object | None = None,
    created_at: datetime | None = None,
    dictionary: ProjectTranslationDictionary | None = None,
    dictionary_sha256: str | None = None,
) -> TranscriptTranslation:
    """Build one unpublished non-final provider candidate from exact source units."""

    from ewp_transcripts.translation_execution import TranslationExecutionPolicy

    if execution_policy is not None and not isinstance(
        execution_policy, TranslationExecutionPolicy
    ):
        raise TypeError("execution_policy must be TranslationExecutionPolicy")
    review = prepare_translation_review(
        result_path,
        target_language=target_language,
        revision_path=revision_path,
        style=style,
    )
    if dictionary is not None:
        if dictionary_sha256 is None:
            raise ValueError("translation dictionary SHA-256 is required")
        if not dictionary.applies_to(review.header.job_id):
            raise ValueError("translation dictionary is not approved for this job")
        if (dictionary.source_language, dictionary.target_language) != (
            review.header.source_language,
            review.header.target_language,
        ):
            raise ValueError("translation dictionary direction does not match the job")
    translated_units: list[TranslationUnit] = []
    translation_warnings: list[TranslationWarning] = []
    for index, source_unit in enumerate(review.units):
        request = build_automated_translation_request(
            review,
            index,
            provider=provider,
            prompt_id=prompt_id,
            context_units=context_units,
            dictionary=dictionary,
            dictionary_sha256=dictionary_sha256,
        )
        if resume_directory is None:
            from ewp_transcripts.translation_execution import execute_translation_call

            response = execute_translation_call(provider, request, policy=execution_policy).response
        else:
            from ewp_transcripts.translation_state import call_translation_resumable

            response = call_translation_resumable(
                provider,
                request,
                state_directory=resume_directory,
                execution_policy=execution_policy,
            ).response
        target_text = validate_automated_translation_response(request, response)
        translation_warnings.extend(
            TranslationWarning(
                code=code,
                severity="warning",
                message=(
                    f"Provider compatibility output was discarded for {source_unit.unit_id}; "
                    "manually review the translated unit."
                ),
            )
            for code in response.warning_codes
        )
        translated_units.append(
            TranslationUnit(
                unit_id=source_unit.unit_id,
                speaker_id=source_unit.speaker_id,
                source_token_ids=source_unit.source_token_ids,
                source_text_sha256=source_unit.source_text_sha256,
                start_ms=source_unit.start_ms,
                end_ms=source_unit.end_ms,
                target_text=target_text,
                target_status="translated",
            )
        )
    units = tuple(translated_units)
    return TranscriptTranslation(
        schema_version="1.1",
        application_version=__version__,
        translation_id=uuid4(),
        translation_number=1,
        job_id=review.header.job_id,
        created_at=created_at or datetime.now(UTC),
        direction=TranslationDirection(
            source_language=review.header.source_language,
            target_language=review.header.target_language,
        ),
        style=review.header.style,
        source=review.header.source,
        dictionary=(
            TranslationDictionaryProvenance(
                dictionary_version=dictionary.dictionary_version,
                dictionary_id=dictionary.dictionary_id,
                project_id=dictionary.project_id,
                sha256=dictionary_sha256,
            )
            if dictionary is not None and dictionary_sha256 is not None
            else None
        ),
        provenance=TranslationProvenance(
            method="llm",
            interface="api",
            llm=TranslationLlmProvenance(
                provider=provider.provider_id,
                model=provider.model_id,
                endpoint_kind=provider.endpoint_kind,
                prompt_id=prompt_id,
                prompt_sha256=provider.prompt_sha256(prompt_id),
                parameters={
                    **provider.provenance_parameters,
                    "dictionary_id": dictionary.dictionary_id if dictionary else None,
                    "dictionary_sha256": dictionary_sha256,
                    "dictionary_project_id": dictionary.project_id if dictionary else None,
                    "dictionary_selection_contract": DICTIONARY_SELECTION_CONTRACT,
                },
            ),
        ),
        units=units,
        statistics=TranslationStatistics(
            unit_count=len(units),
            source_tokens=sum(len(unit.source_token_ids) for unit in units),
            target_tokens=sum(len(unit.target_text.split()) for unit in units),
            intentionally_empty_units=0,
            warning_count=len(translation_warnings),
        ),
        warnings=tuple(translation_warnings),
    )
