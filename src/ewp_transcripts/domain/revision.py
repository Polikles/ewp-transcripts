"""Strict immutable transcript-revision models and base compatibility checks."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ewp_transcripts.domain.canonical import CanonicalResult
from ewp_transcripts.domain.errors import InvalidRevisionError


class RevisionModel(BaseModel):
    """Frozen revision-schema object that rejects undocumented fields."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class RevisionBaseResult(RevisionModel):
    job_id: str = Field(min_length=1)
    result_version: int = Field(ge=1)
    schema_version: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    filename: str | None = Field(default=None, min_length=1)


class RevisionParent(RevisionModel):
    revision_id: UUID
    revision_number: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    filename: str | None = Field(default=None, min_length=1)


class RevisionDictionaryProvenance(RevisionModel):
    version: str = Field(min_length=1)
    dictionary_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    proposal_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RevisionLlmProvenance(RevisionModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    endpoint_kind: Literal["local", "cloud", "mock"]
    prompt_id: str | None = Field(default=None, min_length=1)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parameters: dict[str, str | int | float | bool | None] | None = None
    dictionary: RevisionDictionaryProvenance | None = None


class RevisionProvenance(RevisionModel):
    method: Literal["manual", "llm"]
    interface: Literal["cli", "gui", "api"]
    llm: RevisionLlmProvenance | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_llm_metadata(self) -> Self:
        if self.method == "llm" and self.llm is None:
            raise ValueError("LLM revisions require LLM provenance")
        if self.method == "manual" and self.llm is not None:
            raise ValueError("manual revisions cannot contain LLM provenance")
        return self


class RevisionInsertionAnchor(RevisionModel):
    after_word_id: str | None = Field(default=None, pattern=r"^word_[0-9]{6,}$")
    before_word_id: str | None = Field(default=None, pattern=r"^word_[0-9]{6,}$")

    @model_validator(mode="after")
    def require_neighbor(self) -> Self:
        if self.after_word_id is None and self.before_word_id is None:
            raise ValueError("insertion anchors require an adjacent canonical word")
        if self.after_word_id == self.before_word_id:
            raise ValueError("insertion anchor neighbors must be different")
        return self


class RevisionToken(RevisionModel):
    token_id: str = Field(pattern=r"^rt_[0-9]{6,}$")
    text: str = Field(min_length=1, pattern=r".*\S.*")
    speaker_id: str = Field(pattern=r"^speaker_[0-9]{3,}$")
    source_word_ids: tuple[str, ...]
    insertion_anchor: RevisionInsertionAnchor | None = None

    @model_validator(mode="after")
    def validate_source_mapping(self) -> Self:
        if len(self.source_word_ids) != len(set(self.source_word_ids)):
            raise ValueError("source_word_ids must be unique within a revision token")
        if self.source_word_ids and self.insertion_anchor is not None:
            raise ValueError("mapped tokens cannot contain an insertion anchor")
        if not self.source_word_ids and self.insertion_anchor is None:
            raise ValueError("inserted tokens require an insertion anchor")
        for word_id in self.source_word_ids:
            if not word_id.startswith("word_") or not word_id[5:].isdigit() or len(word_id) < 11:
                raise ValueError("source_word_ids must use canonical word identifiers")
        return self


class RevisionTranscript(RevisionModel):
    language: Literal["pl", "en"]
    tokens: tuple[RevisionToken, ...]
    speaker_labels: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_token_ids(self) -> Self:
        token_ids = [token.token_id for token in self.tokens]
        if len(token_ids) != len(set(token_ids)):
            raise ValueError("revision token IDs must be unique")
        return self

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


class RevisionAlignment(RevisionModel):
    strategy: Literal["anchored-token-v1"]
    review_format_version: Literal[1]
    anchor_count: int = Field(ge=1)
    ambiguous_regions: int = Field(ge=0)


class RevisionStatistics(RevisionModel):
    source_tokens: int = Field(ge=0)
    revision_tokens: int = Field(ge=0)
    unchanged: int = Field(ge=0)
    substitutions: int = Field(ge=0)
    merges: int = Field(ge=0)
    splits: int = Field(ge=0)
    insertions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    punctuation_only_changes: int = Field(ge=0)
    speaker_changes: int = Field(ge=0)
    alignment_warnings: int = Field(ge=0)


class RevisionWarning(RevisionModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    severity: Literal["info", "warning", "error"]
    message: str = Field(min_length=1)
    context: dict[str, Any] | None = None


class TranscriptRevision(RevisionModel):
    """One standalone immutable corrected-transcript snapshot."""

    schema_version: Literal["1.0"]
    application_version: str = Field(min_length=1)
    revision_id: UUID
    revision_number: int = Field(ge=1)
    job_id: str = Field(min_length=1)
    created_at: datetime
    base_result: RevisionBaseResult
    parent_revision: RevisionParent | None
    provenance: RevisionProvenance
    transcript: RevisionTranscript
    alignment: RevisionAlignment
    statistics: RevisionStatistics
    warnings: tuple[RevisionWarning, ...]

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if self.job_id != self.base_result.job_id:
            raise ValueError("revision and base-result job IDs must match")
        if self.statistics.revision_tokens != len(self.transcript.tokens):
            raise ValueError("revision token statistics must match the transcript")
        if self.statistics.alignment_warnings != len(self.warnings):
            raise ValueError("alignment warning statistics must match warnings")
        return self


def sha256_file(path: Path) -> str:
    """Hash one artifact without loading it fully into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_transcript_revision(path: Path) -> TranscriptRevision:
    """Read and strictly validate one transcript-revision JSON artifact."""

    try:
        return TranscriptRevision.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise InvalidRevisionError(f"Cannot read valid transcript revision: {path}") from error


def validate_revision_base(
    revision: TranscriptRevision,
    base: CanonicalResult,
    *,
    base_sha256: str,
) -> None:
    """Reject a revision that cannot be safely resolved against its claimed base result."""

    expected = revision.base_result
    if base.status != "completed":
        raise InvalidRevisionError("Transcript revisions require a completed canonical result")
    if revision.job_id != base.job_id or expected.job_id != base.job_id:
        raise InvalidRevisionError("Revision job ID does not match the canonical result")
    if expected.result_version != base.result_version:
        raise InvalidRevisionError("Revision result version does not match the canonical result")
    if expected.schema_version != base.schema_version:
        raise InvalidRevisionError("Revision schema version does not match the canonical result")
    if expected.sha256 != base_sha256:
        raise InvalidRevisionError("Revision base-result SHA-256 does not match")

    canonical_words = [word for segment in base.transcript.segments for word in segment.words]
    word_positions: dict[str, int] = {}
    for position, word in enumerate(canonical_words):
        if word.word_id in word_positions:
            raise InvalidRevisionError("Canonical result contains duplicate word IDs")
        word_positions[word.word_id] = position
    speaker_ids = {speaker.speaker_id for speaker in base.speakers}

    allowed_speaker_ids = speaker_ids | set(revision.transcript.speaker_labels)

    mapped_positions: list[int] = []
    for token in revision.transcript.tokens:
        if token.speaker_id not in allowed_speaker_ids:
            raise InvalidRevisionError(f"Revision references unknown speaker: {token.speaker_id}")
        references = list(token.source_word_ids)
        if token.insertion_anchor is not None:
            references.extend(
                word_id
                for word_id in (
                    token.insertion_anchor.after_word_id,
                    token.insertion_anchor.before_word_id,
                )
                if word_id is not None
            )
        missing = [word_id for word_id in references if word_id not in word_positions]
        if missing:
            raise InvalidRevisionError(f"Revision references unknown canonical word: {missing[0]}")

        token_positions = [word_positions[word_id] for word_id in token.source_word_ids]
        if token_positions != sorted(token_positions):
            raise InvalidRevisionError("Revision token source words are out of canonical order")
        mapped_positions.extend(token_positions)

        anchor = token.insertion_anchor
        if anchor is not None and anchor.after_word_id and anchor.before_word_id:
            after = word_positions[anchor.after_word_id]
            before = word_positions[anchor.before_word_id]
            if after >= before:
                raise InvalidRevisionError("Revision insertion anchor is out of canonical order")

    if mapped_positions != sorted(mapped_positions):
        raise InvalidRevisionError("Revision tokens are out of canonical word order")
