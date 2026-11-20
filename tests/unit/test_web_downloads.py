from pathlib import Path

import pytest

from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.web_downloads import GuiExportDownloads
from ewp_transcripts.web_reviews import GuiReviewController
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[2]


def setup_exports(tmp_path: Path):
    result = tmp_path / "episode_results.json"
    result.write_bytes((ROOT / "examples/results.example.json").read_bytes())
    config = ApplicationConfig()
    resolver = GuiWorkflowController((tmp_path,)).resolve_allowed_path
    reviews = GuiReviewController(config=config, resolve_path=resolver)
    draft = reviews.prepare(str(result), str(tmp_path / "reviews"))
    reviews.preview(draft["review_path"], str(result))
    applied = reviews.apply(draft["review_path"], str(result), str(tmp_path / "revisions"))
    revision = applied["revision_path"]
    exports = reviews.export(
        str(result),
        revision,
        str(tmp_path / "exports"),
        ["txt", "srt", "vtt", "html", "ytt", "segments"],
    )

    def downloads():
        return GuiExportDownloads(
            config=config, resolve_path=resolver, registry=tmp_path / "state/downloads.json"
        )

    return downloads, str(result), revision, exports


def test_legacy_existing_exports_download_exact_bytes_and_recover_after_restart(tmp_path: Path):
    factory, result, revision, _exported = setup_exports(tmp_path)
    service = factory()
    request = dict(result=result, revision=revision, directory=str(tmp_path / "exports"))
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (tmp_path / "exports").iterdir()
        if path.is_file() and not path.name.startswith(".")
    }
    listed = service.list(**request)["exports"]
    assert len(listed) == 6
    for item in listed:
        name, payload = service.open(item["url"].rsplit("/", 1)[1])
        assert payload == before[name][0]
    restarted = factory()
    with pytest.raises(ValueError, match="expired"):
        restarted.open(listed[0]["url"].rsplit("/", 1)[1])
    assert len(restarted.list(**request)["exports"]) == 6
    assert all(
        path.stat().st_mtime_ns == before[path.name][1]
        for path in (tmp_path / "exports").iterdir()
        if path.name in before
    )


def test_download_rejects_modified_artifact_lineage_symlink_and_arbitrary_path(tmp_path: Path):
    factory, result, revision, _exported = setup_exports(tmp_path)
    service = factory()
    request = dict(result=result, revision=revision, directory=str(tmp_path / "exports"))
    listed = service.list(**request)["exports"]
    item = listed[0]
    path = tmp_path / "exports" / item["filename"]
    original = path.read_bytes()
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        service.open(item["url"].rsplit("/", 1)[1])
    assert item["filename"] in service.list(**request)["unavailable"]
    path.unlink()
    secret = tmp_path / "private.txt"
    secret.write_bytes(original)
    path.symlink_to(secret)
    with pytest.raises(ValueError, match="Symbolic"):
        service.open(item["url"].rsplit("/", 1)[1])
    with pytest.raises(ValueError):
        service.open(str(secret))
    path.unlink()
    path.write_bytes(original)
    Path(revision).write_bytes(Path(revision).read_bytes() + b"\n")
    with pytest.raises(ValueError, match="lineage"):
        service.open(item["url"].rsplit("/", 1)[1])


def test_registry_retains_exact_custom_palette_export_versions(tmp_path: Path):
    from ewp_transcripts.config import ApplicationConfig
    from ewp_transcripts.web_reviews import GuiReviewController
    from ewp_transcripts.web_workflows import GuiWorkflowController

    factory, result, revision, _exported = setup_exports(tmp_path)
    reviews = GuiReviewController(
        config=ApplicationConfig(),
        resolve_path=GuiWorkflowController((tmp_path,)).resolve_allowed_path,
    )
    service = factory()
    for color in ("#112233", "#446688"):
        exported = reviews.export(
            result,
            revision,
            str(tmp_path / "exports"),
            ["ytt"],
            speaker_colors={"speaker_001": color},
        )
        service.register(result=result, revision=revision, paths=exported["written"])
    files = factory().list(result=result, revision=revision, directory=str(tmp_path / "exports"))[
        "exports"
    ]
    ytt = [item for item in files if item["filename"].endswith(".ytt")]
    assert len(ytt) == 3
    assert len({item["sha256"] for item in ytt}) == 3


def test_damaged_legacy_segments_does_not_hide_other_registered_downloads(tmp_path: Path):
    import json

    factory, result, revision, _exported = setup_exports(tmp_path)
    service = factory()
    request = dict(result=result, revision=revision, directory=str(tmp_path / "exports"))
    assert len(service.list(**request)["exports"]) == 6
    segments = next((tmp_path / "exports").glob("*segments*.json"))
    document = json.loads(segments.read_text())
    document["generated_at"] = "2026-11-20T12:00:00"
    segments.write_text(json.dumps(document))
    listing = service.list(**request)
    assert len(listing["exports"]) == 5
    assert listing["unavailable"] == [segments.name]
