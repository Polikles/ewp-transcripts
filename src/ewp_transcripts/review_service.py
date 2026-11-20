"""Model-free preparation of editable reviews from completed canonical results."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from itertools import groupby
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
    validate_review_base,
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


def sentence_end(text: str) -> bool:
    """Conservative EN/PL terminal punctuation, excluding common abbreviations/initials."""
    clean = text.rstrip("\"'”’»)]}")
    if clean.lower() in {
        "dr.",
        "prof.",
        "mgr.",
        "np.",
        "tzn.",
        "tj.",
        "itd.",
        "itp.",
        "mr.",
        "mrs.",
        "ms.",
        "vs.",
        "e.g.",
        "i.e.",
    }:
        return False
    if re.fullmatch(r"[^\W\d_]\.", clean):
        return False
    return bool(re.search(r"[.!?…]$", clean))


def sentence_ranges(
    texts: list[str],
    *,
    target_words: int,
    speakers: list[str] | None = None,
    target_blocks: int | None = None,
) -> tuple[tuple[int, int], ...]:
    """Prefer nearby sentence ends; bound long unpunctuated ASR with a disclosed fallback."""
    if target_words < 1 or (target_blocks is not None and target_blocks < 1):
        raise ValueError("Review word and speaker-block targets must be positive")
    if not texts:
        return ((0, 0),)
    terminals = [index + 1 for index, text in enumerate(texts) if sentence_end(text)]
    ranges: list[tuple[int, int]] = []
    start = 0
    while start < len(texts):
        blocks = 1
        ideal = len(texts)
        for index in range(start + 1, len(texts)):
            changed = speakers is not None and speakers[index] != speakers[index - 1]
            if index - start >= target_words or (
                changed and target_blocks and blocks >= target_blocks
            ):
                ideal = index
                break
            blocks += bool(changed)
        if ideal == len(texts):
            end = len(texts)
        else:
            lower = start + max(1, (ideal - start) // 2)
            upper = min(len(texts), start + target_words * 2)
            candidates = [end for end in terminals if lower <= end <= upper]
            end = min(candidates, key=lambda end: (abs(end - ideal), end)) if candidates else ideal
        ranges.append((start, end))
        start = end
    return tuple(ranges)


def _anchor_ranges(
    base: CanonicalResult,
    *,
    target_words: int,
    target_speaker_blocks: int | None,
) -> tuple[tuple[int, int], ...]:
    units = _canonical_units(base)
    return sentence_ranges(
        [word.text.strip() for word, _ in units],
        target_words=target_words,
        speakers=[speaker for _, speaker in units],
        target_blocks=target_speaker_blocks,
    )


def review_sentence_warning(review: TranscriptReview) -> bool:
    """Flag heuristic fallback; this is not an ASR confidence measurement."""
    texts = [block.text for anchor in review.anchors for block in anchor.speaker_blocks]
    tokens = " ".join(texts).split()
    if len(tokens) >= 30 and not any(sentence_end(text) for text in tokens):
        return True
    return any(
        not sentence_end(anchor.speaker_blocks[-1].text)
        for anchor in review.anchors[:-1]
        if anchor.speaker_blocks[-1].text.strip()
    )


def bounded_review_document(
    review: TranscriptReview, base: CanonicalResult, *, target_words: int, target_blocks: int
) -> TranscriptReview:
    """Project old oversized drafts into bounded sections without changing saved bytes."""
    validate_review_base(review, base, base_sha256=review.header.base_result_sha256)
    units = _canonical_units(base)
    blocks = [block for anchor in review.anchors for block in anchor.speaker_blocks]
    tokens = [
        (text, block.speaker_id, index)
        for index, block in enumerate(blocks)
        for text in block.text.split()
    ]
    ranges = _anchor_ranges(base, target_words=target_words, target_speaker_blocks=target_blocks)
    boundaries = [(units[start][0].word_id, units[end - 1][0].word_id) for start, end in ranges]
    # Parent revisions may contain indivisible multi-word references. Their already
    # protected anchors cannot be repartitioned from canonical punctuation alone.
    if (
        review.header.source_revision_id is None
        and boundaries != [(anchor.first_word_id, anchor.last_word_id) for anchor in review.anchors]
        and (
            review_sentence_warning(review)
            or any(
                sum(len(block.text.split()) for block in anchor.speaker_blocks) > target_words * 2
                for anchor in review.anchors
            )
        )
        and [text for text, _, _ in tokens] == [word.text.strip() for word, _ in units]
    ):
        return review.model_copy(
            update={
                "anchors": tuple(
                    ReviewAnchor(
                        first_word_id=units[start][0].word_id,
                        last_word_id=units[end - 1][0].word_id,
                        speaker_blocks=tuple(
                            ReviewSpeakerBlock(
                                speaker_id=identity[0], text=" ".join(text for text, _, _ in values)
                            )
                            for identity, values in groupby(
                                tokens[start:end], key=lambda item: item[1:]
                            )
                        ),
                    )
                    for start, end in ranges
                )
            }
        )
    return review.model_copy(
        update={
            "anchors": tuple(
                anchor.model_copy(
                    update={
                        "speaker_blocks": tuple(
                            ReviewSpeakerBlock(
                                speaker_id=block.speaker_id,
                                text=" ".join(words[start:end]),
                            )
                            for block in anchor.speaker_blocks
                            for words in [block.text.split()]
                            for start, end in sentence_ranges(words, target_words=target_words)
                        )
                    }
                )
                for anchor in review.anchors
            )
        }
    )


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
    anchor_target_speaker_blocks: int | None = 5,
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
    ranges = _anchor_ranges(
        base,
        target_words=anchor_target_words,
        target_speaker_blocks=anchor_target_speaker_blocks,
    )
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
