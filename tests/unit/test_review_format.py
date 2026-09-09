"""Contract tests for parsing and rendering ``EWP-REVIEW 1`` files."""

import hashlib
from pathlib import Path

import pytest

from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.errors import InvalidReviewError
from ewp_transcripts.domain.review import validate_review_base
from ewp_transcripts.review_format import load_review, parse_review, render_review

ROOT = Path(__file__).resolve().parents[2]
REVIEW_EXAMPLE = ROOT / "examples/review.example.txt"
RESULT_EXAMPLE = ROOT / "examples/results.example.json"


def _review_text() -> str:
    return REVIEW_EXAMPLE.read_text(encoding="utf-8")


def _complete_base_review_text() -> str:
    base_sha256 = hashlib.sha256(RESULT_EXAMPLE.read_bytes()).hexdigest()
    return f"""# EWP-REVIEW 1
# job_id: S01E01
# base_result_file: results.example.json
# base_result_sha256: {base_sha256}
# base_result_schema_version: 1.0
# base_result_version: 1
# language: en
# generated_at: 2026-08-14T14:00:00Z
# application_version: 0.2.0

@@ anchor word_000001..word_000004
@@ speaker speaker_001

Pierwszy blok.

@@ speaker speaker_002
Drugi blok.

@@ anchor word_000005..word_000008
@@ speaker speaker_002
Ostatni blok.
"""


def _out_of_order_review_text() -> str:
    return (
        _complete_base_review_text()
        .replace("@@ anchor word_000001..word_000004", "@@ anchor temporary", 1)
        .replace(
            "@@ anchor word_000005..word_000008",
            "@@ anchor word_000001..word_000004",
            1,
        )
        .replace("@@ anchor temporary", "@@ anchor word_000005..word_000008", 1)
    )


def test_example_parses_and_round_trips_deterministically() -> None:
    review = load_review(REVIEW_EXAMPLE)
    rendered = render_review(review)

    assert parse_review(rendered) == review
    assert rendered.endswith("\n")
    assert "\r" not in rendered


def test_parser_accepts_crlf_and_normalizes_editable_whitespace() -> None:
    text = _review_text().replace("Rozmawiamy o OpenAI.", "Rozmawiamy\r\n   o   OpenAI.")

    review = parse_review(text.replace("\n", "\r\n"))

    assert review.anchors[0].speaker_blocks[0].text == "Rozmawiamy o OpenAI."


def test_literal_directive_prefix_is_unescaped_and_reescaped() -> None:
    text = _review_text().replace("Rozmawiamy o OpenAI.", "@@@ literal directive-like text")

    review = parse_review(text)

    assert review.anchors[0].speaker_blocks[0].text == "@@ literal directive-like text"
    assert "@@@ literal directive-like text" in render_review(review)


def test_revision_scoped_speaker_labels_round_trip() -> None:
    text = _review_text().replace(
        "# application_version: 0.2.0",
        '# application_version: 0.2.0\n# speaker_labels: {"speaker_001":"Szymon"}',
    )

    review = parse_review(text)

    assert review.header.speaker_labels == {"speaker_001": "Szymon"}
    assert '# speaker_labels: {"speaker_001":"Szymon"}' in render_review(review)


@pytest.mark.parametrize(
    ("old", "new", "code"),
    [
        (
            "@@ anchor word_000001..word_000006",
            "@@ anchor word_1..word_6",
            "REVISION_ANCHOR_INVALID",
        ),
        ("@@ speaker speaker_001", "@@ speaker Damian", "REVISION_SPEAKER_INVALID"),
    ],
)
def test_malformed_known_directive_has_specific_code(old: str, new: str, code: str) -> None:
    with pytest.raises(InvalidReviewError) as captured:
        parse_review(_review_text().replace(old, new, 1))

    assert captured.value.code == code


