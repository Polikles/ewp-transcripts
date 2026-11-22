"""Check pending media and a failed cloud snapshot across a real server restart.

Use only a disposable loopback server whose transcription service is a no-provider failure stub.
Run save phase, restart server, then recover phase with the same --output. No API key is needed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import wave
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def stage(page, name):
    page.locator(f'[data-gui-stage="{name}"]').click()


def save(page, name):
    stage(page, "saved")
    page.locator("#workspace-list").select_option("")
    page.locator("#workspace-name").fill(name)
    page.locator("#save-workspace").click()
    expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
    expect(page.locator("#workspace-file-location")).to_contain_text(".json")


def load(page, name):
    stage(page, "saved")
    option = page.locator("#workspace-list option").filter(has_text=name)
    expect(option).to_have_count(1)
    page.locator("#workspace-list").select_option(option.get_attribute("value"))
    page.locator("#load-workspace").click()
    page.wait_for_function("()=>!workspaceRestoreBusy")
    expect(page.locator("#workspace-status")).to_contain_text("Workspace loaded:")
    expect(page.locator("#workspace-name")).to_have_value(name)
    expect(page.locator("#workspace-name")).to_have_attribute("aria-invalid", "false")
    assert page.locator("#workspace-name").evaluate("e=>e.readOnly")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--confirm-fake-service", action="store_true")
    args = parser.parse_args()
    assert urlsplit(args.url).hostname in {"localhost", "127.0.0.1"}
    if not args.recover and not args.confirm_fake_service:
        parser.error("A deliberate failed start requires --confirm-fake-service")
    args.output.mkdir(parents=True, exist_ok=args.recover)
    sources = [args.output / f"s0e09-{speaker}.wav" for speaker in ("A", "B")]
    errors, external = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.on("pageerror", lambda error: errors.append(str(error)))
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
        project = args.output / "project"
        page.locator("#output-path").fill(str(project))
        if args.recover:
            stage(page, "saved")
            page.locator("#save-workspace").click()
            expect(page.locator("#workspace-name")).to_have_attribute("aria-invalid", "true")
            load(page, "Cloud recovery fixture")
            page.wait_for_function("()=>guiQueueJobs.length===2")
            assert sorted(page.evaluate("guiQueueJobs.map(j=>j.status)")) == ["completed", "failed"]
            failed = page.evaluate("guiQueueJobs.find(j=>j.status==='failed')")
            assert failed["speech"]["provider"] == "openrouter"
            assert failed["error"]["code"] == "SPEECH_ENGINE_ERROR"
            expect(page.locator("#cloud-asr-confirmed")).not_to_be_checked()
            stage(page, "saved")
            page.locator("#save-workspace").click()
            expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
            assert page.locator("#workspace-name").input_value() == "Cloud recovery fixture"
            page.evaluate(
                "async()=>{await queuePost('/api/v1/transcriptions/clear-current',"
                "{confirmed:true});await refreshJobs();}"
            )
            load(page, "Pending media fixture")
            assert page.evaluate("selectedGuiAudio.length") == 2
            assert page.locator("#input-path").input_value()
            assert page.evaluate("guiBatchPlan?.results.length") == 1
            stage(page, "workspace")
            page.locator("#workflow input[type=file]").set_input_files(sources)
            page.wait_for_function("()=>!nativeMediaButton.disabled")
            assert page.evaluate("selectedGuiAudio.length") == 2
            assert page.evaluate("guiBatchRequests().length") == 1
            page.locator("#workflow input[name=confirmed]").check()
            page.locator("#workflow button[value=transcriptions]").click()
            page.wait_for_function("()=>guiQueueJobs.length===1")
            assert page.evaluate("guiQueueJobs[0].status") == "staged"
        else:
            for index, source in enumerate(sources):
                with wave.open(str(source), "wb") as out:
                    out.setparams((1, 2, 16000, 0, "NONE", ""))
                    out.writeframes(bytes([index, 0]) * 16000 * 8)
            page.locator("#workflow input[type=file]").set_input_files(sources)
            page.wait_for_function("()=>!nativeMediaButton.disabled")
            page.locator("#workflow button[value=dry-run]").click()
            expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
            save(page, "Pending media fixture")
            manifest = json.loads(next(project.glob("*.json")).read_text())
            assert manifest["workspace_version"] == 3 and len(manifest["pending_media"]) == 2
            assert all(Path(m["path"]).exists() for m in manifest["pending_media"])
            load(page, "Pending media fixture")
            stage(page, "workspace")
            page.locator("#workflow input[type=file]").set_input_files(sources)
            page.wait_for_function("()=>!nativeMediaButton.disabled")
            assert page.evaluate("selectedGuiAudio.length") == 2
            page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
            page.locator("#cloud-asr-provider").select_option("openrouter")
            page.locator("#workflow button[value=dry-run]").click()
            expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
            page.locator("#workflow input[name=confirmed]").check()
            page.locator("#workflow button[value=transcriptions]").click()
            page.wait_for_function("()=>guiQueueJobs.length===1")
            document = json.loads((ROOT / "examples/results.example.json").read_text())
            for source in document["sources"]:
                source.update(
                    input_path=str(sources[0]),
                    normalized_path=str(sources[0]),
                    filename=sources[0].name,
                    sha256=hashlib.sha256(sources[0].read_bytes()).hexdigest(),
                    size_bytes=sources[0].stat().st_size,
                    duration_ms=8000,
                )
            canonical = args.output / f"{document['job_id']}_results.json"
            canonical.write_text(json.dumps(document))
            page.locator("#workflow input[type=file]").set_input_files(canonical)
            page.wait_for_function("()=>guiQueueJobs.length===2")
            save(page, "Cloud recovery fixture")
            stage(page, "workspace")
            page.locator("#cloud-asr-confirmed").check()
            page.locator("#start-queue").click()
            page.wait_for_function("()=>guiQueueJobs.some(j=>j.status==='failed')")
            assert list(project.glob("s0e09_results.failed.json"))
            page.locator("#cloud-asr-key").click()
            expect(page.locator("#save-openrouter-key")).to_be_disabled()
            page.route(
                "**/api/v1/credentials/openrouter",
                lambda route: route.fulfill(json={"configured": True}),
            )
            page.locator("#credential-use").click()
            expect(page.locator("#openrouter-key-dialog-status")).to_contain_text(
                "active for this session"
            )
            expect(page.locator("#save-openrouter-key")).to_be_disabled()
            page.locator("#openrouter-api-key").fill("fake-test-key")
            expect(page.locator("#save-openrouter-key")).to_be_enabled()
            page.locator("#openrouter-api-key").fill("")
            expect(page.locator("#save-openrouter-key")).to_be_disabled()
            page.locator("#cancel-openrouter-key").click()
            for locale in ("en", "pl"):
                page.locator("#gui-locale").select_option(locale)
                for theme in ("light", "dark"):
                    page.locator("#gui-theme").select_option(theme)
                    for width in (960, 1920, 3840):
                        page.set_viewport_size({"width": width, "height": 1080})
                        assert page.evaluate(
                            "getComputedStyle(document.documentElement).backgroundImage.includes('web-pattern')"
                        )
                        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        assert not errors and not external, (errors, external)
        report = {
            "recover": args.recover,
            "page_errors": errors,
            "external_requests": external,
            "pending_media": "durable, hashed, replanned and deduplicated",
            "failed_snapshot": "restored after real restart"
            if args.recover
            else "staged snapshot saved before fake failure",
            "auto_starts": 0,
            "real_provider_calls": 0,
        }
        (args.output / ("recovery-report.json" if args.recover else "report.json")).write_text(
            json.dumps(report, indent=2)
        )
        print(json.dumps(report))
        browser.close()


if __name__ == "__main__":
    main()
