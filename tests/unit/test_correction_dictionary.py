"""Tests for project correction dictionary proposal extraction."""

import hashlib
import json
from pathlib import Path

import pytest

from ewp_transcripts.correction_dictionary import (
    CorrectionDictionaryManualConvention,
    ProjectCorrectionDictionary,
    _strip_boundary_punctuation,
    approve_correction_dictionary,
    load_project_correction_dictionary,
    propose_correction_dictionary,
    select_correction_dictionary_terms,
    write_correction_dictionary_proposal,
)
from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.review import ReviewSpeakerBlock
from ewp_transcripts.review_service import prepare_review
from ewp_transcripts.revision_service import build_revision

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/results.example.json"
PROJECT_DICTIONARY = (
    ROOT / "dictionaries/ethics-in-the-loop/correction/pl/ethics-in-the-loop-pl-v1.json"
)


def test_proposal_extracts_consistent_manual_lexical_mapping(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    revisions = tmp_path / "revisions"
    canonical.mkdir()
    revisions.mkdir()
    result_path = canonical / "case_results.json"
    result_path.write_bytes(EXAMPLE.read_bytes())
    review = prepare_review(result_path)
    blocks = list(review.anchors[0].speaker_blocks)
    blocks[0] = ReviewSpeakerBlock(
        speaker_id=blocks[0].speaker_id,
        text=blocks[0].text.replace("Welcome", "Greetings"),
    )
    edited = review.model_copy(
        update={
            "anchors": (review.anchors[0].model_copy(update={"speaker_blocks": tuple(blocks)}),)
        }
    )
    revision = build_revision(edited, load_canonical_result(result_path), base_path=result_path)
    (revisions / "S01E01_revision_001.json").write_text(
        revision.model_dump_json(), encoding="utf-8"
    )

    proposal = propose_correction_dictionary(
        canonical_directory=canonical,
        revision_directory=revisions,
        project_id="example",
        minimum_occurrences=1,
    )

    assert proposal.case_count == 1
    assert [(item.source, item.target, item.status) for item in proposal.candidates] == [
        ("Welcome", "Greetings", "pending")
    ]
    assert "[[Welcome]]" in proposal.candidates[0].evidence[0].source_context
    assert "[[Greetings]]" in proposal.candidates[0].evidence[0].target_context

    proposal_path = tmp_path / "proposal.json"
    write_correction_dictionary_proposal(proposal, proposal_path)
    with pytest.raises(ValueError, match="pending candidates"):
        approve_correction_dictionary(
            proposal_path=proposal_path,
            dictionary_id="example-pl-v1",
            output_path=tmp_path / "dictionary.json",
        )

    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["candidates"][0]["status"] = "approved"
    proposal_path.write_text(json.dumps(payload), encoding="utf-8")
    dictionary = approve_correction_dictionary(
        proposal_path=proposal_path,
        dictionary_id="example-pl-v1",
        output_path=tmp_path / "dictionary.json",
    )

    assert dictionary.project_id == "example"
    assert [(item.source, item.target) for item in dictionary.entries] == [("Welcome", "Greetings")]
    selected = select_correction_dictionary_terms(dictionary, "Welcome everyone")
    assert [(item.source, item.target) for item in selected] == [("Welcome", "Greetings")]
    assert select_correction_dictionary_terms(dictionary, "A welcoming message") == ()

    carried = propose_correction_dictionary(
        canonical_directory=canonical,
        revision_directory=revisions,
        project_id="example",
        minimum_occurrences=1,
        previous_dictionary=dictionary,
        previous_dictionary_sha256="c" * 64,
    )
    assert carried.previous_dictionary_sha256 == "c" * 64
    assert carried.candidates[0].status == "approved"

    manual_dictionary = dictionary.model_copy(
        update={
            "manual_conventions": (
                CorrectionDictionaryManualConvention(
                    source="Project title",
                    target="Project Title",
                    rationale="Stable project convention.",
                ),
            )
        }
    )
    carried_manual = propose_correction_dictionary(
        canonical_directory=canonical,
        revision_directory=revisions,
        project_id="example",
        minimum_occurrences=1,
        previous_dictionary=manual_dictionary,
        previous_dictionary_sha256="d" * 64,
    )
    assert carried_manual.manual_conventions == manual_dictionary.manual_conventions

    rejected_payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    rejected_payload["candidates"][0]["status"] = "rejected"
    rejected_path = tmp_path / "rejected-proposal.json"
    rejected_path.write_text(json.dumps(rejected_payload), encoding="utf-8")
    rejected_dictionary = approve_correction_dictionary(
        proposal_path=rejected_path,
        dictionary_id="example-pl-v2",
        output_path=tmp_path / "rejected-dictionary.json",
    )
    assert rejected_dictionary.entries[0].status == "rejected"
    assert select_correction_dictionary_terms(rejected_dictionary, "Welcome everyone") == ()


def test_dictionary_keys_discard_boundary_quotes_and_punctuation() -> None:
    assert _strip_boundary_punctuation("Anthropic,") == "Anthropic"
    assert _strip_boundary_punctuation('"akceptuję",') == "akceptuję"
    assert _strip_boundary_punctuation("etykawpetli.pl") == "etykawpetli.pl"


def test_manual_project_conventions_are_auditable_and_source_bound() -> None:
    dictionary = ProjectCorrectionDictionary(
        dictionary_id="example-pl-v2",
        project_id="example",
        job_ids=("case",),
        proposal_sha256="a" * 64,
        entries=(
            {
                "source": "podcastu",
                "target": "podkastu",
                "status": "approved",
            },
        ),
        manual_conventions=(
            CorrectionDictionaryManualConvention(
                source="Etyka w pętli",
                target='"Etyka w Pętli"',
                rationale="Project-owned podcast title capitalization and quotation convention.",
            ),
        ),
    )

    assert [
        (term.source, term.target)
        for term in select_correction_dictionary_terms(dictionary, "Witamy w Etyka w pętli.")
    ] == [("Etyka w pętli", '"Etyka w Pętli"')]
    assert select_correction_dictionary_terms(dictionary, "Niepowiązany tekst") == ()


def test_published_project_dictionary_retains_exact_review_lineage() -> None:
    dictionary, digest = load_project_correction_dictionary(PROJECT_DICTIONARY)
    proposal = PROJECT_DICTIONARY.with_name("ethics-in-the-loop-pl-v1.proposal.json")

    assert digest == "5d1bb1c57ac60930d81bf7120f8eed0df4369b0cb21fdaac5927d13d954b15db"
    assert dictionary.proposal_sha256 == hashlib.sha256(proposal.read_bytes()).hexdigest()
    assert sum(item.status == "approved" for item in dictionary.entries) == 19
    assert sum(item.status == "rejected" for item in dictionary.entries) == 22
