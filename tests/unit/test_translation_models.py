"""Tests for strict immutable translation artifacts."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ewp_transcripts.domain.translation import (
    TranscriptTranslation,
    TranslationCanonicalSource,
    TranslationDirection,
    TranslationProvenance,
    TranslationSource,
    TranslationStatistics,
    TranslationStyle,
    TranslationUnit,
)


def _translation() -> TranscriptTranslation:
    return TranscriptTranslation(
        schema_version="1.0",
        application_version="0.3.0",
        translation_id=uuid4(),
        translation_number=1,
        job_id="episode",
        created_at=datetime.now(UTC),
        direction=TranslationDirection(source_language="pl", target_language="en"),
        style=TranslationStyle(),
        source=TranslationSource(
            canonical_result=TranslationCanonicalSource(
                job_id="episode",
                result_version=1,
                schema_version="1.0",
                sha256="a" * 64,
                filename="episode_results.json",
            ),
            verification="raw",
        ),
        provenance=TranslationProvenance(method="manual", interface="cli"),
        units=(
            TranslationUnit(
                unit_id="tu_000001",
                speaker_id="speaker_001",
                source_token_ids=("word_000001",),
                source_text_sha256="b" * 64,
                start_ms=0,
                end_ms=500,
                target_text="Hello there.",
            ),
        ),
        statistics=TranslationStatistics(
            unit_count=1, source_tokens=1, target_tokens=2, warning_count=0
        ),
    )


def test_translation_snapshot_is_strict_and_frozen() -> None:
    translation = _translation()

    assert translation.direction.target_language == "en"
    assert translation.style.register_mode == "preserve"
    assert translation.style.model_dump()["register"] == "preserve"
    with pytest.raises(ValidationError):
        translation.translation_number = 2  # type: ignore[misc]


def test_translation_rejects_same_language_direction() -> None:
    with pytest.raises(ValidationError, match="must differ"):
        TranslationDirection(source_language="pl", target_language="pl")


def test_translation_rejects_duplicate_source_ownership() -> None:
    translation = _translation()
    duplicate = translation.units[0].model_copy(
        update={"unit_id": "tu_000002", "target_text": "Again."}
    )

    with pytest.raises(ValidationError, match="owned exactly once"):
        TranscriptTranslation.model_validate(
            translation.model_dump() | {"units": (*translation.units, duplicate)}
        )


def test_raw_source_cannot_claim_a_revision() -> None:
    data = _translation().source.model_dump()
    data["transcript_revision"] = {
        "revision_id": uuid4(),
        "revision_number": 1,
        "sha256": "c" * 64,
        "filename": "episode_revision_001.json",
        "method": "manual",
    }

    with pytest.raises(ValidationError, match="raw translation source"):
        TranslationSource.model_validate(data)


def test_schema_11_records_intentionally_empty_units() -> None:
    translation = _translation()
    data = translation.model_dump()
    data["schema_version"] = "1.1"
    data["units"] = (
        translation.units[0].model_copy(
            update={"target_text": "", "target_status": "intentionally_empty"}
        ),
    )
    data["statistics"] = translation.statistics.model_copy(
        update={"target_tokens": 0, "intentionally_empty_units": 1}
    )

    parsed = TranscriptTranslation.model_validate(data)

    assert parsed.units[0].target_status == "intentionally_empty"
    assert parsed.statistics.intentionally_empty_units == 1


def test_schema_10_rejects_intentionally_empty_units() -> None:
    translation = _translation()
    data = translation.model_dump()
    data["units"] = (
        translation.units[0].model_copy(
            update={"target_text": "", "target_status": "intentionally_empty"}
        ),
    )
    data["statistics"] = translation.statistics.model_copy(
        update={"target_tokens": 0, "intentionally_empty_units": 1}
    )

    with pytest.raises(ValidationError, match="schema 1.0"):
        TranscriptTranslation.model_validate(data)
