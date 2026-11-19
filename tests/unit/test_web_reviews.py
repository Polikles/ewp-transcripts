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
    assert prepared["canonical_speakers"] == ["speaker_001", "speaker_002"]
    assert prepared["speaker_labels"] == {"speaker_001": "jan", "speaker_002": "anna"}
    assert prepared["anchors"][0]["start_ms"] == 1240
    assert prepared["anchors"][0]["end_ms"] == 6320
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


def test_browser_review_rejects_audio_instead_of_a_canonical_result(tmp_path: Path) -> None:
    media = tmp_path / "episode.wav"
    media.write_bytes(b"not a canonical result")

    with pytest.raises(GuiReviewError) as invalid:
        controller(tmp_path).prepare(str(media), str(tmp_path / "reviews"))

    assert invalid.value.code == "GUI_REVIEW_RESULT_INVALID"
    assert "not an audio" in str(invalid.value)


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


def test_browser_review_can_add_a_revision_local_speaker(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    blocks = prepared["anchors"][0]["blocks"]
    first = blocks[0]
    blocks.insert(1, {"speaker_id": "speaker_003", "text": "another episode."})
    first["text"] = "Welcome to"

    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
        speaker_labels={"speaker_003": "Guest"},
    )
    assert saved["speakers"] == ["speaker_001", "speaker_002", "speaker_003"]
    assert saved["speaker_labels"]["speaker_003"] == "Guest"

    service.preview(saved["review_path"], str(result))
    applied = service.apply(saved["review_path"], str(result), str(tmp_path / "revisions"))
    revision = load_transcript_revision(Path(applied["revision_path"]))
    assert revision.transcript.speaker_labels["speaker_003"] == "Guest"
    assert any(token.speaker_id == "speaker_003" for token in revision.transcript.tokens)

    child = service.prepare(
        str(result), str(tmp_path / "child-reviews"), str(applied["revision_path"])
    )
    assert child["speakers"] == ["speaker_001", "speaker_002", "speaker_003"]
    assert child["speaker_labels"]["speaker_003"] == "Guest"

    exported = service.export(
        str(result), applied["revision_path"], str(tmp_path / "exports"), ["txt", "segments"]
    )
    contents = {
        path.suffix: path.read_text(encoding="utf-8") for path in map(Path, exported["written"])
    }
    assert "Guest:" in contents[".txt"]
    assert '"speaker_id": "speaker_003"' in contents[".json"]
    assert '"speaker_label": "Guest"' in contents[".json"]


def test_browser_review_can_remove_an_unused_revision_local_speaker(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
        speaker_labels={"speaker_003": "Unused guest"},
    )
    assert saved["speakers"] == ["speaker_001", "speaker_002", "speaker_003"]

    removed = service.save(
        saved["review_path"],
        str(result),
        expected_sha256=saved["review_sha256"],
        anchors=saved["anchors"],
        speaker_labels={},
    )
    assert removed["speakers"] == ["speaker_001", "speaker_002"]
    assert removed["speaker_labels"] == {"speaker_001": "jan", "speaker_002": "anna"}
    assert "speaker_003" not in Path(removed["review_path"]).read_text(encoding="utf-8")


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
    assert restored["session"]["source_revision_path"] == ""


def test_browser_review_session_requires_saved_pointer(tmp_path: Path) -> None:
    service = controller(tmp_path)

    with pytest.raises(GuiReviewError, match="No saved") as missing:
        service.restore_session(str(tmp_path))

    assert missing.value.code == "GUI_REVIEW_SESSION_NOT_FOUND"


def test_browser_review_sessions_are_restored_per_canonical_result(tmp_path: Path) -> None:
    first_result = tmp_path / "first_results.json"
    second_result = tmp_path / "second_results.json"
    first_result.write_bytes(EXAMPLE.read_bytes())
    second_result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    project = tmp_path / "project"
    first = service.prepare(str(first_result), str(project / "reviews"))
    second = service.prepare(str(second_result), str(project / "reviews"))
    for result, prepared in ((first_result, first), (second_result, second)):
        service.remember_session(
            project_output_directory=str(project),
            result=str(result),
            review=prepared["review_path"],
            review_output_directory=str(project / "reviews"),
            revision_output_directory=str(project / "revisions"),
            export_output_directory=str(project / "exports"),
        )

    assert (
        service.restore_session(str(project), str(first_result))["review_path"]
        == first["review_path"]
    )
    assert (
        service.restore_session(str(project), str(second_result))["review_path"]
        == second["review_path"]
    )


