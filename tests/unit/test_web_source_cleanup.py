from datetime import UTC, datetime
from pathlib import Path

import pytest

from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.storage import preserve_gui_selected_source
from ewp_transcripts.web_jobs import GuiTranscriptionJob
from ewp_transcripts.web_source_cleanup import (
    GuiManagedSourceCleanupError,
    cleanup_managed_sources,
    inventory_managed_sources,
)
from ewp_transcripts.web_workspaces import GuiWorkspaceDocument


def job(path: Path, output: Path, *, status: str = "staged") -> GuiTranscriptionJob:
    now = datetime.now(UTC)
    return GuiTranscriptionJob(
        job_id="queue-id",
        status=status,
        input_path=str(path),
        output_directory=str(output),
        planned_job_id="episode",
        planned_result_path=str(output / "episode_results.json"),
        source_sha256="a" * 64,
        language=LanguageMode.POLISH,
        speaker_count="auto",
        created_at=now,
        updated_at=now,
    )


def test_unreferenced_managed_source_can_be_inventoried_and_deleted(tmp_path: Path) -> None:
    output = tmp_path / "output"
    source = tmp_path / "episode.wav"
    source.write_bytes(b"audio")
    preserved, _ = preserve_gui_selected_source(source, output_directory=output, category="media")
    publication = output / "exports" / "episode.txt"
    publication.parent.mkdir()
    publication.write_text("published", encoding="utf-8")

    inventory = inventory_managed_sources(output, queue_jobs=(), workspaces=())

    assert len(inventory) == 1
    assert inventory[0].removable
    removed = cleanup_managed_sources(
        output, (inventory[0].relative_path,), queue_jobs=(), workspaces=()
    )
    assert removed == (inventory[0].relative_path,)
    assert not preserved.exists()
    assert publication.read_text(encoding="utf-8") == "published"


def test_current_queue_and_saved_workspace_protect_managed_sources(tmp_path: Path) -> None:
    output = tmp_path / "output"
    media = tmp_path / "episode.wav"
    media.write_bytes(b"audio")
    preserved_media, digest = preserve_gui_selected_source(
        media, output_directory=output, category="media"
    )
    canonical = tmp_path / "episode_results.json"
    canonical.write_text("{}", encoding="utf-8")
    preserved_result, result_digest = preserve_gui_selected_source(
        canonical, output_directory=output, category="canonical"
    )
    workspace = GuiWorkspaceDocument(
        workspace_id="4bf6dd33-d48c-4eb7-bd9b-15f5e6c20a29",
        name="backup",
        saved_at=datetime.now(UTC),
        current_step="workspace-heading",
        fields={"review-result-path": str(preserved_result)},
    )

    inventory = inventory_managed_sources(
        output,
        queue_jobs=(job(preserved_media, output),),
        workspaces=(workspace,),
    )
    by_digest = {item.sha256: item for item in inventory}

    assert not by_digest[digest].removable
    assert "current queue: episode (staged)" in by_digest[digest].references
    assert not by_digest[result_digest].removable
    assert "saved workspace: backup" in by_digest[result_digest].references


def test_revision_lineage_protects_managed_canonical_result(tmp_path: Path) -> None:
    output = tmp_path / "output"
    canonical = tmp_path / "episode_results.json"
    canonical.write_text('{"canonical": true}', encoding="utf-8")
    _, digest = preserve_gui_selected_source(
        canonical, output_directory=output, category="canonical"
    )
    revision = output / "revisions" / "episode_revision_001.json"
    revision.parent.mkdir()
    revision.write_text(f'{{"base_result": {{"sha256": "{digest}"}}}}', encoding="utf-8")

    item = inventory_managed_sources(output, queue_jobs=(), workspaces=())[0]

    assert not item.removable
    assert item.references == ("workflow lineage: revisions/episode_revision_001.json",)
    with pytest.raises(GuiManagedSourceCleanupError, match="still referenced"):
        cleanup_managed_sources(output, (item.relative_path,), queue_jobs=(), workspaces=())


def test_changed_managed_source_is_never_eligible_for_cleanup(tmp_path: Path) -> None:
    output = tmp_path / "output"
    source = tmp_path / "episode.wav"
    source.write_bytes(b"audio")
    preserved, _ = preserve_gui_selected_source(source, output_directory=output, category="media")
    preserved.write_bytes(b"changed")

    item = inventory_managed_sources(output, queue_jobs=(), workspaces=())[0]

    assert not item.removable
    assert item.references == ("content hash no longer matches its managed path",)
