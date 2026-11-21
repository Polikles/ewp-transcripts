"""Tests for subtitle cue construction and serialization."""

from pathlib import Path

import pytest

from ewp_transcripts.config import SubtitlesConfig
from ewp_transcripts.domain.canonical import CanonicalSegment, load_canonical_result
from ewp_transcripts.exporters import subtitles as subtitle_exporter
from ewp_transcripts.exporters.subtitles import (
    SubtitleCue,
    build_subtitle_cues,
    render_srt,
    render_vtt,
    wrap_subtitle_text,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = ROOT / "examples/results.example.json"


def test_builds_bounded_cues_with_labels_on_speaker_changes() -> None:
    result = load_canonical_result(EXAMPLE_PATH)

    cues = build_subtitle_cues(result)

    assert len(cues) == 2
    assert cues[0] == SubtitleCue(
        start_ms=1240,
        end_ms=3900,
        lines=("jan: Welcome to another episode.",),
        speaker_id="speaker_001",
    )
    assert cues[1] == SubtitleCue(
        start_ms=4320,
        end_ms=6320,
        lines=("anna: Today we discuss transcription.",),
        speaker_id="speaker_002",
    )
    assert all(len(cue.lines) <= 2 for cue in cues)
    assert all(len(line) <= 50 for cue in cues for line in cue.lines)


def test_cue_planning_preserves_event_kind_without_styling_it() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first, second = result.transcript.segments
    second = second.model_copy(update={"kind": "laugh"})
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (first, second)})}
    )

    cues = build_subtitle_cues(result)

    assert [cue.kind for cue in cues] == ["speech", "laugh"]
    assert "[" not in " ".join(cues[1].lines)


def test_srt_and_vtt_have_valid_headers_timestamps_and_spacing() -> None:
    cues = (
        SubtitleCue(1240, 3900, ("First cue.",), "speaker_001"),
        SubtitleCue(4320, 6320, ("Second cue.",), "speaker_002"),
    )

    assert render_srt(cues) == (
        "1\n00:00:01,240 --> 00:00:03,900\nFirst cue.\n\n"
        "2\n00:00:04,320 --> 00:00:06,320\nSecond cue.\n"
    )
    assert render_vtt(cues) == (
        "WEBVTT\n\n"
        "00:00:01.240 --> 00:00:03.900\nFirst cue.\n\n"
        "00:00:04.320 --> 00:00:06.320\nSecond cue.\n"
    )


def test_never_mode_suppresses_speaker_labels() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    config = SubtitlesConfig(speaker_labels="never")

    cues = build_subtitle_cues(result, config)

    assert cues[0].lines == ("Welcome to another episode.",)
    assert cues[1].lines == ("Today we discuss transcription.",)


def test_wraps_only_at_word_boundaries_and_rejects_impossible_text() -> None:
    assert wrap_subtitle_text("one two three four", max_lines=2, max_chars_per_line=10) == (
        "one two",
        "three four",
    )
    with pytest.raises(ValueError, match="word exceeds"):
        wrap_subtitle_text("extraordinary", max_lines=2, max_chars_per_line=5)
    with pytest.raises(ValueError, match="exceeds max_lines"):
        wrap_subtitle_text("one two three", max_lines=1, max_chars_per_line=5)


@pytest.mark.parametrize("connective", ["i", "na", "to"])
def test_wrap_avoids_polish_connective_at_end_of_visible_line(connective: str) -> None:
    lines = wrap_subtitle_text(
        f"To jest pierwsza część {connective} druga część zdania.",
        max_lines=2,
        max_chars_per_line=28,
    )

    assert lines[0].split()[-1] != connective


def test_short_cue_extension_stops_before_next_cue() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first = result.transcript.segments[0]
    short_word = first.words[0].model_copy(update={"end_ms": 1400})
    short = first.model_copy(update={"end_ms": 1400, "text": "Welcome", "words": (short_word,)})
    following = result.transcript.segments[1].model_copy(update={"start_ms": 1600, "end_ms": 2500})
    following_words = tuple(
        word.model_copy(update={"start_ms": 1600 + index * 100, "end_ms": 1680 + index * 100})
        for index, word in enumerate(following.words)
    )
    following = following.model_copy(update={"words": following_words})
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (short, following)})}
    )

    cues = build_subtitle_cues(result)

    assert cues[0].end_ms == 1520
    assert cues[1].start_ms == 1600