def test_browser_review_can_start_from_automated_candidate(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    automated = apply_mock_correction(
        result,
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        provider=DeterministicMockCorrectionProvider(),
        output_directory=tmp_path / "candidates",
    )

    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"), str(automated.revision_path))

    assert prepared["source_verification"] == "automated_candidate"
    assert prepared["source_revision_path"] == str(automated.revision_path)

    preview = service.preview(
        prepared["review_path"], str(result), prepared["source_revision_path"]
    )
    assert preview["revision_number"] == 1
    applied = service.apply(
        prepared["review_path"],
        str(result),
        str(tmp_path / "revisions"),
        prepared["source_revision_path"],
    )
    assert load_transcript_revision(Path(applied["revision_path"])).parent_revision is not None


def test_browser_review_restores_automated_candidate_parent_from_session(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    automated = apply_mock_correction(
        result,
        config=ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work")),
        provider=DeterministicMockCorrectionProvider(),
        output_directory=tmp_path / "candidates",
    )
    project = tmp_path / "project"
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(project / "reviews"), str(automated.revision_path))
    service.remember_session(
        project_output_directory=str(project),
        result=str(result),
        review=prepared["review_path"],
        review_output_directory=str(project / "reviews"),
        revision_output_directory=str(project / "revisions"),
        export_output_directory=str(project / "exports"),
        source_revision=prepared["source_revision_path"],
    )

    restored = controller(tmp_path).restore_session(str(project))

    assert restored["session"]["source_revision_path"] == str(automated.revision_path)
    preview = controller(tmp_path).preview(
        restored["review_path"], str(result), restored["session"]["source_revision_path"]
    )
    assert preview["revision_number"] == 1


def test_gui_export_palette_preserves_production_and_real_timing(tmp_path: Path) -> None:
    import xml.etree.ElementTree as ET

    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    original = result.read_bytes()
    service = controller(tmp_path)
    review = service.prepare(str(result), str(tmp_path / "reviews"))
    service.preview(review["review_path"], str(result))
    applied = service.apply(review["review_path"], str(result), str(tmp_path / "revisions"))
    production = service.export(
        str(result), applied["revision_path"], str(tmp_path / "exports"), ["ytt"]
    )
    production_path = Path(production["written"][0])
    old_bytes = production_path.read_bytes()
    brand = service.export(
        str(result),
        applied["revision_path"],
        str(tmp_path / "exports"),
        ["ytt"],
        speaker_colors={"speaker_001": "#F5F7FA", "speaker_002": "#BF734D"},
    )
    brand_path = Path(brand["written"][0])
    assert brand_path != production_path
    assert production_path.read_bytes() == old_bytes
    assert result.read_bytes() == original
    old, new = ET.fromstring(old_bytes), ET.fromstring(brand_path.read_bytes())
    assert [pen.attrib["fc"] for pen in new.findall("./head/pen")][:2] == ["#F5F7FA", "#BF734D"]
    assert [p.attrib for p in old.findall("./body/p")] == [
        p.attrib for p in new.findall("./body/p")
    ]
    assert [p.text for p in old.findall("./body/p")] == [p.text for p in new.findall("./body/p")]


@pytest.mark.parametrize(
    "colors", [{"speaker_001": "red"}, {"speaker_999": "#123456"}, {"speaker_001": 123}]
)
def test_gui_export_rejects_invalid_palette_without_writing(tmp_path: Path, colors: dict) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    review = service.prepare(str(result), str(tmp_path / "reviews"))
    service.preview(review["review_path"], str(result))
    applied = service.apply(review["review_path"], str(result), str(tmp_path / "revisions"))
    with pytest.raises(GuiReviewError, match="known speaker"):
        service.export(
            str(result),
            applied["revision_path"],
            str(tmp_path / "exports"),
            ["ytt"],
            speaker_colors=colors,
        )
    assert not (tmp_path / "exports").exists()


def test_playback_locates_split_blocks_at_real_source_word_starts(tmp_path: Path) -> None:
    import json

    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    assert prepared["playback_sources"][0]["source_id"] == "source_001"
    prepared["anchors"][0]["blocks"] = [
        {"speaker_id": "speaker_001", "text": "Welcome"},
        {"speaker_id": "speaker_001", "text": "to another episode."},
        prepared["anchors"][0]["blocks"][1],
    ]
    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
    )
    words = json.loads(result.read_text())["transcript"]["segments"][0]["words"]
    position = service.playback_position(
        saved["review_path"], str(result), 0, 1, expected_sha256=saved["review_sha256"]
    )
    assert position["start_ms"] == words[1]["start_ms"]
    assert not position["approximate"]
    with pytest.raises(ValueError, match="existing transcript"):
        service.playback_position(
            saved["review_path"], str(result), 0, -1, expected_sha256=saved["review_sha256"]
        )


def test_playback_inserted_text_uses_disclosed_real_anchor_time(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    prepared["anchors"][0]["blocks"].insert(0, {"speaker_id": "speaker_001", "text": "Inserted."})
    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
    )
    position = service.playback_position(
        saved["review_path"], str(result), 0, 0, expected_sha256=saved["review_sha256"]
    )
    assert position == {"start_ms": prepared["anchors"][0]["start_ms"], "approximate": True}


def test_playback_rejects_an_externally_changed_review(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    with pytest.raises(GuiReviewError) as error:
        service.playback_position(
            prepared["review_path"], str(result), 0, 0, expected_sha256="0" * 64
        )
    assert error.value.code == "GUI_REVIEW_CONFLICT"


def test_source_filename_follows_original_words_after_speaker_reassignment(tmp_path: Path) -> None:
    import json

    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    service = controller(tmp_path)
    prepared = service.prepare(str(result), str(tmp_path / "reviews"))
    names = [source["filename"] for source in json.loads(result.read_text())["sources"]]
    assert prepared["anchors"][0]["block_sources"] == [[names[0]], [names[1]]]
    prepared["anchors"][0]["blocks"][0]["speaker_id"] = "speaker_002"
    saved = service.save(
        prepared["review_path"],
        str(result),
        expected_sha256=prepared["review_sha256"],
        anchors=prepared["anchors"],
    )
    assert saved["anchors"][0]["block_sources"][0] == [names[0]]
