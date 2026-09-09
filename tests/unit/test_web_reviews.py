from pathlib import Path

import pytest

from ewp_transcripts.application import apply_mock_correction
from ewp_transcripts.config import ApplicationConfig, RuntimeConfig
from ewp_transcripts.correction import DeterministicMockCorrectionProvider
from ewp_transcripts.domain.revision import load_transcript_revision
from ewp_transcripts.web_reviews import GuiReviewController, GuiReviewError
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/results.example.json"


def controller(tmp_path: Path) -> GuiReviewController:
    paths = GuiWorkflowController((tmp_path.resolve(),))
    return GuiReviewController(
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        resolve_path=paths.resolve_allowed_path,
    )


def test_browser_review_prepare_edit_preview_and_apply(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    reviews = tmp_path / "reviews"
    revisions = tmp_path / "revisions"
    service = controller(tmp_path)

    prepared = service.prepare(str(result), str(reviews))
    assert prepared["source_verification"] == "canonical_asr"
    assert prepared["review_path"].endswith("S01E01.review.txt")
    assert prepared["speaker_labels"] == {"speaker_001": "jan", "speaker_002": "anna"}
    prepared["anchors"][0]["blocks"][0]["text"] += " corrected"

    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
    )
    assert saved["review_sha256"] != prepared["review_sha256"]
    assert saved["anchors"][0]["blocks"][0]["text"].endswith("corrected")

    preview = service.preview(saved["review_path"], str(result))
    assert preview["revision_number"] == 1
    applied = service.apply(saved["review_path"], str(result), str(revisions))
    assert applied["revision_number"] == 1
    assert Path(applied["revision_path"]).is_file()
    exported = service.export(
        str(result),
        applied["revision_path"],
        str(tmp_path / "exports"),
        ["txt", "srt", "vtt"],
    )
    assert len(exported["written"]) == 3


def test_browser_review_can_split_and_reassign_a_speaker_block(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    blocks = prepared["anchors"][0]["blocks"]
    first = blocks[0]
    blocks.insert(1, {"speaker_id": "speaker_002", "text": "another episode."})
    first["text"] = "Welcome to"

    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
    )

    assert [block["speaker_id"] for block in saved["anchors"][0]["blocks"]] == [
        "speaker_001",
        "speaker_002",
        "speaker_002",
    ]
    preview = service.preview(saved["review_path"], str(result))
    assert preview["statistics"]["speaker_changes"] > 0


def test_browser_review_persists_revision_scoped_speaker_labels(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    assert prepared["speaker_labels"] == {"speaker_001": "jan", "speaker_002": "anna"}

    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
        speaker_labels={"speaker_001": "Szymon", "speaker_002": "Damian"},
    )
    assert saved["speaker_labels"] == {"speaker_001": "Szymon", "speaker_002": "Damian"}
    assert '"speaker_001":"Szymon"' in Path(saved["review_path"]).read_text(encoding="utf-8")

    service.preview(saved["review_path"], str(result))
    applied = service.apply(saved["review_path"], str(result), str(tmp_path / "revisions"))
    revision = load_transcript_revision(Path(applied["revision_path"]))
    assert revision.transcript.speaker_labels == {
        "speaker_001": "Szymon",
        "speaker_002": "Damian",
    }
    child = service.prepare(
        str(result), str(tmp_path / "child-reviews"), str(applied["revision_path"])
    )
    assert child["speaker_labels"] == {"speaker_001": "Szymon", "speaker_002": "Damian"}

    exported = service.export(
        str(result), applied["revision_path"], str(tmp_path / "exports"), ["txt", "segments"]
    )
    contents = {
        path.suffix: path.read_text(encoding="utf-8") for path in map(Path, exported["written"])
    }
    assert "Szymon:" in contents[".txt"]
    assert "Damian:" in contents[".txt"]
    assert '"speaker_label": "Szymon"' in contents[".json"]


def test_browser_review_rejects_empty_split_blocks(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    prepared["anchors"][0]["blocks"].append({"speaker_id": "speaker_001", "text": ""})

    with pytest.raises(GuiReviewError, match="cannot be empty") as error:
        service.save(
            prepared["review_path"],
            str(result),
            expected_sha256=prepared["review_sha256"],
            anchors=prepared["anchors"],
        )

    assert error.value.code == "GUI_REVIEW_STRUCTURE_INVALID"


def test_browser_review_requires_current_hash_and_preview(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))

    with pytest.raises(GuiReviewError, match="changed after it was loaded") as conflict:
        service.save(
            prepared["review_path"],
            str(result),
            expected_sha256="0" * 64,
            anchors=prepared["anchors"],
        )
    assert conflict.value.code == "GUI_REVIEW_CONFLICT"

    with pytest.raises(GuiReviewError, match="Preview") as missing_preview:
        service.apply(prepared["review_path"], str(result), str(tmp_path / "revisions"))
    assert missing_preview.value.code == "GUI_REVIEW_PREVIEW_REQUIRED"


def test_browser_review_session_restores_from_project_root(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    project = tmp_path / "project"
    prepared = service.prepare(str(result), str(project / "reviews"))

    remembered = service.remember_session(
        project_output_directory=str(project),
        result=str(result),
        review=prepared["review_path"],
        review_output_directory=str(project / "reviews"),
        revision_output_directory=str(project / "revisions"),
        export_output_directory=str(project / "exports"),
    )
    restored = service.restore_session(str(project))

    assert Path(remembered["session_path"]).name == ".ewp-gui-review-session.json"
    assert restored["review_path"] == prepared["review_path"]
    assert restored["session"]["result_path"] == str(result)


def test_browser_review_session_requires_saved_pointer(tmp_path: Path) -> None:
    service = controller(tmp_path)

    with pytest.raises(GuiReviewError, match="No saved") as missing:
        service.restore_session(str(tmp_path))

    assert missing.value.code == "GUI_REVIEW_SESSION_NOT_FOUND"


def test_browser_review_can_start_from_automated_candidate(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    automated = apply_mock_correction(
        result,
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        provider=DeterministicMockCorrectionProvider(),
        output_directory=tmp_path / "candidates",
    )

    prepared = controller(tmp_path).prepare(
        str(result), str(tmp_path / "reviews"), str(automated.revision_path)
    )

    assert prepared["source_verification"] == "automated_candidate"
