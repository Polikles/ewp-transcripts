"""Optional synthetic browser check for queue cancellation and temporary-workdir maintenance.

Run in an environment with this project and Playwright installed. --output must be a dedicated
/tmp directory. Uses a cooperative fake transcription service, never GPU/models/providers.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright

from ewp_transcripts.config import ApplicationConfig, RuntimeConfig
from ewp_transcripts.web_server import LocalGuiServer, WebConfiguration
from ewp_transcripts.workdirs import allocate_work_directory, retain_work_directory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    output = parser.parse_args().output.resolve()
    if Path("/tmp") not in output.parents:
        raise ValueError("Use a dedicated directory below /tmp")
    output.mkdir(parents=True, exist_ok=False)
    os.environ["XDG_STATE_HOME"] = str(output / "state")
    config = ApplicationConfig(runtime=RuntimeConfig(work_root=output / "work"))
    with patch("ewp_transcripts.web_server.load_config", return_value=config):
        server = LocalGuiServer(WebConfiguration.create(port=0))
    release = threading.Event()

    def transcribe(path, **kwargs):
        assert release.wait(60), "Fake native stage did not return"
        kwargs["cancellation"].check()
        return SimpleNamespace(result_path=None)

    server.gui_transcriptions._service = transcribe
    first = server.gui_transcriptions.stage(
        output / "runme.wav",
        output / "output",
        planned_job_id="runme",
        planned_result_path=str(output / "output/runme_results.json"),
    )
    server.gui_transcriptions.stage(
        output / "waiting.wav",
        output / "output",
        planned_job_id="waiting",
        planned_result_path=str(output / "output/waiting_results.json"),
    )
    protected = allocate_work_directory(config.runtime.work_root, run_id=uuid4(), job_id="active")
    retained = []
    for reason in ("failed", "cancelled", "successful-retained"):
        workspace = allocate_work_directory(config.runtime.work_root, run_id=uuid4(), job_id=reason)
        (workspace.path / "working.wav").write_bytes(b"synthetic")
        retain_work_directory(workspace, reason)
        retained.append(workspace)
    worker = threading.Thread(target=server.serve_forever)
    worker.start()
    errors, external, layouts = [], [], []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route(
                "**/*",
                lambda route: (
                    route.continue_()
                    if route.request.url.startswith(f"http://127.0.0.1:{server.server_port}/")
                    else (external.append(route.request.url), route.abort())
                ),
            )
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            page.wait_for_function("() => csrfToken.length > 0")
            page.locator('[data-gui-stage="workspace"]').click()
            waiting = page.locator("#transcription-jobs tbody tr").filter(has_text="waiting.wav")
            running = page.locator("#transcription-jobs tbody tr").filter(has_text="runme.wav")
            page.locator("#start-queue").click()
            expect(running.locator(".gui-job-status")).to_have_text("RUNNING")
            waiting.get_by_role("button", name="Cancel task", exact=True).click()
            expect(waiting.locator(".gui-job-status")).to_have_text("CANCELLED")
            running.get_by_role("button", name="Cancel task", exact=True).click()
            expect(running.locator(".gui-job-status")).to_have_text("CANCELLATION REQUESTED")
            for locale in ("en", "pl"):
                page.locator("#gui-locale").select_option(locale)
                page.set_viewport_size({"width": 960, "height": 1080})
                assert page.locator("#transcription-jobs").evaluate(
                    "e=>e.scrollWidth<=e.clientWidth+1"
                )
                expect(running.locator("button").first).to_be_disabled()
            page.locator("#gui-locale").select_option("en")
            release.set()
            expect(running.locator(".gui-job-status")).to_have_text("CANCELLED")
            running.get_by_role("button", name="Retry from beginning", exact=True).click()
            assert server.gui_transcriptions.jobs()[0].job_id != first.job_id
            expect(page.locator("#start-queue")).to_be_enabled()
            release.set()
            page.locator("#start-queue").click()
            page.wait_for_function(
                "() => guiQueueJobs.some(job=>job.planned_job_id==='runme' "
                "&& job.status==='completed')"
            )
            page.locator('[data-gui-stage="settings"]').click()
            page.locator("#temporary-workdirs > summary").click()
            page.locator("#workdir-refresh").click()
            expect(page.locator("#workdir-list input[type=checkbox]")).to_have_count(4)
            expect(page.locator("#workdir-list input:disabled")).to_have_count(1)
            for locale in ("en", "pl"):
                page.locator("#gui-locale").select_option(locale)
                for theme in ("light", "dark"):
                    page.locator("#gui-theme").select_option(theme)
                    for width in (1440, 960, 390):
                        page.set_viewport_size({"width": width, "height": 1000})
                        page.locator("#temporary-workdirs").scroll_into_view_if_needed()
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= innerWidth + 1"
                        )
                        expect(page.locator("#workdir-refresh")).to_have_text(
                            "Odśwież listę katalogów tymczasowych"
                            if locale == "pl"
                            else "Refresh temporary inventory"
                        )
                        page.screenshot(
                            path=str(output / f"maintenance-{locale}-{theme}-{width}.png")
                        )
                        layouts.append(dict(locale=locale, theme=theme, width=width))
            page.locator("#gui-locale").select_option("en")
            page.locator("#workdir-reason").select_option("failed")
            expect(page.locator("#workdir-list input[type=checkbox]")).to_have_count(1)
            page.locator("#workdir-list input[type=checkbox]").check()
            page.locator("#workdir-preview").click()
            expect(page.locator("#workdir-delete")).to_be_enabled()
            assert retained[0].path.exists()
            page.locator("#workdir-delete").click()
            expect(page.locator("#workdir-status")).to_have_text(
                "Temporary directories removed: 1."
            )
            assert not retained[0].path.exists()
            assert protected.path.exists() and all(item.path.exists() for item in retained[1:])
            assert not errors and not external, (errors, external)
            browser.close()
        report = dict(
            layouts=layouts,
            page_errors=errors,
            external_requests=external,
            cancellation="synthetic service only",
            cleanup="preview/filter/confirmed deletion and active protection passed",
        )
        (output / "report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join()


if __name__ == "__main__":
    main()
