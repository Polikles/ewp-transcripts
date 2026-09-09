"""Validate the implemented v0.2.0 revision contract artifacts."""

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/revision.schema.json"
EXAMPLE_PATH = ROOT / "examples/revision.example.json"
REVIEW_PATH = ROOT / "examples/review.example.txt"

REQUIRED_REVIEW_HEADERS = {
    "job_id",
    "base_result_file",
    "base_result_sha256",
    "base_result_schema_version",
    "base_result_version",
    "language",
    "generated_at",
    "application_version",
}
HEADER_PATTERN = re.compile(r"^# ([a-z0-9_]+): (.+)$")
ANCHOR_PATTERN = re.compile(r"^@@ anchor word_\d{6,}\.\.word_\d{6,}$")
SPEAKER_PATTERN = re.compile(r"^@@ speaker speaker_\d{3,}$")


def test_revision_schema_is_valid_draft_2020_12() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)


def test_revision_example_matches_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    ).validate(example)


def test_revision_schema_accepts_revision_scoped_speaker_labels() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    example["transcript"]["speaker_labels"] = {"speaker_001": "Szymon"}

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)


def test_review_example_contains_required_contract_structure() -> None:
    lines = REVIEW_PATH.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# EWP-REVIEW 1"

    header_end = lines.index("")
    headers = {
        match.group(1)
        for line in lines[1:header_end]
        if (match := HEADER_PATTERN.fullmatch(line)) is not None
    }
    body = lines[header_end + 1 :]

    assert headers == REQUIRED_REVIEW_HEADERS
    assert any(ANCHOR_PATTERN.fullmatch(line) for line in body)
    assert any(SPEAKER_PATTERN.fullmatch(line) for line in body)
