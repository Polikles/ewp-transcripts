"""Tests for read-only completed-result indexing."""

import json
from pathlib import Path

import pytest

from ewp_transcripts.domain.errors import InvalidExistingResultError
from ewp_transcripts.storage import (
    find_existing_results,
    is_preserved_gui_result,
    preserve_gui_selected_source,
    read_existing_result,
)


def _write_result(
    path: Path,
    *,
    job_id: str = "episode",
    signature: str = "a" * 64,
    version: int = 1,
    status: str = "completed",
) -> None:
    path.write_text(
        json.dumps(
            {
                "job_id": job_id,
                "status": status,
                "result_version": version,
                "episode": {"episode_signature_sha256": signature},
            }
        ),
        encoding="utf-8",
    )


def test_gui_selected_canonical_source_is_durable_and_content_addressed(tmp_path: Path) -> None:
    selected = tmp_path / "selected" / "episode_results.json"
    selected.parent.mkdir()
    selected.write_bytes(b'{"version": 1}')
    output = tmp_path / "output"

    first, first_digest = preserve_gui_selected_source(
        selected, output_directory=output, category="canonical"
    )
    repeated, repeated_digest = preserve_gui_selected_source(
        selected, output_directory=output, category="canonical"
    )
    selected.write_bytes(b'{"version": 2}')
    second, second_digest = preserve_gui_selected_source(
        selected, output_directory=output, category="canonical"
    )

    assert first == repeated
    assert first_digest == repeated_digest
    assert second != first
    assert second_digest != first_digest
    assert first.read_bytes() == b'{"version": 1}'
    assert second.read_bytes() == b'{"version": 2}'
    assert is_preserved_gui_result(first, output, first_digest)
    assert not list(output.rglob("*.tmp"))


def test_missing_output_directory_has_no_existing_results(tmp_path: Path) -> None:
    assert find_existing_results(tmp_path / "missing") == ()


def test_completed_results_are_indexed_in_stable_filename_order(tmp_path: Path) -> None:
    _write_result(tmp_path / "show_results_v002.json", version=2, signature="b" * 64)
    _write_result(tmp_path / "show_results.json", version=1)
    (tmp_path / "notes.json").write_text("{}", encoding="utf-8")
    _write_result(tmp_path / "show_results.partial.json", status="running")
    _write_result(tmp_path / "show_results.failed.json", status="failed")

    results = find_existing_results(tmp_path)

    assert [item.path.name for item in results] == [
        "show_results.json",
        "show_results_v002.json",
    ]
    assert [item.result_version for item in results] == [1, 2]


def test_corrupt_completed_result_is_not_silently_ignored(tmp_path: Path) -> None:
    path = tmp_path / "episode_results.json"
    path.write_text("not JSON", encoding="utf-8")

    with pytest.raises(InvalidExistingResultError, match="Cannot read"):
        read_existing_result(path)


@pytest.mark.parametrize(
    "change",
    [
        {"status": "running"},
        {"result_version": 0},
        {"job_id": ""},
        {"episode": {}},
    ],
)
def test_invalid_completed_metadata_is_rejected(tmp_path: Path, change: dict) -> None:
    path = tmp_path / "episode_results.json"
    data = {
        "job_id": "episode",
        "status": "completed",
        "result_version": 1,
        "episode": {"episode_signature_sha256": "a" * 64},
    }
    data.update(change)
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(InvalidExistingResultError):
        read_existing_result(path)
