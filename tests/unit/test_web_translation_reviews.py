from pathlib import Path

from ewp_transcripts.application import apply_automated_translation
from ewp_transcripts.automated_translation import DeterministicMockTranslationProvider
from ewp_transcripts.config import ApplicationConfig, RuntimeConfig
from ewp_transcripts.web_translation_reviews import GuiTranslationReviewController
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/results.example.json"


def test_gui_translation_review_prepare_save_preview_apply_and_export(tmp_path: Path) -> None:
    result = tmp_path / EXAMPLE.name
    result.write_bytes(EXAMPLE.read_bytes())
    config = ApplicationConfig(runtime=RuntimeConfig(work_root=tmp_path / "work"))
    candidate = apply_automated_translation(
        result,
        config=config,
        provider=DeterministicMockTranslationProvider(),
        target_language="pl",
        output_directory=tmp_path / "candidates",
    )
    assert candidate.translation_path is not None
    paths = GuiWorkflowController((tmp_path.resolve(),))
    controller = GuiTranslationReviewController(
        config=config, resolve_path=paths.resolve_allowed_path
    )

    review = controller.prepare(
        result=str(result),
        revision="",
        parent=str(candidate.translation_path),
        output=str(tmp_path / "reviews"),
    )
    loaded = controller.document(review["review_path"], result, None, candidate.translation_path)
    assert loaded["review_sha256"] == review["review_sha256"]
    targets = [
        {"unit_id": unit["unit_id"], "target_text": unit["target_text"]} for unit in review["units"]
    ]
    saved = controller.save(
        review=review["review_path"],
        result=str(result),
        revision="",
        parent=str(candidate.translation_path),
        expected_sha256=review["review_sha256"],
        targets=targets,
    )
    controller.preview(
        review=saved["review_path"],
        result=str(result),
        revision="",
        parent=str(candidate.translation_path),
    )
    applied = controller.apply(
        review=saved["review_path"],
        result=str(result),
        revision="",
        parent=str(candidate.translation_path),
        output=str(tmp_path / "accepted"),
    )
    exported = controller.audit_export(
        translation=applied["translation_path"],
        result=str(result),
        revision="",
        audit_output=str(tmp_path / "audits"),
        export_output=str(tmp_path / "exports"),
        formats=["txt", "srt", "vtt", "html"],
    )

    assert applied["final"] is True
    assert Path(exported["audit_path"]).is_file()
    assert len(exported["written"]) == 5
