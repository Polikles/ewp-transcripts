"""Focused model-free GUI checks; requires isolated Playwright and a disposable local server.

Uses synthetic media/canonical data and intercepts only the new read-only cloud checks. No ASR,
provider upload or real credentials. Output must be a dedicated temporary directory.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import wave
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MODELS = [
    "openai/whisper-large-v3",
    "openai/whisper-large-v3-turbo",
    "elevenlabs/scribe-v2",
    "microsoft/mai-transcribe-2",
]


def wav(path):
    with wave.open(str(path), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", ""))
        audio.writeframes(b"\0\0" * 16000)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert urlsplit(args.url).hostname in {"localhost", "127.0.0.1"}
    args.output.mkdir(parents=True, exist_ok=False)
    single = wav(args.output / "single.wav")
    multi = args.output / "multistream.mkv"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=duration=1:sample_rate=16000",
            "-f",
            "lavfi",
            "-i",
            "sine=duration=1:sample_rate=16000",
            "-map",
            "0:a",
            "-map",
            "1:a",
            "-c:a",
            "pcm_s16le",
            str(multi),
        ],
        check=True,
    )
    canonical = json.loads((ROOT / "examples/results.example.json").read_text())
    canonical["job_id"] = canonical["episode"]["episode_id"] = "FEEDBACK_HISTORY"
    previous = args.output / "FEEDBACK_HISTORY_results.json"
    previous.write_text(json.dumps(canonical))
    errors, external, cloud_requests = [], [], []
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
        page.locator("#workflow input[type=file]").set_input_files([single, multi, previous])
        expect(page.locator("#gui-audio-choices li")).to_have_count(2)
        expect(page.locator("#transcription-jobs tbody tr")).to_have_count(1)
        page.wait_for_function("() => !nativeMediaButton.disabled")
        expect(page.locator("#gui-add-audio")).to_have_text("Add files")
        expect(page.locator("#workflow button[aria-pressed]")).to_have_count(0)
        expect(page.locator("#read-media-options")).to_have_count(0)
        expect(page.locator("#discover-media-directory")).to_have_count(0)
        assert page.locator("#input-path").evaluate(
            "e=>!e.nextElementSibling?.classList.contains('path-browser-button')"
        )
        expect(page.get_by_role("button", name="Browse output folder…", exact=True)).to_have_count(
            1
        )
        rows = page.locator("#gui-audio-choices li")
        rows.nth(0).locator("[data-episode-language]").select_option("pl")
        rows.nth(0).locator("[data-episode-speakers]").select_option("1")
        rows.nth(1).locator("[data-episode-language]").select_option("en")
        rows.nth(1).locator("[data-episode-speakers]").select_option("2")
        expect(rows.nth(0).locator("select[data-source-path]")).to_have_count(0)
        expect(rows.nth(1).locator("select[data-source-path]")).to_have_count(1)
        rows.nth(0).locator(".gui-language-info summary").click()
        expect(rows.nth(0).locator(".gui-language-info p")).to_be_visible()
        page.locator("#output-path").click()
        assert not rows.nth(0).locator(".gui-language-info").evaluate("e=>e.open")
        page.locator("#workflow button[value=dry-run]").click()
        expect(page.locator("#operation-status")).to_contain_text("GUI_AUDIO_STREAM_REQUIRED")
        rows.nth(1).locator("select[data-source-path]").select_option("1")
        page.locator("#workflow button[value=dry-run]").click()
        expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
        expect(page.locator("#operation-summary table")).to_have_count(1)
        expect(page.locator("#operation-summary tbody tr")).to_have_count(2)
        assert page.locator("#operation-summary tbody tr").all_text_contents() == [
            "single.wavprocessNonepl *1 **",
            "multistream.mkvprocessNoneen *2 **",
        ]
        page.locator("#cloud-asr-panel").evaluate("e=>e.open=true")
        page.locator("#cloud-asr-provider").select_option("openrouter")
        page.locator("#cloud-asr-model").select_option("elevenlabs/scribe-v2")
        expect(page.locator("#cloud-asr-budget")).to_have_count(0)
        page.route("**/api/v1/speech/check", lambda route: route.fulfill(json={"status": "ok"}))
        page.locator("#cloud-asr-check").click()
        expect(page.locator("#cloud-asr-check-status")).to_contain_text("No audio was uploaded")

        def estimate(route):
            cloud_requests.append(route.request.post_data_json)
            route.fulfill(
                json={
                    "recordings": 2,
                    "audio_seconds": 2,
                    "models": [
                        {
                            "id": model,
                            "available": index != 1,
                            "status": "ok" if index != 1 else "unavailable",
                            "minimum_usd_per_hour": "0.1",
                            "maximum_usd_per_hour": "0.2",
                            "estimated_minimum_usd": "0.01",
                            "estimated_maximum_usd": "0.02",
                        }
                        for index, model in enumerate(MODELS)
                    ],
                }
            )

        page.route("**/api/v1/speech/estimate", estimate)
        page.locator("#cloud-asr-refresh").click()
        expect(page.locator("#cloud-asr-prices tbody tr")).to_have_count(4)
        assert len(cloud_requests[-1]["items"]) == 2
        expect(page.locator("#cloud-asr-model option").nth(1)).to_be_disabled()
        rows.nth(0).locator("[data-episode-language]").select_option("en")
        expect(page.locator("#cloud-asr-estimate-status")).to_have_text(
            "Recordings or settings changed. Refresh the cost estimate."
        )
        page.locator("#cloud-asr-refresh").click()
        expect(page.locator("#cloud-asr-estimate-status")).to_contain_text(
            "Estimated recordings: 2"
        )
        failures = [
            {
                "status": "failed",
                "planned_job_id": f"JOB{n}",
                "error": {
                    "code": "GUI_TRANSCRIPTION_FAILED",
                    "message": "Transcription failed unexpectedly. Open failure technical details "
                    "to identify the failed operation.",
                    "exception_type": "PermissionError",
                    "errno": "13",
                    "traceback": "state.py:69 in _publish_exclusive_json",
                },
            }
            for n in [1, 2]
        ]
        page.evaluate("jobs=>renderTranscriptionErrors(jobs)", failures)
        expect(page.locator(".transcription-failure")).to_have_count(2)
        assert page.locator(".transcription-failure > p").count() == 2
        for row in page.locator(".transcription-failure").all():
            assert not row.evaluate("e=>e.open")
            row.locator(">summary").click()
        measurements = []
        for locale in ("en", "pl"):
            page.locator("#gui-locale").select_option(locale)
            for width in (1440, 960, 720, 390):
                page.set_viewport_size({"width": width, "height": 1080})
                measurements.append(
                    page.evaluate(
                        "()=>({width:innerWidth,page:document.documentElement.scrollWidth})"
                    )
                )
                assert measurements[-1]["page"] <= width
        expect(page.locator("#gui-add-audio")).to_have_text("Dodaj pliki")
        expect(page.locator("#cloud-asr-check")).to_have_text(
            "Sprawdź klucz i połączenie z OpenRouter"
        )
        expect(page.locator("#cloud-asr-estimate-status")).to_contain_text("Liczba nagrań: 2")
        expect(page.locator("#cloud-asr-provider option").first).to_have_text(
            "Lokalne GPU (domyślne)"
        )
        expect(page.locator(".transcription-failure >p").first).to_contain_text(
            "Otwórz szczegóły techniczne"
        )
        page.locator("#gui-locale").select_option("en")
        rows.nth(0).get_by_role("button", name="Remove from list", exact=True).click()
        expect(rows).to_have_count(1)
        assert page.locator("#input-path").input_value()
        page.locator("#workflow button[value=dry-run]").click()
        expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
        # Two same-name recordings need identity inputs only after a real collision.
        alias_page = browser.new_page()
        alias_page.on("pageerror", lambda error: errors.append(str(error)))
        alias_page.goto(args.url)
        expect(alias_page.locator("#compatibility")).to_have_text("Status: local service ready")
        alias_page.evaluate(
            "async()=>{await queuePost('/api/v1/transcriptions/clear-current',"
            "{confirmed:true});await refreshJobs();}"
        )
        alias_page.locator("#output-path").fill(str(args.output / "alias-project"))
        same_names = []
        for name in ("first", "second"):
            directory = args.output / name
            directory.mkdir()
            same_names.append(wav(directory / "same.wav"))
        alias_page.locator("#workflow input[type=file]").set_input_files(same_names)
        alias_page.wait_for_function("() => !nativeMediaButton.disabled")
        expect(alias_page.locator("#gui-audio-choices li")).to_have_count(2)
        aliases = alias_page.locator("#gui-audio-choices input[maxlength='100']")
        expect(aliases).to_have_count(0)
        alias_page.locator("#workflow button[value=dry-run]").click()
        expect(alias_page.locator("#operation-status")).to_contain_text(
            "GUI_RECORDING_ID_COLLISION"
        )
        expect(aliases).to_have_count(2)
        aliases.nth(0).fill("first-recording")
        aliases.nth(1).fill("second-recording")
        alias_page.locator("#workflow button[value=dry-run]").click()
        expect(alias_page.locator("#operation-status")).to_have_text("Dry-run completed")
        assert "first-recording" in alias_page.locator("#operation-summary").inner_text()
        assert "second-recording" in alias_page.locator("#operation-summary").inner_text()
        alias_page.close()
        assert not errors and not external, (errors, external)
        report = {
            "checks": "main JSON/media picker, per-recording settings, conditional streams, "
            "one table, language help, cloud mock checks/prices/staleness, "
            "error disclosures, ENPL responsive geometry, removal and conditional collision IDs",
            "pageErrors": errors,
            "externalRequests": external,
            "measurements": measurements,
            "cloudAudioUploads": 0,
        }
        (args.output / "report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
        browser.close()


if __name__ == "__main__":
    main()
