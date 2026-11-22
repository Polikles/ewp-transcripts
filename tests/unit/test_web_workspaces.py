import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ewp_transcripts.storage import preserve_gui_selected_source
from ewp_transcripts.web_workflows import GuiWorkflowController
from ewp_transcripts.web_workspaces import _FIELD_NAMES, GuiWorkspaceController


def test_browser_workspace_fields_match_server_allowlist() -> None:
    app = (Path(__file__).parents[2] / "src/ewp_transcripts/web_assets/app.js").read_text()
    declared = re.search(r"const workspaceFieldIds = \[(.*?)\];", app)
    assert declared is not None
    browser_fields = set(re.findall(r'"([a-z][a-z-]+)"', declared.group(1)))
    for script in ["translation_provider_controls.js", "cloud_asr_controls.js"]:
        source = (Path(__file__).parents[2] / "src/ewp_transcripts/web_assets" / script).read_text()
        added = re.search(r"workspaceFieldIds\.push\((.*?)\);", source)
        assert added is not None
        browser_fields.update(re.findall(r'"([a-z][a-z-]+)"', added.group(1)))
    assert browser_fields == _FIELD_NAMES


def test_workspace_autosave_is_explicit_and_inventory_has_inline_feedback() -> None:
    app = (Path(__file__).parents[2] / "src/ewp_transcripts/web_assets/app.js").read_text()

    assert 'id="workspace-autosave" type="checkbox" disabled' in app
    assert 'id="workspace-autosave" type="checkbox" checked' not in app
    assert '"#refresh-managed-sources", "#cleanup-managed-sources"' in app
    assert '{trigger: document.querySelector("#refresh-managed-sources")}' in app
    assert "function workspaceKey(workspaceId, storageDirectory)" in app
    assert "selectedWorkspace.storageDirectory" in app
    assert "item.catalog" in app
    assert "option.dataset.available = String(item.available)" in app
    assert "option.disabled = !item.available" not in app
    assert "This saved workspace references unavailable paths" in app


def test_workspace_saves_complete_current_browser_field_set(tmp_path: Path) -> None:
    workspaces, _ = controller(tmp_path)
    fields = {name: "" for name in _FIELD_NAMES}
    fields["translation-provider"] = "openrouter"
    fields["translation-reasoning"] = "0"

    saved = workspaces.save(name="Full form", current_step="workspace-heading", fields=fields)

    assert workspaces.load(saved.workspace_id).fields == fields


def test_workspace_drops_expired_native_picker_field_without_rejecting_save(
    tmp_path: Path,
) -> None:
    temporary_root = tmp_path / "ewp-transcripts-gui-selections"
    stale_media = temporary_root / "old-session" / "selection-123" / "episode.wav"
    workspaces = GuiWorkspaceController(
        state_directory=tmp_path / "saved",
        resolve_path=GuiWorkflowController().resolve_allowed_path,
        temporary_selection_root=temporary_root,
    )

    saved = workspaces.save(
        name="After restart",
        current_step="workspace-heading",
        fields={"input-path": str(stale_media), "output-path": str(tmp_path / "durable")},
    )

    assert saved.fields["input-path"] == ""
    assert saved.fields["output-path"] == str(tmp_path / "durable")
    assert workspaces.list()[0].available is True


def test_workspace_save_omits_stale_fields_and_terminal_jobs_when_requested(
    tmp_path: Path,
) -> None:
    workspaces, allowed = controller(tmp_path)
    output = allowed / "output"
    output.mkdir()
    missing = allowed / "missing_results.json"
    now = datetime.now(UTC)

    saved = workspaces.save(
        name="Recoverable remainder",
        current_step="workspace-heading",
        fields={"review-result-path": str(missing), "output-path": str(output)},
        terminal_jobs=[
            {
                "job_id": "ec6d26a5-709a-487b-b459-87f85d64a81d",
                "status": "completed",
                "input_path": str(missing),
                "output_directory": str(output),
                "planned_job_id": "missing",
                "planned_result_path": str(missing),
                "source_sha256": "a" * 64,
                "language": "pl",
                "speaker_count": "auto",
                "created_at": now,
                "updated_at": now,
                "result_path": str(missing),
            }
        ],
        omit_unavailable=True,
    )

    assert saved.fields["review-result-path"] == ""
    assert saved.fields["output-path"] == str(output)
    assert saved.terminal_jobs == ()


