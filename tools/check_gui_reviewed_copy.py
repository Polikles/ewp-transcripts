"""Verify integrated owner copy against its reference in a disposable loopback GUI.

Uses only repository reference text and synthetic formatter values. No providers or media jobs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert urlsplit(args.url).hostname in {"127.0.0.1", "localhost"}
    args.output.mkdir(parents=True)
    reference = json.loads((ROOT / "docs/ui-language/integration.json").read_text())
    changes = reference["changes"]
    errors, external, cases = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 1080})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(
            "**/*",
            lambda route: (
                route.continue_()
                if urlsplit(route.request.url).hostname in {"127.0.0.1", "localhost"}
                else (external.append(route.request.url), route.abort())
            ),
        )
        page.goto(args.url)
        expect(page.locator("#compatibility")).to_have_text("Status: local service ready")
        page.wait_for_function(
            "()=>typeof guiWorkflowGuides!=='undefined' && guiWorkflowGuides?.review"
        )
        static = [row for row in changes if row["kind"] == "text"]
        for locale in ["en", "pl", "en", "pl"]:
            page.locator("#gui-locale").select_option(locale)
            failures = page.evaluate(
                """({rows,locale})=>rows.flatMap(row=>{
              const actual=guiUiText(row.en).trim(),expected=(locale==='pl'?row.pl:row.en).trim();
              return actual===expected?[]:[{id:row.id,actual,expected}];})""",
                {"rows": static, "locale": locale},
            )
            assert not failures, failures
        for row in changes:
            if row["kind"] == "guide":
                parts = row["id"].removeprefix("guide.").split(".")
                actual = page.evaluate(
                    "parts=>{let v=guiWorkflowGuides;for(const p of parts)v=v[p];return v.pl}",
                    parts,
                )
                assert actual == row["pl"], row
        for row in reference.get("derived_changes", []):
            parts = row["id"].removeprefix("guide.").split(".")
            actual = page.evaluate(
                "parts=>{let v=guiWorkflowGuides;for(const p of parts)v=v[p];return v.pl}", parts
            )
            assert actual == row["pl"], row
        warning = next(row for row in changes if row["id"] == "ui.e34d7f4f8c23f4bf")
        expected = warning["pl"].replace(
            "{payload_source_verification}", page.evaluate("guiUiText('raw')")
        )
        actual = page.evaluate(
            "text=>guiUiText(text)", warning["en"].replace("{payload_source_verification}", "raw")
        )
        assert actual == expected, (actual, expected)
        assert (
            page.evaluate("guiUiText('speaker_001 display name')")
            == "speaker_001 wyświetlana nazwa"
        )
        for locale in ["en", "pl"]:
            page.locator("#gui-locale").select_option(locale)
            for theme in ["light", "dark"]:
                page.locator("#gui-theme").select_option(theme)
                for width in [390, 960, 1920]:
                    page.set_viewport_size({"width": width, "height": 1080})
                    for stage in ["dictionary", "saved", "settings"]:
                        page.locator(f'[data-gui-stage="{stage}"]').click()
                        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
                        cases.append(
                            {"locale": locale, "theme": theme, "width": width, "stage": stage}
                        )
                        if locale == "pl" and theme == "light" and width == 960:
                            page.screenshot(path=str(args.output / f"{stage}.png"), full_page=True)
                    if locale == "pl":
                        expect(page.locator(".gui-artwork-credit")).to_contain_text(
                            "adresem zastępczym"
                        )
            page.locator('[data-gui-stage="review"]').click()
            link = page.locator('#gui-stage-instructions a[href^="/help/"]').first
            assert f"lang={locale}" in link.get_attribute("href")
            response = page.request.get(args.url + link.get_attribute("href"))
            assert response.ok
            body = response.text()
            for label in (
                [
                    "Otwórz EwP Transcripts",
                    "Inne instrukcje",
                    "Instrukcje pracy z programem",
                    "Zamknij tę kartę aby powrócić do swojej pracy.",
                ]
                if locale == "pl"
                else ["Open EwP Transcripts", "Other workflow guides"]
            ):
                assert label in body
            assert "<script" not in body
        assert not errors and not external, (errors, external)
        result = {
            "reference_rows": reference["rows"],
            "owner_changed_rows": len(changes),
            "exact_copy_checked": len(static),
            "dynamic_templates_checked": 2,
            "quick_guides_checked": 2,
            "derived_quick_guides_checked": len(reference.get("derived_changes", [])),
            "help_chrome_checked": 4,
            "locale_roundtrips": 4,
            "layout_cases": len(cases),
            "page_errors": errors,
            "external_requests": external,
            "real_provider_calls": 0,
        }
        (args.output / "report.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        browser.close()


if __name__ == "__main__":
    main()
