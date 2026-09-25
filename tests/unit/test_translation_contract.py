"""Validate the translation schema and public example artifact."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from ewp_transcripts.domain.translation import TranscriptTranslation

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/translation.schema.json"
EXAMPLE_PATH = ROOT / "examples/translation.example.json"


def test_translation_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_translation_example_matches_schema_and_domain_model() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    serialized = EXAMPLE_PATH.read_text(encoding="utf-8")
    example = json.loads(serialized)

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
    translation = TranscriptTranslation.model_validate_json(serialized)

    assert translation.direction.source_language == "en"
    assert translation.direction.target_language == "pl"
    assert translation.source.verification == "raw"
    assert translation.statistics.unit_count == 2


def test_translation_schema_11_requires_explicit_empty_unit_status() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    document["units"][0]["target_text"] = ""
    document["units"][0]["target_status"] = "intentionally_empty"
    document["statistics"]["target_tokens"] = 4
    document["statistics"]["intentionally_empty_units"] = 1
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    validator.validate(document)
    del document["units"][0]["target_status"]

    with pytest.raises(ValidationError):
        validator.validate(document)


def test_legacy_translation_schema_10_remains_readable() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    document["schema_version"] = "1.0"
    for unit in document["units"]:
        del unit["target_status"]
    del document["statistics"]["intentionally_empty_units"]

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    translation = TranscriptTranslation.model_validate_json(json.dumps(document))

    assert all(unit.target_status == "translated" for unit in translation.units)
