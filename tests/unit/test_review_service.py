"""Tests for model-free review preparation from canonical results."""

import json
from datetime import UTC, datetime
from pathlib import Path

from ewp_transcripts.application import preview_review_file
from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.review import validate_review_base
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.review_format import parse_review, render_review
from ewp_transcripts.review_service import prepare_review
from ewp_transcripts.revision_service import build_revision

ROOT = Path(__file__).resolve().parents[2]
RESULT_EXAMPLE = ROOT / "examples/results.example.json"
NOW = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)


def test_prepare_review_covers_base_and_preserves_speaker_turns() -> None:
    review = prepare_review(RESULT_EXAMPLE, generated_at=NOW, application_version="0.2.0")
    base = load_canonical_result(RESULT_EXAMPLE)

    validate_review_base(review, base, base_sha256=sha256_file(RESULT_EXAMPLE))
    assert review.header.base_result_file == RESULT_EXAMPLE.name
    assert review.anchors[0].first_word_id == "word_000001"
    assert review.anchors[-1].last_word_id == "word_000008"
    assert [block.speaker_id for block in review.anchors[0].speaker_blocks] == [
        "speaker_001",
        "speaker_002",
    ]


def test_small_anchor_target_splits_only_at_segment_boundaries() -> None:
    review = prepare_review(
        RESULT_EXAMPLE,
        anchor_target_words=4,
        anchor_target_speaker_blocks=None,
        generated_at=NOW,
    )

    assert [(anchor.first_word_id, anchor.last_word_id) for anchor in review.anchors] == [
        ("word_000001", "word_000004"),
        ("word_000005", "word_000008"),
    ]


def test_default_review_groups_five_speaker_blocks_per_section(tmp_path: Path) -> None:
    document = json.loads(RESULT_EXAMPLE.read_text(encoding="utf-8"))
    words = [word for segment in document["transcript"]["segments"] for word in segment["words"]]
    for index, word in enumerate(words):
        word["speaker_id"] = "speaker_001" if index % 2 == 0 else "speaker_002"
    result = tmp_path / RESULT_EXAMPLE.name
    result.write_text(json.dumps(document), encoding="utf-8")

    review = prepare_review(result, generated_at=NOW)

    assert [len(anchor.speaker_blocks) for anchor in review.anchors] == [5, 3]


def test_prepared_review_round_trips_without_changing_canonical_file() -> None:
    before = RESULT_EXAMPLE.read_bytes()
    review = prepare_review(RESULT_EXAMPLE, generated_at=NOW)

    reparsed = parse_review(render_review(review))

    assert reparsed == review
    assert RESULT_EXAMPLE.read_bytes() == before


def test_prepare_review_prefills_exact_revision_and_records_parent(tmp_path: Path) -> None:
    base_path = tmp_path / RESULT_EXAMPLE.name
    base_path.write_bytes(RESULT_EXAMPLE.read_bytes())
    base = load_canonical_result(base_path)
    original = prepare_review(base_path, generated_at=NOW)
    revision = build_revision(original, base, base_path=base_path, created_at=NOW)
    revision_path = tmp_path / "S01E01_revision_001.json"
    revision_path.write_text(revision.model_dump_json(indent=2) + "\n", encoding="utf-8")

    review = prepare_review(
        base_path,
        source_revision_path=revision_path,
        generated_at=NOW,
    )

    assert review.header.source_revision_id is not None
    assert review.header.source_revision_number == 1
    assert review.header.source_revision_sha256 == sha256_file(revision_path)
    assert review.header.extensions[0].value == "manually_verified"
    rendered = render_review(review)
    assert "Today we discuss transcription." in rendered
    review_path = tmp_path / "S01E01.review.txt"
    review_path.write_text(rendered, encoding="utf-8")

    preview = preview_review_file(
        review_path,
        results_directory=tmp_path,
        revisions_directory=tmp_path,
    )

    assert preview.revision.parent_revision is not None
    assert preview.revision.parent_revision.sha256 == sha256_file(revision_path)