def test_workspace_save_still_rejects_unsafe_paths_when_omitting_unavailable(
    tmp_path: Path,
) -> None:
    prohibited = tmp_path / "system"
    prohibited.mkdir()
    unsafe = prohibited / "result.json"
    unsafe.write_text("{}", encoding="utf-8")
    workspaces = GuiWorkspaceController(
        state_directory=tmp_path / "state",
        resolve_path=GuiWorkflowController(
            prohibited_roots=(prohibited.resolve(),)
        ).resolve_allowed_path,
    )

    with pytest.raises(ValueError, match="prohibited"):
        workspaces.save(
            name="Unsafe",
            current_step="",
            fields={"review-result-path": str(unsafe)},
            omit_unavailable=True,
        )


def controller(tmp_path: Path) -> tuple[GuiWorkspaceController, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    workflows = GuiWorkflowController((allowed.resolve(),))
    return (
        GuiWorkspaceController(
            state_directory=tmp_path / "state",
            resolve_path=workflows.resolve_allowed_path,
        ),
        allowed,
    )


def test_workspace_round_trip_contains_only_allowlisted_non_secret_fields(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")

    saved = workspaces.save(
        name="Episode work",
        current_step="correction-heading",
        fields={
            "input-path": str(media),
            "output-path": str(allowed / "output"),
            "workflow-language": "pl",
            "workflow-speaker-auto": True,
        },
    )
    loaded = workspaces.load(saved.workspace_id)
    listed = workspaces.list()

    assert loaded == saved
    assert loaded.fields["input-path"] == str(media)
    assert listed[0].workspace_id == saved.workspace_id
    assert listed[0].available is True
    assert workspaces.document_path(saved.workspace_id).stat().st_mode & 0o777 == 0o600


def test_workspace_rejects_unknown_fields_and_prohibited_paths(tmp_path: Path) -> None:
    workspaces, _ = controller(tmp_path)

    with pytest.raises(ValueError, match="unsupported field"):
        workspaces.save(name="Bad", current_step="", fields={"api_key": "secret"})
    prohibited = tmp_path / "system"
    prohibited.mkdir()
    outside = prohibited / "outside.wav"
    outside.write_bytes(b"audio")
    protected_workspaces = GuiWorkspaceController(
        state_directory=tmp_path / "protected-state",
        resolve_path=GuiWorkflowController(
            prohibited_roots=(prohibited.resolve(),)
        ).resolve_allowed_path,
    )
    with pytest.raises(ValueError, match="prohibited"):
        protected_workspaces.save(
            name="Bad path", current_step="", fields={"input-path": str(outside)}
        )


def test_missing_saved_path_marks_summary_unavailable(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    saved = workspaces.save(
        name="Temporary",
        current_step="workspace-heading",
        fields={"input-path": str(media)},
    )
    media.unlink()

    assert workspaces.list()[0].available is False
    with pytest.raises(FileNotFoundError):
        workspaces.load(saved.workspace_id)


def test_workspace_delete_removes_only_the_selected_record(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    first = workspaces.save(name="First", current_step="", fields={"input-path": str(media)})
    second = workspaces.save(name="Second", current_step="", fields={"input-path": str(media)})

    workspaces.delete(first.workspace_id)

    assert [item.workspace_id for item in workspaces.list()] == [second.workspace_id]
    with pytest.raises(ValueError, match="does not exist"):
        workspaces.load(first.workspace_id)


def test_workspace_import_copies_a_valid_selected_state_into_the_chosen_catalog(
    tmp_path: Path,
) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    saved = workspaces.save(name="Backup", current_step="", fields={"input-path": str(media)})
    imported = GuiWorkspaceController(
        state_directory=tmp_path / "backup-catalog",
        resolve_path=GuiWorkflowController().resolve_allowed_path,
    ).import_file(workspaces.document_path(saved.workspace_id))

    assert imported.workspace_id == saved.workspace_id
    assert imported.name == "Backup"


def test_workspace_retains_only_hash_bound_staged_queue_identity(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    output = allowed / "output"
    saved = workspaces.save(
        name="Queued episode",
        current_step="workspace-heading",
        fields={"input-path": str(media), "output-path": str(output)},
        staged_jobs=[
            {
                "input_path": str(media),
                "output_directory": str(output),
                "planned_job_id": "episode",
                "planned_result_path": str(output / "episode_results.json"),
                "source_sha256": "a" * 64,
                "language": "pl",
                "speaker_count": "auto",
            }
        ],
    )

    assert saved.staged_jobs[0]["planned_job_id"] == "episode"
    assert workspaces.load(saved.workspace_id).staged_jobs == saved.staged_jobs


def test_workspace_restores_imported_result_after_browser_selection_expires(tmp_path: Path) -> None:
    workspaces, allowed = controller(tmp_path)
    selected = allowed / "episode_results.json"
    selected.write_bytes(b'{"status":"completed"}')
    output = allowed / "output"
    preserved, digest = preserve_gui_selected_source(
        selected, output_directory=output, category="canonical"
    )
    now = datetime.now(UTC)
    saved = workspaces.save(
        name="Imported episode",
        current_step="review-heading",
        fields={"review-result-path": str(preserved), "review-project-path": str(output)},
        terminal_jobs=[
            {
                "job_id": "ec6d26a5-709a-487b-b459-87f85d64a81d",
                "status": "completed",
                "input_path": str(preserved),
                "output_directory": str(output),
                "planned_job_id": "episode",
                "planned_result_path": str(preserved),
                "source_sha256": digest,
                "language": "pl",
                "speaker_count": "auto",
                "created_at": now,
                "updated_at": now,
                "result_path": str(preserved),
            }
        ],
    )
    selected.unlink()

    assert workspaces.list()[0].available is True
    assert workspaces.load(saved.workspace_id).terminal_jobs[0].result_path == str(preserved)
    preserved.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="changed on disk"):
        workspaces.load(saved.workspace_id)


@pytest.mark.parametrize("terminal_status", ["failed", "cancelled"])
def test_workspace_retains_terminal_queue_history_without_credentials(
    tmp_path: Path, terminal_status: str
) -> None:
    workspaces, allowed = controller(tmp_path)
    media = allowed / "episode.wav"
    media.write_bytes(b"audio")
    output = allowed / "output"
    output.mkdir()
    result = output / "episode_results.json"
    result.write_text("{}", encoding="utf-8")
    now = datetime.now(UTC)
    saved = workspaces.save(
        name="Completed episode",
        current_step="translation-heading",
        fields={"input-path": str(media), "output-path": str(output)},
        terminal_jobs=[
            {
                "job_id": "ec6d26a5-709a-487b-b459-87f85d64a81d",
                "status": "completed",
                "input_path": str(media),
                "output_directory": str(output),
                "planned_job_id": "episode",
                "planned_result_path": str(result),
                "source_sha256": "a" * 64,
                "language": "pl",
                "speaker_count": "auto",
                "created_at": now,
                "updated_at": now,
                "result_path": str(result),
                "error": None,
                "workflow_errors": {"translation": "INVALID_TRANSLATION_RESPONSE"},
                "workflow_skips": ["correction"],
            },
            {
                "job_id": "f2a7fdd3-4bdb-4c84-9156-b4177df5670f",
                "status": terminal_status,
                "input_path": str(media),
                "output_directory": str(output),
                "planned_job_id": "failed-episode",
                "planned_result_path": str(output / "failed-episode_results.json"),
                "source_sha256": "b" * 64,
                "language": "pl",
                "speaker_count": "auto",
                "created_at": now,
                "updated_at": now,
                "result_path": None,
                "error": {"code": "GUI_TRANSCRIPTION_FAILED", "message": "Retained failure."},
                "workflow_errors": {},
                "workflow_skips": [],
            },
        ],
    )

    restored = workspaces.load(saved.workspace_id)

    assert restored.workspace_version == 3
    assert len(restored.terminal_jobs) == 2
    assert restored.terminal_jobs[0].workflow_skips == {"correction"}
    assert restored.terminal_jobs[0].workflow_errors == {
        "translation": "INVALID_TRANSLATION_RESPONSE"
    }
    assert restored.terminal_jobs[1].status == terminal_status


@pytest.mark.parametrize("missing_media", [False, True])
def test_cancelled_history_is_saved_when_retry_published_the_planned_result(
    tmp_path: Path, missing_media: bool
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    media = tmp_path / "episode.wav"
    if not missing_media:
        media.write_bytes(b"audio")
    result = output / "episode_results.json"
    result.write_text("{}")
    now = datetime.now(UTC)
    workspaces = GuiWorkspaceController(
        state_directory=tmp_path / "state",
        resolve_path=GuiWorkflowController().resolve_allowed_path,
    )
    saved = workspaces.save(
        name="cancelled attempt",
        current_step="workspace-heading",
        fields={},
        terminal_jobs=[
            dict(
                job_id="cancelled",
                status="cancelled",
                input_path=str(media),
                output_directory=str(output),
                planned_job_id="episode",
                planned_result_path=str(result),
                source_sha256="a" * 64,
                language="pl",
                speaker_count=2,
                created_at=now,
                updated_at=now,
            )
        ],
        omit_unavailable=True,
    )
    assert len(saved.terminal_jobs) == 1
    assert workspaces.load(saved.workspace_id).terminal_jobs[0].status == "cancelled"


def test_named_workspace_files_preserve_identity_and_migrate_legacy_names(tmp_path: Path) -> None:
    from pathlib import PureWindowsPath

    workspaces, _ = controller(tmp_path)
    first = workspaces.save(name="Odcinek Żółć", current_step="", fields={})
    first_path = workspaces.document_path(first.workspace_id)
    assert first_path.name.startswith("Odcinek Żółć--")
    second = workspaces.save(name="Odcinek Żółć", current_step="", fields={})
    assert first.workspace_id != second.workspace_id
    assert len(list(first_path.parent.glob("*.workspace.json"))) == 2
    legacy = first_path.parent / f"{first.workspace_id}.json"
    data = first.model_dump(mode="json")
    data["workspace_version"] = 2
    data.pop("pending_media")
    legacy.write_text(json.dumps(data))
    first_path.unlink()
    assert workspaces.load(first.workspace_id).workspace_version == 2
    updated = workspaces.save(
        name=first.name,
        current_step="workspace-heading",
        fields={},
        workspace_id=first.workspace_id,
    )
    assert (
        updated.workspace_id == first.workspace_id and first_path.exists() and not legacy.exists()
    )
    workspaces.delete(first.workspace_id)
    assert workspaces.load(second.workspace_id).name == second.name
    for name in ["CON", "AUX.txt", 'a/b:c?*<>|"', "..", "   ", "🎙" * 100]:
        from ewp_transcripts.web_workspaces import workspace_filename

        filename = workspace_filename(name, second.workspace_id)
        assert Path(filename).name == filename and not PureWindowsPath(filename).is_reserved()
        assert not any(c in filename for c in '<>:"/\\|?*')
        assert len(filename.encode("utf-8")) <= 255


def test_last_workspace_directories_survive_restart_and_validate_paths(tmp_path: Path) -> None:
    from ewp_transcripts.web_workspaces import GuiWorkspaceLocations

    output, catalog = tmp_path / "Desktop output", tmp_path / "Saved work"
    output.mkdir()
    catalog.mkdir()
    path = tmp_path / "private" / "workspace-locations.json"
    resolve = GuiWorkflowController().resolve_allowed_path
    first = GuiWorkspaceLocations(path, resolve)
    first.remember(output_directory=str(output), storage_directory=str(catalog))
    second = GuiWorkspaceLocations(path, resolve)
    restored = second.available()
    assert restored.output_directory == str(output) and restored.storage_directory == str(catalog)
    assert restored.catalogs == (str(catalog),)
    another = tmp_path / "other"
    another.mkdir()
    second.remember(output_directory=str(another), storage_directory="")
    assert second.available().catalogs == (str(another), str(catalog))
    catalog.rmdir()
    assert second.available().catalogs == (str(another),)
    assert "key" not in path.read_text() and path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ValueError):
        second.remember(output_directory="/etc", storage_directory="")
