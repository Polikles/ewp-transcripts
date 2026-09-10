"""Project-scoped correction dictionary proposals from exact manual revisions."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.correction import CorrectionDictionaryTerm
from ewp_transcripts.domain.errors import InvalidCorrectionResponseError
from ewp_transcripts.domain.revision import (
    load_transcript_revision,
    sha256_file,
    validate_revision_base,
)
from ewp_transcripts.revision_audit import build_revision_audit


class CorrectionDictionaryEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    job_id: str = Field(min_length=1)
    source_context: str = Field(min_length=1)
    target_context: str = Field(min_length=1)


class CorrectionDictionaryCandidate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    occurrences: int = Field(ge=1)
    case_count: int = Field(ge=1)
    evidence: tuple[CorrectionDictionaryEvidence, ...] = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"] = "pending"


class CorrectionDictionaryManualConvention(BaseModel):
    """One human-owned project convention outside lexical corpus extraction."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class CorrectionDictionaryProposal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    proposal_version: Literal["1.1"] = "1.1"
    project_id: str = Field(min_length=1)
    source_language: Literal["pl"] = "pl"
    canonical_directory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    revision_directory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_count: int = Field(ge=1)
    job_ids: tuple[str, ...] = Field(min_length=1)
    minimum_occurrences: int = Field(ge=1)
    previous_dictionary_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    candidates: tuple[CorrectionDictionaryCandidate, ...]
    manual_conventions: tuple[CorrectionDictionaryManualConvention, ...] = ()


class CorrectionDictionaryEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    status: Literal["approved", "rejected"] = "approved"


class ProjectCorrectionDictionary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    dictionary_version: Literal["1.1"] = "1.1"
    dictionary_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    project_id: str = Field(min_length=1)
    language: Literal["pl"] = "pl"
    job_ids: tuple[str, ...] = Field(min_length=1)
    proposal_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    entries: tuple[CorrectionDictionaryEntry, ...] = Field(min_length=1)
    manual_conventions: tuple[CorrectionDictionaryManualConvention, ...] = ()

    @model_validator(mode="after")
    def unique_source_terms(self) -> ProjectCorrectionDictionary:
        sources = [entry.source.casefold() for entry in self.entries]
        sources.extend(item.source.casefold() for item in self.manual_conventions)
        if len(sources) != len(set(sources)):
            raise ValueError("correction dictionary source terms must be unique")
        return self


def propose_correction_dictionary(
    *,
    canonical_directory: Path,
    revision_directory: Path,
    project_id: str,
    minimum_occurrences: int = 2,
    previous_dictionary: ProjectCorrectionDictionary | None = None,
    previous_dictionary_sha256: str | None = None,
) -> CorrectionDictionaryProposal:
    """Aggregate consistent lexical mappings from latest exact manual revisions."""

    bases = {path.name: path for path in canonical_directory.glob("*_results.json")}
    selected: dict[str, tuple[int, Path]] = {}
    for path in revision_directory.glob("*_revision_*.json"):
        if path.name.endswith("_audit.json"):
            continue
        revision = load_transcript_revision(path)
        if revision.provenance.method != "manual" or revision.base_result.filename not in bases:
            continue
        previous = selected.get(revision.job_id)
        if previous is None or revision.revision_number > previous[0]:
            selected[revision.job_id] = (revision.revision_number, path)
    if not selected:
        raise ValueError("No compatible manual revisions found for dictionary proposal")
    if previous_dictionary is not None:
        if previous_dictionary.project_id != project_id:
            raise ValueError("Previous correction dictionary belongs to another project")
        if previous_dictionary_sha256 is None:
            raise ValueError("Previous correction dictionary SHA-256 is required")
    previous_decisions = (
        {
            (entry.source.casefold(), entry.target.casefold()): entry.status
            for entry in previous_dictionary.entries
        }
        if previous_dictionary is not None
        else {}
    )
    mappings: dict[str, list[tuple[str, str, CorrectionDictionaryEvidence]]] = defaultdict(list)
    for job_id, (_number, revision_path) in sorted(selected.items()):
        revision = load_transcript_revision(revision_path)
        assert revision.base_result.filename is not None
        base_path = bases[revision.base_result.filename]
        base = load_canonical_result(base_path)
        validate_revision_base(revision, base, base_sha256=sha256_file(base_path))
        audit = build_revision_audit(
            base, revision, base_path=base_path, revision_path=revision_path
        )
        source_tokens = tuple(
            word for segment in base.transcript.segments for word in segment.words
        )
        source_positions = {word.word_id: index for index, word in enumerate(source_tokens)}
        target_positions = {
            token.token_id: index for index, token in enumerate(revision.transcript.tokens)
        }
        changes = cast(list[dict[str, object]], audit["changes"])
        for change in changes:
            if change["classification"] not in {"substitution", "merge", "split"}:
                continue
            before_raw, after_raw = change["before"], change["after"]
            if (
                isinstance(before_raw, str)
                and isinstance(after_raw, str)
                and (before := _strip_boundary_punctuation(before_raw))
                and (after := _strip_boundary_punctuation(after_raw))
                and before.casefold() != after.casefold()
            ):
                source_ids = change.get("source_word_ids")
                token_id = change.get("token_id")
                if (
                    not isinstance(source_ids, list)
                    or not source_ids
                    or not isinstance(token_id, str)
                ):
                    continue
                source_indexes = [
                    source_positions[item] for item in source_ids if item in source_positions
                ]
                target_index = target_positions.get(token_id)
                if not source_indexes or target_index is None:
                    continue
                evidence = CorrectionDictionaryEvidence(
                    job_id=job_id,
                    source_context=_context(
                        tuple(word.text for word in source_tokens),
                        min(source_indexes),
                        max(source_indexes) + 1,
                    ),
                    target_context=_context(
                        tuple(token.text for token in revision.transcript.tokens),
                        target_index,
                        target_index + 1,
                    ),
                )
                mappings[before.casefold()].append((before, after, evidence))
    candidates: list[CorrectionDictionaryCandidate] = []
    for observations in mappings.values():
        targets = {after.casefold() for _before, after, _evidence in observations}
        if len(targets) != 1:
            continue
        if len(observations) < minimum_occurrences:
            continue
        candidates.append(
            CorrectionDictionaryCandidate(
                source=observations[0][0],
                target=observations[0][1],
                occurrences=len(observations),
                case_count=len({item.job_id for _before, _after, item in observations}),
                evidence=tuple(item for _before, _after, item in observations),
                status=previous_decisions.get(
                    (observations[0][0].casefold(), observations[0][1].casefold()), "pending"
                ),
            )
        )
    candidates.sort(key=lambda item: (-item.case_count, -item.occurrences, item.source.casefold()))
    return CorrectionDictionaryProposal(
        project_id=project_id,
        canonical_directory_sha256=_directory_hash(bases.values()),
        revision_directory_sha256=_directory_hash(path for _number, path in selected.values()),
        case_count=len(selected),
        job_ids=tuple(sorted(selected)),
        minimum_occurrences=minimum_occurrences,
        previous_dictionary_sha256=previous_dictionary_sha256,
        candidates=tuple(candidates),
        manual_conventions=(
            previous_dictionary.manual_conventions if previous_dictionary is not None else ()
        ),
    )