def test_text_before_speaker_reports_the_exact_review_line() -> None:
    text = _complete_base_review_text().replace("@@ speaker speaker_001\n", "", 1)
    expected_line = text.splitlines().index("Pierwszy blok.") + 1

    with pytest.raises(
        InvalidReviewError,
        match=rf"Transcript text appears before a speaker directive at line {expected_line}$",
    ):
        parse_review(text)


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("# EWP-REVIEW 2", "must begin"),
        ("# job: revision-example", "Unknown review header"),
        ("# base_result_version: zero", "positive integer"),
        ("@@ typo word_000001", "Unknown review directive"),
    ],
)
def test_malformed_review_is_rejected(replacement: str, message: str) -> None:
    text = _review_text()
    if replacement.startswith("# EWP"):
        text = text.replace("# EWP-REVIEW 1", replacement)
    elif replacement.startswith("# job:"):
        text = text.replace("# job_id: revision-example", replacement)
    elif replacement.startswith("# base_result_version"):
        text = text.replace("# base_result_version: 1", replacement)
    else:
        text = text.replace("@@ anchor word_000001..word_000006", replacement)

    with pytest.raises(InvalidReviewError, match=message):
        parse_review(text)


def test_unknown_extension_header_is_preserved_in_sorted_order() -> None:
    text = _review_text().replace(
        "# application_version: 0.2.0",
        "# application_version: 0.2.0\n# x_zeta: z\n# x_alpha: a",
    )

    rendered = render_review(parse_review(text))

    assert rendered.index("# x_alpha: a") < rendered.index("# x_zeta: z")


def test_complete_review_validates_against_exact_canonical_base() -> None:
    review = parse_review(_complete_base_review_text())
    base = load_canonical_result(RESULT_EXAMPLE)

    validate_review_base(
        review,
        base,
        base_sha256=hashlib.sha256(RESULT_EXAMPLE.read_bytes()).hexdigest(),
    )


@pytest.mark.parametrize(
    ("old", "new", "code"),
    [
        ("word_000008", "word_999999", "REVISION_SOURCE_WORD_MISSING"),
        ("word_000005..word_000008", "word_000006..word_000008", "REVISION_ANCHOR_INVALID"),
        ("speaker_002", "speaker_999", "REVISION_SPEAKER_INVALID"),
    ],
)
def test_base_validation_returns_stable_failure_code(old: str, new: str, code: str) -> None:
    text = _complete_base_review_text().replace(old, new, 1)
    review = parse_review(text)
    base = load_canonical_result(RESULT_EXAMPLE)

    with pytest.raises(InvalidReviewError) as captured:
        validate_review_base(
            review,
            base,
            base_sha256=hashlib.sha256(RESULT_EXAMPLE.read_bytes()).hexdigest(),
        )

    assert captured.value.code == code


def test_base_hash_mismatch_returns_stable_failure_code() -> None:
    expected_hash = hashlib.sha256(RESULT_EXAMPLE.read_bytes()).hexdigest()
    review = parse_review(_complete_base_review_text().replace(expected_hash, "f" * 64))
    base = load_canonical_result(RESULT_EXAMPLE)

    with pytest.raises(InvalidReviewError) as captured:
        validate_review_base(review, base, base_sha256=expected_hash)

    assert captured.value.code == "REVISION_BASE_HASH_MISMATCH"


@pytest.mark.parametrize(
    "text",
    [
        _complete_base_review_text().split("@@ anchor word_000005", 1)[0],
        _complete_base_review_text().replace(
            "@@ anchor word_000005..word_000008",
            "@@ anchor word_000001..word_000004",
        ),
        _out_of_order_review_text(),
    ],
    ids=("missing", "duplicate", "out-of-order"),
)
def test_missing_duplicate_or_out_of_order_anchor_is_rejected(text: str) -> None:
    review = parse_review(text)
    base = load_canonical_result(RESULT_EXAMPLE)

    with pytest.raises(InvalidReviewError) as captured:
        validate_review_base(
            review,
            base,
            base_sha256=hashlib.sha256(RESULT_EXAMPLE.read_bytes()).hexdigest(),
        )

    assert captured.value.code == "REVISION_ANCHOR_INVALID"
