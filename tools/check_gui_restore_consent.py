"""Check restored cloud consent and layout against an isolated, fake-service GUI server.

The server MUST replace transcription with a no-provider stub. --recover repeats loading after
an actual server restart; only --recover deliberately starts that stub. No API key is needed.
"""

from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def stage(page, name):
    page.locator(f'[data-gui-stage="{name}"]').click()


def blocked_start(page):
    stage(page, "workspace")
    page.locator("#start-queue").click()
    expect(page.locator("#operation-status")).to_contain_text("GUI_CLOUD_CONSENT_REQUIRED")
    expect(page.locator("#cloud-asr-confirmed")).to_be_focused()
    expect(page.locator("#cloud-asr-confirmed")).not_to_be_checked()
    page.wait_for_function("()=>!guiQueueStarting")
    assert page.evaluate("()=>guiQueueJobs.every(j=>j.status==='staged')")
    result = page.evaluate("""async()=>{
      const response=await fetch('/api/v1/transcriptions/start',{
        method:'POST',headers:{'Content-Type':'application/json','X-EWP-CSRF':csrfToken},
        body:JSON.stringify({cloud_confirmed:true})});
      return {status:response.status,code:(await response.json()).error.code};
    }""")
    assert result == {"status": 400, "code": "GUI_CLOUD_CONSENT_REQUIRED"}, result