def write_correction_dictionary_proposal(
    proposal: CorrectionDictionaryProposal, output_path: Path
) -> None:
    if output_path.exists():
        raise ValueError(f"Dictionary proposal output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_path.write_text(proposal.model_dump_json(indent=2) + "\n", encoding="utf-8")


def approve_correction_dictionary(
    *, proposal_path: Path, dictionary_id: str, output_path: Path
) -> ProjectCorrectionDictionary:
    payload = proposal_path.read_bytes()
    proposal = CorrectionDictionaryProposal.model_validate_json(payload)
    if any(candidate.status == "pending" for candidate in proposal.candidates):
        raise ValueError("Dictionary proposal still contains pending candidates")
    decisions = tuple(
        CorrectionDictionaryEntry(
            source=item.source,
            target=item.target,
            status=cast(Literal["approved", "rejected"], item.status),
        )
        for item in proposal.candidates
    )
    dictionary = ProjectCorrectionDictionary(
        dictionary_id=dictionary_id,
        project_id=proposal.project_id,
        job_ids=proposal.job_ids,
        proposal_sha256=hashlib.sha256(payload).hexdigest(),
        entries=decisions,
        manual_conventions=proposal.manual_conventions,
    )
    if output_path.exists():
        raise ValueError(f"Correction dictionary output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_path.write_text(dictionary.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return dictionary


def load_project_correction_dictionary(path: Path) -> tuple[ProjectCorrectionDictionary, str]:
    try:
        payload = path.read_bytes()
        dictionary = ProjectCorrectionDictionary.model_validate_json(payload)
    except (OSError, UnicodeError, ValueError) as error:
        raise InvalidCorrectionResponseError(
            f"Cannot read valid project correction dictionary: {path}"
        ) from error
    return dictionary, hashlib.sha256(payload).hexdigest()


def select_correction_dictionary_terms(
    dictionary: ProjectCorrectionDictionary, editable_text: str
) -> tuple[CorrectionDictionaryTerm, ...]:
    """Select source-present terms as model context; never rewrite text directly."""

    selected = []
    for entry in dictionary.entries:
        if entry.status != "approved":
            continue
        pattern = rf"(?<!\w){re.escape(entry.source)}(?!\w)"
        if re.search(pattern, editable_text, flags=re.IGNORECASE):
            selected.append(CorrectionDictionaryTerm(source=entry.source, target=entry.target))
    for convention in dictionary.manual_conventions:
        pattern = rf"(?<!\w){re.escape(convention.source)}(?!\w)"
        if re.search(pattern, editable_text, flags=re.IGNORECASE):
            selected.append(
                CorrectionDictionaryTerm(source=convention.source, target=convention.target)
            )
    return tuple(selected)


def _directory_hash(paths) -> str:  # type: ignore[no-untyped-def]
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(sha256_file(path).encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _strip_boundary_punctuation(value: str) -> str:
    value = value.strip()
    start = 0
    end = len(value)
    while start < end and unicodedata.category(value[start]).startswith("P"):
        start += 1
    while end > start and unicodedata.category(value[end - 1]).startswith("P"):
        end -= 1
    return value[start:end].strip()


def _context(tokens: tuple[str, ...], start: int, end: int, *, radius: int = 4) -> str:
    left = " ".join(tokens[max(0, start - radius) : start])
    owned = " ".join(tokens[start:end])
    right = " ".join(tokens[end : min(len(tokens), end + radius)])
    return " ".join(part for part in (left, f"[[{owned}]]", right) if part)