def test_nearby_same_speaker_fragments_merge_across_rhetorical_pause() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first, second = result.transcript.segments
    first_words = tuple(
        word.model_copy(
            update={
                "text": text,
                "start_ms": 1000 + index * 350,
                "end_ms": 1300 + index * 350,
                "speaker_id": "speaker_001",
            }
        )
        for index, (word, text) in enumerate(zip(first.words[:2], ("Może", "i"), strict=True))
    )
    first = first.model_copy(
        update={
            "start_ms": 1000,
            "end_ms": 1650,
            "text": "Może i",
            "speaker_id": "speaker_001",
            "active_speaker_ids": ("speaker_001",),
            "words": first_words,
        }
    )
    second_words = tuple(
        word.model_copy(
            update={
                "text": text,
                "start_ms": 2450 + index * 250,
                "end_ms": 2650 + index * 250,
                "speaker_id": "speaker_001",
            }
        )
        for index, (word, text) in enumerate(
            zip(second.words[:3], ("nikt", "nie", "zauważy."), strict=True)
        )
    )
    second = second.model_copy(
        update={
            "start_ms": 2450,
            "end_ms": 3150,
            "text": "nikt nie zauważy.",
            "speaker_id": "speaker_001",
            "active_speaker_ids": ("speaker_001",),
            "words": second_words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (first, second)})}
    )

    cues = build_subtitle_cues(result)

    assert cues == (
        SubtitleCue(
            start_ms=1000,
            end_ms=3150,
            lines=("jan: Może i nikt nie zauważy.",),
            speaker_id="speaker_001",
        ),
    )


def test_trailing_fragment_is_rebalanced_without_exceeding_limits() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    original = result.transcript.segments[0]
    words = tuple(
        original.words[0].model_copy(
            update={
                "word_id": f"word_balance_{index}",
                "text": "aa",
                "start_ms": 1000 + index * 500,
                "end_ms": 1400 + index * 500,
            }
        )
        for index in range(10)
    )
    segment = original.model_copy(
        update={
            "start_ms": words[0].start_ms,
            "end_ms": words[-1].end_ms,
            "text": " ".join(word.text for word in words),
            "words": words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (segment,)})}
    )
    config = SubtitlesConfig(
        max_lines=1,
        max_chars_per_line=20,
        max_chars_per_second=100,
        min_words_per_cue=4,
        speaker_labels="never",
    )

    cues = build_subtitle_cues(result, config)

    assert len(cues) == 2
    assert all(len(" ".join(cue.lines).split()) >= 4 for cue in cues)
    assert all(len(line) <= 20 for cue in cues for line in cue.lines)


def test_short_standalone_sentence_surrounded_by_silence_is_preserved() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first, second = result.transcript.segments
    first_words = tuple(
        word.model_copy(update={"text": text})
        for word, text in zip(first.words[:2], ("Tak", "jest."), strict=True)
    )
    first = first.model_copy(
        update={"text": "Tak jest.", "words": first_words, "end_ms": first_words[-1].end_ms}
    )
    second_words = tuple(
        word.model_copy(
            update={
                "text": text,
                "start_ms": 7000 + index * 400,
                "end_ms": 7300 + index * 400,
                "speaker_id": "speaker_001",
            }
        )
        for index, (word, text) in enumerate(
            zip(second.words[:4], ("Dalsza", "część", "tej", "wypowiedzi."), strict=True)
        )
    )
    second = second.model_copy(
        update={
            "start_ms": 7000,
            "end_ms": second_words[-1].end_ms,
            "text": "Dalsza część tej wypowiedzi.",
            "speaker_id": "speaker_001",
            "active_speaker_ids": ("speaker_001",),
            "words": second_words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (first, second)})}
    )

    cues = build_subtitle_cues(result)

    assert cues[0].lines == ("jan: Tak jest.",)
    assert cues[1].lines == ("Dalsza część tej wypowiedzi.",)


