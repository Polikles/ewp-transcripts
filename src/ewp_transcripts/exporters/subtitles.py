"""Subtitle cue construction and SRT/WebVTT serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ewp_transcripts.config import SubtitlesConfig
from ewp_transcripts.domain.canonical import (
    CanonicalResult,
    CanonicalSegment,
    CanonicalWord,
    TimedEventKind,
)

_NONFINAL_CONNECTIVES = frozenset(
    {
        "a",
        "ale",
        "bo",
        "czy",
        "do",
        "i",
        "lub",
        "na",
        "o",
        "od",
        "po",
        "to",
        "u",
        "w",
        "we",
        "z",
        "za",
        "ze",
        "że",
    }
)


@dataclass(frozen=True, slots=True)
class SubtitleCue:
    """One validated subtitle cue on the canonical millisecond timeline."""

    start_ms: int
    end_ms: int
    lines: tuple[str, ...]
    speaker_id: str | None
    overlap: bool = False
    kind: TimedEventKind = "speech"


@dataclass(frozen=True, slots=True)
class _CueDraft:
    """Unlabelled cue candidate awaiting global timeline ordering."""

    start_ms: int
    end_ms: int
    text: str
    speaker_id: str | None
    overlap: bool
    sequence: int
    words: tuple[CanonicalWord, ...] = ()
    kind: TimedEventKind = "speech"


def build_subtitle_cues(
    result: CanonicalResult, config: SubtitlesConfig | None = None
) -> tuple[SubtitleCue, ...]:
    """Build bounded cues without reading media or invoking inference libraries."""

    settings = config or SubtitlesConfig()
    labels = {speaker.speaker_id: speaker.speaker_label for speaker in result.speakers}
    multiple_speakers = len(result.speakers) > 1
    drafts: list[_CueDraft] = []
    previous_segment_speaker: str | None | object = object()

    for segment_index, segment in enumerate(result.transcript.segments):
        speaker_id = _effective_speaker(segment)
        label = labels[speaker_id] if speaker_id is not None else "Unknown"
        first_prefix = (
            f"{label}: "
            if _show_speaker_label(
                settings.speaker_labels,
                multiple_speakers=multiple_speakers,
                speaker_id=speaker_id,
                previous_speaker=previous_segment_speaker,
                first_chunk=True,
            )
            else ""
        )
        repeated_prefix = (
            f"{label}: " if multiple_speakers and settings.speaker_labels == "always" else ""
        )
        chunks = _segment_chunks(
            segment,
            settings,
            first_prefix=first_prefix,
            repeated_prefix=repeated_prefix,
        )
        for index, (start_ms, end_ms, text, words) in enumerate(chunks):
            drafts.append(
                _CueDraft(
                    start_ms=start_ms,
                    end_ms=end_ms,
                    text=text,
                    speaker_id=speaker_id,
                    overlap=segment.overlap,
                    sequence=segment_index * 1_000_000 + index,
                    words=words,
                    kind=segment.kind,
                )
            )
        previous_segment_speaker = speaker_id
    drafts.sort(key=lambda cue: (cue.start_ms, cue.end_ms, cue.sequence))
    drafts = _repartition_continuous_chains(
        drafts,
        settings,
        labels=labels,
        multiple_speakers=multiple_speakers,
    )
    drafts = _stabilize_drafts(
        drafts,
        settings,
        labels=labels,
        multiple_speakers=multiple_speakers,
    )
    # Repartitioning may move a word boundary across another speaker's explicitly
    # overlapping cue. Restore timeline order after every timing-changing pass while
    # retaining both cues and their overlap metadata.
    drafts.sort(key=lambda cue: (cue.start_ms, cue.end_ms, cue.sequence))

    cues: list[SubtitleCue] = []
    previous_speaker: str | None | object = object()
    for draft in drafts:
        text = draft.text
        if _show_speaker_label(
            settings.speaker_labels,
            multiple_speakers=multiple_speakers,
            speaker_id=draft.speaker_id,
            previous_speaker=previous_speaker,
            first_chunk=True,
        ):
            label = labels[draft.speaker_id] if draft.speaker_id is not None else "Unknown"
            text = f"{label}: {text}"
        cues.append(
            SubtitleCue(
                start_ms=draft.start_ms,
                end_ms=draft.end_ms,
                lines=wrap_subtitle_text(
                    text,
                    max_lines=settings.max_lines,
                    max_chars_per_line=settings.max_chars_per_line,
                ),
                speaker_id=draft.speaker_id,
                overlap=draft.overlap,
                kind=draft.kind,
            )
        )
        previous_speaker = draft.speaker_id
    return _extend_short_cues(tuple(cues), settings)


def _repartition_continuous_chains(
    drafts: list[_CueDraft],
    settings: SubtitlesConfig,
    *,
    labels: dict[str, str],
    multiple_speakers: bool,
) -> list[_CueDraft]:
    """Globally partition continuous timed words instead of preserving greedy splits."""

    repartitioned: list[_CueDraft] = []
    index = 0
    while index < len(drafts):
        first = drafts[index]
        end = index + 1
        while end < len(drafts) and _same_continuous_chain(drafts[end - 1], drafts[end], settings):
            end += 1
        chain = drafts[index:end]
        if all(draft.words for draft in chain):
            words = tuple(word for draft in chain for word in draft.words)
            first_prefix = _capacity_prefix(
                settings,
                labels=labels,
                multiple_speakers=multiple_speakers,
                speaker_id=first.speaker_id,
                previous_speaker=(repartitioned[-1].speaker_id if repartitioned else object()),
            )
            repeated_prefix = first_prefix if settings.speaker_labels == "always" else ""
            partition = _optimal_word_partition(
                words,
                settings,
                first_prefix=first_prefix,
                repeated_prefix=repeated_prefix,
            )
            if partition is not None:
                chain = [
                    _CueDraft(
                        start_ms=chunk[0].start_ms,
                        end_ms=chunk[-1].end_ms,
                        text=_word_text(list(chunk)),
                        speaker_id=first.speaker_id,
                        overlap=first.overlap,
                        sequence=first.sequence + chunk_index,
                        words=chunk,
                        kind=first.kind,
                    )
                    for chunk_index, chunk in enumerate(partition)
                ]
        repartitioned.extend(chain)
        index = end
    return repartitioned


def _same_continuous_chain(
    previous: _CueDraft, following: _CueDraft, settings: SubtitlesConfig
) -> bool:
    gap_ms = following.start_ms - previous.end_ms
    return (
        previous.speaker_id == following.speaker_id
        and previous.kind == following.kind
        and previous.overlap == following.overlap
        and bool(previous.words)
        and bool(following.words)
        and gap_ms <= settings.max_merge_gap_ms
        and following.start_ms >= previous.start_ms
    )


def _optimal_word_partition(
    words: tuple[CanonicalWord, ...],
    settings: SubtitlesConfig,
    *,
    first_prefix: str,
    repeated_prefix: str,
) -> tuple[tuple[CanonicalWord, ...], ...] | None:
    """Find the best valid partition of a complete continuous word chain."""

    solutions: list[tuple[tuple[int, ...], tuple[tuple[int, int], ...]] | None] = [None] * (
        len(words) + 1
    )
    solutions[len(words)] = (0, 0, 0, 0, 0, 0, 0), ()
    for start in range(len(words) - 1, -1, -1):
        best: tuple[tuple[int, ...], tuple[tuple[int, int], ...]] | None = None
        prefix = first_prefix if start == 0 else repeated_prefix
        for end in range(start + 1, len(words) + 1):
            chunk = list(words[start:end])
            if not _word_chunk_hard_fits(chunk, settings, prefix=prefix):
                continue
            # Cloud ASR may give neighboring words slightly overlapping time windows.
            # Keep those words in the same cue instead of clipping their canonical times
            # or publishing overlapping ordinary cues at this partition boundary.
            if end < len(words) and max(word.end_ms for word in chunk) > words[end].start_ms:
                continue
            remainder = solutions[end]
            if remainder is None:
                continue
            remainder_score, boundaries = remainder
            duration_ms = chunk[-1].end_ms - chunk[0].start_ms
            is_nonfinal = end < len(words)
            orphan = int(
                len(chunk) < settings.min_words_per_cue or duration_ms < settings.min_duration_ms
            )
            one_line = int(
                _display_line_count(chunk, settings, prefix=prefix) == 1
                and (is_nonfinal or start > 0)
            )
            linguistic = int(is_nonfinal and _ends_connective(chunk))
            linguistic += _internal_line_connective_count(chunk, settings, prefix=prefix)
            displayed_chars = len(f"{prefix}{_word_text(chunk)}")
            readable_duration_ms = (
                displayed_chars * 1000 + settings.max_chars_per_second - 1
            ) // settings.max_chars_per_second
            speed_deficit = max(0, readable_duration_ms - duration_ms)
            unfinished = int(is_nonfinal and not _ends_sentence(chunk))
            target = settings.target_chars_per_line * settings.max_lines
            deviation = abs(displayed_chars - target)
            local_score = (
                orphan,
                one_line,
                linguistic,
                speed_deficit,
                unfinished,
                1,
                deviation,
            )
            score = tuple(
                local + remaining
                for local, remaining in zip(local_score, remainder_score, strict=True)
            )
            candidate = score, ((start, end), *boundaries)
            if best is None or candidate[0] < best[0]:
                best = candidate
        solutions[start] = best

    solution = solutions[0]
    if solution is None:
        return None
    return tuple(tuple(words[start:end]) for start, end in solution[1])


def _stabilize_drafts(
    drafts: list[_CueDraft],
    settings: SubtitlesConfig,
    *,
    labels: dict[str, str],
    multiple_speakers: bool,
) -> list[_CueDraft]:
    """Repeat merge and balancing until a multi-cue chain stops changing."""

    stable = drafts
    for _ in range(len(drafts) + 1):
        updated = _merge_adjacent_drafts(
            stable,
            settings,
            labels=labels,
            multiple_speakers=multiple_speakers,
        )
        updated = _rebalance_adjacent_drafts(
            updated,
            settings,
            labels=labels,
            multiple_speakers=multiple_speakers,
        )
        if updated == stable:
            return updated
        stable = updated
    return stable


def _merge_adjacent_drafts(
    drafts: list[_CueDraft],
    settings: SubtitlesConfig,
    *,
    labels: dict[str, str],
    multiple_speakers: bool,
) -> list[_CueDraft]:
    """Merge nearby same-speaker fragments into readable bounded cues."""

    merged: list[_CueDraft] = []
    for draft in drafts:
        if not merged:
            merged.append(draft)
            continue
        previous = merged[-1]
        gap_ms = draft.start_ms - previous.end_ms
        text = f"{previous.text} {draft.text}".strip()
        prefix = _capacity_prefix(
            settings,
            labels=labels,
            multiple_speakers=multiple_speakers,
            speaker_id=previous.speaker_id,
            previous_speaker=merged[-2].speaker_id if len(merged) > 1 else object(),
        )
        duration_ms = draft.end_ms - previous.start_ms
        chars_per_second = len(text) * 1000 / max(duration_ms, 1)
        can_merge = (
            previous.speaker_id == draft.speaker_id
            and previous.kind == draft.kind
            and not previous.overlap
            and not draft.overlap
            and 0 <= gap_ms <= settings.max_merge_gap_ms
            and duration_ms <= settings.max_duration_ms
            and chars_per_second <= settings.max_chars_per_second
            and _fits_line_limits(f"{prefix}{text}", settings)
        )
        if can_merge:
            merged[-1] = _CueDraft(
                start_ms=previous.start_ms,
                end_ms=draft.end_ms,
                text=text,
                speaker_id=previous.speaker_id,
                overlap=False,
                sequence=previous.sequence,
                words=((*previous.words, *draft.words) if previous.words and draft.words else ()),
                kind=previous.kind,
            )
        else:
            merged.append(draft)
    return merged


def _rebalance_adjacent_drafts(
    drafts: list[_CueDraft],
    settings: SubtitlesConfig,
    *,
    labels: dict[str, str],
    multiple_speakers: bool,
) -> list[_CueDraft]:
    """Move continuous sentence boundaries when a complete merge cannot fit."""

    balanced = list(drafts)
    for index in range(len(balanced) - 1):
        previous = balanced[index]
        following = balanced[index + 1]
        gap_ms = following.start_ms - previous.end_ms
        if (
            previous.speaker_id != following.speaker_id
            or previous.overlap
            or following.overlap
            or not previous.words
            or not following.words
            or not 0 <= gap_ms <= settings.max_merge_gap_ms
        ):
            continue
        previous_prefix = _capacity_prefix(
            settings,
            labels=labels,
            multiple_speakers=multiple_speakers,
            speaker_id=previous.speaker_id,
            previous_speaker=balanced[index - 1].speaker_id if index > 0 else object(),
        )
        following_prefix = _capacity_prefix(
            settings,
            labels=labels,
            multiple_speakers=multiple_speakers,
            speaker_id=following.speaker_id,
            previous_speaker=previous.speaker_id,
        )

        while (
            len(previous.words) < settings.min_words_per_cue
            and len(following.words) > settings.min_words_per_cue
        ):
            previous_candidate = _draft_with_words(previous, (*previous.words, following.words[0]))
            following_candidate = _draft_with_words(following, following.words[1:])
            if not _draft_fits(
                previous_candidate, settings, prefix=previous_prefix
            ) or not _draft_fits(following_candidate, settings, prefix=following_prefix):
                break
            previous, following = previous_candidate, following_candidate

        while (
            len(following.words) < settings.min_words_per_cue
            and len(previous.words) > settings.min_words_per_cue
        ):
            previous_candidate = _draft_with_words(previous, previous.words[:-1])
            following_candidate = _draft_with_words(
                following, (previous.words[-1], *following.words)
            )
            if not _draft_fits(
                previous_candidate, settings, prefix=previous_prefix
            ) or not _draft_fits(following_candidate, settings, prefix=following_prefix):
                break
            previous, following = previous_candidate, following_candidate

        if _ends_connective(previous.words) and len(previous.words) > 1:
            previous_candidate = _draft_with_words(previous, previous.words[:-1])
            following_candidate = _draft_with_words(
                following, (previous.words[-1], *following.words)
            )
            if _draft_fits(previous_candidate, settings, prefix=previous_prefix) and _draft_fits(
                following_candidate, settings, prefix=following_prefix
            ):
                previous, following = previous_candidate, following_candidate

        optimized_previous, optimized_following = _best_word_boundary(
            list(previous.words),
            list(following.words),
            settings,
            previous_prefix=previous_prefix,
            following_prefix=following_prefix,
        )
        if max(word.end_ms for word in optimized_previous) > optimized_following[0].start_ms:
            continue
        previous = _draft_with_words(previous, tuple(optimized_previous))
        following = _draft_with_words(following, tuple(optimized_following))

        balanced[index] = previous
        balanced[index + 1] = following
    return balanced


def _draft_with_words(draft: _CueDraft, words: tuple[CanonicalWord, ...]) -> _CueDraft:
    return _CueDraft(
        start_ms=words[0].start_ms,
        end_ms=words[-1].end_ms,
        text=_word_text(list(words)),
        speaker_id=draft.speaker_id,
        overlap=draft.overlap,
        sequence=draft.sequence,
        words=words,
        kind=draft.kind,
    )


def _draft_fits(draft: _CueDraft, settings: SubtitlesConfig, *, prefix: str) -> bool:
    duration_ms = draft.end_ms - draft.start_ms
    chars_per_second = len(draft.text) * 1000 / max(duration_ms, 1)
    return (
        duration_ms <= settings.max_duration_ms
        and chars_per_second <= settings.max_chars_per_second
        and _fits_line_limits(f"{prefix}{draft.text}", settings)
    )


def _capacity_prefix(
    settings: SubtitlesConfig,
    *,
    labels: dict[str, str],
    multiple_speakers: bool,
    speaker_id: str | None,
    previous_speaker: str | None | object,
) -> str:
    if not _show_speaker_label(
        settings.speaker_labels,
        multiple_speakers=multiple_speakers,
        speaker_id=speaker_id,
        previous_speaker=previous_speaker,
        first_chunk=True,
    ):
        return ""
    label = labels[speaker_id] if speaker_id is not None else "Unknown"
    return f"{label}: "


def render_srt(cues: tuple[SubtitleCue, ...]) -> str:
    """Serialize cues as SubRip with sequential numbering."""

    _validate_cues(cues)
    blocks = [
        f"{index}\n{_timestamp(cue.start_ms, separator=',')} --> "
        f"{_timestamp(cue.end_ms, separator=',')}\n" + "\n".join(cue.lines)
        for index, cue in enumerate(cues, start=1)
    ]
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def render_vtt(cues: tuple[SubtitleCue, ...]) -> str:
    """Serialize cues as WebVTT."""

    _validate_cues(cues)
    blocks = [
        f"{_timestamp(cue.start_ms, separator='.')} --> "
        f"{_timestamp(cue.end_ms, separator='.')}\n" + "\n".join(cue.lines)
        for cue in cues
    ]
    body = "\n\n".join(blocks)
    return "WEBVTT\n\n" + body + ("\n" if body else "")


def wrap_subtitle_text(text: str, *, max_lines: int, max_chars_per_line: int) -> tuple[str, ...]:
    """Wrap at word boundaries while enforcing hard line and line-count limits."""

    if max_lines < 1 or max_chars_per_line < 1:
        raise ValueError("subtitle line limits must be positive")
    words = text.split()
    if not words:
        raise ValueError("subtitle cue text must not be empty")
    if any(len(word) > max_chars_per_line for word in words):
        raise ValueError("a subtitle word exceeds max_chars_per_line")
    if len(text) <= max_chars_per_line:
        return (text,)

    candidates: list[tuple[str, ...]] = []

    def collect(start: int, lines: tuple[str, ...]) -> None:
        if len(lines) >= max_lines:
            return
        for end in range(start + 1, len(words) + 1):
            line = " ".join(words[start:end])
            if len(line) > max_chars_per_line:
                break
            if end == len(words):
                candidates.append((*lines, line))
            else:
                collect(end, (*lines, line))

    collect(0, ())
    if not candidates:
        raise ValueError("subtitle cue exceeds max_lines")
    return min(candidates, key=_line_break_score)


def _line_break_score(lines: tuple[str, ...]) -> tuple[int, int, int]:
    dangling_connectives = sum(
        _normalized_word(line.split()[-1]) in _NONFINAL_CONNECTIVES for line in lines[:-1]
    )
    single_word_lines = sum(len(line.split()) == 1 for line in lines)
    lengths = [len(line) for line in lines]
    return dangling_connectives, single_word_lines, max(lengths) - min(lengths)


def _segment_chunks(
    segment: CanonicalSegment,
    settings: SubtitlesConfig,
    *,
    first_prefix: str,
    repeated_prefix: str,
) -> list[tuple[int, int, str, tuple[CanonicalWord, ...]]]:
    if not segment.words:
        return [(segment.start_ms, segment.end_ms, segment.text.strip(), ())]
    word_chunks: list[list[CanonicalWord]] = []
    current: list[CanonicalWord] = []
    for word in segment.words:
        candidate = [*current, word]
        text = _word_text(candidate)
        prefix = first_prefix if not word_chunks else repeated_prefix
        displayed_text = f"{prefix}{text}"
        duration_ms = candidate[-1].end_ms - candidate[0].start_ms
        chars_per_second = len(text) * 1000 / max(duration_ms, 1)
        exceeds = (
            not _fits_line_limits(displayed_text, settings)
            or duration_ms > settings.max_duration_ms
            or chars_per_second > settings.max_chars_per_second
        )
        if current and exceeds:
            word_chunks.append(current)
            current = [word]
        else:
            current = candidate
        if (
            current[-1].text.rstrip().endswith((".", "!", "?"))
            and len(_word_text(current)) >= settings.target_chars_per_line
        ):
            word_chunks.append(current)
            current = []
    if current:
        word_chunks.append(current)
    _rebalance_orphan_chunks(
        word_chunks,
        settings,
        first_prefix=first_prefix,
        repeated_prefix=repeated_prefix,
    )
    return [(*_word_chunk(words), tuple(words)) for words in word_chunks]


def _rebalance_orphan_chunks(
    chunks: list[list[CanonicalWord]],
    settings: SubtitlesConfig,
    *,
    first_prefix: str,
    repeated_prefix: str,
) -> None:
    """Avoid stranded sentence fragments while preserving hard cue limits."""

    if settings.min_words_per_cue <= 1:
        return

    # A short trailing fragment belongs to the preceding unfinished sentence. Move
    # its boundary left when both resulting cues remain valid.
    for index in range(1, len(chunks)):
        previous = chunks[index - 1]
        current = chunks[index]
        if _ends_sentence(previous):
            continue
        while (
            len(current) < settings.min_words_per_cue and len(previous) > settings.min_words_per_cue
        ):
            previous_candidate = previous[:-1]
            current_candidate = [previous[-1], *current]
            if not _word_chunk_fits(
                previous_candidate,
                settings,
                prefix=first_prefix if index == 1 else repeated_prefix,
            ) or not _word_chunk_fits(current_candidate, settings, prefix=repeated_prefix):
                break
            previous[:] = previous_candidate
            current[:] = current_candidate

    # A short leading fragment of an unfinished sentence can borrow from the following
    # cue. A punctuated short sentence remains independent.
    for index in range(len(chunks) - 1):
        current = chunks[index]
        following = chunks[index + 1]
        if _ends_sentence(current):
            continue
        while (
            len(current) < settings.min_words_per_cue
            and len(following) > settings.min_words_per_cue
        ):
            current_candidate = [*current, following[0]]
            following_candidate = following[1:]
            if not _word_chunk_fits(
                current_candidate,
                settings,
                prefix=first_prefix if index == 0 else repeated_prefix,
            ) or not _word_chunk_fits(following_candidate, settings, prefix=repeated_prefix):
                break
            current[:] = current_candidate
            following[:] = following_candidate

    for index in range(len(chunks) - 1):
        current = chunks[index]
        following = chunks[index + 1]
        optimized_current, optimized_following = _best_word_boundary(
            current,
            following,
            settings,
            previous_prefix=first_prefix if index == 0 else repeated_prefix,
            following_prefix=repeated_prefix,
        )
        current[:] = optimized_current
        following[:] = optimized_following


def _best_word_boundary(
    previous: list[CanonicalWord],
    following: list[CanonicalWord],
    settings: SubtitlesConfig,
    *,
    previous_prefix: str,
    following_prefix: str,
) -> tuple[list[CanonicalWord], list[CanonicalWord]]:
    """Select the best valid split across two fragments without greedy transfer."""

    if not previous or not following:
        return previous, following
    combined = [*previous, *following]
    original_boundary = len(previous)
    best = (previous, following)
    original_fits = _word_chunk_fits(
        previous, settings, prefix=previous_prefix
    ) and _word_chunk_fits(following, settings, prefix=following_prefix)
    best_score = (
        _word_boundary_score(
            previous,
            following,
            settings,
            previous_prefix=previous_prefix,
            following_prefix=following_prefix,
            movement=0,
        )
        if original_fits
        else (10**9, 10**9, 10**9, 10**9, 10**9)
    )
    for boundary in range(1, len(combined)):
        previous_candidate = combined[:boundary]
        following_candidate = combined[boundary:]
        if max(word.end_ms for word in previous_candidate) > following_candidate[0].start_ms:
            continue
        if not _word_chunk_fits(
            previous_candidate, settings, prefix=previous_prefix
        ) or not _word_chunk_fits(following_candidate, settings, prefix=following_prefix):
            continue
        score = _word_boundary_score(
            previous_candidate,
            following_candidate,
            settings,
            previous_prefix=previous_prefix,
            following_prefix=following_prefix,
            movement=abs(boundary - original_boundary),
        )
        if score < best_score:
            best = previous_candidate, following_candidate
            best_score = score
    return best


def _word_boundary_score(
    previous: list[CanonicalWord],
    following: list[CanonicalWord],
    settings: SubtitlesConfig,
    *,
    previous_prefix: str,
    following_prefix: str,
    movement: int,
) -> tuple[int, int, int, int, int]:
    nonfinal_one_line_penalty = int(
        _display_line_count(previous, settings, prefix=previous_prefix) == 1
    )
    linguistic_penalty = int(_ends_connective(previous))
    linguistic_penalty += _internal_line_connective_count(
        previous, settings, prefix=previous_prefix
    )
    linguistic_penalty += _internal_line_connective_count(
        following, settings, prefix=following_prefix
    )
    orphan_penalty = int(len(previous) < settings.min_words_per_cue) + int(
        len(following) < settings.min_words_per_cue
    )
    imbalance = abs(len(previous) - len(following))
    return nonfinal_one_line_penalty, linguistic_penalty, orphan_penalty, movement, imbalance


def _display_line_count(
    words: list[CanonicalWord], settings: SubtitlesConfig, *, prefix: str
) -> int:
    return len(
        wrap_subtitle_text(
            f"{prefix}{_word_text(words)}",
            max_lines=settings.max_lines,
            max_chars_per_line=settings.max_chars_per_line,
        )
    )


def _internal_line_connective_count(
    words: list[CanonicalWord], settings: SubtitlesConfig, *, prefix: str
) -> int:
    lines = wrap_subtitle_text(
        f"{prefix}{_word_text(words)}",
        max_lines=settings.max_lines,
        max_chars_per_line=settings.max_chars_per_line,
    )
    return sum(_normalized_word(line.split()[-1]) in _NONFINAL_CONNECTIVES for line in lines[:-1])


def _word_chunk_fits(words: list[CanonicalWord], settings: SubtitlesConfig, *, prefix: str) -> bool:
    if not words:
        return False
    text = _word_text(words)
    duration_ms = words[-1].end_ms - words[0].start_ms
    chars_per_second = len(text) * 1000 / max(duration_ms, 1)
    return (
        duration_ms <= settings.max_duration_ms
        and chars_per_second <= settings.max_chars_per_second
        and _fits_line_limits(f"{prefix}{text}", settings)
    )


def _word_chunk_hard_fits(
    words: list[CanonicalWord], settings: SubtitlesConfig, *, prefix: str
) -> bool:
    if not words:
        return False
    duration_ms = words[-1].end_ms - words[0].start_ms
    return duration_ms <= settings.max_duration_ms and _fits_line_limits(
        f"{prefix}{_word_text(words)}", settings
    )


def _ends_sentence(words: list[CanonicalWord]) -> bool:
    return bool(words and words[-1].text.rstrip().endswith((".", "!", "?")))


def _ends_connective(words: list[CanonicalWord] | tuple[CanonicalWord, ...]) -> bool:
    return bool(words and _normalized_word(words[-1].text) in _NONFINAL_CONNECTIVES)


def _normalized_word(text: str) -> str:
    return text.casefold().strip(".,!?;:—–-…()[]{}\"'„”’")


def _fits_line_limits(text: str, settings: SubtitlesConfig) -> bool:
    try:
        wrap_subtitle_text(
            text,
            max_lines=settings.max_lines,
            max_chars_per_line=settings.max_chars_per_line,
        )
    except ValueError:
        return False
    return True


def _word_chunk(words: list[CanonicalWord]) -> tuple[int, int, str]:
    return words[0].start_ms, words[-1].end_ms, _word_text(words)


def _word_text(words: list[CanonicalWord]) -> str:
    return " ".join(word.text.strip() for word in words if word.text.strip())


def _show_speaker_label(
    mode: Literal["on-change", "always", "never"],
    *,
    multiple_speakers: bool,
    speaker_id: str | None,
    previous_speaker: str | None | object,
    first_chunk: bool,
) -> bool:
    if not multiple_speakers or mode == "never":
        return False
    if mode == "always":
        return True
    return first_chunk and speaker_id != previous_speaker


def _effective_speaker(segment: CanonicalSegment) -> str | None:
    if segment.speaker_id is not None:
        return segment.speaker_id
    if len(segment.active_speaker_ids) == 1:
        return segment.active_speaker_ids[0]
    return None


def _extend_short_cues(
    cues: tuple[SubtitleCue, ...], settings: SubtitlesConfig
) -> tuple[SubtitleCue, ...]:
    extended: list[SubtitleCue] = []
    for index, cue in enumerate(cues):
        duration = cue.end_ms - cue.start_ms
        displayed_chars = len(" ".join(cue.lines))
        readable_duration = (
            displayed_chars * 1000 + settings.max_chars_per_second - 1
        ) // settings.max_chars_per_second
        target_duration = min(
            settings.max_duration_ms,
            max(settings.min_duration_ms, readable_duration),
        )
        if duration >= target_duration:
            extended.append(cue)
            continue
        desired_end = cue.start_ms + target_duration
        maximum_end = desired_end
        if index + 1 < len(cues) and not (cue.overlap or cues[index + 1].overlap):
            maximum_end = min(maximum_end, cues[index + 1].start_ms - settings.min_gap_ms)
        end_ms = max(cue.end_ms, min(desired_end, maximum_end))
        extended.append(
            SubtitleCue(
                start_ms=cue.start_ms,
                end_ms=end_ms,
                lines=cue.lines,
                speaker_id=cue.speaker_id,
                overlap=cue.overlap,
                kind=cue.kind,
            )
        )
    return tuple(extended)


def _timestamp(milliseconds: int, *, separator: Literal[",", "."]) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"


def _validate_cues(cues: tuple[SubtitleCue, ...]) -> None:
    for index, cue in enumerate(cues):
        if cue.start_ms < 0 or cue.end_ms < cue.start_ms:
            raise ValueError("subtitle cue timestamps are invalid")
        if not cue.lines or any(not line.strip() for line in cue.lines):
            raise ValueError("subtitle cues must contain non-empty lines")
        if index == 0:
            continue
        previous = cues[index - 1]
        if cue.start_ms < previous.start_ms:
            raise ValueError("subtitle cues must be sorted chronologically")
        if cue.start_ms < previous.end_ms and not (cue.overlap or previous.overlap):
            raise ValueError("ordinary subtitle cues must not overlap")
