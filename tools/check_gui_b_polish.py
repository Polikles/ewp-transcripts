"""Exercise B workflow feedback against a disposable loopback server without provider calls.

Uses generated media/results, real review/export services and a local deterministic translation
provider invoked in the repository environment. All cloud/key/credential checks are intercepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import wave
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MOCK_TRANSLATION = """
import json, sys
from pathlib import Path
from ewp_transcripts.application import apply_automated_translation
from ewp_transcripts.automated_translation import DeterministicMockTranslationProvider
from ewp_transcripts.config import ApplicationConfig, RuntimeConfig
from ewp_transcripts.web_translations import GuiTranslationController
from ewp_transcripts.web_workflows import GuiWorkflowController

r = json.load(sys.stdin)


def runner(result, **kw):
    return apply_automated_translation(
        result,
        config=kw["config"],
        provider=DeterministicMockTranslationProvider(),
        target_language=kw["target_language"],
        revision_path=kw["revision_path"],
        style=kw["style"],
        output_directory=kw["output_directory"],
        resume_directory=kw["resume_directory"],
        dictionary=kw["dictionary"],
        dictionary_sha256=kw["dictionary_sha256"],
    )


controller = GuiTranslationController(
    config=ApplicationConfig(
        runtime=RuntimeConfig(work_root=Path(r["output_directory"]).parent / "work")
    ),
    resolve_path=GuiWorkflowController().resolve_allowed_path,
    runner=runner,
    preflight=lambda *args: None,
)
result = controller.generate(
    result=r["result_path"],
    source_revision=r.get("source_revision_path", ""),
    output_directory=r["output_directory"],
    resume_directory=r["resume_directory"],
    target_language=r["target_language"],
    provider_name=r["provider"],
    model=r["model"],
    endpoint=r["endpoint"],
    allow_remote_endpoint=False,
    allow_cloud=r["allow_cloud"],
    reasoning_max_tokens=None,
    output_mode=r["output_mode"],
    dictionary_path="",
    confirmed=r["confirmed"],
    api_key="fake-test-key",
)
print(json.dumps(result))
"""


def stage(page, name):
    page.locator(f'[data-gui-stage="{name}"]').click()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert urlsplit(args.url).hostname in {"localhost", "127.0.0.1"}
    args.output.mkdir(parents=True, exist_ok=False)
    audio = args.output / "sample.wav"
    with wave.open(str(audio), "wb") as out:
        out.setparams((1, 2, 16000, 0, "NONE", ""))
        out.writeframes(b"\0\0" * 16000 * 8)
    document = json.loads((ROOT / "examples/results.example.json").read_text())
    document["result_version"] = 3
    for source in document["sources"]:
        source.update(
            input_path=str(audio),
            normalized_path=str(audio),
            filename=audio.name,
            sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),
            size_bytes=audio.stat().st_size,
            duration_ms=8000,
        )
    result = args.output / f"{document['job_id']}_results_v003.json"
    result.write_text(json.dumps(document))
    errors, external, starts, generations = [], [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 1080})
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
        page.evaluate(
            "async()=>{await queuePost('/api/v1/transcriptions/clear-current',"
            "{confirmed:true});await refreshJobs();}"
        )
        page.locator("#output-path").fill(str(args.output / "project"))
        page.locator("#workflow input[type=file]").set_input_files(audio)
        page.wait_for_function("()=>!nativeMediaButton.disabled")
        page.locator("[data-episode-speakers]").select_option("auto")
        page.locator("#workflow button[value=dry-run]").click()
        expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
        page.locator("#gui-locale").select_option("pl")
        expect(page.locator("#gui-add-audio")).to_have_text("Dodaj pliki")
        expect(page.locator(".plan-table tbody")).to_contain_text("przetwórz")
        expect(page.locator(".plan-table td").last).to_have_text("automatycznie **")
        for width in (1440, 960, 720, 390):
            page.set_viewport_size({"width": width, "height": 1080})
            assert (
                page.locator(".plan-table th")
                .nth(2)
                .evaluate(
                    "e=>{const r=document.createRange();r.selectNodeContents(e);"
                    "return r.getClientRects().length}"
                )
                == 1
            )
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        page.set_viewport_size({"width": 960, "height": 1080})
        page.locator("#gui-locale").select_option("en")
        page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
        page.locator("#cloud-asr-provider").select_option("openrouter")
        page.locator("[data-episode-speakers]").select_option("1")
        page.locator("#workflow button[value=dry-run]").click()
        expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
        page.locator("#workflow input[name=confirmed]").check()
        page.locator("#workflow button[value=transcriptions]").click()
        expect(page.locator("#transcription-jobs tbody tr")).to_have_count(1)
        page.route(
            "**/api/v1/transcriptions/start",
            lambda route: (starts.append(True), route.fulfill(json={"queued": 0})),
        )
        page.locator("#start-queue").click()
        expect(page.locator("#cloud-asr-confirmed")).to_be_focused()
        expect(page.locator("#cloud-asr-confirmed")).to_have_attribute("aria-invalid", "true")
        expect(page.locator("#operation-status")).to_contain_text("Confirm audio upload")
        assert not starts
        page.locator("#cloud-asr-confirmed").check()
        expect(page.locator("#cloud-asr-confirmed")).to_have_attribute("aria-invalid", "false")
        assert not page.locator("#cloud-asr-consent").evaluate(
            "e=>e.classList.contains('field-error')"
        )
        page.locator("#start-queue").click()
        page.wait_for_function("()=>!guiQueueStarting")
        assert len(starts) == 1
        # No real credential store or provider check is touched.
        page.route(
            "**/api/v1/credentials/openrouter",
            lambda route: route.fulfill(json={"configured": True}),
        )
        checks = []
        page.route(
            "**/api/v1/speech/check",
            lambda route: (
                checks.append(route.request.post_data_json),
                route.fulfill(json={"status": "ok"}),
            ),
        )
        page.locator("#cloud-asr-key").click()
        page.locator("#openrouter-api-key").fill("fake-test-key")
        page.locator("#check-openrouter-key").click()
        expect(page.locator("#openrouter-key-check-status")).to_contain_text(
            "No audio was uploaded"
        )
        assert checks == [{"api_key": "fake-test-key"}]
        expect(page.locator("#openrouter-api-key")).to_have_value("")
        page.locator("#openrouter-api-key").fill("fake-test-key")
        page.locator("#save-openrouter-key").click()
        expect(page.locator("#openrouter-key-dialog-status")).to_contain_text(
            "active for this session"
        )
        expect(page.get_by_role("dialog")).to_be_visible()
        page.locator("#credential-save").click()
        expect(page.locator("#openrouter-key-dialog-status")).to_contain_text("saved in the OS")
        page.locator("#credential-use").click()
        expect(page.locator("#openrouter-key-dialog-status")).to_contain_text(
            "active for this session"
        )
        page.locator("#cancel-openrouter-key").click()
        expect(page.get_by_role("dialog")).not_to_be_visible()
        page.locator("#cloud-asr-key").click()
        page.locator("#close-openrouter-key-icon").click()
        expect(page.get_by_role("dialog")).not_to_be_visible()
        page.evaluate(
            "async()=>{await queuePost('/api/v1/transcriptions/clear-current',"
            "{confirmed:true});document.querySelector('#workflow').reset();await refreshJobs();}"
        )
        page.locator("#output-path").fill(str(args.output / "project"))
        page.locator("#workflow input[type=file]").set_input_files(result)
        page.wait_for_function(
            '()=>guiQueueJobs.length===1 && guiQueueJobs[0].status==="completed"'
        )
        page.evaluate("()=>openStageQueueItem(guiQueueJobs[0],'correction')")
        page.locator("#generate-correction").click()
        expect(page.locator("#correction-workflow input[name=confirmed]")).to_be_focused()
        expect(page.locator("#correction-status")).to_contain_text("Confirm the API disclosure")
        page.evaluate("()=>openStageQueueItem(guiQueueJobs[0],'review')")
        expect(page.locator("#review-editor textarea").first).to_be_visible()
        page.locator("#save-review").click()
        page.wait_for_function("()=>!reviewDirty")
        page.locator("#preview-review").click()
        expect(page.locator("#apply-review")).to_be_enabled()
        page.locator("#review-workflow input[name=verified]").check()
        page.locator("#apply-review").click()
        expect(page.locator("#export-review")).to_be_enabled()
        for box in page.locator("#review-workflow input[name=format]").all():
            box.set_checked(box.get_attribute("value") == "srt")
        page.locator("#export-review").click()
        expect(page.locator("#review-status")).to_contain_text("exports completed")
        page.wait_for_function('()=>guiQueueJobs[0].workflow.original_export.state==="complete"')
        assert not list((args.output / "project/exports").glob("*.txt"))
        assert page.evaluate("nextWorkflowStage(guiQueueJobs[0])") == "translation"
        page.evaluate("()=>openStageQueueItem(guiQueueJobs[0],'translation')")
        page.locator("#gui-translation-inputs").evaluate("e=>e.open=true")
        expect(
            page.locator("[data-picker-for=translation-dictionary]").locator(
                "xpath=ancestor::details[1]"
            )
        ).to_have_class("gui-optional-dictionary")
        page.locator("#generate-translation").click()
        expect(page.locator("#translation-workflow input[name=confirmed]")).to_be_focused()
        page.locator("#translation-workflow input[name=confirmed]").check()
        page.locator("#translation-workflow .provider-settings").evaluate("e=>e.open=true")
        page.locator("#translation-provider").select_option("lm-studio")
        page.locator("#translation-model").fill("deterministic-test")

        def generate(route):
            request = route.request.post_data_json
            generations.append(True)
            completed = subprocess.run(
                [str(ROOT / ".venv/bin/python"), "-c", MOCK_TRANSLATION],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                check=True,
            )
            route.fulfill(json=json.loads(completed.stdout))

        page.route("**/api/v1/translations/generate", generate)
        page.locator("#generate-translation").click()
        expect(page.locator("#translation-status")).to_contain_text("candidate generated")
        page.wait_for_function(
            '()=>guiQueueJobs[0].workflow.assisted_translation.state==="complete"'
        )
        expect(page.locator("#generate-translation")).to_be_disabled()
        assert page.evaluate("nextWorkflowStage(guiQueueJobs[0])") == "semantic-review"
        assert page.evaluate("stageState(guiQueueJobs[0],'semantic-review').state") == "pending"
        page.locator("#review-translation").click()
        expect(page.locator("#translation-review-editor textarea").first).to_be_visible()
        page.locator("#save-translation-review").click()
        page.wait_for_function("()=>!translationReviewDirty")
        page.locator("#preview-translation-review").click()
        expect(page.locator("#apply-translation-review")).to_be_enabled()
        page.locator("#translation-review-confirmed").check()
        page.locator("#apply-translation-review").click()
        expect(page.locator("#export-translation-review")).to_be_enabled()
        page.locator("#export-translation-review").click()
        page.wait_for_function('()=>guiQueueJobs[0].workflow.translated_export.state==="complete"')
        assert page.evaluate("stageState(guiQueueJobs[0],'semantic-review').state") == "complete"
        expect(page.locator("#translation-export-downloads a")).not_to_have_count(0)
        for locale in ("en", "pl"):
            page.locator("#gui-locale").select_option(locale)
            for width in (1440, 960, 720):
                page.set_viewport_size({"width": width, "height": 1080})
                stage(page, "review")
                source_boxes = (
                    page.locator("#review-workflow .review-control-line")
                    .first.locator("button")
                    .evaluate_all("es=>es.map(e=>e.getBoundingClientRect().toJSON())")
                )
                assert (
                    max(x["top"] for x in source_boxes) - min(x["top"] for x in source_boxes) <= 2
                )
                clear = page.locator("#clear-review").bounding_box()
                assert abs(clear["x"] + clear["width"] - source_boxes[-1]["right"]) <= 2
                stage(page, "semantic-review")
                boxes = (
                    page.locator(".translation-review-controls .review-control-line")
                    .first.locator("button")
                    .evaluate_all("es=>es.map(e=>e.getBoundingClientRect().toJSON())")
                )
                assert max(x["top"] for x in boxes) - min(x["top"] for x in boxes) <= 2, (
                    locale,
                    width,
                    boxes,
                )
                clear = page.locator("#clear-translation-review").bounding_box()
                assert abs(clear["x"] + clear["width"] - boxes[-1]["right"]) <= 2
        stage(page, "review")
        expect(page.locator("#source-export-downloads")).to_contain_text(
            "Pobierz plik. Eksporty są także zapisane"
        )
        stage(page, "semantic-review")
        expect(page.locator("#translation-export-downloads")).to_contain_text(
            "Tłumaczenia są zapisane w folderze translation-exports"
        )
        page.locator("#gui-locale").select_option("en")
        page.evaluate("()=>openStageQueueItem(guiQueueJobs[0],'translation')")
        expect(page.locator("#generate-translation")).to_be_enabled()
        assert page.evaluate("nextWorkflowStage(guiQueueJobs[0])") == "finished"
        assert len(generations) == 1 and not errors and not external, (errors, external)
        report = {
            "sourceSrtOnlyVersion3": "pass",
            "translationCandidateStatusAndGenerationLock": "pass",
            "manualTranslationStatusAndExports": "pass",
            "consentAndKeyDialog": "pass (mock key/OS responses)",
            "planHeaderAndControlRows": "pass ENPL / 1440,960,720; plan also 390",
            "pageErrors": errors,
            "externalRequests": external,
            "paidProviderCalls": 0,
        }
        (args.output / "report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
        browser.close()


if __name__ == "__main__":
    main()