def test_short_cross_segment_fragment_borrows_timed_words_from_following_cue() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first, second = result.transcript.segments
    first_words = tuple(
        first.words[0].model_copy(
            update={
                "word_id": f"word_cross_first_{index}",
                "text": "aa",
                "start_ms": 1000 + index * 500,
                "end_ms": 1400 + index * 500,
                "speaker_id": "speaker_001",
            }
        )
        for index in range(1)
    )
    first = first.model_copy(
        update={
            "start_ms": first_words[0].start_ms,
            "end_ms": first_words[-1].end_ms,
            "text": "aa",
            "speaker_id": "speaker_001",
            "active_speaker_ids": ("speaker_001",),
            "words": first_words,
        }
    )
    second_words = tuple(
        second.words[0].model_copy(
            update={
                "word_id": f"word_cross_second_{index}",
                "text": "aa",
                "start_ms": 2300 + index * 500,
                "end_ms": 2700 + index * 500,
                "speaker_id": "speaker_001",
            }
        )
        for index in range(8)
    )
    second = second.model_copy(
        update={
            "start_ms": second_words[0].start_ms,
            "end_ms": second_words[-1].end_ms,
            "text": " ".join(word.text for word in second_words),
            "speaker_id": "speaker_001",
            "active_speaker_ids": ("speaker_001",),
            "words": second_words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (first, second)})}
    )
    config = SubtitlesConfig(
        max_lines=1,
        max_chars_per_line=14,
        max_chars_per_second=100,
        min_words_per_cue=3,
        speaker_labels="never",
    )

    cues = build_subtitle_cues(result, config)

    assert all(len(" ".join(cue.lines).split()) >= 3 for cue in cues)
    assert cues[0].start_ms == first_words[0].start_ms
    assert cues[-1].end_ms == second_words[-1].end_ms


def test_on_change_label_reserves_capacity_only_for_first_speaker_chunk() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    original = result.transcript.segments[1]
    words = tuple(
        original.words[0].model_copy(
            update={
                "word_id": f"word_label_capacity_{index}",
                "text": "aa",
                "start_ms": 1000 + index * 500,
                "end_ms": 1400 + index * 500,
                "speaker_id": "speaker_002",
            }
        )
        for index in range(12)
    )
    segment = original.model_copy(
        update={
            "start_ms": words[0].start_ms,
            "end_ms": words[-1].end_ms,
            "text": " ".join(word.text for word in words),
            "speaker_id": "speaker_002",
            "active_speaker_ids": ("speaker_002",),
            "words": words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (segment,)})}
    )
    config = SubtitlesConfig(
        max_lines=1,
        max_chars_per_line=20,
        max_chars_per_second=100,
        speaker_labels="on-change",
    )

    cues = build_subtitle_cues(result, config)

    assert tuple(len(" ".join(cue.lines).removeprefix("anna: ").split()) for cue in cues) == (5, 7)
    assert cues[0].lines[0].startswith("anna: ")
    assert not cues[1].lines[0].startswith("anna: ")


def test_reported_speaker_opening_micro_cues_are_balanced_from_one_segment() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first_template, second_template = result.transcript.segments
    texts = (
        "Może",
        "i",
        "nikt",
        "nie",
        "zauważy,",
        "ale",
        "pamiętajmy,",
        "że",
        "powiedzenie",
        "internet",
        "nie",
        "zapomina,",
        "bo",
        "dotyczy",
        "także,",
        "a",
        "może",
        "przede",
        "wszystkim",
        "algorytmów.",
    )
    starts = (
        15444,
        15704,
        15784,
        16004,
        16124,
        16945,
        17105,
        17965,
        18085,
        18925,
        19406,
        19526,
        20666,
        20766,
        21166,
        21867,
        21947,
        22167,
        22427,
        23147,
    )
    ends = (
        15644,
        15744,
        15964,
        16084,
        16885,
        17065,
        17945,
        18045,
        18885,
        19386,
        19486,
        20646,
        20726,
        21106,
        21827,
        21907,
        22127,
        22387,
        23107,
        24648,
    )
    words = tuple(
        second_template.words[0].model_copy(
            update={
                "word_id": f"word_reported_opening_{index}",
                "text": text,
                "start_ms": start,
                "end_ms": end,
                "speaker_id": "speaker_002",
            }
        )
        for index, (text, start, end) in enumerate(zip(texts, starts, ends, strict=True))
    )
    segment = second_template.model_copy(
        update={
            "start_ms": starts[0],
            "end_ms": ends[-1],
            "text": " ".join(texts),
            "speaker_id": "speaker_002",
            "active_speaker_ids": ("speaker_002",),
            "words": words,
        }
    )
    result = result.model_copy(
        update={
            "transcript": result.transcript.model_copy(
                update={"segments": (first_template, segment)}
            )
        }
    )

    cues = build_subtitle_cues(result)
    speaker_two_cues = [cue for cue in cues if cue.speaker_id == "speaker_002"]

    assert all(cue.end_ms - cue.start_ms >= 1000 for cue in speaker_two_cues)
    assert all(
        len(" ".join(cue.lines).removeprefix("anna: ").split()) >= 4 for cue in speaker_two_cues
    )
    assert " ".join(speaker_two_cues[0].lines).startswith("anna: Może i nikt nie zauważy")


