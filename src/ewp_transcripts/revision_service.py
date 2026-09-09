"""Deterministic anchored alignment from editable reviews to immutable revisions."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ewp_transcripts import __version__
from ewp_transcripts.domain.canonical import CanonicalResult, CanonicalWord
from ewp_transcripts.domain.errors import InvalidReviewError
from ewp_transcripts.domain.review import TranscriptReview, validate_review_base
from ewp_transcripts.domain.revision import (
    RevisionAlignment,
    RevisionBaseResult,
    RevisionInsertionAnchor,
    RevisionParent,
    RevisionProvenance,
    RevisionStatistics,
    RevisionToken,
    RevisionTranscript,
    RevisionWarning,
    TranscriptRevision,
    sha256_file,
    validate_revision_base,
)


@dataclass(frozen=True, slots=True)
class _Corrected:
    text: str
    speaker_id: str


@dataclass(frozen=True, slots=True)
class _Step:
    source_count: int
    corrected_count: int


def _lexical(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _align(
    source: tuple[CanonicalWord, ...],
    corrected: tuple[_Corrected, ...],
    *,
    preserve_speaker_attribution: bool = False,
) -> tuple[tuple[_Step, ...], bool]:
    """Return one stable minimum-cost path and whether another optimum exists."""

    width = len(corrected) + 1
    costs: list[list[int | None]] = [[None] * width for _ in range(len(source) + 1)]
    counts = [[0] * width for _ in range(len(source) + 1)]
    paths: list[list[tuple[_Step, ...] | None]] = [[None] * width for _ in range(len(source) + 1)]
    costs[0][0], counts[0][0], paths[0][0] = 0, 1, ()
    transitions = tuple(
        [(1, 1), (1, 0), (0, 1)]
        + [
            (left, right)
            for left in range(1, 4)
            for right in range(1, 4)
            if (left, right) != (1, 1) and (left == 1 or right == 1)
        ]
    )
    for left in range(len(source) + 1):
        for right in range(len(corrected) + 1):
            current_cost = costs[left][right]
            current_path = paths[left][right]
            if current_cost is None or current_path is None:
                continue
            for source_count, corrected_count in transitions:
                next_left, next_right = left + source_count, right + corrected_count
                if next_left > len(source) or next_right > len(corrected):
                    continue
                if preserve_speaker_attribution and source_count and corrected_count:
                    source_speakers = {item.speaker_id for item in source[left:next_left]}
                    corrected_speakers = {item.speaker_id for item in corrected[right:next_right]}
                    if (
                        len(source_speakers) != 1
                        or len(corrected_speakers) != 1
                        or source_speakers != corrected_speakers
                    ):
                        continue
                if source_count == 0 or corrected_count == 0:
                    step_cost = 2 * max(source_count, corrected_count)
                else:
                    source_text = "".join(_lexical(item.text) for item in source[left:next_left])
                    corrected_text = "".join(
                        _lexical(item.text) for item in corrected[right:next_right]
                    )
                    if (source_count, corrected_count) == (1, 1):
                        step_cost = 0 if source_text == corrected_text else 3
                    elif source_text and source_text == corrected_text:
                        step_cost = 1
                    else:
                        continue
                candidate = current_cost + step_cost
                existing = costs[next_left][next_right]
                candidate_path = current_path + (_Step(source_count, corrected_count),)
                if existing is None or candidate < existing:
                    costs[next_left][next_right] = candidate
                    counts[next_left][next_right] = counts[left][right]
                    paths[next_left][next_right] = candidate_path
                elif candidate == existing:
                    counts[next_left][next_right] = min(
                        2, counts[next_left][next_right] + counts[left][right]
                    )
    path = paths[-1][-1]
    if path is None:
        raise InvalidReviewError("REVISION_ALIGNMENT_AMBIGUOUS", "Review text cannot be aligned")
    return path, counts[-1][-1] > 1


def build_revision(
    review: TranscriptReview,
    base: CanonicalResult,
    *,
    base_path: Path,
    long_gap_warning_ms: int = 2000,
    created_at: datetime | None = None,
    parent_revision: TranscriptRevision | None = None,
    parent_path: Path | None = None,
    provenance: RevisionProvenance | None = None,
    preserve_speaker_attribution: bool = False,
) -> TranscriptRevision:
    """Validate and align one review into a complete unpublished revision snapshot."""

    base_hash = sha256_file(base_path)
    validate_review_base(review, base, base_sha256=base_hash)
    parent = None
    source_id = review.header.source_revision_id
    if source_id is not None:
        if parent_revision is None or parent_path is None:
            raise InvalidReviewError(
                "REVISION_BASE_HASH_MISMATCH",
                "Review parent revision cannot be located",
            )
        validate_revision_base(parent_revision, base, base_sha256=base_hash)
        parent_hash = sha256_file(parent_path)
        if (
            source_id != parent_revision.revision_id
            or review.header.source_revision_number != parent_revision.revision_number
            or review.header.source_revision_sha256 != parent_hash
        ):
            raise InvalidReviewError(
                "REVISION_BASE_HASH_MISMATCH",
                "Review parent revision identity does not match",
            )
        parent = RevisionParent(
            revision_id=parent_revision.revision_id,
            revision_number=parent_revision.revision_number,
            sha256=parent_hash,
            filename=parent_path.name,
        )
    elif parent_revision is not None or parent_path is not None:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "A parent revision was supplied for a base-relative review",
        )
    words = tuple(word for segment in base.transcript.segments for word in segment.words)
    positions = {word.word_id: index for index, word in enumerate(words)}
    tokens: list[RevisionToken] = []
    warnings: list[RevisionWarning] = []
    counts = dict(
        unchanged=0,
        substitutions=0,
        merges=0,
        splits=0,
        insertions=0,
        deletions=0,
        punctuation_only_changes=0,
        speaker_changes=0,
    )
    for anchor_index, anchor in enumerate(review.anchors):
        first, last = positions[anchor.first_word_id], positions[anchor.last_word_id]
        source = words[first : last + 1]
        corrected = tuple(
            _Corrected(text=text, speaker_id=block.speaker_id)
            for block in anchor.speaker_blocks
            for text in block.text.split()
        )
        path, ambiguous = _align(
            source,
            corrected,
            preserve_speaker_attribution=preserve_speaker_attribution,
        )
        if ambiguous:
            warnings.append(
                RevisionWarning(
                    code="REVISION_ALIGNMENT_AMBIGUOUS",
                    severity="warning",
                    message="Anchor has multiple equally optimal alignments",
                    context={"anchor_index": anchor_index + 1},
                )
            )
        source_at = corrected_at = 0
        for step in path:
            mapped = source[source_at : source_at + step.source_count]
            revised = corrected[corrected_at : corrected_at + step.corrected_count]
            if not revised:
                counts["deletions"] += len(mapped)
            elif len(mapped) > 1 and len(revised) == 1:
                counts["merges"] += 1
            elif len(mapped) == 1 and len(revised) > 1:
                counts["splits"] += 1
            for item in revised:
                source_ids = tuple(word.word_id for word in mapped)
                insertion_anchor = None
                if not mapped:
                    global_position = first + source_at
                    previous = words[global_position - 1] if global_position else None
                    following = words[global_position] if global_position < len(words) else None
                    insertion_anchor = RevisionInsertionAnchor(
                        after_word_id=previous.word_id if previous else None,
                        before_word_id=following.word_id if following else None,
                    )
                    counts["insertions"] += 1
                    if (
                        previous
                        and following
                        and following.start_ms - previous.end_ms >= long_gap_warning_ms
                    ):
                        warnings.append(
                            RevisionWarning(
                                code="REVISION_INSERT_ACROSS_LONG_GAP",
                                severity="warning",
                                message=(
                                    "Inserted text falls between canonical words separated by "
                                    "a long gap"
                                ),
                                context={
                                    "after_word_id": previous.word_id,
                                    "before_word_id": following.word_id,
                                },
                            )
                        )
                elif len(mapped) == 1 and len(revised) == 1:
                    original = mapped[0]
                    if item.text == original.text:
                        counts["unchanged"] += 1
                    elif _lexical(item.text) == _lexical(original.text):
                        counts["punctuation_only_changes"] += 1
                    else:
                        counts["substitutions"] += 1
                if mapped and any(word.speaker_id != item.speaker_id for word in mapped):
                    counts["speaker_changes"] += 1
                tokens.append(
                    RevisionToken(
                        token_id=f"rt_{len(tokens) + 1:06d}",
                        text=item.text,
                        speaker_id=item.speaker_id,
                        source_word_ids=source_ids,
                        insertion_anchor=insertion_anchor,
                    )
                )
            source_at += step.source_count
            corrected_at += step.corrected_count
    statistics = RevisionStatistics(
        source_tokens=len(words),
        revision_tokens=len(tokens),
        alignment_warnings=len(warnings),
        **counts,
    )
    return TranscriptRevision(
        schema_version="1.0",
        application_version=__version__,
        revision_id=uuid4(),
        revision_number=1,
        job_id=base.job_id,
        created_at=created_at or datetime.now(UTC),
        base_result=RevisionBaseResult(
            job_id=base.job_id,
            result_version=base.result_version,
            schema_version=base.schema_version,
            sha256=base_hash,
            filename=base_path.name,
        ),
        parent_revision=parent,
        provenance=provenance or RevisionProvenance(method="manual", interface="cli"),
        transcript=RevisionTranscript(
            language=review.header.language,
            tokens=tuple(tokens),
            speaker_labels=review.header.speaker_labels,
        ),
        alignment=RevisionAlignment(
            strategy="anchored-token-v1",
            review_format_version=1,
            anchor_count=len(review.anchors),
            ambiguous_regions=sum(
                warning.code == "REVISION_ALIGNMENT_AMBIGUOUS" for warning in warnings
            ),
        ),
        statistics=statistics,
        warnings=tuple(warnings),
    )
