"""Validate translation reviews into complete immutable snapshots."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ewp_transcripts import __version__
from ewp_transcripts.domain.errors import InvalidTranslationError
from ewp_transcripts.domain.translation import (
    TranscriptTranslation,
    TranslationDirection,
    TranslationProvenance,
    TranslationStatistics,
    TranslationUnit,
)
from ewp_transcripts.domain.translation_review import TranslationReview


def build_manual_translation(
    review: TranslationReview,
    *,
    created_at: datetime | None = None,
    allow_empty_units: bool = False,
) -> TranscriptTranslation:
    """Build an unpublished manual translation after complete target validation."""

    missing = [unit.unit_id for unit in review.units if not unit.target_text.strip()]
    if missing and not allow_empty_units:
        raise InvalidTranslationError(
            f"Translation review contains untranslated unit: {missing[0]}"
        )
    units = tuple(
        TranslationUnit(
            unit_id=unit.unit_id,
            speaker_id=unit.speaker_id,
            source_token_ids=unit.source_token_ids,
            source_text_sha256=unit.source_text_sha256,
            start_ms=unit.start_ms,
            end_ms=unit.end_ms,
            target_text=" ".join(unit.target_text.split()),
            target_status=("intentionally_empty" if not unit.target_text.strip() else "translated"),
        )
        for unit in review.units
    )
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
        parent_translation=review.header.parent_translation,
        dictionary=review.header.dictionary,
        provenance=TranslationProvenance(method="manual", interface="cli"),
        units=units,
        statistics=TranslationStatistics(
            unit_count=len(units),
            source_tokens=sum(len(unit.source_token_ids) for unit in units),
            target_tokens=sum(len(unit.target_text.split()) for unit in units),
            intentionally_empty_units=len(missing),
            warning_count=0,
        ),
    )
