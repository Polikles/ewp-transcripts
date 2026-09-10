"""Tests for provider-neutral automated translation."""

from pathlib import Path

import pytest

from ewp_transcripts.automated_translation import (
    DeterministicMockTranslationProvider,
    build_automated_translation,
    build_automated_translation_request,
    validate_automated_translation_response,
)
from ewp_transcripts.domain.automated_translation import AutomatedTranslationResponse
from ewp_transcripts.domain.errors import InvalidTranslationResponseError
from ewp_transcripts.translation_dictionary import (
    ProjectTranslationDictionary,
    TranslationDictionaryEntry,
    load_project_translation_dictionary,
)
from ewp_transcripts.translation_review_service import prepare_translation_review

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/results.example.json"
PROJECT_TRANSLATION_V2 = (
    ROOT
    / "dictionaries/ethics-in-the-loop/translation/pl-en/ethics-in-the-loop-pl-en-v2.json"
)


def test_request_owns_one_unit_and_context_is_read_only() -> None:
    review = prepare_translation_review(EXAMPLE, target_language="pl")
    provider = DeterministicMockTranslationProvider()

    request = build_automated_translation_request(review, 1, provider=provider, context_units=1)

    assert request.unit.unit_id == review.units[1].unit_id
    assert tuple(unit.unit_id for unit in request.preceding_context) == (review.units[0].unit_id,)
    assert request.following_context == ()
    assert len(request.operation_id) == 64


def test_request_includes_only_dictionary_terms_present_in_owned_unit() -> None:
    review = prepare_translation_review(EXAMPLE, target_language="pl")
    dictionary = ProjectTranslationDictionary(
        dictionary_id="example",
        project_id="example",
        job_ids=("S01E01",),
        source_language="en",
        target_language="pl",
        entries=(
            TranslationDictionaryEntry(source="Welcome", target="Witamy"),
            TranslationDictionaryEntry(source="come", target="przyjść"),
            TranslationDictionaryEntry(source="Unrelated", target="Niepowiązane"),
        ),
    )

    request = build_automated_translation_request(
        review,
        0,
        provider=DeterministicMockTranslationProvider(),
        dictionary=dictionary,
        dictionary_sha256="a" * 64,
    )

    assert [(term.source, term.target) for term in request.dictionary_terms] == [
        ("Welcome", "Witamy")
    ]


def test_project_wide_dictionary_applies_to_future_job_ids() -> None:
    dictionary = ProjectTranslationDictionary(
        dictionary_id="example-project",
        project_id="example",
        job_ids=("*",),
        source_language="en",
        target_language="pl",
        entries=(TranslationDictionaryEntry(source="Welcome", target="Witamy"),),
    )

    assert dictionary.applies_to("future-episode") is True


def test_project_translation_v2_preserves_english_site_convention() -> None:
    dictionary, _digest = load_project_translation_dictionary(PROJECT_TRANSLATION_V2)

    assert dictionary.dictionary_id == "ethics-in-the-loop-pl-en-v2"
    assert dictionary.applies_to("future-episode") is True
    assert {
        entry.source: entry.target
        for entry in dictionary.entries
        if entry.source in {"etykawpetli.pl", "etykawpętli.pl"}
    } == {
        "etykawpetli.pl": "ethicsintheloop.eu",
        "etykawpętli.pl": "ethicsintheloop.eu",
    }


def test_project_wide_dictionary_rejects_mixed_wildcard_scope() -> None:
    with pytest.raises(ValueError, match="project-wide"):
        ProjectTranslationDictionary(
            dictionary_id="example-project",
            project_id="example",
            job_ids=("*", "S01E01"),
            source_language="en",
            target_language="pl",
            entries=(TranslationDictionaryEntry(source="Welcome", target="Witamy"),),
        )


def test_response_must_match_operation_and_owned_unit() -> None:
    review = prepare_translation_review(EXAMPLE, target_language="pl")
    provider = DeterministicMockTranslationProvider()
    request = build_automated_translation_request(review, 0, provider=provider)

    with pytest.raises(InvalidTranslationResponseError, match="operation ID"):
        validate_automated_translation_response(
            request,
            AutomatedTranslationResponse(
                operation_id="0" * 64,
                unit_id=request.unit.unit_id,
                target_text="Translated.",
            ),
        )


def test_builds_non_final_llm_candidate_with_exact_unit_lineage(tmp_path: Path) -> None:
    provider = DeterministicMockTranslationProvider(
        {"tu_000001": "Welcome to another episode.", "tu_000002": "Transcription today."}
    )

    translation = build_automated_translation(
        EXAMPLE,
        provider,
        target_language="pl",
        resume_directory=tmp_path / "state",
    )
    repeated = build_automated_translation(
        EXAMPLE,
        provider,
        target_language="pl",
        resume_directory=tmp_path / "state",
    )

    assert translation.provenance.method == "llm"
    assert translation.provenance.llm is not None
    assert translation.provenance.llm.provider == "ewp-mock-translation"
    assert translation.provenance.llm.parameters is not None
    assert (
        translation.provenance.llm.parameters["dictionary_selection_contract"]
        == "owned-source-unicode-phrase-v2"
    )
    assert translation.source.verification == "raw"
    assert [unit.target_text for unit in translation.units] == [
        "Welcome to another episode.",
        "Transcription today.",
    ]
    assert [unit.source_token_ids for unit in repeated.units] == [
        unit.source_token_ids for unit in translation.units
    ]
    assert len(tuple((tmp_path / "state").glob("*.json"))) == 2


def test_provider_warning_is_preserved_without_note_content() -> None:
    class NotesProvider(DeterministicMockTranslationProvider):
        def translate(self, request, *, timeout_seconds=None):  # type: ignore[no-untyped-def]
            response = super().translate(request, timeout_seconds=timeout_seconds)
            return response.model_copy(
                update={"warning_codes": ("PROVIDER_TRANSLATOR_NOTES_DISCARDED",)}
            )

    translation = build_automated_translation(EXAMPLE, NotesProvider(), target_language="pl")

    assert translation.statistics.warning_count == len(translation.units)
    assert all(
        warning.code == "PROVIDER_TRANSLATOR_NOTES_DISCARDED" for warning in translation.warnings
    )
    assert "Unsolicited" not in translation.model_dump_json()