def test_connective_moves_from_end_of_cue_to_following_fragment() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    original = result.transcript.segments[0]
    texts = (*("aa" for _ in range(6)), "i", *("aa" for _ in range(4)))
    words = tuple(
        original.words[0].model_copy(
            update={
                "word_id": f"word_connective_{index}",
                "text": text,
                "start_ms": 1000 + index * 500,
                "end_ms": 1400 + index * 500,
            }
        )
        for index, text in enumerate(texts)
    )
    segment = original.model_copy(
        update={
            "start_ms": words[0].start_ms,
            "end_ms": words[-1].end_ms,
            "text": " ".join(texts),
            "words": words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (segment,)})}
    )
    config = SubtitlesConfig(
        max_lines=1,
        max_chars_per_line=20,
        max_chars_per_second=100,
        speaker_labels="never",
    )

    cues = build_subtitle_cues(result, config)

    assert all(" ".join(cue.lines).split()[-1] != "i" for cue in cues[:-1])


def test_reported_na_line_ending_is_removed_by_neighboring_cue_boundary_search() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first_template = result.transcript.segments[0]
    texts = (
        "I",
        "w",
        "jaki",
        "sposób",
        "jednak",
        "te",
        "dane",
        "pozostają",
        "na",
        "profilach",
        "reklamowych,",
        "jeśli",
        "przedsiębiorstwo",
        "faktycznie",
        "usunęło",
        "nasze",
        "dane",
        "ze",
        "swoich",
        "zbiorów?",
    )
    starts = (
        96772,
        96952,
        97032,
        97252,
        97813,
        98233,
        98393,
        98713,
        99314,
        99514,
        100075,
        101015,
        101256,
        102337,
        103037,
        103538,
        103818,
        104098,
        104198,
        104518,
    )
    ends = (
        96912,
        96992,
        97212,
        97773,
        98153,
        98353,
        98673,
        99274,
        99454,
        100035,
        100975,
        101216,
        102276,
        102977,
        103498,
        103758,
        104058,
        104158,
        104498,
        105179,
    )
    words = tuple(
        first_template.words[0].model_copy(
            update={
                "word_id": f"word_reported_na_{index}",
                "text": text,
                "start_ms": start,
                "end_ms": end,
                "speaker_id": "speaker_001",
            }
        )
        for index, (text, start, end) in enumerate(zip(texts, starts, ends, strict=True))
    )
    segment = first_template.model_copy(
        update={
            "start_ms": starts[0],
            "end_ms": ends[-1],
            "text": " ".join(texts),
            "speaker_id": "speaker_001",
            "active_speaker_ids": ("speaker_001",),
            "words": words,
        }
    )
    result = result.model_copy(
        update={
            "transcript": result.transcript.model_copy(
                update={"segments": (first_template, segment)}
            )
        }
    )

    cues = build_subtitle_cues(result)
    reported_cues = [cue for cue in cues if cue.start_ms >= starts[0]]

    assert all(
        line.split()[-1].casefold() not in {"na", "to"}
        for cue in reported_cues
        for line in cue.lines
    )
    assert " ".join(" ".join(cue.lines) for cue in reported_cues).count("przedsiębiorstwo") == 1


