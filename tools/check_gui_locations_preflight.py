"""Check folder recall, readable saves and cloud-key gating using an isolated stub server.

Run once with --output, restart the same fake-service server, then run --recover. The recovery
phase deliberately starts the stub; --confirm-fake-service is required. Never use a real provider.
"""

from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def stage(page, value):
    page.locator(f'[data-gui-stage="{value}"]').click()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--confirm-fake-service", action="store_true")
    args = parser.parse_args()
    assert urlsplit(args.url).hostname in {"localhost", "127.0.0.1"}
    if args.recover and not args.confirm_fake_service:
        parser.error("Use only a stub server and confirm it with --confirm-fake-service")
    args.output.mkdir(parents=True, exist_ok=args.recover)
    errors, external, cases = [], [], []
    project = args.output / "Desktop results"
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
        if args.recover:
            expect(page.locator("#output-path")).to_have_value(str(project))
            stage(page, "saved")
            options = page.locator(
                f"#workspace-list option[data-storage-directory={json.dumps(str(project))}]"
            )
            option = options.filter(has_text="Test Żółć")
            expect(option).to_have_count(1)
            expect(options.filter(has_text="Second workspace")).to_have_count(1)
            page.locator("#workspace-list").select_option(option.get_attribute("value"))
            page.locator("#load-workspace").click()
            expect(page.locator("#workspace-status")).to_contain_text("Workspace loaded:")
            expect(page.locator("#workspace-file-location")).to_contain_text("Test Żółć--")
            page.wait_for_function("()=>guiQueueJobs.length===1 && !workspaceRestoreBusy")
            stage(page, "workspace")
            page.locator("#cloud-asr-confirmed").check()
            page.locator("#start-queue").click()
            expect(page.locator("#operation-status")).to_contain_text("GUI_OPENROUTER_KEY_REQUIRED")
            assert page.evaluate("guiQueueJobs[0].status") == "staged"
            assert not list(project.glob("*.partial.json")) and not list(
                project.glob("*.failed.json")
            )
            page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
            page.locator("#cloud-asr-key").click()
            page.locator("#openrouter-api-key").fill("invalid-fixture-key")
            page.locator("#save-openrouter-key").click()
            expect(page.locator("#openrouter-key-dialog-status")).to_contain_text(
                "active for this session"
            )
            page.locator("#cancel-openrouter-key").click()
            page.locator("#cloud-asr-confirmed").check()
            page.locator("#start-queue").click()
            expect(page.locator("#operation-status")).to_contain_text(
                "GUI_OPENROUTER_PREFLIGHT_FAILED"
            )
            assert page.evaluate("guiQueueJobs[0].status") == "staged"
            assert not list(project.glob("*.partial.json")) and not list(
                project.glob("*.failed.json")
            )
            page.locator("#cloud-asr-key").click()
            page.locator("#credential-use").click()
            expect(page.locator("#openrouter-key-dialog-status")).to_contain_text(
                "active for this session"
            )
            expect(page.locator("#save-openrouter-key")).to_be_disabled()
            page.locator("#cancel-openrouter-key").click()
            page.locator("#cloud-asr-confirmed").check()
            page.locator("#start-queue").click()
            page.wait_for_function("()=>guiQueueJobs[0].status==='completed'")
        else:
            page.evaluate(
                "async()=>{await queuePost('/api/v1/transcriptions/clear-current',"
                "{confirmed:true});await refreshJobs();}"
            )
            audio = args.output / "s0e19.wav"
            with wave.open(str(audio), "wb") as out:
                out.setparams((1, 2, 16000, 0, "NONE", ""))
                out.writeframes(b"\0\0" * 16000 * 4)
            page.locator("#output-path").fill(str(project))
            page.locator("#output-path").press("Tab")
            page.locator("#workflow input[type=file]").set_input_files(audio)
            page.wait_for_function("()=>!nativeMediaButton.disabled")
            page.locator("[data-episode-speakers]").select_option("1")
            page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
            page.locator("#cloud-asr-provider").select_option("openrouter")
            page.locator("#workflow button[value=dry-run]").click()
            expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
            page.locator("#workflow input[name=confirmed]").check()
            page.locator("#workflow button[value=transcriptions]").click()
            page.wait_for_function("()=>guiQueueJobs.length===1")
            stage(page, "saved")
            for name in ["Test Żółć", "Second workspace"]:
                page.locator("#workspace-list").select_option("")
                page.locator("#workspace-name").fill(name)
                page.locator("#save-workspace").click()
                expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
                expect(page.locator("#workspace-file-location")).to_contain_text(name + "--")
                assert len(list(project.glob(name + "--*.workspace.json"))) == 1
            stage(page, "workspace")
            page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
            page.locator("#cloud-asr-key").click()
            for locale in ["en", "pl"]:
                page.evaluate(
                    """locale=>{const control=document.querySelector('#gui-locale');
                    control.value=locale;
                    control.dispatchEvent(new Event('change',{bubbles:true}));}""",
                    locale,
                )
                expect(page.locator("#credential-save")).to_have_text(
                    "Zapisz klucz" if locale == "pl" else "Save key"
                )
                expect(page.locator("#credential-use")).to_have_text(
                    "Użyj zapisanego klucza" if locale == "pl" else "Use saved key"
                )
                expect(page.locator("#save-openrouter-key")).to_have_text(
                    "Ustaw tylko na sesję" if locale == "pl" else "Set session only"
                )
                for theme in ["light", "dark"]:
                    page.evaluate(
                        """theme=>{const control=document.querySelector('#gui-theme');
                        control.value=theme;
                        control.dispatchEvent(new Event('change',{bubbles:true}));}""",
                        theme,
                    )
                    for width in [390, 960, 1920]:
                        page.set_viewport_size({"width": width, "height": 1080})
                        geometry = page.evaluate("""()=>{
                          const r=id=>document.querySelector(id).getBoundingClientRect();
                          const save=r('#credential-save'),use=r('#credential-use');
                          const remove=r('#credential-remove'),clear=r('#credential-clear-session');
                          const close=r('#cancel-openrouter-key');
                          const footer=r('.credential-dialog-footer');
                          return {saveTop:save.top,useTop:use.top,removeTop:remove.top,
                            clearTop:clear.top,
                            clearBottom:clear.bottom,closeTop:close.top,closeRight:close.right,
                            footerRight:footer.right,footerBottom:footer.bottom,
                            closeBottom:close.bottom};
                        }""")
                        assert abs(geometry["saveTop"] - geometry["useTop"]) <= 1, geometry
                        assert abs(geometry["removeTop"] - geometry["clearTop"]) <= 1, geometry
                        assert geometry["closeTop"] >= geometry["clearBottom"], geometry
                        assert abs(geometry["closeRight"] - geometry["footerRight"]) <= 1, geometry
                        assert abs(geometry["closeBottom"] - geometry["footerBottom"]) <= 1, (
                            geometry
                        )
                        assert (
                            page.locator("#credential-remove").evaluate(
                                "e=>getComputedStyle(e).backgroundColor"
                            )
                            == "rgba(0, 0, 0, 0)"
                        )
                        cases.append({"locale": locale, "theme": theme, "width": width})
            page.locator("#credential-use").click()
            expect(page.locator("#save-openrouter-key")).to_be_disabled()
            page.locator("#credential-clear-session").click()
            page.locator("#cancel-openrouter-key").click()
        assert not errors and not external, (errors, external)
        result = {
            "recovery": args.recover,
            "page_errors": errors,
            "external_requests": external,
            "dialog_cases": len(cases),
            "readable_filenames": True,
            "folder_recall_without_picker_or_refresh": args.recover,
            "missing_and_invalid_keys_stay_staged": args.recover,
            "real_provider_calls": 0,
        }
        (args.output / ("recovery-report.json" if args.recover else "report.json")).write_text(
            json.dumps(result, indent=2)
        )
        print(json.dumps(result))
        browser.close()


if __name__ == "__main__":
    main()
