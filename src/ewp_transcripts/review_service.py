"""Model-free preparation of editable reviews from completed canonical results."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from ewp_transcripts import __version__
from ewp_transcripts.domain.canonical import CanonicalResult, CanonicalWord, load_canonical_result
from ewp_transcripts.domain.errors import InvalidReviewError
from ewp_transcripts.domain.review import (
    ReviewAnchor,
    ReviewExtensionHeader,
    ReviewHeader,
    ReviewSpeakerBlock,
    TranscriptReview,
)
from ewp_transcripts.domain.revision import (
    TranscriptRevision,
    load_transcript_revision,
    sha256_file,
    validate_revision_base,
)


def _speaker_id(
    word: CanonicalWord,
    *,
    segment_speaker_id: str | None,
    fallback_speaker_id: str | None,
) -> str:
    speaker_id = word.speaker_id or segment_speaker_id or fallback_speaker_id
    if speaker_id is None:
        raise InvalidReviewError(
            "REVISION_SPEAKER_INVALID",
            "Canonical word has no unambiguous speaker for review preparation",
        )
    return speaker_id


def _canonical_units(base: CanonicalResult) -> tuple[tuple[CanonicalWord, str], ...]:
    fallback = base.speakers[0].speaker_id if len(base.speakers) == 1 else None
    units: list[tuple[CanonicalWord, str]] = []
    for segment in base.transcript.segments:
        for word in segment.words:
            units.append(
                (
                    word,
                    _speaker_id(
                        word,
                        segment_speaker_id=segment.speaker_id,
                        fallback_speaker_id=fallback,
                    ),
                )
            )
    if not units:
        raise InvalidReviewError(
            "REVISION_ANCHOR_INVALID",
            "Canonical result contains no words to prepare for review",
        )
    word_ids = [word.word_id for word, _ in units]
    if len(word_ids) != len(set(word_ids)):
        raise InvalidReviewError(
            "REVISION_SOURCE_WORD_MISSING",
            "Canonical result contains duplicate word IDs",
        )
    return tuple(units)


def _anchor_ranges(base: CanonicalResult, *, target_words: int) -> tuple[tuple[int, int], ...]:
    if target_words < 1:
        raise ValueError("anchor_target_words must be positive")
    segment_sizes = [len(segment.words) for segment in base.transcript.segments if segment.words]
    ranges: list[tuple[int, int]] = []
    start = 0
    accumulated = 0
    for size in segment_sizes:
        if accumulated and accumulated + size > target_words:
            ranges.append((start, start + accumulated))
            start += accumulated
            accumulated = 0
        accumulated += size
    if accumulated:
        ranges.append((start, start + accumulated))
    return tuple(ranges)


def _speaker_blocks(units: tuple[tuple[CanonicalWord, str], ...]) -> tuple[ReviewSpeakerBlock, ...]:
    blocks: list[ReviewSpeakerBlock] = []
    speaker_id: str | None = None
    words: list[str] = []
    for word, current_speaker_id in units:
        if speaker_id is not None and current_speaker_id != speaker_id:
            blocks.append(ReviewSpeakerBlock(speaker_id=speaker_id, text=" ".join(words)))
            words = []
        speaker_id = current_speaker_id
        words.append(word.text.strip())
    if speaker_id is not None:
        blocks.append(ReviewSpeakerBlock(speaker_id=speaker_id, text=" ".join(words)))
    return tuple(blocks)


def prepare_review(
    result_path: Path,
    *,
    source_revision_path: Path | None = None,
    anchor_target_words: int = 200,
    generated_at: datetime | None = None,
    application_version: str = __version__,
) -> TranscriptReview:
    """Create a complete human-editable review model from one canonical result file."""

    try:
        base = load_canonical_result(result_path)
    except Exception as error:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            f"Cannot read a valid completed canonical result: {result_path}",
        ) from error
    if base.status != "completed":
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Only completed canonical results can be prepared for review",
        )
    if base.transcript.language not in {"pl", "en"}:
        raise InvalidReviewError(
            "REVISION_BASE_HASH_MISMATCH",
            "Canonical transcript language must resolve to pl or en",
        )
    language = cast(Literal["pl", "en"], base.transcript.language)
    units = _canonical_units(base)
    source_revision: TranscriptRevision | None = None
    if source_revision_path is not None:
        try:
            source_revision = load_transcript_revision(source_revision_path)
            validate_revision_base(
                source_revision,
                base,
                base_sha256=sha256_file(result_path),
            )
        except Exception as error:
            raise InvalidReviewError(
                "REVISION_BASE_HASH_MISMATCH",
                "Cannot use an incompatible source revision for review preparation",
            ) from error
    ranges = _anchor_ranges(base, target_words=anchor_target_words)
    if source_revision is not None:
        ranges = _revision_safe_ranges(ranges, source_revision, units)
    anchors = tuple(
        ReviewAnchor(
            first_word_id=units[start][0].word_id,
            last_word_id=units[end - 1][0].word_id,
            speaker_blocks=(
                _revision_speaker_blocks(source_revision, units, start=start, end=end)
                if source_revision is not None
                else _speaker_blocks(units[start:end])
            ),
        )
        for start, end in ranges
    )
    return TranscriptReview(
        format_version=1,
        header=ReviewHeader(
            job_id=base.job_id,
            base_result_file=result_path.name,
            base_result_sha256=sha256_file(result_path),
            base_result_schema_version=base.schema_version,
            base_result_version=base.result_version,
            language=language,
            generated_at=generated_at or datetime.now(UTC),
            application_version=application_version,
            source_revision_id=(source_revision.revision_id if source_revision else None),
            source_revision_sha256=(
                sha256_file(source_revision_path) if source_revision_path else None
            ),
            source_revision_number=(source_revision.revision_number if source_revision else None),
            speaker_labels=(source_revision.transcript.speaker_labels if source_revision else {}),
            extensions=(
                (
                    ReviewExtensionHeader(
                        key="x_source_verification",
                        value=(
                            "automated_candidate"
                            if source_revision.provenance.method == "llm"
                            else "manually_verified"
                        ),
                    ),
                )
                if source_revision is not None
                else ()
            ),
        ),
        anchors=anchors,
    )


def _revision_safe_ranges(
    ranges: tuple[tuple[int, int], ...],
    revision: TranscriptRevision,
    units: tuple[tuple[CanonicalWord, str], ...],
) -> tuple[tuple[int, int], ...]:
    positions = {word.word_id: index for index, (word, _speaker) in enumerate(units)}
    forbidden_cuts = {
        cut
        for token in revision.transcript.tokens
        if token.source_word_ids
        for cut in range(
            positions[token.source_word_ids[0]] + 1,
            positions[token.source_word_ids[-1]] + 1,
        )
    }
    retained_ends = [end for _start, end in ranges[:-1] if end not in forbidden_cuts]
    boundaries = [0, *retained_ends, len(units)]
    return tuple(zip(boundaries, boundaries[1:], strict=False))


def _revision_speaker_blocks(
    revision: TranscriptRevision,
    units: tuple[tuple[CanonicalWord, str], ...],
    *,
    start: int,
    end: int,
) -> tuple[ReviewSpeakerBlock, ...]:
    positions = {word.word_id: index for index, (word, _speaker) in enumerate(units)}
    selected = []
    for token in revision.transcript.tokens:
        references = token.source_word_ids
        if references:
            position = positions[references[0]]
        else:
            assert token.insertion_anchor is not None
            reference = (
                token.insertion_anchor.after_word_id or token.insertion_anchor.before_word_id
            )
            assert reference is not None
            position = positions[reference]
        if start <= position < end:
            selected.append((token.text, token.speaker_id))
    if not selected:
        return (ReviewSpeakerBlock(speaker_id=units[start][1], text=""),)
    blocks: list[ReviewSpeakerBlock] = []
    speaker_id = selected[0][1]
    words: list[str] = []
    for text, current_speaker in selected:
        if current_speaker != speaker_id:
            blocks.append(ReviewSpeakerBlock(speaker_id=speaker_id, text=" ".join(words)))
            speaker_id = current_speaker
            words = []
        words.append(text)
    blocks.append(ReviewSpeakerBlock(speaker_id=speaker_id, text=" ".join(words)))
    return tuple(blocks)
