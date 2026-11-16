"""Optional model-free browser check; run with an isolated Playwright installation.

Point --url at a disposable GUI server and --output at a dedicated temporary directory.
This clears that server's inactive queue and writes synthetic reviews/exports/workspaces.
It never starts transcription or calls a provider. See docs/27-gui-34a-verification.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = [(1440, 1000), (960, 1080), (768, 1024), (720, 1000), (900, 1440), (390, 844)]


def geometry(page: Page) -> dict:
    """Measure actual controls, allowing the queue table's local scroll region."""
    return page.evaluate("""() => {
      const visible = e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
      const selector = 'main button, main select, main textarea, main fieldset, main h4';
      const overflow = [...document.querySelectorAll(selector)]
        .filter(e => visible(e) && !e.closest('#transcription-jobs'))
        .filter(e => { const r = e.getBoundingClientRect();
          return r.left < -1 || r.right > innerWidth + 1; })
        .map(e => e.id || e.className || e.tagName);
      const overlaps = [...document.querySelectorAll('.feedback-anchor')].filter(visible)
        .filter(e => { const b = e.querySelector('button')?.getBoundingClientRect();
          const s = e.querySelector('.inline-working')?.getBoundingClientRect();
          return b && s && b.bottom > s.top + 1; }).length;
      return {viewport: innerWidth, pageWidth: document.documentElement.scrollWidth,
        overflow, feedbackOverlaps: overlaps,
        tableBleed: [...document.querySelectorAll('#transcription-jobs td .workflow-indicator')]
          .filter(e => e.getBoundingClientRect().right >
            e.closest('td').getBoundingClientRect().right + 1).length,
        editorWidth: document.querySelector('#review-editor textarea')
          ?.getBoundingClientRect().width};
    }""")


def capture(page: Page, output: Path, label: str, baseline: bool) -> list[dict]:
    results = []
    for theme in ("light", "dark"):
        page.emulate_media(color_scheme=theme, reduced_motion="reduce")
        for width, height in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": height})
            # Keep a caret and batch selection while resizing; no re-render or replacement.
            for selector, name in [
                ("#transcription-jobs", "queue"),
                ("#review-editor", "editor"),
                ("#translation-review-editor", "translation"),
            ]:
                page.locator(selector).evaluate("e => e.scrollIntoView({block:'start'})")
                page.screenshot(path=str(output / f"{label}-{theme}-{width}-{name}.png"))
            measured = geometry(page)
            measured.update(theme=theme, height=height)
            results.append(measured)
            if not baseline:
                assert measured["pageWidth"] <= width + 1, measured
                assert not measured["overflow"], measured
                assert not measured["feedbackOverlaps"], measured
                assert not measured["tableBleed"], measured
                assert measured["editorWidth"] >= min(280, width - 120), measured
            expect(
                page.locator('#stage-queue-correction input[type="checkbox"]:checked')
            ).to_have_count(1)
            expect(page.locator("#review-editor textarea").first).to_have_value(
                "Welcome to another episode. Żółć"
            )
    return results