def load(page, output):
    stage(page, "workspace")
    page.locator("#output-path").fill(str(output / "project"))
    stage(page, "saved")
    option = page.locator("#workspace-list option").filter(has_text="Restore consent fixture")
    expect(option).to_have_count(1)
    page.locator("#workspace-list").select_option(option.get_attribute("value"))
    page.locator("#load-workspace").click()
    expect(page.locator("#gui-workspace-restore")).not_to_be_visible()
    page.wait_for_function("()=>!workspaceRestoreBusy && guiQueueJobs.length===1")
    assert page.evaluate("()=>guiQueueJobs[0].speech.provider") == "openrouter"
    assert page.evaluate("()=>guiQueueJobs[0].speech.model") == "openai/whisper-large-v3"
    assert page.evaluate("currentGuiCloudConsentToken()") == ""
    expect(page.locator("#cloud-asr-confirmed")).not_to_be_checked()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--confirm-fake-service", action="store_true")
    args = parser.parse_args()
    if args.recover and not args.confirm_fake_service:
        parser.error("Recovery start requires --confirm-fake-service and a no-provider stub server")
    assert urlsplit(args.url).hostname in {"localhost", "127.0.0.1"}
    args.output.mkdir(parents=True, exist_ok=args.recover)
    errors, external, starts, measurements = [], [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 1080})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                starts.append(True) if request.url.endswith("/transcriptions/start") else None
            ),
        )
        page.route(
            "**/*",
            lambda route: (
                route.continue_()
                if urlsplit(route.request.url).hostname in {"localhost", "127.0.0.1"}
                else (external.append(route.request.url), route.abort())
            ),
        )
        page.goto(args.url)
        expect(page.locator("#compatibility")).to_have_text("Status: local service ready")
        if args.recover:
            load(page, args.output)
            blocked_start(page)
            page.locator("#cloud-asr-confirmed").evaluate("e=>e.checked=true")
            blocked_start(page)
            page.locator("#cloud-asr-confirmed").check()
            page.wait_for_function("()=>!!currentGuiCloudConsentToken()")
            page.locator("#start-queue").click()
            page.wait_for_function("()=>guiQueueJobs[0].status==='completed'")
            expect(page.locator("#cloud-asr-confirmed")).not_to_be_checked()
            assert page.evaluate("currentGuiCloudConsentToken()") == ""
        else:
            page.evaluate(
                "async()=>{await queuePost('/api/v1/transcriptions/clear-current',"
                "{confirmed:true});await refreshJobs();}"
            )
            audio = args.output / "sample.wav"
            with wave.open(str(audio), "wb") as stream:
                stream.setparams((1, 2, 16000, 0, "NONE", ""))
                stream.writeframes(b"\0\0" * 16000 * 4)
            page.locator("#output-path").fill(str(args.output / "project"))
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
            blocked_start(page)
            page.locator("#cloud-asr-confirmed").check()
            page.wait_for_function("()=>!!currentGuiCloudConsentToken()")
            stage(page, "saved")
            page.locator("#save-workspace").click()
            expect(page.locator("#workspace-name")).to_be_focused()
            expect(page.locator("#workspace-name")).to_have_attribute("aria-invalid", "true")
            page.locator("#workspace-name").fill("Restore consent fixture")
            expect(page.locator("#workspace-name")).to_have_attribute("aria-invalid", "false")
            page.locator("#save-workspace").click()
            expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
            files = list((args.output / "project").glob("*.json"))
            assert len(files) == 1, files
            manifest = json.loads(files[0].read_text())
            token = page.evaluate("currentGuiCloudConsentToken()")
            assert token and token not in files[0].read_text()
            assert "cloud-asr-confirmed" not in manifest["fields"]
            load(page, args.output)
            rejected = page.evaluate(
                """async token=>{
              const response=await fetch('/api/v1/transcriptions/start',{
                method:'POST',headers:{'Content-Type':'application/json','X-EWP-CSRF':csrfToken},
                body:JSON.stringify({cloud_confirmed:true,cloud_consent_token:token})});
              return response.status;
            }""",
                token,
            )
            assert rejected == 400, rejected
            blocked_start(page)
            page.locator("#cloud-asr-confirmed").evaluate("e=>e.checked=true")
            blocked_start(page)
            page.locator("#gui-locale").select_option("pl")
            page.locator("#cloud-asr-panel").evaluate("e=>e.open=false")
            expect(
                page.locator("#workflow .gui-workflow-step").filter(has_text="2.")
            ).to_be_visible()
            assert page.locator("#workspace-directory-group").evaluate(
                "e=>e.children[0].htmlFor==='workspace-directory' && "
                "e.children[1].id==='workspace-directory-hint' && "
                "e.children[2].id==='workspace-directory'"
            )
            expect(page.locator("#workspace-directory-hint")).to_have_text(
                "Wybierz katalog dla plików zapisu obszaru pracy i kopii zapasowych. "
                "Puste pole oznacza zapisanie stanu pracy w katalogu wyników."
            )
            for locale in ("en", "pl"):
                page.locator("#gui-locale").select_option(locale)
                for theme in ("light", "dark"):
                    page.locator("#gui-theme").select_option(theme)
                    for width in (390, 960, 1440, 1920, 2560, 3840):
                        page.set_viewport_size({"width": width, "height": 1080})
                        for current in ("workspace", "saved"):
                            stage(page, current)
                            measurement = page.evaluate(
                                """()=>{
                                  const app=document.querySelector('.gui-workbench')
                                    .getBoundingClientRect();
                                  const main=document.querySelector('main').getBoundingClientRect();
                                  return {width:innerWidth,
                                    page:document.documentElement.scrollWidth,
                                    app:app.width,main:main.width,left:app.left,
                                    right:innerWidth-app.right};
                                }"""
                            )
                            assert measurement["page"] <= width, measurement
                            assert measurement["app"] <= 1600.1 and measurement["main"] <= 1024.1, (
                                measurement
                            )
                            assert abs(measurement["left"] - measurement["right"]) <= 1, measurement
                            measurements.append(
                                {"locale": locale, "theme": theme, "stage": current, **measurement}
                            )
            page.locator("#gui-locale").select_option("en")
            page.set_viewport_size({"width": 960, "height": 1080})
            stage(page, "workspace")
            page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
            page.route("**/api/v1/speech/check", lambda route: route.fulfill(json={"ready": True}))
            page.locator("#cloud-asr-key").click()
            page.locator("#check-openrouter-key").click()
            expect(page.locator("#openrouter-key-check-status")).to_contain_text(
                "No audio was uploaded"
            )
            positions = page.locator(".credential-key-check").evaluate(
                """e=>{const b=e.querySelector('button').getBoundingClientRect();
                  const s=e.querySelector('p').getBoundingClientRect();
                  return {bottom:b.bottom,top:s.top,left:b.left,statusLeft:s.left};}"""
            )
            assert (
                positions["bottom"] <= positions["top"]
                and abs(positions["left"] - positions["statusLeft"]) <= 1
            ), positions
            page.locator("#close-openrouter-key-icon").click()
            stage(page, "saved")
            positions = page.evaluate("""()=>{
              const rect=s=>document.querySelector(s).getBoundingClientRect();
              const save=rect('#save-workspace'),refresh=rect('#refresh-workspaces');
              const open=rect('.workspace-primary-actions .feedback-anchor:last-child button');
              const remove=rect('.workspace-removal-actions');
              return {saveBottom:save.bottom,refreshTop:refresh.top,
                saveLeft:save.left,refreshLeft:refresh.left,openRight:open.right,
                removeRight:remove.right};
            }""")
            assert positions["saveBottom"] <= positions["refreshTop"], positions
            assert abs(positions["saveLeft"] - positions["refreshLeft"]) <= 1, positions
            assert abs(positions["openRight"] - positions["removeRight"]) <= 1, positions
            expect(page.locator("#delete-workspace")).not_to_have_class("danger")
            favicon = browser.new_page(viewport={"width": 400, "height": 400})
            svg = page.request.get(args.url + "/assets/brand/favicon.svg").text()
            favicon.set_content(
                "<style>body{margin:0}body>svg{width:400px;height:400px}</style>" + svg
            )
            center = favicon.locator("svg svg").evaluate("""e=>{
              const b=e.getBBox();
              const p=new DOMPoint(b.x+b.width/2,b.y+b.height/2)
                .matrixTransform(e.getScreenCTM());return {x:p.x,y:p.y};
            }""")
            assert abs(center["x"] - 200) < 0.01 and abs(center["y"] - 200) < 0.01, center
            favicon.screenshot(path=str(args.output / "favicon-centered.png"))
            favicon.close()
        assert not errors and not external, (errors, external)
        report = {
            "recovery": args.recover,
            "page_errors": errors,
            "external_requests": external,
            "layout_cases": len(measurements),
            "measurements": measurements,
            "blocked_boolean_without_grant": True,
            "programmatic_checkbox_blocked": True,
            "provider": "openrouter",
            "model": "openai/whisper-large-v3",
            "fake_service_only": True,
        }
        (args.output / ("recovery-report.json" if args.recover else "report.json")).write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(json.dumps({k: v for k, v in report.items() if k != "measurements"}))
        browser.close()


if __name__ == "__main__":
    main()
