"""Check untouched default outputs and two-track recovery without model/provider calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--fixture-root", required=True, type=Path)
parser.add_argument("--url", required=True)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--recover", action="store_true")
args = parser.parse_args()
assert urlsplit(args.url).hostname in {"127.0.0.1", "localhost"}
args.output.mkdir(parents=True, exist_ok=True)
errors, external, calls = [], [], []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "request",
        lambda request: (
            calls.append(request.url)
            if request.url.endswith(("/dry-run", "/transcriptions")) and request.method == "POST"
            else None
        ),
    )
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
        "()=>automaticRecoveryReady && activeWorkspaceId"
        " && !workspaceRestoreBusy && !workspaceAutosaveBusy"
    )
    outputs = args.fixture_root / "outputs"
    expect(page.locator("#output-path")).to_have_value(str(outputs))
    if not args.recover:
        sources = [args.fixture_root / f"episode-{speaker}.wav" for speaker in ("left", "right")]
        for source in sources:
            source.write_bytes((args.fixture_root / "episode.wav").read_bytes())
        page.locator("#workflow input[type=file]").set_input_files(sources)
        page.wait_for_function(
            "()=>selectedGuiAudio.length===2 && !workspaceAutosaveBusy"
            " && workspaceFingerprint()===lastWorkspaceFingerprint",
            timeout=5000,
        )
        manifest = next(outputs.glob("*.workspace.json"))
        saved = json.loads(manifest.read_text())
        assert len(saved["pending_media"]) == 2
        assert all(Path(item["path"]).is_file() for item in saved["pending_media"])
        page.reload()
        page.wait_for_function("()=>automaticRecoveryReady && !workspaceRestoreBusy")
    assert page.evaluate(
        "selectedGuiAudio.length===2 && guiAudioEpisodes().length===1 && guiBatchPlan===null"
    )
    assert page.evaluate("guiQueueJobs.every(job=>job.status!=='running')")
    assert not page.locator("#cloud-asr-confirmed").is_checked()
    page.locator('[data-gui-stage="saved"]').click()
    page.locator("#gui-locale").select_option("pl")
    page.screenshot(
        path=str(
            args.output / ("restart-default-outputs.png" if args.recover else "default-outputs.png")
        ),
        full_page=True,
    )
    assert not errors and not external and not calls, (errors, external, calls)
    report = {
        "result": "PASS",
        "cases": [
            "managed default outputs with no folder selection",
            "two tracks saved immediately after upload",
            "change-aware save without timer wait",
            "fresh browser recovery",
            "no planning or processing or upload consent",
        ]
        + (["actual server restart"] if args.recover else []),
        "page_errors": errors,
        "external_requests": external,
        "unexpected_planning_or_staging": calls,
        "provider_calls": 0,
    }
    (args.output / ("restart-report.json" if args.recover else "browser-report.json")).write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))
    browser.close()
