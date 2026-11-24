"""Check automatic private/output workspace recovery using the explicit synthetic GUI fixture.

Use a new fixture directory and --empty-queue. Restart that same fixture, then use --recover.
No speech model or paid provider is invoked.
"""

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
assert urlsplit(args.url).hostname in ("localhost", "127.0.0.1")
base = args.output
base.mkdir(parents=True, exist_ok=True)
errors = []
external = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(
        "**/*",
        lambda r: (
            r.continue_()
            if urlsplit(r.request.url).hostname in ("localhost", "127.0.0.1")
            else (external.append(r.request.url), r.abort())
        ),
    )
    page.goto(args.url)
    expect(page.locator("#compatibility")).to_have_text("Status: local service ready")
    page.wait_for_function(
        "()=>automaticRecoveryReady && activeWorkspaceId && !workspaceAutosaveBusy", timeout=15000
    )
    if args.recover:
        expect(page.locator("#output-path")).to_have_value(str(args.fixture_root / "output"))
        assert page.evaluate("selectedGuiAudio.length") == 1
        assert not page.locator("#cloud-asr-confirmed").is_checked()
        (base / "server-restart-report.json").write_text(
            json.dumps(
                {
                    "result": "PASS",
                    "cases": [
                        "actual server restart",
                        "automatic pending-media recovery",
                        "fresh cloud consent required",
                    ],
                    "page_errors": errors,
                    "external_requests": external,
                }
            )
        )
        assert not errors and not external
        browser.close()
        raise SystemExit(0)
    assert page.evaluate("activeWorkspaceStorageDirectory") == ""
    print(
        "Initial automatic private checkpoint",
        page.evaluate(
            "({id:activeWorkspaceId,storage:activeWorkspaceStorageDirectory,status:workspaceAutosaveStatus.textContent})"
        ),
    )
    assert page.evaluate("workspaceAutosave.checked && !workspaceAutosave.disabled")
    page.evaluate(
        "async()=>{await queuePost('/api/v1/transcriptions/clear-current',"
        "{confirmed:true});await refreshJobs();}"
    )
    output = args.fixture_root / "output"
    page.locator("#output-path").fill(str(output))
    page.locator("#output-path").dispatch_event("change")
    page.wait_for_function(
        "(root)=>activeWorkspaceStorageDirectory===root && !workspaceAutosaveBusy",
        arg=str(output),
        timeout=15000,
    )
    initial = page.evaluate("activeWorkspaceId")
    page.locator("#workflow input[type=file]").set_input_files(args.fixture_root / "episode.wav")
    page.wait_for_function("()=>selectedGuiAudio.length===1")
    page.wait_for_function(
        "()=>!workspaceAutosaveBusy && workspaceFingerprint()===lastWorkspaceFingerprint",
        timeout=15000,
    )
    checkpoint = next(output.glob("*.workspace.json"))
    data = json.loads(checkpoint.read_text())
    assert data["pending_media"], data
    assert not any(k in str(data) for k in ("api_key", "hf_token", "cloud-asr-confirmed"))
    # Fresh browser context: no browser local/session storage can supply this recovery.
    context.close()
    context = browser.new_context()
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(
        "**/*",
        lambda r: (
            r.continue_()
            if urlsplit(r.request.url).hostname in ("localhost", "127.0.0.1")
            else (external.append(r.request.url), r.abort())
        ),
    )
    page.goto(args.url)
    page.wait_for_function(
        "(id)=>automaticRecoveryReady && activeWorkspaceId===id && !workspaceRestoreBusy",
        arg=initial,
        timeout=20000,
    )
    assert page.locator("#output-path").input_value() == str(output)
    assert page.evaluate("selectedGuiAudio.length") == 1
    assert page.evaluate('guiQueueJobs.every(job=>job.status!=="running")')
    assert not page.locator("#cloud-asr-confirmed").is_checked()
    page.screenshot(path=str(base / "startup-recovered.png"), full_page=True)
    print("Fresh-context pending media/output recovery PASS")
    # An unavailable last checkpoint must survive; manually choosing a good one re-enables saving.
    missing = args.fixture_root / "missing-reference.txt"
    missing.write_text("synthetic reference")
    page.evaluate(
        """async ({path,storage})=>workspacePost('/api/v1/workspaces/save',{
          name:'Unavailable recovery test',current_step:'workspace-heading',
          fields:{'input-path':path},pending_media:[]},{storageDirectory:storage,feedback:false})""",
        {"path": str(missing), "storage": str(output)},
    )
    missing.unlink()
    context.close()
    context = browser.new_context()
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(args.url)
    expect(page.locator("#workspace-autosave-status")).to_contain_text(
        "The last work state is unavailable"
    )
    page.locator('[data-gui-stage="saved"]').click()
    key = page.evaluate(
        "({id,storage})=>workspaceKey(id,storage)", {"id": initial, "storage": str(output)}
    )
    page.locator("#workspace-list").select_option(key)
    page.locator("#load-workspace").click()
    page.wait_for_function("()=>automaticRecoveryReady && !workspaceRestoreBusy")
    page.locator('[data-gui-stage="saved"]').click()
    page.locator("#workspace-name").fill("Recovery manual resume")
    page.wait_for_function(
        "()=>!workspaceAutosaveBusy && workspaceFingerprint()===lastWorkspaceFingerprint"
    )
    checkpoint = next(output.glob(f"*--{initial}.workspace.json"))
    assert json.loads(checkpoint.read_text())["name"] == "Recovery manual resume"
    assert not errors and not external, (errors, external)
    (base / "browser-report.json").write_text(
        json.dumps(
            {
                "result": "PASS",
                "cases": [
                    "initial private autosave",
                    "output-root association",
                    "pending-media durable autosave",
                    "fresh-context automatic recovery",
                    "no restored upload consent",
                    "no automatic transcription",
                    "unavailable checkpoint preservation and manual recovery autosave",
                ],
                "page_errors": errors,
                "external_requests": external,
            },
            indent=2,
        )
    )
    context.close()
    browser.close()
