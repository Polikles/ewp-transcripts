"""Offline instructions retain source docs, numbering and a fixed route boundary."""

import json
from pathlib import Path

import pytest

from ewp_transcripts.web_guides import GUIDE_FILES
from ewp_transcripts.web_server import WebConfiguration, dispatch_get

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src/ewp_transcripts/web_assets"


def test_packaged_guides_match_docs_and_short_instruction_numbers() -> None:
    metadata = json.loads((ASSETS / "guides/index.json").read_text())
    assert set(metadata) == {
        "workspace",
        "correction",
        "review",
        "translation",
        "semantic-review",
        "dictionary",
        "saved",
        "settings",
    }
    for guide in metadata.values():
        text = (ROOT / guide["document"]).read_text()
        assert text == (ASSETS / "guides" / GUIDE_FILES[guide["slug"]]).read_text()
        for number, step in enumerate(guide["steps"], 1):
            assert f"{number}. {step['title']['en']}: {step['text']['en']}" in text
            assert step["title"]["pl"] and step["text"]["pl"]
    assert (ROOT / "WSL config/UBUNTU_UPGRADE.md").read_bytes() == (
        ASSETS / "guides/ubuntu-upgrade.md"
    ).read_bytes()


@pytest.mark.parametrize("slug", GUIDE_FILES)
def test_offline_guides_serve_readable_html_without_scripts(slug: str) -> None:
    response = dispatch_get(
        WebConfiguration.create(port=8765),
        server_port=8765,
        host="localhost:8765",
        target=f"/help/{slug}",
    )
    assert response.status == 200
    assert response.content_type == "text/html; charset=utf-8"
    assert b"<h1>" in response.body and b"<ol>" in response.body
    assert b"<script" not in response.body
    assert b"/assets/app.css" in response.body


@pytest.mark.parametrize(
    "path", ["/help/../../pyproject.toml", "/help/unknown", "/help/%2e%2e/config"]
)
def test_guide_routes_never_resolve_arbitrary_files(path: str) -> None:
    response = dispatch_get(
        WebConfiguration.create(port=8765),
        server_port=8765,
        host="localhost:8765",
        target=path,
    )
    assert response.status == 404
