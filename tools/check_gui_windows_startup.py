"""Windows-session startup, live polling and keyboard regression against a synthetic local service.

Requires a disposable server preloaded with fixture/cancel-waiting/cancel-active local jobs and a
synthetic ProgressEvent service. --confirm-synthetic-service is mandatory; never use real ASR.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--fixture-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--confirm-synthetic-service", action="store_true")
    args = parser.parse_args()
    assert args.confirm_synthetic_service
    assert urlsplit(args.url).hostname in {"localhost", "127.0.0.1"}
    args.output.mkdir(parents=True)
    errors, external, polls = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 1080})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                polls.append(request.url)
                if request.url.endswith("/api/v1/transcriptions")
                else None
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

        def windows(route):
            response = route.fetch()
            data = response.json()
            data["platform"] = "win32"
            route.fulfill(response=response, json=data)

        page.route("**/api/v1/session", windows)
        page.goto(args.url)
        expect(page.locator("#compatibility")).to_have_text("Status: local service ready")
        expect(page.locator("#application-version")).not_to_have_text("Loading…")
        expect(page.locator("#api-version")).not_to_have_text("Loading…")
        expect(page.locator("#dependency-upgrade-help")).to_have_attribute(
            "href", "/help/windows-native?lang=en"
        )
        page.wait_for_function("()=>guiQueueJobs.length===3")
        timer = page.evaluate("guiQueuePollingTimer")
        page.evaluate("""async()=>{window.savedRestoreReview=restoreReview;
          restoreReview=async()=>{throw new Error('Synthetic optional restore failure')};
          await start();}""")
        expect(page.locator("#compatibility")).to_contain_text("GUI_INITIALIZATION_FAILED")
        assert page.evaluate("guiQueuePollingTimer") == timer
        page.evaluate("async()=>{restoreReview=window.savedRestoreReview;await start()}")
        expect(page.locator("#compatibility")).to_have_text("Status: local service ready")
        # Escape must work from all entry points, and focus must not Tab behind the dialog.
        opened = 0
        for locale in ["en", "pl"]:
            page.locator("#gui-locale").select_option(locale)
            expect(page.locator("header .eyebrow")).to_have_text(
                "Lokalne narzędzie do transkrypcji"
                if locale == "pl"
                else "Local-first transcript workflow"
            )
            for stage, selector in [
                ("workspace", "#cloud-asr-key"),
                ("correction", "#openrouter-options button"),
                ("translation", "#translation-set-openrouter-key"),
                ("settings", "#gui-credentials button"),
            ]:
                page.locator(f'[data-gui-stage="{stage}"]').click()
                if stage == "workspace":
                    page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
                    page.locator("#cloud-asr-provider").select_option("openrouter")
                if stage == "correction":
                    page.locator("#correction-workflow .provider-settings").evaluate(
                        "e=>e.open=true"
                    )
                if stage == "translation":
                    page.locator("#translation-workflow .provider-settings").evaluate(
                        "e=>e.open=true"
                    )
                    page.locator("#translation-provider").select_option("openrouter")
                opener = page.locator(selector).first
                opener.click()
                expect(page.locator("#openrouter-key-dialog")).to_be_visible()
                page.locator("#cancel-openrouter-key").focus()
                page.keyboard.press("Tab")
                assert page.evaluate("openRouterKeyDialog.contains(document.activeElement)")
                page.locator("#gui-theme").evaluate("e=>e.focus()")
                page.keyboard.press("Escape")
                expect(page.locator("#openrouter-key-dialog")).to_be_hidden()
                expect(opener).to_be_focused()
                opened += 1
        page.locator("#gui-locale").select_option("en")
        page.locator('[data-gui-stage="workspace"]').click()
        # Per-recording help sits on the caption row and keeps native label association.
        page.locator("#workflow input[type=file]").set_input_files(
            args.fixture_root / "episode.wav"
        )
        page.wait_for_function("()=>selectedGuiAudio.length===1 && !nativeMediaButton.disabled")
        for width in [390, 960, 1920]:
            page.set_viewport_size({"width": width, "height": 1080})
            host = page.locator("#gui-audio-choices .gui-language-choice")
            geometry = host.evaluate("""e=>{const l=e.querySelector('label');
              const i=e.querySelector('summary'),s=e.querySelector('select');
              const a=l.getBoundingClientRect(),b=i.getBoundingClientRect();
              const c=s.getBoundingClientRect();
              return {labelTop:a.top,labelBottom:a.bottom,iconTop:b.top,iconBottom:b.bottom,
                selectTop:c.top,associated:l.htmlFor===s.id};}""")
            assert geometry["associated"] and geometry["selectTop"] >= max(
                geometry["labelBottom"], geometry["iconBottom"]
            ), geometry
            assert (
                abs(
                    (geometry["labelTop"] + geometry["labelBottom"])
                    - (geometry["iconTop"] + geometry["iconBottom"])
                )
                < 2
            ), geometry
            host.locator("summary").click()
            expect(host.locator("details")).to_have_attribute("open", "")
            page.locator("#workspace-heading").click()
            expect(host.locator("details")).not_to_have_attribute("open", "")
        page.set_viewport_size({"width": 960, "height": 1080})
        page.locator("#start-queue").click()
        page.wait_for_function(
            "()=>guiQueueJobs.find(j=>j.planned_job_id==='fixture')?.status==='running'"
        )
        waiting = page.locator("#transcription-jobs tbody tr").filter(has_text="cancel-waiting ·")
        waiting.get_by_role("button", name="Cancel task", exact=True).click()
        page.wait_for_function(
            "()=>guiQueueJobs.find(j=>j.planned_job_id==='cancel-waiting')?.status==='cancelled'"
        )
        phases = []
        for phase, locale, label in [
            ("transcribe", "pl", "Transkrypcja"),
            ("align", "en", "Aligning words"),
        ]:
            page.wait_for_function(
                "phase=>guiQueueJobs.find(j=>j.planned_job_id==='fixture')?.runtime_progress?.phase===phase",
                arg=phase,
            )
            page.locator("#gui-locale").select_option(locale)
            row = page.locator("#transcription-jobs tbody tr").filter(has_text="fixture ·")
            expect(row.locator("progress")).to_be_visible()
            expect(row.locator(".gui-runtime-progress")).to_contain_text(label)
            phases.append(phase)
        page.wait_for_function(
            "()=>guiQueueJobs.find(j=>j.planned_job_id==='fixture')?.status==='completed'"
        )
        page.locator("#gui-locale").select_option("en")
        row = page.locator("#transcription-jobs tbody tr").filter(has_text="fixture ·")
        expect(row).to_contain_text("ASR completed")
        expect(row.get_by_role("button", name="Cancel task", exact=True)).to_have_count(0)
        page.wait_for_function(
            "()=>guiQueueJobs.find(j=>j.planned_job_id==='cancel-active')?.status==='running'"
        )
        active = page.locator("#transcription-jobs tbody tr").filter(has_text="cancel-active ·")
        active.get_by_role("button", name="Cancel task", exact=True).click()
        page.wait_for_function(
            "()=>guiQueueJobs.find(j=>j.planned_job_id==='cancel-active')?.status==='cancelled'"
        )
        assert len(polls) >= 7, len(polls)
        assert not errors and not external, (errors, external)
        page.screenshot(path=str(args.output / "completed-queue.png"), full_page=True)
        result = {
            "windows_session_startup": True,
            "metadata_loaded": True,
            "optional_restore_failure_polling_survives": True,
            "queue_phase_changes": phases,
            "completion_updated_without_manual_refresh": True,
            "cancel_queued_and_running": True,
            "key_dialog_entry_locale_cases": opened,
            "caption_layout_widths": [390, 960, 1920],
            "queue_GETs": len(polls),
            "page_errors": errors,
            "external_requests": external,
            "real_ASR_or_provider_calls": 0,
        }
        (args.output / "report.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        browser.close()


if __name__ == "__main__":
    main()
