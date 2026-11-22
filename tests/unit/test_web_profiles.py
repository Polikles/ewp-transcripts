"""Portable profiles retain dictionary bytes and inactive workspace references, never keys."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ewp_transcripts.config import SubtitlesConfig
from ewp_transcripts.gui_library import GuiLibrary
from ewp_transcripts.web_profiles import GuiProfileController
from ewp_transcripts.web_projects import GuiProjects, ProjectCatalog
from ewp_transcripts.web_workflows import GuiWorkflowController
from ewp_transcripts.web_workspaces import GuiWorkspaceController, GuiWorkspaceDocument

ROOT = Path(__file__).resolve().parents[2]


def controller(root: Path) -> GuiProfileController:
    resolve = GuiWorkflowController().resolve_allowed_path
    library = GuiLibrary(
        state_directory=root / "workspaces", resolve_path=resolve, subtitles=SubtitlesConfig()
    )
    workspaces = GuiWorkspaceController(state_directory=root / "workspaces", resolve_path=resolve)
    return GuiProfileController(state_directory=root, workspaces=workspaces, library=library)


def capture(service: GuiProfileController, **kwargs):
    return service.capture(
        name="Portable",
        preferences={"locale": "pl", "showEta": True, "playbackSpeed": 1.5},
        fields={"workflow-language": "en"},
        workspaces=(),
        dictionary_paths=[],
        **kwargs,
    )


def test_profile_can_transfer_locations_without_embedded_dictionary_bytes(tmp_path):
    first, second = controller(tmp_path / "first"), controller(tmp_path / "second")
    for service in (first, second):
        service.projects = GuiProjects(
            service.directory / "projects.json", GuiWorkflowController().resolve_allowed_path
        )
    first.projects.merge(
        ProjectCatalog.model_validate(
            {
                "locations": [
                    {"name": "Windows input", "kind": "input", "path": "C:\\Podcasts\\Audio"}
                ]
            }
        )
    )
    profile = first.capture(
        name="References only",
        preferences={},
        fields={"correction-dictionary": "C:\\Podcasts\\dictionary.json"},
        workspaces=(),
        dictionary_paths=[],
    )
    payload = profile.model_dump(mode="json")
    assert not payload["dictionaries"]
    assert payload["fields"]["correction-dictionary"] == "C:\\Podcasts\\dictionary.json"
    second.restore(payload)
    assert not second.projects.listing()["locations"][0]["available"]
    assert not (second.directory / "profile-dictionaries").exists()


def test_profile_transfer_preserves_immutable_dictionaries_and_missing_workspace_paths(
    tmp_path: Path,
) -> None:
    first, second = controller(tmp_path / "first"), controller(tmp_path / "second")
    original = ROOT / "dictionaries/ethics-in-the-loop/correction/pl/ethics-in-the-loop-pl-v1.json"
    dictionary = tmp_path / original.name
    dictionary.write_bytes(original.read_bytes().replace(b"\n", b"\r\n"))
    before = dictionary.read_bytes()
    first.library.save_profile(name="Custom", colors=["#123456"])
    first.library.visibility(
        path=str(dictionary), digest=first.library.view(str(dictionary))["sha256"], visible=False
    )
    workspace = GuiWorkspaceDocument(
        workspace_id=str(uuid4()),
        name="Away",
        saved_at="2026-11-20T00:00:00Z",
        current_step="workspace-heading",
        fields={
            "input-path": str(tmp_path / "missing.wav"),
            "correction-dictionary": str(dictionary),
        },
    )
    saved = first.capture(
        name="Portable",
        preferences={"locale": "pl", "showEta": True, "playbackSpeed": 2},
        fields={"workflow-language": "en", "correction-dictionary": str(dictionary)},
        workspaces=(workspace,),
        dictionary_paths=[str(dictionary)],
    )
    result = second.restore(saved.model_dump(mode="json"))
    assert result["profile"]["preferences"]["showEta"] is True
    assert len(second.workspaces.documents()) == 2
    away = next(item for item in second.workspaces.documents() if item.name == "Away")
    transferred = Path(away.fields["correction-dictionary"])
    assert transferred.read_bytes() == before == dictionary.read_bytes()
    assert second.library.hidden(str(transferred), second.library.view(str(transferred))["sha256"])
    assert not next(item for item in second.workspaces.list() if item.name == "Away").available
    assert any(item["id"] == "Custom" for item in second.library.profiles()["profiles"])
    # Importing again is idempotent and does not start jobs or require original media.
    second.restore(saved.model_dump(mode="json"))
    assert len(second.workspaces.documents()) == 2
    second.load()
    assert len(second.workspaces.documents()) == 2
    assert not (tmp_path / "missing.wav").exists()
    assert not (second.directory / "runtime-timings.json").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda doc: doc.update(api_key="DO-NOT-PERSIST"),
        lambda doc: doc["preferences"].update(api_key="DO-NOT-PERSIST"),
        lambda doc: doc["fields"].update(confirmed=True),
        lambda doc: doc["preferences"].update(playbackSpeed=9),
        lambda doc: doc["preferences"].update(showEta="true"),
    ],
)
def test_invalid_profile_is_rejected_before_any_writes(tmp_path: Path, mutation) -> None:
    first = controller(tmp_path / "first")
    document = capture(first).model_dump(mode="json")
    mutation(document)
    target = controller(tmp_path / "target")
    with pytest.raises(ValueError):
        target.restore(document)
    assert not target.directory.exists()


def test_dictionary_transfer_rejects_hash_change_without_overwrite(tmp_path: Path) -> None:
    first = controller(tmp_path / "first")
    source = ROOT / "dictionaries/ethics-in-the-loop/correction/pl/ethics-in-the-loop-pl-v1.json"
    saved = first.capture(
        name="Test", preferences={}, fields={}, workspaces=(), dictionary_paths=[str(source)]
    )
    document = saved.model_dump(mode="json")
    document["dictionaries"][0]["sha256"] = "0" * 64
    target = controller(tmp_path / "target")
    with pytest.raises(ValueError, match="hash"):
        target.restore(document)
    assert not target.directory.exists()


def test_independent_dictionary_import_export_never_rewrites_editions(tmp_path: Path) -> None:
    library = controller(tmp_path / "state").library
    source = ROOT / "dictionaries/ethics-in-the-loop/correction/pl/ethics-in-the-loop-pl-v1.json"
    exported = library.export_dictionary(str(source))
    imported = library.import_dictionary(
        payload=exported["payload"], directory=str(tmp_path / "dicts")
    )
    assert Path(imported["path"]).read_bytes() == source.read_bytes()
    assert library.export_dictionary(imported["path"]) == exported
    assert (
        library.import_dictionary(payload=exported["payload"], directory=str(tmp_path / "dicts"))
        == imported
    )
    changed = json.loads(exported["payload"])
    changed["entries"][0]["target"] = "Changed"
    with pytest.raises(ValueError, match="different content"):
        library.import_dictionary(payload=json.dumps(changed), directory=str(tmp_path / "dicts"))
    assert Path(imported["path"]).read_bytes() == source.read_bytes()


def test_profile_discards_consent_and_rejects_credentials_in_endpoints(tmp_path: Path) -> None:
    service = controller(tmp_path / "state")
    profile = service.capture(
        name="Safe",
        preferences={},
        fields={"correction-allow-remote": True},
        workspaces=(),
        dictionary_paths=[],
    )
    assert profile.fields["correction-allow-remote"] is False
    document = profile.model_dump(mode="json")
    document["fields"]["correction-endpoint"] = "https://user:DO-NOT-PERSIST@example.invalid/api"
    with pytest.raises(ValueError, match="credentials") as failure:
        service.restore(document)
    assert "DO-NOT-PERSIST" not in str(failure.value)
    assert "DO-NOT-PERSIST" not in service.path.read_text()


def test_imported_palette_does_not_overwrite_existing_custom_palette(tmp_path: Path) -> None:
    source, target = controller(tmp_path / "source"), controller(tmp_path / "target")
    source.library.save_profile(name="Personal", colors=["#123456"])
    target.library.save_profile(name="Personal", colors=["#654321"])
    source.library.save_profile(name="pl", colors=["#abcdef"])
    target.library.save_profile(name="pl", colors=["#fedcba"])
    profile = source.capture(
        name="Colors",
        preferences={},
        fields={"workflow-language": "pl", "gui-palette-profile": "pl"},
        workspaces=(),
        dictionary_paths=[],
    )
    target.restore(profile.model_dump(mode="json"))
    imported_fields = target.workspaces.documents()[0].fields
    assert imported_fields["workflow-language"] == "pl"
    assert imported_fields["gui-palette-profile"] != "pl"
    palettes = {item["id"]: item["colors"] for item in target.library.profiles()["profiles"]}
    assert palettes["Personal"] == ["#654321"]
    assert ["#123456"] in palettes.values()
    assert len(palettes) == len(target.library.profiles()["profiles"])


@pytest.mark.parametrize("speed", [0.25, 0.5, 1.5, 2, 4])
def test_native_playback_rates_can_be_saved_in_profiles(speed):
    from ewp_transcripts.web_profiles import GuiPreferences

    assert GuiPreferences(playbackSpeed=speed).playbackSpeed == speed


def test_portable_profile_keeps_pending_media_references_without_media_or_approval(tmp_path):
    from datetime import UTC, datetime

    service = controller(tmp_path / "first")
    workspace = GuiWorkspaceDocument(
        workspace_id=str(uuid4()),
        name="Pending",
        saved_at=datetime.now(UTC),
        current_step="workspace-heading",
        fields={},
        pending_media=[
            {
                "path": "C:\\Podcast\\pending.wav",
                "name": "pending.wav",
                "source_sha256": "a" * 64,
                "language": "pl",
                "speaker_count": 2,
            }
        ],
    )
    profile = service.capture(
        name="Pending references",
        preferences={},
        fields={},
        workspaces=(workspace,),
        dictionary_paths=[],
    )
    target = controller(tmp_path / "second")
    target.restore(profile.model_dump(mode="json"))
    restored = target.workspaces.documents()[0]
    assert restored.pending_media[0].path == "C:\\Podcast\\pending.wav"
    assert restored.workspace_version == 3 and not restored.staged_jobs
    assert target.workspaces.list()[0].available is False
    assert not list((tmp_path / "second").rglob("*.wav"))