def test_default_flexible_ceiling_keeps_reported_continuation_in_one_balanced_cue() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first_template = result.transcript.segments[0]
    texts = (
        "danych",
        "przez",
        "przedsiębiorstwo,",
        "to",
        "faktycznie",
        "w",
        "tym",
        "zbiorze",
        "może",
        "nie",
        "być",
        "usuniętych",
        "przez",
        "nas",
        "treści.",
    )
    words = tuple(
        first_template.words[0].model_copy(
            update={
                "word_id": f"word_flexible_ceiling_{index}",
                "text": text,
                "start_ms": 75976 + index * 360,
                "end_ms": 76256 + index * 360,
                "speaker_id": "speaker_001",
            }
        )
        for index, text in enumerate(texts)
    )
    segment = first_template.model_copy(
        update={
            "start_ms": words[0].start_ms,
            "end_ms": words[-1].end_ms,
            "text": " ".join(texts),
            "speaker_id": "speaker_001",
            "active_speaker_ids": ("speaker_001",),
            "words": words,
        }
    )
    result = result.model_copy(
        update={
            "transcript": result.transcript.model_copy(
                update={"segments": (first_template, segment)}
            )
        }
    )

    cues = build_subtitle_cues(result)
    reported_cues = [cue for cue in cues if cue.start_ms >= words[0].start_ms]

    assert len(reported_cues) == 1
    assert tuple(len(line) for line in reported_cues[0].lines) == (50, 49)


def test_one_line_cue_is_rebalanced_when_same_speaker_turn_continues() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    speaker_one_template, speaker_two = result.transcript.segments

    def segment_with_words(
        texts: tuple[str, ...], *, start_ms: int, word_prefix: str
    ) -> CanonicalSegment:
        words = tuple(
            speaker_one_template.words[0].model_copy(
                update={
                    "word_id": f"word_{word_prefix}_{index}",
                    "text": text,
                    "start_ms": start_ms + index * 420,
                    "end_ms": start_ms + index * 420 + 340,
                    "speaker_id": "speaker_001",
                }
            )
            for index, text in enumerate(texts)
        )
        return speaker_one_template.model_copy(
            update={
                "start_ms": words[0].start_ms,
                "end_ms": words[-1].end_ms,
                "text": " ".join(texts),
                "speaker_id": "speaker_001",
                "active_speaker_ids": ("speaker_001",),
                "words": words,
            }
        )

    opening = segment_with_words(
        ("Dodajmy", "tutaj", "doprecyzowanie."),
        start_ms=52603,
        word_prefix="turn_opening",
    )
    continuation = segment_with_words(
        (
            "W",
            "poprzednich",
            "odcinkach",
            "wspomnieliśmy,",
            "że",
            "kliknięcie",
            "Usuń",
            "tak",
            "naprawdę",
            "niczego",
            "nie",
            "usuwa.",
        ),
        start_ms=54584,
        word_prefix="turn_continuation",
    )
    result = result.model_copy(
        update={
            "transcript": result.transcript.model_copy(
                update={"segments": (speaker_two, opening, continuation)}
            )
        }
    )

    cues = build_subtitle_cues(result)
    speaker_one_cues = [cue for cue in cues if cue.speaker_id == "speaker_001"]

    assert len(speaker_one_cues) >= 2
    assert all(len(cue.lines) == 2 for cue in speaker_one_cues[:-1])


