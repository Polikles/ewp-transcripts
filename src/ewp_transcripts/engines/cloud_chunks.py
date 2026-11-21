"""Bounded audio requests and within-recording timed-context stitching, without biometrics."""

from __future__ import annotations

import re
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines.protocols import (
    AlignedSegment,
    AlignedTranscript,
    DiarizationResult,
    DiarizationTurn,
)

# Bound the complete JSON wire request, not just the WAV before base64 expansion.
MAX_REQUEST_BYTES = 24_000_000
JSON_MARGIN_BYTES = 4096
WAV_HEADER_BYTES = 44


@dataclass(frozen=True)
class AudioChunk:
    start: int
    end: int
    core_start: int
    core_end: int


def plan_audio_chunks(
    total: int, *, rate: int, frame_bytes: int, seconds: int, diarize: bool
) -> tuple[AudioChunk, ...]:
    """Partition PCM frames; shared context is included in both neighboring requests."""
    maximum_frames = (
        (MAX_REQUEST_BYTES - JSON_MARGIN_BYTES) // 4 * 3 - WAV_HEADER_BYTES
    ) // frame_bytes
    if maximum_frames < 1:
        raise SpeechEngineError("Cloud ASR audio format cannot fit within the request size limit")
    desired = min(rate * seconds, maximum_frames)
    context = min(rate * 5, desired // 3, maximum_frames // 6) if diarize else 0
    step = min(desired, maximum_frames - 2 * context)
    return tuple(
        AudioChunk(
            max(0, start - context),
            min(total, start + step + context),
            start,
            min(total, start + step),
        )
        for start in range(0, total, step)
    )


@dataclass(frozen=True)
class _ContextWord:
    segment: AlignedSegment
    speaker: str
    retained: bool


def _key(word: AlignedSegment) -> str:
    return "".join(re.findall(r"\w+", word.text.casefold()))


def _pairs(
    previous: tuple[_ContextWord, ...], current: tuple[AlignedSegment, ...]
) -> dict[int, int]:
    """One-to-one shared-word matches using text AND original absolute time, not speaker numbers."""
    starts = [word.segment.start_ms for word in previous]
    matched: dict[int, int] = {}
    used: set[int] = set()
    for index, word in enumerate(current):
        token = _key(word)
        candidates = []
        for other in range(
            bisect_left(starts, word.start_ms - 750), bisect_right(starts, word.start_ms + 750)
        ):
            old = previous[other].segment
            if other in used or not token or token != _key(old):
                continue
            if min(old.end_ms, word.end_ms) < max(old.start_ms, word.start_ms) - 250:
                continue
            candidates.append(
                (abs(old.start_ms - word.start_ms) + abs(old.end_ms - word.end_ms), other)
            )
        if candidates:
            _, other = min(candidates)
            matched[index] = other
            used.add(other)
    return matched


class MixedChunkMerger:
    """Merge adjacent responses on the original timeline; uncertain voices stay distinct."""

    def __init__(self) -> None:
        self._previous: tuple[_ContextWord, ...] = ()
        self._next_speaker = 1
        self.segments: list[AlignedSegment] = []
        self.turns: list[DiarizationTurn] = []
        self.notes: list[dict[str, Any]] = []
        self.mapping: dict[str, str] = {}

    def add(
        self,
        aligned: AlignedTranscript,
        diarization: DiarizationResult,
        *,
        core_start_ms: int,
        core_end_ms: int,
        final: bool,
        chunk_index: int,
    ) -> None:
        words = aligned.segments
        local = [turn.speaker_label for turn in diarization.turns]
        pairs = _pairs(self._previous, words)
        votes: dict[str, Counter[str]] = defaultdict(Counter)
        for current, old in pairs.items():
            votes[local[current]][self._previous[old].speaker] += 1
        proposed: dict[str, tuple[str, int]] = {}
        for speaker, counts in votes.items():
            ordered = counts.most_common()
            target, count = ordered[0]
            runner_up = ordered[1][1] if len(ordered) > 1 else 0
            if count >= 2 and count > runner_up and count >= 2 * runner_up:
                proposed[speaker] = target, count
        mapping: dict[str, str] = {}
        for speaker, (target, count) in proposed.items():
            rivals = [
                score
                for other, (candidate, score) in proposed.items()
                if other != speaker and candidate == target
            ]
            if not rivals or count > max(rivals):
                mapping[speaker] = target
        new = []
        for speaker in dict.fromkeys(local):
            if speaker not in mapping:
                mapping[speaker] = f"cloud_speaker_{self._next_speaker:03d}"
                self._next_speaker += 1
                new.append(mapping[speaker])
        if chunk_index > 1 and new:
            self.notes.append(
                {
                    "chunk_index": chunk_index,
                    "boundary_ms": core_start_ms,
                    "unresolved_speaker_labels": new,
                }
            )
        context = []
        for index, (word, speaker) in enumerate(zip(words, local, strict=True)):
            midpoint = (word.start_ms + word.end_ms) // 2
            owned = core_start_ms <= midpoint and (midpoint < core_end_ms or final)
            previous = self._previous[pairs[index]] if index in pairs else None
            # Shared-word ownership survives timestamp jitter around the cut: a previously
            # retained word is not repeated; a previously deferred word belongs here.
            retain = not previous.retained if previous else owned
            if previous is not None and not previous.retained:
                retain = midpoint < core_end_ms or final
            global_speaker = mapping[speaker]
            if retain:
                self.segments.append(word)
                self.turns.append(
                    DiarizationTurn(
                        start_ms=word.start_ms, end_ms=word.end_ms, speaker_label=global_speaker
                    )
                )
            context.append(
                _ContextWord(word, global_speaker, retain or bool(previous and previous.retained))
            )
        self._previous = tuple(context)
        self.mapping = mapping

    def result(self) -> tuple[tuple[AlignedSegment, ...], tuple[DiarizationTurn, ...]]:
        order = sorted(range(len(self.segments)), key=lambda index: self.segments[index].start_ms)
        return tuple(self.segments[i] for i in order), tuple(self.turns[i] for i in order)
