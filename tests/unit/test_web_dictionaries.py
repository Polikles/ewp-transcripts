from pathlib import Path

from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.review import ReviewSpeakerBlock
from ewp_transcripts.review_service import prepare_review
from ewp_transcripts.revision_service import build_revision
from ewp_transcripts.web_dictionaries import GuiDictionaryController
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[2]


def test_gui_dictionary_retains_decisions_and_publishes(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    revisions = tmp_path / "revisions"
    canonical.mkdir()
    revisions.mkdir()
    source_result = ROOT / "examples/results.example.json"
    result = canonical / "case_results.json"
    result.write_bytes(source_result.read_bytes())
    review = prepare_review(result)
    blocks = list(review.anchors[0].speaker_blocks)
    blocks[0] = ReviewSpeakerBlock(
        speaker_id=blocks[0].speaker_id,
        text=blocks[0].text.replace("Welcome", "Greetings"),
    )
    edited = review.model_copy(
        update={
            "anchors": (review.anchors[0].model_copy(update={"speaker_blocks": tuple(blocks)}),)
        }
    )
    revision = build_revision(edited, load_canonical_result(result), base_path=result)
    (revisions / "S01E01_revision_001.json").write_text(
        revision.model_dump_json(), encoding="utf-8"
    )
    paths = GuiWorkflowController((tmp_path.resolve(),))
    controller = GuiDictionaryController(resolve_path=paths.resolve_allowed_path)

    proposal = controller.propose(
        canonical_directory=str(canonical),
        revision_directory=str(revisions),
        output_root=str(tmp_path),
        project_id="example",
        minimum_occurrences=1,
        previous_dictionary="",
    )
    decisions = [
        {"source": item["source"], "target": item["target"], "status": "rejected"}
        for item in proposal["candidates"]
    ]
    saved = controller.save(
        proposal_path=proposal["proposal_path"],
        expected_sha256=proposal["proposal_sha256"],
        decisions=decisions,
    )
    published = controller.publish(
        proposal_path=saved["proposal_path"],
        dictionary_id="example-pl-v1",
        output_root=str(tmp_path),
    )

    assert saved["counts"]["pending"] == 0
    assert Path(published["dictionary_path"]).is_file()
    assert all(item["status"] == "rejected" for item in published["dictionary"]["entries"])


def test_gui_dictionary_catalog_discovers_both_project_dictionary_kinds(tmp_path: Path) -> None:
    source = ROOT / "dictionaries/ethics-in-the-loop"
    correction = source / "correction/pl/ethics-in-the-loop-pl-v1.json"
    translation = source / "translation/pl-en/ethics-in-the-loop-pl-en-v1.json"
    (tmp_path / "catalog").mkdir()
    (tmp_path / "catalog" / correction.name).write_bytes(correction.read_bytes())
    (tmp_path / "catalog" / translation.name).write_bytes(translation.read_bytes())
    paths = GuiWorkflowController((tmp_path.resolve(),))

    catalog = GuiDictionaryController(resolve_path=paths.resolve_allowed_path).catalog(
        str(tmp_path / "catalog")
    )

    assert catalog["count"] == 2
    assert {item["kind"] for item in catalog["items"]} == {"correction", "translation"}


def test_gui_dictionary_catalog_ignores_proposals_and_unrelated_json() -> None:
    paths = GuiWorkflowController((ROOT.resolve(),))

    catalog = GuiDictionaryController(resolve_path=paths.resolve_allowed_path).catalog(
        str(ROOT / "dictionaries")
    )

    assert catalog["count"] == 3
    assert {item["dictionary_id"] for item in catalog["items"]} == {
        "ethics-in-the-loop-pl-v1",
        "ethics-in-the-loop-pl-en-v1",
        "ethics-in-the-loop-pl-en-v2",
    }
