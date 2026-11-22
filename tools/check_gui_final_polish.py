"""Verify final duplicate-save rejection and key feedback using a synthetic loopback server."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert urlsplit(args.url).hostname in {"localhost", "127.0.0.1"}
    args.output.mkdir(parents=True)
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
        output = args.output / "results"
        output.mkdir()
        page.locator("#output-path").fill(str(output))
        page.locator("#output-path").press("Tab")
        page.locator('[data-gui-stage="saved"]').click()
        page.locator("#workspace-name").fill("Episode save " + args.output.name)
        page.locator("#save-workspace").click()
        expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
        files = list(output.glob("*.workspace.json"))
        assert len(files) == 1
        before = files[0].read_bytes()
        page.locator("#workspace-list").select_option("")
        page.locator("#gui-locale").select_option("pl")
        page.locator("#workspace-name").fill("Episode save " + args.output.name)
        page.locator("#save-workspace").click()
        expect(page.locator("#workspace-status")).to_contain_text(
            "Taki zapis już istnieje, spróbuj innej nazwy"
        )
        expect(page.locator("#workspace-name")).to_have_attribute("aria-invalid", "true")
        assert len(list(output.glob("*.workspace.json"))) == 1
        assert files[0].read_bytes() == before
        page.locator("#workspace-name").fill("Another save " + args.output.name)
        page.locator("#save-workspace").click()
        expect(page.locator("#workspace-status")).to_contain_text("Zapisano obszar pracy:")
        assert len(list(output.glob("*.workspace.json"))) == 2
        page.locator("#gui-locale").select_option("en")
        page.locator("#save-workspace").click()
        expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
        assert len(list(output.glob("*.workspace.json"))) == 2
        page.locator('[data-gui-stage="workspace"]').click()
        page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
        page.locator("#cloud-asr-provider").select_option("openrouter")
        page.locator("#cloud-asr-key").click()
        for locale in ["en", "pl"]:
            page.evaluate(
                "locale=>{const e=document.querySelector('#gui-locale');"
                "e.value=locale;e.dispatchEvent(new Event('change',{bubbles:true}));}",
                locale,
            )
            for theme in ["light", "dark"]:
                page.evaluate(
                    "theme=>{const e=document.querySelector('#gui-theme');"
                    "e.value=theme;e.dispatchEvent(new Event('change',{bubbles:true}));}",
                    theme,
                )
                for width in [390, 960, 1920]:
                    page.set_viewport_size({"width": width, "height": 1080})
                    page.locator("#check-openrouter-key").click()
                    expect(page.locator("#openrouter-key-check-status")).to_have_text(
                        "Klucz i połączenie działają.\nNie wysłano audio."
                        if locale == "pl"
                        else "Key and connection are ready.\nNo audio was uploaded."
                    )
                    geometry = page.locator(".credential-key-check").evaluate("""e=>{
                        const b=e.querySelector('button').getBoundingClientRect();
                        const s=e.querySelector('p').getBoundingClientRect();
                        return {buttonRight:b.right,statusLeft:s.left,bottom:s.bottom,
                            right:s.right,dialogRight:e.closest('.credential-dialog-panel')
                            .getBoundingClientRect().right};}""")
                    assert geometry["buttonRight"] <= geometry["statusLeft"], geometry
                    assert geometry["right"] <= geometry["dialogRight"], geometry
                    cases.append({"locale": locale, "theme": theme, "width": width})
                    if locale == "pl" and theme == "light" and width == 960:
                        page.locator(".credential-dialog-panel").screenshot(
                            path=str(args.output / "key-dialog.png")
                        )
        assert not errors and not external, (errors, external)
        report = {
            "duplicate_save_rejected_without_mutation": True,
            "existing_update_passes": True,
            "dialog_cases": len(cases),
            "page_errors": errors,
            "external_requests": external,
            "real_provider_calls": 0,
        }
        (args.output / "report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
        browser.close()


if __name__ == "__main__":
    main()