def exercise(page: Page, output: Path, baseline: bool) -> list[dict]:
    page.wait_for_function("csrfToken.length > 0")
    page.evaluate("queuePost('/api/v1/transcriptions/clear-current', {confirmed:true})")
    page.locator("#output-path").fill(str(output / "project"))
    page.locator("#output-path").dispatch_event("change")
    fixtures = []
    for number in (1, 2):
        document = json.loads((ROOT / "examples/results.example.json").read_text())
        document["job_id"] = f"S01E0{number}"
        document["episode"]["episode_id"] = document["job_id"]
        path = output / (f"S01E0{number}_Żółć_" + "long-name-" * 8 + "_results.json")
        path.write_text(json.dumps(document), encoding="utf-8")
        fixtures.append(path)
    originals = [hashlib.sha256(path.read_bytes()).hexdigest() for path in fixtures]
    page.locator('#stage-queue-correction input[type="file"]').set_input_files(fixtures)
    expect(page.locator("#stage-queue-review .stage-queue-item")).to_have_count(2)
    page.locator('#stage-queue-correction input[type="checkbox"]').first.click()
    page.locator("#stage-queue-review .stage-queue-item button").last.click()
    text = page.locator("#review-editor textarea").first
    expect(text).to_have_value("Welcome to another episode.")
    text.fill("Welcome to another episode. Żółć")
    text.evaluate("e => {e.focus(); e.setSelectionRange(0,7)}")
    identity = page.locator("#review-identity").inner_text()
    # Manual translation for the other result, through the real application API.
    result = page.evaluate("stageQueueJobs[0].result_path")
    page.evaluate(
        """async result => {
      translationCandidate = {result_path:result, revision_path:'', candidate_path:'',
        output_root:document.querySelector('#output-path').value, target_language:'pl'};
      await openEnhancedTranslationReview(translationCandidate);
    }""",
        result,
    )
    expect(page.locator("#translation-review-editor textarea").first).to_be_visible()
    page.locator("#translation-review-editor textarea").first.fill("Przykładowe tłumaczenie. Żółć")
    measurements = capture(page, output, "baseline" if baseline else "after", baseline)
    assert page.locator("#review-identity").inner_text() == identity
    assert text.evaluate("e => [e.selectionStart,e.selectionEnd]") == [0, 7]
    if baseline:
        return measurements

    page.set_viewport_size({"width": 720, "height": 1000})
    # Keyboard selection isolation and stable speaker ownership, not cursor splitting.
    text.focus()
    text.evaluate("e => e.setSelectionRange(0,7)")
    separate = page.get_by_role("button", name="Separate selected text").first
    separate.focus()
    separate.press("Enter")
    expect(page.locator("#review-editor textarea").first).to_have_value("Welcome")
    page.locator("#review-editor select").first.select_option("speaker_002")
    page.locator("#preview-review").click()
    expect(page.locator("#apply-review")).to_be_enabled()
    page.locator('#review-workflow input[name="verified"]').check()
    page.locator("#apply-review").click()
    expect(page.locator("#export-review")).to_be_enabled()
    page.locator("#export-review").click()
    expect(page.locator("#review-status")).to_contain_text("exports completed")
    # Switching the active review preserves the independent batch selection.
    page.locator("#stage-queue-review .stage-queue-item button").first.click()
    expect(page.locator("#review-identity")).not_to_have_text(identity)
    expect(page.locator('#stage-queue-correction input[type="checkbox"]:checked')).to_have_count(1)

    page.locator("#workspace-name").fill("GUI-34a synthetic recovery")
    page.locator("#save-workspace").click()
    expect(page.locator("#workspace-status")).to_contain_text("saved", ignore_case=True)
    catalog = page.locator("#workspace-directory").input_value()
    saved_key = page.locator("#workspace-list").input_value()
    page.reload()
    page.wait_for_function("csrfToken.length > 0")
    page.locator("#workspace-directory").fill(catalog)
    page.locator("#refresh-workspaces").click()
    page.wait_for_function(
        "key => [...document.querySelector('#workspace-list').options].some(o=>o.value===key)",
        arg=saved_key,
    )
    page.locator("#workspace-list").select_option(saved_key)
    page.locator("#load-workspace").click()
    expect(page.locator("#stage-queue-review .stage-queue-item")).to_have_count(2)
    # Keyboard access to the locally scrolling queue and its rightmost action.
    queue = page.locator("#transcription-jobs")
    queue.focus()
    expect(queue).to_be_focused()
    queue.press("Home")
    queue.press("ArrowRight")
    page.wait_for_function("() => document.querySelector('#transcription-jobs').scrollLeft > 0")
    assert queue.evaluate("e => getComputedStyle(e).outlineStyle") != "none"
    queue.press("End")
    action = queue.locator("button").first
    action.focus()
    assert action.evaluate(
        """e => {const r=e.getBoundingClientRect();
        const c=e.closest('#transcription-jobs').getBoundingClientRect();
        return r.left >= c.left && r.right <= c.right + 1}"""
    )
    action.press("Tab")
    assert page.evaluate("document.activeElement !== document.body")
    # Mixed terminal states use real queue annotations, with no simulated provider call.
    page.evaluate("""async () => {
      await queuePost('/api/v1/transcriptions/workflow-error', {
        result_path:stageQueueJobs[0].result_path, stage:'assisted_translation',
        code:'GUI_BROWSER_FIXTURE_FAILURE'});
      await reportWorkflowSkip(stageQueueJobs[1].result_path, 'correction');
    }""")
    expect(page.locator("#transcription-jobs .workflow-failed").first).to_be_visible()
    expect(page.locator("#transcription-jobs .workflow-skipped").first).to_be_visible()
    page.locator("#transcription-jobs").evaluate(
        "e => {e.scrollLeft=0; e.scrollIntoView({block:'start'})}"
    )
    page.screenshot(path=str(output / "after-mixed-states.png"))
    assert originals == [hashlib.sha256(path.read_bytes()).hexdigest() for path in fixtures]
    assert list((output / "project" / "exports").glob("*.srt"))
    return measurements


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    if urlsplit(args.url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("Use a disposable loopback GUI server")
    args.output.mkdir(parents=True, exist_ok=False)
    errors = []
    external = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(
            "**/*",
            lambda route: (
                route.continue_()
                if urlsplit(route.request.url).hostname in {"127.0.0.1", "localhost", "::1"}
                else (external.append(route.request.url), route.abort())
            ),
        )
        page.goto(args.url)
        try:
            measurements = exercise(page, args.output, args.baseline)
        except Exception:
            print(
                page.locator(
                    ".stage-queue-status, #review-status, "
                    "#translation-review-status, #workspace-status"
                ).all_text_contents()
            )
            print("ERRORS", errors)
            raise
        assert not errors, errors
        assert not external, external
        report = {
            "playwright": version("playwright"),
            "chromium": browser.version,
            "measurements": measurements,
            "pageErrors": errors,
            "externalRequests": external,
            "browserZoom": "NOT_RUN: viewport resizing is not browser zoom",
        }
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
