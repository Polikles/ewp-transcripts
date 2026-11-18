"""Library edits never replace editions or invalidate references held by older runs."""

import json
from pathlib import Path

import pytest

from ewp_transcripts.config import SubtitlesConfig
from ewp_transcripts.gui_library import GuiLibrary
from ewp_transcripts.web_dictionaries import GuiDictionaryController
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[2]


def library(tmp_path: Path) -> tuple[GuiLibrary, GuiDictionaryController]:
    paths = GuiWorkflowController((tmp_path.resolve(),))
    service = GuiLibrary(
        state_directory=tmp_path / "state",
        resolve_path=paths.resolve_allowed_path,
        subtitles=SubtitlesConfig(),
    )
    return service, GuiDictionaryController(
        resolve_path=paths.resolve_allowed_path, library=service
    )


def test_edit_dictionary_keeps_old_bytes_and_records_manual_provenance(tmp_path: Path) -> None:
    service, catalog = library(tmp_path)
    source = ROOT / "dictionaries/ethics-in-the-loop/correction/pl/ethics-in-the-loop-pl-v1.json"
    original = tmp_path / source.name
    original.write_bytes(source.read_bytes())
    old_bytes = original.read_bytes()
    opened = service.view(str(original))
    edited = dict(opened["document"], dictionary_id="edited-v2")
    edited["entries"][0]["target"] = "A different preferred spelling"
    result = service.edition(
        document=edited,
        directory=str(tmp_path),
        previous_path=str(original),
        previous_sha256=opened["sha256"],
    )
    assert original.read_bytes() == old_bytes
    assert result["path"] != opened["path"]
    assert result["document"]["entries"][0]["target"] == "A different preferred spelling"
    provenance = tmp_path / ".edits" / f"{result['document']['proposal_sha256']}.json"
    assert json.loads(provenance.read_text())["previous_sha256"] == opened["sha256"]
    assert catalog.catalog(str(tmp_path))["count"] == 2
    with pytest.raises(ValueError, match="already exists"):
        service.edition(
            document=edited,
            directory=str(tmp_path),
            previous_path=str(original),
            previous_sha256=opened["sha256"],
        )
    edited["dictionary_id"] = "stale-v3"
    with pytest.raises(ValueError, match="changed"):
        service.edition(
            document=edited,
            directory=str(tmp_path),
            previous_path=str(original),
            previous_sha256="0" * 64,
        )
    edited["dictionary_id"] = opened["document"]["dictionary_id"]
    with pytest.raises(ValueError, match="immutable"):
        service.edition(
            document=edited,
            directory=str(tmp_path),
            previous_path=str(original),
            previous_sha256=opened["sha256"],
        )


def test_hide_and_restore_is_persistent_and_preserves_dictionary(tmp_path: Path) -> None:
    service, catalog = library(tmp_path)
    raw = {
        "dictionary_id": "custom-en-pl-v1",
        "project_id": "custom",
        "dictionary_version": "1.0",
        "job_ids": ["*"],
        "source_language": "en",
        "target_language": "pl",
        "entries": [{"source": "podcast", "target": "podcast"}],
    }
    saved = service.edition(
        document=raw, directory=str(tmp_path / "dicts"), previous_path="", previous_sha256=""
    )
    service.visibility(path=saved["path"], digest=saved["sha256"], visible=False)
    assert Path(saved["path"]).is_file()
    assert catalog.catalog(str(tmp_path / "dicts"))["items"] == []
    service2, catalog2 = library(tmp_path)
    assert (
        catalog2.catalog(str(tmp_path / "dicts"), include_hidden=True)["items"][0]["hidden"] is True
    )
    service2.visibility(path=saved["path"], digest=saved["sha256"], visible=True)
    assert catalog2.catalog(str(tmp_path / "dicts"))["count"] == 1
    with pytest.raises(ValueError, match="changed"):
        service.visibility(path=saved["path"], digest="0" * 64, visible=False)


def test_dictionary_validation_rejects_unsafe_ids_and_duplicate_terms(tmp_path: Path) -> None:
    service, _ = library(tmp_path)
    document = {
        "dictionary_id": "../escape",
        "project_id": "custom",
        "dictionary_version": "1.0",
        "job_ids": ["*"],
        "source_language": "en",
        "target_language": "pl",
        "entries": [{"source": "term", "target": "termin"}],
    }
    with pytest.raises(ValueError):
        service.edition(
            document=document, directory=str(tmp_path), previous_path="", previous_sha256=""
        )
    document["dictionary_id"] = "safe-id"
    document["entries"] *= 2
    with pytest.raises(ValueError, match="unique"):
        service.edition(
            document=document, directory=str(tmp_path), previous_path="", previous_sha256=""
        )
    assert not (tmp_path / "safe-id.json").exists()


def test_profiles_keep_configured_and_brand_distinct_and_persist_custom(tmp_path: Path) -> None:
    service, _ = library(tmp_path)
    profiles = {item["name"]: item["colors"] for item in service.profiles()["profiles"]}
    assert profiles["Configured production"] != profiles["EwP brand"]
    service.save_profile(name="My podcast", colors=["#abcdef", "#123456"])
    reloaded, _ = library(tmp_path)
    assert reloaded.profiles()["profiles"][-1] == {
        "name": "My podcast",
        "colors": ["#ABCDEF", "#123456"],
        "custom": True,
    }
    with pytest.raises(ValueError, match="custom name"):
        service.save_profile(name="EwP brand", colors=["#ffffff"])
    with pytest.raises(ValueError, match="#RRGGBB"):
        service.save_profile(name="Bad", colors=["red"])
