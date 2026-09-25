"""Tests for manual translation preview construction."""

from pathlib import Path

import pytest

from ewp_transcripts.domain.errors import InvalidTranslationError
from ewp_transcripts.translation_review_service import prepare_translation_review
from ewp_transcripts.translation_service import build_manual_translation

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "examples/results.example.json"


def test_complete_review_builds_manual_snapshot() -> None:
    prepared = prepare_translation_review(RESULT, target_language="pl")
    units = tuple(
        unit.model_copy(update={"target_text": f"Tłumaczenie {index}."})
        for index, unit in enumerate(prepared.units, start=1)
    )

    translation = build_manual_translation(prepared.model_copy(update={"units": units}))

    assert translation.provenance.method == "manual"
    assert translation.direction.source_language == "en"
    assert translation.direction.target_language == "pl"
    assert translation.statistics.unit_count == len(units)
    assert translation.statistics.source_tokens == 8
    assert translation.parent_translation is None


def test_blank_target_fails_preview() -> None:
    prepared = prepare_translation_review(RESULT, target_language="pl")

    with pytest.raises(InvalidTranslationError, match="untranslated unit"):
        build_manual_translation(prepared)


def test_explicit_empty_target_builds_a_versioned_omission() -> None:
    prepared = prepare_translation_review(RESULT, target_language="pl")
    units = tuple(
        unit.model_copy(update={"target_text": "" if index == 0 else "Przetłumaczone."})
        for index, unit in enumerate(prepared.units)
    )

    translation = build_manual_translation(
        prepared.model_copy(update={"units": units}), allow_empty_units=True
    )

    assert translation.schema_version == "1.1"
    assert translation.units[0].target_status == "intentionally_empty"
    assert translation.statistics.intentionally_empty_units == 1
