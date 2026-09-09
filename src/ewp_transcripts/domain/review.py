"""Typed ``EWP-REVIEW 1`` models and canonical-base validation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ewp_transcripts.domain.canonical import CanonicalResult
from ewp_transcripts.domain.errors import InvalidReviewError


class ReviewModel(BaseModel):
    """Frozen review-format object that rejects undocumented fields."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class ReviewExtensionHeader(ReviewModel):
    key: str = Field(pattern=r"^x_[a-z0-9_]+$")
    value: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def require_printable_single_line_value(cls, value: str) -> str:
        if not value.isprintable() or "\n" in value or "\r" in value:
            raise ValueError("review extension values must be printable single lines")
        return value


class ReviewHeader(ReviewModel):
    job_id: str = Field(min_length=1)
    base_result_file: str = Field(min_length=1)
    base_result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_result_schema_version: str = Field(min_length=1)
    base_result_version: int = Field(ge=1)
    language: Literal["pl", "en"]
    generated_at: datetime
    application_version: str = Field(min_length=1)
    source_revision_id: UUID | None = None
    source_revision_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_revision_number: int | None = Field(default=None, ge=1)
    speaker_labels: dict[str, str] = Field(default_factory=dict)
    extensions: tuple[ReviewExtensionHeader, ...] = ()

    @field_validator(
        "job_id",
        "base_result_file",
        "base_result_schema_version",
        "application_version",
    )
    @classmethod
    def require_printable_single_line_value(cls, value: str) -> str:
        if not value.isprintable() or "\n" in value or "\r" in value:
            raise ValueError("review header values must be printable single lines")
        return value

    @field_validator("speaker_labels")
    @classmethod
    def require_revision_scoped_speaker_labels(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for speaker_id, label in value.items():
            if re.fullmatch(r"speaker_[0-9]{3,}", speaker_id) is None:
                raise ValueError("speaker label keys must be speaker identifiers")
            cleaned = " ".join(label.split())
            if not cleaned or not cleaned.isprintable():
                raise ValueError("speaker labels must be printable and non-empty")
            normalized[speaker_id] = cleaned
        return dict(sorted(normalized.items()))

    @model_validator(mode="after")
    def validate_optional_revision_identity(self) -> Self:
        source_fields = (
            self.source_revision_id,
            self.source_revision_sha256,
            self.source_revision_number,
        )
        if any(value is not None for value in source_fields) and not all(
            value is not None for value in source_fields
        ):
            raise ValueError("source revision identity must be complete")
        extension_keys = [extension.key for extension in self.extensions]
        if len(extension_keys) != len(set(extension_keys)):
            raise ValueError("review extension header keys must be unique")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must contain an explicit timezone")
        return self


class ReviewSpeakerBlock(ReviewModel):
    speaker_id: str = Field(pattern=r"^speaker_[0-9]{3,}$")
    text: str

    @field_validator("text")
    @classmethod
    def require_normalized_single_line_text(cls, value: str) -> str:
        if "\n" in value or "\r" in value or "\x00" in value:
            raise ValueError("parsed review block text must be normalized to one line")
        return value


class ReviewAnchor(ReviewModel):
    first_word_id: str = Field(pattern=r"^word_[0-9]{6,}$")
    last_word_id: str = Field(pattern=r"^word_[0-9]{6,}$")
    speaker_blocks: tuple[ReviewSpeakerBlock, ...] = Field(min_length=1)


class TranscriptReview(ReviewModel):
    format_version: Literal[1]
    header: ReviewHeader
    anchors: tuple[ReviewAnchor, ...] = Field(min_length=1)


def validate_review_base(
    review: TranscriptReview,
    base: CanonicalResult,
    *,
    base_sha256: str,
) -> None:
    """Validate machine-owned review metadata and anchors against one canonical result."""

    header = review.header
    if base.status != "completed":
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Transcript review requires a completed canonical result",
        )
    if header.base_result_sha256 != base_sha256:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Review base-result SHA-256 does not match",
        )
    if header.job_id != base.job_id:
        raise InvalidReviewError("REVISION_BASE_HASH_MISMATCH", "Review job ID does not match")
    if header.base_result_version != base.result_version:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Review result version does not match",
        )
    if header.base_result_schema_version != base.schema_version:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Review result schema version does not match",
        )
    if header.language != base.transcript.language:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Review language does not match the canonical transcript",
        )

    canonical_word_ids = tuple(
        word.word_id for segment in base.transcript.segments for word in segment.words
    )
    if len(canonical_word_ids) != len(set(canonical_word_ids)):
        raise InvalidReviewError(
            "REVISION_SOURCE_WORD_MISSING",
            "Canonical result contains duplicate word IDs",
        )
    positions = {word_id: position for position, word_id in enumerate(canonical_word_ids)}
    covered: list[str] = []
    for anchor in review.anchors:
        if anchor.first_word_id not in positions or anchor.last_word_id not in positions:
            raise InvalidReviewError(
                "REVISION_SOURCE_WORD_MISSING",
                "Review anchor references an unknown canonical word",
            )
        first = positions[anchor.first_word_id]
        last = positions[anchor.last_word_id]
        if first > last:
            raise InvalidReviewError(
                "REVISION_ANCHOR_INVALID",
                "Review anchor endpoints are out of canonical order",
            )
        covered.extend(canonical_word_ids[first : last + 1])
    if tuple(covered) != canonical_word_ids:
        raise InvalidReviewError(
            "REVISION_ANCHOR_INVALID",
            "Review anchors must cover canonical words exactly once and in order",
        )

    speaker_ids = {speaker.speaker_id for speaker in base.speakers}
    unknown_labels = set(header.speaker_labels) - speaker_ids
    if unknown_labels:
        raise InvalidReviewError(
            "REVISION_SPEAKER_INVALID",
            f"Review references unknown speaker label: {sorted(unknown_labels)[0]}",
        )
    for anchor in review.anchors:
        for block in anchor.speaker_blocks:
            if block.speaker_id not in speaker_ids:
                raise InvalidReviewError(
                    "REVISION_SPEAKER_INVALID",
                    f"Review references unknown speaker: {block.speaker_id}",
                )
