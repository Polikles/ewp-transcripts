"""Read-only discovery and portable reference catalogs never grant path authority."""

from pathlib import Path

import pytest

from ewp_transcripts.web_projects import GuiProjects, ProjectCatalog
from ewp_transcripts.web_workflows import GuiWorkflowController

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/results.example.json"


def service(tmp_path):
    return GuiProjects(
        tmp_path / "state/projects.json", GuiWorkflowController().resolve_allowed_path
    )


def test_scan_validates_content_skips_invalid_and_does_not_write_outputs(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    (results / "unusual-name.json").write_bytes(EXAMPLE.read_bytes())
    (results / "fake_results.json").write_text('{"fake":true}')
    target = tmp_path / "elsewhere.json"
    target.write_bytes(EXAMPLE.read_bytes())
    (results / "linked.json").symlink_to(target)
    before = sorted(results.iterdir())
    scan = service(tmp_path).scan(str(results))
    assert len(scan["items"]) == 1
    assert scan["items"][0]["job_id"] == "S01E01"
    assert scan["rejected"] == 2
    assert before == sorted(results.iterdir())
    assert not (tmp_path / "state").exists()


def test_named_locations_and_recent_sessions_survive_restart_and_forget_keeps_files(tmp_path):
    source = tmp_path / "result.json"
    source.write_bytes(EXAMPLE.read_bytes())
    catalog = service(tmp_path)
    catalog.location(name="Podcast input", kind="input", path=str(tmp_path))
    catalog.remember(output_root=str(tmp_path), result_path=str(source), name="Podcast")
    restored = service(tmp_path).listing()
    assert restored["recent"][0]["available"]
    assert restored["locations"][0]["available"]
    catalog.forget(restored["recent"][0]["id"])
    assert source.read_bytes() == EXAMPLE.read_bytes()
    assert not catalog.listing()["recent"]


def test_portable_unavailable_paths_do_not_create_directories_or_get_used(tmp_path):
    path = tmp_path / "missing" / "source"
    document = ProjectCatalog.model_validate(
        {"locations": [{"name": "Other computer", "kind": "input", "path": str(path)}]}
    )
    catalog = service(tmp_path)
    catalog.merge(document)
    assert not catalog.listing()["locations"][0]["available"]
    assert not path.exists()
    with pytest.raises(ValueError, match="unavailable"):
        catalog.location(name="Missing", kind="input", path=str(path))


def test_imported_location_name_collision_preserves_both_references(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    catalog = service(tmp_path)
    catalog.location(name="Audio", kind="input", path=str(first))
    catalog.merge(
        ProjectCatalog.model_validate(
            {"locations": [{"name": "Audio", "kind": "input", "path": str(second)}]}
        )
    )
    assert {item["path"] for item in catalog.listing()["locations"]} == {str(first), str(second)}
