"""Optional Playwright verification for the offline artist-reference ZIP contents."""

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import expect, sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check an unpacked artist reference without server/network."
    )
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.package.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((root / "manifest-sha256.json").read_text())
    for name, digest in manifest.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name

    class LocalLinks(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for name, value in attrs:
                if name not in {"href", "src"} or not value:
                    continue
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (document.parent / unquote(parsed.path)).resolve()
                assert target.is_relative_to(root), (document, value)
                assert target.is_file(), (document, value)

    guides = list((root / "guides").rglob("*.html"))
    assert len(guides) == 30
    for document in guides:
        LocalLinks().feed(document.read_text())
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        external = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("http://**/*", lambda route: (external.append(route.request.url), route.abort()))
        page.route(
            "https://**/*", lambda route: (external.append(route.request.url), route.abort())
        )
        page.goto((root / "index.html").as_uri())
        page.wait_for_function('() => typeof csrfToken !== "undefined" && csrfToken.length > 0')
        expect(page.locator("#transcription-jobs tbody tr")).to_have_count(3)
        for stage in (
            "workspace",
            "correction",
            "review",
            "translation",
            "semantic-review",
            "dictionary",
            "saved",
            "settings",
        ):
            page.locator(f'[data-gui-stage="{stage}"]').click()
        page.locator('[data-gui-stage="review"]').click()
        page.locator("#stage-queue-review .stage-queue-item button").first.click()
        expect(page.locator("#review-editor textarea").first).to_be_visible()
        page.wait_for_function("() => playbackAudio.readyState >= 1")
        page.locator(".review-seek").nth(1).click()
        page.wait_for_function("() => playbackAudio.currentTime>=4.32")
        page.evaluate("playbackAudio.pause()")
        page.locator("#review-editor textarea").first.fill("Artist edited sample text.")
        page.locator("#save-review").click()
        expect(page.locator("#review-status")).to_contain_text("Draft saved")
        page.locator("#preview-review").click()
        expect(page.locator("#apply-review")).to_be_enabled()
        page.locator("#review-workflow input[name=verified]").check()
        page.locator("#apply-review").click()
        expect(page.locator("#export-review")).to_be_enabled()
        page.locator("#export-review").click()
        expect(page.locator("#review-status")).to_contain_text("exports completed")
        page.locator('[data-gui-stage="semantic-review"]').click()
        page.locator("#stage-queue-semantic-review .stage-queue-item button").first.click()
        expect(page.locator("#translation-review-editor textarea").first).to_be_visible()
        page.locator("#translation-review-editor textarea").first.fill(
            "Przegląd tłumaczenia przez grafika."
        )
        page.locator("#save-translation-review").click()
        expect(page.locator("#translation-review-status")).to_contain_text("saved")
        page.locator("#preview-translation-review").click()
        expect(page.locator("#apply-translation-review")).to_be_enabled()
        page.locator("#translation-review-confirmed").check()
        page.locator("#apply-translation-review").click()
        expect(page.locator("#export-translation-review")).to_be_enabled()
        page.locator("#export-translation-review").click()
        expect(page.locator("#translation-review-status")).to_contain_text("audited and exported")
        page.locator('[data-gui-stage="dictionary"]').click()
        expect(page.locator(".library-item")).to_have_count(1)
        page.locator("#library-example").click()
        page.locator("#library-id").fill("artist-example-v2")
        page.locator("#library-save").click()
        expect(page.locator(".library-item")).to_have_count(2)
        page.locator('[data-gui-stage="review"]').click()
        page.locator("#review-speaker-names").evaluate("e=>e.open=true")
        page.locator("#gui-export-palette").select_option("brand")
        page.locator("#gui-preview-palette").click()
        page.locator("#gui-apply-palette").click()
        page.locator("#gui-palette-name").fill("Artist sample")
        page.locator("#gui-save-palette").click()
        expect(page.locator("#gui-palette-status")).to_contain_text("Custom profile saved")
        page.locator('[data-gui-stage="correction"]').click()
        page.locator("#stage-queue-correction .stage-queue-item button").first.click()
        page.evaluate("correctionForm.querySelectorAll('details').forEach(e=>e.open=true)")
        page.locator("#correction-workflow input[name=confirmed]").check()
        page.locator("#generate-correction").click()
        expect(page.locator("#correction-status")).to_contain_text("candidate generated")
        page.locator('[data-gui-stage="saved"]').click()
        page.locator("#workspace-name").fill("Artist review")
        page.locator("#save-workspace").click()
        expect(page.locator("#workspace-status")).to_contain_text("Workspace saved")
        page.locator('[data-gui-stage="settings"]').click()
        page.locator("#test-dependencies").click()
        expect(page.locator("#dependency-checks")).to_contain_text("Visual preview only")
        page.locator("#artist-demo-toolbar").get_by_role(
            "button", name="Running", exact=True
        ).click()
        page.locator('[data-gui-stage="workspace"]').click()
        expect(page.locator(".gui-runtime-progress progress")).to_be_visible()
        for locale in ("en", "pl"):
            page.locator("#gui-locale").select_option(locale)
            for theme in ("light", "dark"):
                page.locator("#gui-theme").select_option(theme)
                for width in (960, 1920):
                    page.set_viewport_size({"width": width, "height": 1080})
                    page.screenshot(path=str(args.output / f"artist-{locale}-{theme}-{width}.png"))
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        # Help must work from file://, including locale query removal and cross-language links.
        for locale in ("en", "pl"):
            page.locator("#gui-locale").select_option(locale)
            with page.expect_popup() as opened:
                page.locator('#gui-stage-instructions a[href^="/help/"]').first.click()
            guide = opened.value
            guide.wait_for_load_state()
            expect(guide.locator("html")).to_have_attribute("lang", locale)
            expect(guide.locator("h1")).to_be_visible()
            other = "pl" if locale == "en" else "en"
            guide.locator(f".guide-languages a[lang={other}]").click()
            expect(guide.locator("html")).to_have_attribute("lang", other)
            guide.close()
        page.goto((root / "icon-inventory.html").as_uri())
        expect(page.locator("tr")).to_have_count(15)
        assert not errors, errors
        assert not external, external
        print(
            json.dumps(
                {
                    "result": "PASS",
                    "frontend": "file://, no backend/network",
                    "checks": "stages, playback, editors, palettes, exports, dictionaries, "
                    "saved work, settings, EN/PL/themes, layout, 30 offline manuals and inventory",
                    "pageErrors": errors,
                    "externalRequests": external,
                }
            )
        )
        browser.close()


if __name__ == "__main__":
    main()
