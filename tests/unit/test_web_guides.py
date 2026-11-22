"""Bilingual offline manuals retain numbering, local navigation and a fixed route boundary."""

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from ewp_transcripts.web_guides import GUIDE_FILES, _markdown, render_guide
from ewp_transcripts.web_server import WebConfiguration, dispatch_get

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src/ewp_transcripts/web_assets"


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.hrefs.extend(value for name, value in attrs if name == "href" and value)


@pytest.mark.parametrize("locale", ["en", "pl"])
def test_packaged_guides_match_complete_docs_and_short_instruction_numbers(locale: str) -> None:
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
    folder = ROOT / "docs/gui" / ("pl" if locale == "pl" else "")
    packaged = ASSETS / "guides" / ("pl" if locale == "pl" else "")
    for slug, filename in GUIDE_FILES.items():
        document = folder / ("README.md" if slug == "index" else filename)
        assert document.read_bytes() == (packaged / filename).read_bytes()
    for guide in metadata.values():
        text = (packaged / GUIDE_FILES[guide["slug"]]).read_text()
        for number, step in enumerate(guide["steps"], 1):
            assert f"{number}. {step['title'][locale]}: {step['text'][locale]}" in text
        assert (ROOT / guide["document"]).exists()


@pytest.mark.parametrize("slug", GUIDE_FILES)
@pytest.mark.parametrize("locale", ["en", "pl"])
def test_offline_guides_and_links_work_without_scripts(slug: str, locale: str) -> None:
    config = WebConfiguration.create(port=8765)
    response = dispatch_get(
        config, server_port=8765, host="localhost:8765", target=f"/help/{slug}?lang={locale}"
    )
    assert response.status == 200
    assert response.content_type == "text/html; charset=utf-8"
    body = response.body.decode()
    assert "<h1>" in body and "<ol>" in body
    assert f'<html lang="{locale}">' in body
    assert "<script" not in body and "/assets/app.css" in body
    for stylesheet in re.findall(r'<link rel="stylesheet" href="([^"]+)"', body):
        assert (
            dispatch_get(config, server_port=8765, host="localhost:8765", target=stylesheet).status
            == 200
        )
    links = Links()
    links.feed(body)
    assert f"/help/transcribe?lang={locale}" in links.hrefs
    for href in links.hrefs:
        if href.startswith("/help"):
            target = urlsplit(href)
            assert parse_qs(target.query)["lang"][0] in {"en", "pl"}
            linked = dispatch_get(config, server_port=8765, host="localhost:8765", target=href)
            assert linked.status == 200, href


@pytest.mark.parametrize("locale", ["pl", "en", "%3Cscript%3E"])
def test_help_index_and_manual_use_requested_language_or_safe_english_fallback(locale: str) -> None:
    for path in ("/help", "/help/source-review"):
        response = dispatch_get(
            WebConfiguration.create(port=8765),
            server_port=8765,
            host="localhost:8765",
            target=f"{path}?lang={locale}",
        )
        assert response.status == 200
        body = response.body.decode()
        if locale == "pl":
            assert '<html lang="pl">' in body
            assert "Weryfikacja i eksport źródła" in body
            assert "Otwórz EwP Transcripts" in body
            assert "Inne instrukcje" in body and "Instrukcje pracy z programem" in body
            assert "Zamknij tę kartę aby powrócić do swojej pracy." in body
        else:
            assert '<html lang="en">' in body
            assert "Source review &amp; export" in body and "Open EwP Transcripts" in body
        assert "<script" not in body


def test_manual_markup_escapes_html_and_rejects_active_and_arbitrary_links() -> None:
    body = _markdown(
        "# Safe\n\n<script>alert(1)</script> & raw\n\n"
        "[bad](javascript:alert) [path](../../private.json) [safe](settings.md)\n\n"
        "- **bold** and `literal <img>`\n\n```text\n<script>code</script>\n```",
        "pl",
    )
    assert "<script>" not in body and "<img>" not in body
    assert "&lt;script&gt;" in body and "<strong>bold</strong>" in body
    assert "javascript:" not in body and "../../private" not in body
    assert 'href="/help/settings?lang=pl"' in body
    assert "<ul>" in body and "<pre><code>" in body
    assert render_guide("settings", locale="../private") == render_guide("settings", locale="en")


@pytest.mark.parametrize(
    "path",
    [
        "/help/../../pyproject.toml",
        "/help/unknown",
        "/help/%2e%2e/config",
        "/help/pl/../../private",
        "/help/pl/transcribe",
    ],
)
def test_guide_routes_never_resolve_arbitrary_files(path: str) -> None:
    response = dispatch_get(
        WebConfiguration.create(port=8765),
        server_port=8765,
        host="localhost:8765",
        target=path,
    )
    assert response.status == 404
