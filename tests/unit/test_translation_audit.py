"""Tests for exact-source translation audit reconstruction."""

from pathlib import Path

from ewp_transcripts.translation_audit import (
    build_translation_audit,
    publish_translation_audit,
)

ROOT = Path(__file__).resolve().parents[2]
TRANSLATION = ROOT / "examples/translation.example.json"


def test_translation_audit_reconstructs_source_and_publishes_idempotently(
    tmp_path: Path,
) -> None:
    audit = build_translation_audit(
        TRANSLATION,
        results_directory=ROOT / "examples",
    )

    first_path, first_written = publish_translation_audit(audit, output_directory=tmp_path)
    second_path, second_written = publish_translation_audit(audit, output_directory=tmp_path)

    units = audit["units"]
    assert isinstance(units, list)
    assert units[0]["source_text"] == "Welcome to another episode."
    assert units[0]["target_text"] == "Witamy w kolejnym odcinku."
    assert units[0]["target_status"] == "translated"
    assert audit["schema_version"] == "1.1"
    assert audit["dictionary"] is None
    assert first_path == second_path
    assert first_written is True
    assert second_written is False