def test_invalid_rapid_micro_cues_do_not_outrank_valid_neighbor_boundaries() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    template = result.transcript.segments[0]
    texts = (
        "On",
        "ma",
        "być",
        "wystarczający,",
        "nie",
        "musi",
        "być",
        "idealny,",
        "chociaż",
        "zawsze",
        "mnie",
        "ciśnie,",
        "żeby",
        "wszystko",
        "dopięć",
        "na",
        "120%,",
        "bo",
        "nawet",
        "110%",
        "ma",
        "za",
        "mały",
        "margines",
        "błędu.",
    )
    starts = (
        487125,
        487245,
        487385,
        487665,
        488627,
        488747,
        488967,
        489168,
        490269,
        490750,
        491050,
        491311,
        491972,
        492192,
        492532,
        492913,
        493013,
        493193,
        493253,
        493414,
        493574,
        493674,
        493854,
        494435,
        494655,
    )
    ends = (
        487205,
        487345,
        487605,
        488587,
        488707,
        488947,
        489127,
        490249,
        490690,
        491030,
        491230,
        491931,
        492172,
        492492,
        492873,
        492993,
        493173,
        493233,
        493394,
        493554,
        493634,
        493754,
        494415,
        494615,
        494796,
    )
    words = tuple(
        template.words[0].model_copy(
            update={
                "word_id": f"word_rapid_{index}",
                "text": text,
                "start_ms": start,
                "end_ms": end,
            }
        )
        for index, (text, start, end) in enumerate(zip(texts, starts, ends, strict=True))
    )
    segment = template.model_copy(
        update={
            "start_ms": words[0].start_ms,
            "end_ms": words[-1].end_ms,
            "text": " ".join(texts),
            "words": words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (segment,)})}
    )

    cues = build_subtitle_cues(result)

    durations = [cue.end_ms - cue.start_ms for cue in cues]
    assert all(duration >= 1000 for duration in durations), durations
    assert all(len(" ".join(cue.lines).removeprefix("jan: ").split()) >= 4 for cue in cues)
    assert all(len(cue.lines) == 2 for cue in cues)
    assert " ".join(" ".join(cue.lines) for cue in cues).count("błędu.") == 1


def test_short_first_word_in_overlap_segment_does_not_become_its_own_cue() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    template = result.transcript.segments[0]
    texts = ("Nie", "zapomnijcie", "też", "o", "udostępnieniu", "odcinka.")
    starts = (2070342, 2070462, 2071003, 2071303, 2071443, 2072104)
    ends = (2070442, 2070963, 2071223, 2071383, 2072064, 2073005)
    words = tuple(
        template.words[0].model_copy(
            update={
                "word_id": f"word_overlap_{index}",
                "text": text,
                "start_ms": start,
                "end_ms": end,
            }
        )
        for index, (text, start, end) in enumerate(zip(texts, starts, ends, strict=True))
    )
    segment = template.model_copy(
        update={
            "start_ms": words[0].start_ms,
            "end_ms": words[-1].end_ms,
            "text": " ".join(texts),
            "overlap": True,
            "active_speaker_ids": ("speaker_001", "speaker_002"),
            "words": words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (segment,)})}
    )

    cues = build_subtitle_cues(result)

    assert len(cues) == 1
    assert " ".join(cues[0].lines) == "jan: Nie zapomnijcie też o udostępnieniu odcinka."
    assert cues[0].start_ms == 2070342
    assert cues[0].end_ms == 2073005


def test_chunking_uses_real_wrapping_limit_not_only_total_capacity() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    original = result.transcript.segments[0]
    texts = ("a" * 30, "b" * 30, "c" * 30)
    words = tuple(
        original.words[0].model_copy(
            update={
                "word_id": f"word_test_{index}",
                "text": text,
                "start_ms": 1000 + index * 2000,
                "end_ms": 3000 + index * 2000,
            }
        )
        for index, text in enumerate(texts)
    )
    segment = original.model_copy(
        update={
            "start_ms": 1000,
            "end_ms": 7000,
            "text": " ".join(texts),
            "words": words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (segment,)})}
    )

    cues = build_subtitle_cues(result)

    assert len(cues) == 2
    assert tuple(line for cue in cues for line in cue.lines) == (
        f"jan: {texts[0]}",
        texts[1],
        texts[2],
    )
    assert all(len(cue.lines) <= 2 for cue in cues)
    assert all(len(line) <= 50 for cue in cues for line in cue.lines)


def test_serializers_reject_accidental_overlap_but_allow_explicit_overlap() -> None:
    ordinary = (
        SubtitleCue(1000, 2000, ("First",), "speaker_001"),
        SubtitleCue(1900, 2500, ("Second",), "speaker_002"),
    )

    with pytest.raises(ValueError, match="must not overlap"):
        render_srt(ordinary)

    explicit = (
        ordinary[0],
        SubtitleCue(1900, 2500, ("Second",), "speaker_002", overlap=True),
    )
    assert "Second" in render_vtt(explicit)


