"""Strict immutable sentence-mapped translation artifacts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ewp_transcripts.domain.errors import InvalidTranslationError

Language = Literal["pl", "en"]


class TranslationModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class TranslationDirection(TranslationModel):
    source_language: Language
    target_language: Language

    @model_validator(mode="after")
    def require_distinct_languages(self) -> Self:
        if self.source_language == self.target_language:
            raise ValueError("translation source and target languages must differ")
        return self


class TranslationStyle(TranslationModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    register_mode: Literal["preserve", "formal", "informal"] = Field(
        default="preserve", alias="register"
    )
    discourse: Literal["preserve", "academic", "general"] = "preserve"


class TranslationCanonicalSource(TranslationModel):
    job_id: str = Field(min_length=1)
    result_version: int = Field(ge=1)
    schema_version: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    filename: str = Field(min_length=1)


class TranslationRevisionSource(TranslationModel):
    revision_id: UUID
    revision_number: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    filename: str = Field(min_length=1)
    method: Literal["manual", "llm"]


class TranslationSource(TranslationModel):
    canonical_result: TranslationCanonicalSource
    transcript_revision: TranslationRevisionSource | None = None
    verification: Literal["raw", "automated_candidate", "manually_verified"]

    @model_validator(mode="after")
    def validate_verification(self) -> Self:
        revision = self.transcript_revision
        if self.verification == "raw" and revision is not None:
            raise ValueError("raw translation source cannot contain a transcript revision")
        if self.verification == "automated_candidate" and (
            revision is None or revision.method != "llm"
        ):
            raise ValueError("automated translation source requires an LLM revision")
        if self.verification == "manually_verified" and (
            revision is None or revision.method != "manual"
        ):
            raise ValueError("verified translation source requires a manual revision")
        return self


class TranslationParent(TranslationModel):
    translation_id: UUID
    translation_number: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    filename: str = Field(min_length=1)


class TranslationDictionaryProvenance(TranslationModel):
    dictionary_version: str = Field(min_length=1)
    dictionary_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class TranslationLlmProvenance(TranslationModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    endpoint_kind: Literal["local", "cloud", "mock"]
    prompt_id: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameters: dict[str, str | int | float | bool | None] | None = None


class TranslationProvenance(TranslationModel):
    method: Literal["manual", "llm"]
    interface: Literal["cli", "gui", "api"]
    llm: TranslationLlmProvenance | None = None

    @model_validator(mode="after")
    def validate_llm(self) -> Self:
        if self.method == "llm" and self.llm is None:
            raise ValueError("LLM translations require LLM provenance")
        if self.method == "manual" and self.llm is not None:
            raise ValueError("manual translations cannot contain LLM provenance")
        return self


class TranslationUnit(TranslationModel):
    unit_id: str = Field(pattern=r"^tu_[0-9]{6,}$")
    speaker_id: str = Field(pattern=r"^speaker_[0-9]{3,}$")
    source_token_ids: tuple[str, ...] = Field(min_length=1)
    source_text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    target_text: str
    target_status: Literal["translated", "intentionally_empty"] = "translated"

    @field_validator("source_token_ids")
    @classmethod
    def validate_source_token_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("translation unit source token IDs must be unique")
        if any(not token_id.startswith(("word_", "rt_")) for token_id in value):
            raise ValueError("translation source token IDs must be canonical or revision IDs")
        return value

    @model_validator(mode="after")
    def validate_unit(self) -> Self:
        if self.end_ms < self.start_ms:
            raise ValueError("translation unit end must not precede start")
        if self.target_status == "translated" and not self.target_text.strip():
            raise ValueError("translated unit target text must not be blank")
        if self.target_status == "intentionally_empty" and self.target_text:
            raise ValueError("intentionally empty unit target text must be empty")
        return self


class TranslationStatistics(TranslationModel):
    unit_count: int = Field(ge=1)
    source_tokens: int = Field(ge=1)
    target_tokens: int = Field(ge=0)
    intentionally_empty_units: int = Field(default=0, ge=0)
    warning_count: int = Field(ge=0)


class TranslationWarning(TranslationModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    severity: Literal["info", "warning", "error"]
    message: str = Field(min_length=1)


class TranscriptTranslation(TranslationModel):
    schema_version: Literal["1.0", "1.1"]
    application_version: str = Field(min_length=1)
    translation_id: UUID
    translation_number: int = Field(ge=1)
    job_id: str = Field(min_length=1)
    created_at: datetime
    direction: TranslationDirection
    style: TranslationStyle
    source: TranslationSource
    parent_translation: TranslationParent | None = None
    dictionary: TranslationDictionaryProvenance | None = None
    provenance: TranslationProvenance
    units: tuple[TranslationUnit, ...] = Field(min_length=1)
    statistics: TranslationStatistics
    warnings: tuple[TranslationWarning, ...] = ()

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if self.created_at.tzinfo is None:
            raise ValueError("translation creation time must include timezone")
        if self.job_id != self.source.canonical_result.job_id:
            raise ValueError("translation and canonical source job IDs must match")
        unit_ids = [unit.unit_id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("translation unit IDs must be unique")
        source_ids = [token_id for unit in self.units for token_id in unit.source_token_ids]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("translation source tokens must be owned exactly once")
        if self.statistics.unit_count != len(self.units):
            raise ValueError("translation unit statistics do not match")
        if self.statistics.source_tokens != len(source_ids):
            raise ValueError("translation source-token statistics do not match")
        target_tokens = sum(len(unit.target_text.split()) for unit in self.units)
        if self.statistics.target_tokens != target_tokens:
            raise ValueError("translation target-token statistics do not match")
        intentionally_empty_units = sum(
            unit.target_status == "intentionally_empty" for unit in self.units
        )
        if self.statistics.intentionally_empty_units != intentionally_empty_units:
            raise ValueError("intentional-empty unit statistics do not match")
        if self.schema_version == "1.0" and intentionally_empty_units:
            raise ValueError("translation schema 1.0 cannot contain intentionally empty units")
        if self.statistics.warning_count != len(self.warnings):
            raise ValueError("translation warning statistics do not match")
        return self


def load_transcript_translation(path: Path) -> TranscriptTranslation:
    try:
        return TranscriptTranslation.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise InvalidTranslationError(
            f"Cannot read valid transcript translation: {path}"
        ) from error