def test_overlapping_speaker_chunks_are_globally_sorted_before_labelling() -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first, second = result.transcript.segments
    late_word = first.words[-1].model_copy(
        update={
            "word_id": "word_late",
            "text": "Continuation.",
            "start_ms": 5000,
            "end_ms": 6000,
        }
    )
    first = first.model_copy(
        update={
            "end_ms": 6000,
            "text": f"{first.text} Continuation.",
            "overlap": True,
            "active_speaker_ids": ("speaker_001", "speaker_002"),
            "words": (*first.words, late_word),
        }
    )
    second_words = tuple(
        word.model_copy(update={"start_ms": 4200 + index * 100, "end_ms": 4280 + index * 100})
        for index, word in enumerate(second.words)
    )
    second = second.model_copy(
        update={
            "start_ms": 4200,
            "end_ms": 5000,
            "overlap": True,
            "active_speaker_ids": ("speaker_001", "speaker_002"),
            "words": second_words,
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (first, second)})}
    )

    cues = build_subtitle_cues(result, SubtitlesConfig(max_duration_ms=3000))

    assert [cue.start_ms for cue in cues] == sorted(cue.start_ms for cue in cues)
    speaker_ids = [cue.speaker_id for cue in cues]
    first_second = speaker_ids.index("speaker_002")
    return_to_first = speaker_ids.index("speaker_001", first_second)
    assert cues[0].lines[0].startswith("jan:")
    assert cues[first_second].lines[0].startswith("anna:")
    assert cues[return_to_first].lines[0].startswith("jan:")
    assert "Continuation" in render_srt(cues)


def test_final_repartition_pass_cannot_leave_overlap_cues_out_of_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = load_canonical_result(EXAMPLE_PATH)
    first, second = result.transcript.segments
    first = first.model_copy(
        update={
            "overlap": True,
            "active_speaker_ids": ("speaker_001", "speaker_002"),
        }
    )
    second = second.model_copy(
        update={
            "overlap": True,
            "active_speaker_ids": ("speaker_001", "speaker_002"),
        }
    )
    result = result.model_copy(
        update={"transcript": result.transcript.model_copy(update={"segments": (first, second)})}
    )
    stabilize = subtitle_exporter._stabilize_drafts

    def return_postprocessed_out_of_order(*args, **kwargs):
        return list(reversed(stabilize(*args, **kwargs)))

    monkeypatch.setattr(
        subtitle_exporter,
        "_stabilize_drafts",
        return_postprocessed_out_of_order,
    )

    cues = build_subtitle_cues(result)

    assert [cue.start_ms for cue in cues] == sorted(cue.start_ms for cue in cues)
    assert all(cue.overlap for cue in cues)
    assert "Welcome" in render_srt(cues)
    assert "Today" in render_vtt(cues)


def test_same_speaker_provider_word_overlap_stays_inside_cue_without_timestamp_changes():
    base = load_canonical_result(EXAMPLE_PATH)
    original = base.transcript.segments[0]
    from ewp_transcripts.domain.canonical import CanonicalWord

    words = tuple(
        CanonicalWord(
            word_id=f"word_{index:06d}",
            text=text,
            start_ms=start,
            end_ms=end,
            speaker_id=original.speaker_id,
            timestamp_source="aligned",
        )
        for index, (text, start, end) in enumerate(
            [
                ("Alpha", 0, 1000),
                ("beta.", 900, 1800),
                ("Gamma", 1900, 2800),
                ("delta.", 2900, 3800),
            ],
            1,
        )
    )
    segments = tuple(
        original.model_copy(
            update={
                "segment_id": f"seg_{index:06d}",
                "text": word.text,
                "start_ms": word.start_ms,
                "end_ms": word.end_ms,
                "words": (word,),
            }
        )
        for index, word in enumerate(words, 1)
    )
    result = base.model_copy(
        update={"transcript": base.transcript.model_copy(update={"segments": segments})}
    )
    before = result.model_dump_json()
    cues = build_subtitle_cues(
        result,
        SubtitlesConfig(
            max_lines=1, max_chars_per_line=14, min_words_per_cue=2, speaker_labels="never"
        ),
    )
    assert len(cues) >= 2
    assert all(a.end_ms <= b.start_ms for a, b in zip(cues, cues[1:], strict=False))
    assert "Alpha beta." in render_srt(cues)
    assert result.model_dump_json() == before
