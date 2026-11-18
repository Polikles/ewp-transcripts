"""Optional model-free browser check; run with an isolated Playwright installation.

Point --url at a disposable GUI server and --output at a dedicated temporary directory.
This clears that server's inactive queue and writes synthetic reviews/exports/workspaces.
It never starts transcription or calls a provider. See docs/28-integrated-gui-preview.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import wave
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
        textareaOverflow: [...document.querySelectorAll(
          '#review-editor textarea, #translation-review-editor textarea')]
          .filter(visible).filter(e => e.scrollHeight > e.clientHeight + 1).length,
        queueScroll: document.querySelector('#transcription-jobs').scrollWidth -
          document.querySelector('#transcription-jobs').clientWidth,
        tableBleed: [...document.querySelectorAll('#transcription-jobs td .workflow-indicator')]
          .filter(e => e.getBoundingClientRect().right >
            e.closest('td').getBoundingClientRect().right + 1).length,
        editorWidth: document.querySelector('#review-editor textarea')
          ?.getBoundingClientRect().width};
    }""")


def stage(page: Page, name: str) -> None:
    page.locator(f'[data-gui-stage="{name}"]').click()


def capture(page: Page, output: Path, label: str, baseline: bool) -> list[dict]:
    results = []
    for locale in ("en", "pl"):
        page.locator("#gui-locale").select_option(locale)
        for theme in ("light", "dark"):
            page.locator("#gui-theme").select_option(theme)
            for width, height in VIEWPORTS:
                page.set_viewport_size({"width": width, "height": height})
                for section, selector in [
                    ("workspace", "#transcription-jobs"),
                    ("review", "#review-editor"),
                    ("semantic-review", "#translation-review-editor"),
                ]:
                    stage(page, section)
                    page.locator(selector).evaluate("e => e.scrollIntoView({block:'start'})")
                    page.screenshot(
                        path=str(output / f"{label}-{locale}-{theme}-{width}-{section}.png")
                    )
                    if section == "semantic-review":
                        label_color = page.locator(".translation-source-label").first.evaluate(
                            "e=>getComputedStyle(e).color"
                        )
                        assert label_color == (
                            "rgb(191, 208, 221)" if theme == "dark" else "rgb(67, 95, 108)"
                        )
                    measured = geometry(page)
                    measured.update(locale=locale, theme=theme, height=height, section=section)
                    results.append(measured)
                    if not baseline:
                        assert measured["pageWidth"] <= width + 1, measured
                        assert not measured["overflow"], measured
                        assert not measured["feedbackOverlaps"], measured
                        assert not measured["textareaOverflow"], measured
                        if section == "workspace":
                            assert not measured["tableBleed"], measured
                            if width >= 720:
                                assert measured["queueScroll"] <= 1, measured
                        if section == "review":
                            assert measured["editorWidth"] >= min(260, width - 130), measured
                    expect(
                        page.locator('#stage-queue-correction input[type="checkbox"]:checked')
                    ).to_have_count(1)
                    expect(page.locator("#review-editor textarea").first).to_have_value(
                        "Welcome to another episode. Żółć"
                    )
                    assert page.locator("#gui-locale").input_value() == locale
                    assert page.locator("html").get_attribute("lang") == locale
                    assert page.locator("html").get_attribute("data-theme") == theme
    page.locator("#gui-locale").select_option("en")
    return results


def stage_audio_without_models(page: Page, output: Path) -> None:
    stage(page, "workspace")
    files = []
    for number in (1, 2):
        path = output / f"audio Żółć {number}.wav"
        with wave.open(str(path), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b"\x00\x00" * 16000)
        files.append(path)
    page.locator("#workflow input[type=file]").set_input_files(files)
    expect(page.locator("#gui-audio-choices li")).to_have_count(2)
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(0)
    for index in (0, 1):
        page.locator("#gui-audio-choices li").nth(index).locator("button[aria-pressed]").click()
        page.locator("#workflow button[value=inspect]").click()
        expect(page.locator("#operation-status")).to_have_text("Inspection completed")
        page.locator("#workflow button[value=dry-run]").click()
        expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
        page.locator("#workflow input[name=confirmed]").check()
        page.locator("#workflow button[value=transcriptions]").click()
        expect(page.locator("#operation-status")).to_have_text("Added to staged queue")
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(2)
    assert page.locator("#transcription-jobs tbody").inner_text().count("STAGED") == 2
    expect(page.locator("#gui-audio-choices li")).to_have_count(2)
    page.locator("#gui-audio-choices li").first.get_by_role(
        "button", name="Remove from list"
    ).click()
    expect(page.locator("#gui-audio-choices li")).to_have_count(1)
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(2)
    page.evaluate("queuePost('/api/v1/transcriptions/clear-current', {confirmed:true})")
    page.evaluate("refreshJobs()")


def check_maintenance_controls(page: Page) -> None:
    """Exercise explicit diagnostics and the terminal repair handoff without installing."""
    stage(page, "workspace")
    expect(page.locator("#test-dependencies")).not_to_be_visible()
    stage(page, "settings")
    expect(page.locator("#test-dependencies")).to_be_visible()
    expect(page.locator("#run-doctor")).to_be_disabled()
    expect(page.locator("#repair-dependencies")).to_be_disabled()
    page.locator("#test-dependencies").click()
    expect(page.locator("#run-doctor")).to_be_enabled(timeout=180000)
    expect(page.locator("#repair-dependencies")).to_be_enabled()
    expect(page.locator("#dependency-checks")).not_to_be_empty()
    page.locator("#run-doctor").click()
    expect(page.locator("#doctor-result")).not_to_be_empty(timeout=90000)
    page.locator("#repair-dependencies").click()
    expect(page.locator("#dependency-repair")).to_be_visible()
    expect(page.locator("#dependency-repair pre")).to_have_text(
        "bash scripts/repair-dependencies.sh"
    )
    page.locator("#gui-locale").select_option("pl")
    expect(page.locator("#repair-dependencies")).to_have_text("Zainstaluj ponownie zależności…")
    page.locator("#gui-locale").select_option("en")
    stage(page, "workspace")
    expect(page.locator("#test-dependencies")).not_to_be_visible()


def check_cursor_and_auto_height(page: Page) -> None:
    """Use real pointer/keyboard carets, including an edit during a saved-draft request."""
    stage(page, "review")
    page.set_viewport_size({"width": 960, "height": 1080})
    text = page.locator("#review-editor textarea").first
    original = text.input_value()
    blocks = page.evaluate("reviewDocument.anchors[0].blocks.length")
    text.focus()
    text.press("Control+Home")
    text.press("ArrowRight")
    page.locator(".review-cursor-split").first.click()
    expect(page.locator(".review-cursor-status").first).to_contain_text(
        "GUI_REVIEW_CURSOR_BOUNDARY"
    )
    assert page.evaluate("reviewDocument.anchors[0].blocks.length") == blocks

    # A physical textarea click immediately after the first word creates a caret.
    text.scroll_into_view_if_needed()
    point = text.evaluate("""e => {
      const style=getComputedStyle(e), box=e.getBoundingClientRect();
      const ctx=document.createElement('canvas').getContext('2d'); ctx.font=style.font;
      return {x:box.left+parseFloat(style.paddingLeft)+ctx.measureText('Welcome').width+1,
        y:box.top+parseFloat(style.paddingTop)+parseFloat(style.lineHeight)/2};
    }""")
    page.mouse.click(point["x"], point["y"])
    caret = text.evaluate("e=>[e.selectionStart,e.selectionEnd]")
    assert caret[0] == caret[1] and caret[0] in (7, 8), caret
    page.locator(".review-cursor-split").first.click()
    expect(page.locator("#review-editor textarea").first).to_have_value("Welcome")
    page.locator("#undo-review").click()
    expect(text).to_have_value(original)

    text.focus()
    text.press("Control+Home")
    text.press("Control+ArrowRight")
    text.press("Tab")
    expect(page.locator(".review-cursor-split").first).to_be_focused()
    page.locator(".review-cursor-split").first.press("Enter")
    expect(page.locator("#review-editor textarea").first).to_have_value("Welcome")
    page.locator("#undo-review").click()
    expect(text).to_have_value(original)

    # Hold a real save response; newer keystrokes must survive and abort the stale split.
    page.evaluate("""() => {
      window.realGuiPostReview=postReview;
      postReview=async (operation, request) => {
        const payload=await window.realGuiPostReview(operation,request);
        if(operation==='save') await new Promise(resolve=>window.releaseGuiSave=resolve);
        return payload;
      };
    }""")
    text.fill(original + " saved snapshot")
    text.press("Control+Home")
    text.press("Control+ArrowRight")
    page.locator(".review-cursor-split").first.click()
    page.wait_for_function("() => typeof window.releaseGuiSave === 'function'")
    text.fill(original + " newer edit")
    page.evaluate("() => {postReview=window.realGuiPostReview; window.releaseGuiSave();}")
    expect(page.locator(".review-cursor-status").first).to_contain_text(
        "GUI_REVIEW_CHANGED_DURING_SAVE"
    )
    expect(text).to_have_value(original + " newer edit")
    assert page.evaluate("reviewDocument.anchors[0].blocks.length") == blocks
    assert page.evaluate("reviewDirty")

    text.fill(("A longer transcript line with Polish words Żółć.\n") * 35)
    stage(page, "correction")
    page.set_viewport_size({"width": 720, "height": 1000})
    stage(page, "review")
    page.wait_for_function("""() => {
      const e=document.querySelector('#review-editor textarea');
      return e.clientHeight >= e.scrollHeight && e.clientHeight > 500;
    }""")
    assert text.evaluate("e=>getComputedStyle(e).resize") == "none"
    text.fill(original)
    page.locator("#save-review").scroll_into_view_if_needed()
    before_save = page.evaluate("window.scrollY")
    page.locator("#save-review").click()
    expect(page.locator("#review-status")).to_contain_text("Draft saved; preview is required again")
    expect(text).to_have_value(original)
    assert abs(page.evaluate("window.scrollY") - before_save) <= 2


def exercise(page: Page, output: Path, baseline: bool) -> list[dict]:
    page.wait_for_function("() => csrfToken.length > 0")
    page.wait_for_function("() => Object.keys(guiWorkflowTargets).length === 8")
    for name in (
        "workspace",
        "correction",
        "review",
        "translation",
        "semantic-review",
        "dictionary",
        "saved",
        "settings",
    ):
        stage(page, name)
        expected_count = page.evaluate("name => guiWorkflowGuides[name].steps.length", name)
        expect(page.locator("#gui-stage-instructions li")).to_have_count(expected_count)
        href = page.locator("#gui-stage-instructions a[target=_blank]").get_attribute("href")
        response = page.request.get(page.url.rstrip("/") + href)
        assert response.ok and "<h1>" in response.text()
        assert page.evaluate(
            "name => Object.values(guiWorkflowTargets[name])"
            ".every(id => document.getElementById(id))",
            name,
        )
    check_maintenance_controls(page)
    page.evaluate("document.fonts.ready")
    assert page.evaluate('document.fonts.check("16px Montserrat")')
    assert page.evaluate("""document.fonts.check('16px "Noto Sans Mono"')""")
    page.evaluate("queuePost('/api/v1/transcriptions/clear-current', {confirmed:true})")
    page.locator("#output-path").fill(str(output / "project"))
    page.locator("#output-path").dispatch_event("change")
    stage_audio_without_models(page, output)
    fixtures = []
    for number in (1, 2):
        document = json.loads((ROOT / "examples/results.example.json").read_text())
        document["job_id"] = f"S01E0{number}"
        document["episode"]["episode_id"] = document["job_id"]
        path = output / (f"S01E0{number}_Żółć_" + "long-name-" * 8 + "_results.json")
        path.write_text(json.dumps(document), encoding="utf-8")
        fixtures.append(path)
    originals = [hashlib.sha256(path.read_bytes()).hexdigest() for path in fixtures]
    stage(page, "correction")
    stage(page, "correction")
    page.locator('#stage-queue-correction input[type="file"]').set_input_files(fixtures)
    expect(page.locator("#stage-queue-review .stage-queue-item")).to_have_count(2)
    page.locator('#stage-queue-correction input[type="checkbox"]').first.click()
    stage(page, "review")
    stage(page, "review")
    page.locator("#stage-queue-review .stage-queue-item button").last.click()
    text = page.locator("#review-editor textarea").first
    expect(text).to_have_value("Welcome to another episode.")
    text.fill("Welcome to another episode. Żółć")
    text.evaluate("e => {e.focus(); e.setSelectionRange(0,7)}")
    identity = page.locator("#review-identity").inner_text()
    check_cursor_and_auto_height(page)
    text.focus()
    text.evaluate("e => e.setSelectionRange(0,7)")
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
    stage(page, "review")
    # Caret-only split uses real anchors, while isolation still requires a selection.
    text.focus()
    text.evaluate("e => e.setSelectionRange(7,7)")
    page.locator(".review-cursor-split").first.click()
    expect(page.locator("#review-editor textarea").first).to_have_value("Welcome")
    page.locator("#undo-review").click()
    expect(page.locator("#review-editor textarea").first).to_have_value(
        "Welcome to another episode. Żółć"
    )
    panel = page.locator("#review-speaker-names")
    panel.evaluate("e => e.open=true")
    assert panel.locator("#gui-palette").count() == 1
    page.locator("#gui-export-palette").select_option("brand")
    expect(page.locator('input[aria-label="Speaker color speaker_001"]')).to_have_value("#f5f7fa")
    page.locator("#gui-export-palette").select_option("configured")
    configured_color = page.evaluate(
        "reviewDocument.configured_speaker_colors.speaker_001.toLowerCase()"
    )
    expect(page.locator('input[aria-label="Speaker color speaker_001"]')).to_have_value(
        configured_color
    )
    for number in range(3, 8):
        page.locator(".review-add-speaker").click()
        expect(
            page.locator(f'#review-speaker-labels input[data-speaker-id="speaker_{number:03d}"]')
        ).to_have_count(1)
    page.locator('input[aria-label="Speaker color speaker_007"]').fill("#123456")
    assert page.evaluate("guiSpeakerColors().speaker_007") == "#123456"
    page.get_by_role("button", name="Remove speaker_007", exact=True).click()
    expect(
        page.locator('#review-speaker-labels input[data-speaker-id="speaker_007"]')
    ).to_have_count(0)
    assert page.evaluate('!("speaker_007" in guiSpeakerColors())')
    page.locator("#undo-review").click()
    expect(
        page.locator('#review-speaker-labels input[data-speaker-id="speaker_007"]')
    ).to_have_count(1)
    assert page.evaluate("guiSpeakerColors().speaker_007") == "#123456"
    page.locator("#gui-production-palette").click()
    page.locator("#gui-export-palette").select_option("brand")
    expect(page.locator('input[aria-label="Speaker color speaker_007"]')).to_have_value("#123456")
    page.locator("#gui-production-palette").click()
    # Keyboard selection isolation and stable speaker ownership, not cursor splitting.
    text.focus()
    text.evaluate("e => e.setSelectionRange(0,7)")
    separate = page.locator(".review-isolate").first
    separate.focus()
    separate.press("Enter")
    expect(page.locator("#review-editor textarea").first).to_have_value("Welcome")
    page.locator("#review-editor select").first.select_option("speaker_002")
    assert page.locator(".review-control-groups").evaluate(
        "e => e.getBoundingClientRect().top >= "
        "document.querySelector('#review-editor').getBoundingClientRect().bottom"
    )
    assert page.locator(".review-control-group").evaluate_all(
        """es => es.length === 2 &&
          Math.abs(es[0].getBoundingClientRect().top - es[1].getBoundingClientRect().top) < 2 &&
          es.every(e => e.getBoundingClientRect().height < 250)"""
    )
    page.locator("#preview-review").scroll_into_view_if_needed()
    before_preview = page.evaluate("window.scrollY")
    page.locator("#preview-review").click()
    expect(page.locator("#apply-review")).to_be_enabled()
    page.wait_for_function(
        "() => document.querySelector('#review-status').textContent.startsWith('Preview passed')"
    )
    assert abs(page.evaluate("window.scrollY") - before_preview) <= 2
    page.locator('#review-workflow input[name="verified"]').check()
    page.locator("#apply-review").click()
    expect(page.locator("#export-review")).to_be_enabled()
    page.locator("#export-review").click()
    expect(page.locator("#review-status")).to_contain_text("exports completed")
    # Switching the active review preserves the independent batch selection.
    page.locator("#stage-queue-review .stage-queue-item button").first.click()
    expect(page.locator("#review-identity")).not_to_have_text(identity)
    expect(page.locator('#stage-queue-correction input[type="checkbox"]:checked')).to_have_count(1)

    # Saved drafts must be distinguishable from defaults before testing restoration.
    recovery_text = "Welcome to another episode. Saved recovery Żółć"
    page.locator("#review-editor textarea").first.fill(recovery_text)
    stage(page, "saved")
    page.locator("#workspace-name").fill("GUI integrated preview recovery")
    page.locator("#save-workspace").click()
    expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
    checkpoint = {
        "catalog": page.locator("#workspace-directory").input_value(),
        "key": page.locator("#workspace-list").input_value(),
        "result": page.evaluate("reviewDocument.result_path"),
        "review": page.evaluate("reviewDocument.review_path"),
        "translation": page.evaluate("translationReview.review_path"),
        "translation_result": page.evaluate("translationReview.result_path"),
        "text": recovery_text,
        "target": "Przykładowe tłumaczenie. Żółć",
    }
    (output / "checkpoint.json").write_text(json.dumps(checkpoint))
    # Remove all browser pointers and server queue rows before loading the saved workspace.
    page.evaluate("""async () => {
      await queuePost('/api/v1/transcriptions/clear-current', {confirmed:true});
      localStorage.clear(); sessionStorage.clear();
      reviewDirty=false; translationReviewDirty=false;
    }""")
    page.reload()
    verify_recovery(page, checkpoint)
    # Keyboard access to the locally scrolling queue and its rightmost action.
    page.set_viewport_size({"width": 390, "height": 844})
    stage(page, "workspace")
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
    page.set_viewport_size({"width": 720, "height": 1000})
    stage(page, "semantic-review")
    for index, textarea in enumerate(page.locator("#translation-review-editor textarea").all()):
        textarea.fill(f"Testowe tłumaczenie jednostki {index + 1}.")
    page.locator("#preview-translation-review").click()
    expect(page.locator("#apply-translation-review")).to_be_enabled()
    page.locator("#translation-review-confirmed").check()
    page.locator("#apply-translation-review").click()
    expect(page.locator("#export-translation-review")).to_be_enabled()
    page.locator("#export-translation-review").click()
    expect(page.locator("#translation-review-status")).to_contain_text("exported")
    stage(page, "workspace")
    # A newer source revision must warn without replacing the reviewed translation.
    stage(page, "review")
    page.locator("#preview-review").click()
    expect(page.locator("#apply-review")).to_be_enabled()
    page.locator('#review-workflow input[name="verified"]').check()
    page.locator("#apply-review").click()
    expect(page.locator("#gui-active-context")).to_contain_text("newer verified source")
    # Mixed terminal states use real queue annotations, with no simulated provider call.
    page.evaluate("""async () => {
      await queuePost('/api/v1/transcriptions/workflow-error', {
        result_path:stageQueueJobs[0].result_path, stage:'assisted_translation',
        code:'GUI_BROWSER_FIXTURE_FAILURE'});
      await reportWorkflowSkip(stageQueueJobs[1].result_path, 'correction');
    }""")
    stage(page, "workspace")
    expect(page.locator("#transcription-jobs .workflow-failed").first).to_be_visible()
    expect(page.locator("#transcription-jobs .workflow-skipped").first).to_be_visible()
    page.locator("#transcription-jobs").evaluate(
        "e => {e.scrollLeft=0; e.scrollIntoView({block:'start'})}"
    )
    for locale in ("en", "pl"):
        page.locator("#gui-locale").select_option(locale)
        for theme in ("light", "dark"):
            page.locator("#gui-theme").select_option(theme)
            expect(page.locator("#transcription-jobs .workflow-failed").first).to_be_visible()
            expect(page.locator("#transcription-jobs .workflow-skipped").first).to_be_visible()
            page.screenshot(path=str(output / f"mixed-{locale}-{theme}.png"))
    page.locator("#gui-locale").select_option("en")
    page.evaluate("reportWorkflowSuccess(stageQueueJobs[0].result_path, 'assisted_translation')")
    expect(page.locator("#transcription-jobs .workflow-failed")).to_have_count(0)
    expect(page.locator("#transcription-jobs .workflow-skipped").first).to_be_visible()
    assert originals == [hashlib.sha256(path.read_bytes()).hexdigest() for path in fixtures]
    assert list((output / "project" / "exports").glob("*.srt"))
    # Refresh the explicit checkpoint after the later semantic-approval test changed its draft.
    stage(page, "saved")
    page.locator("#save-workspace").click()
    expect(page.locator("#workspace-status")).to_contain_text("Workspace saved:")
    checkpoint["target"] = "Testowe tłumaczenie jednostki 1."
    checkpoint["applied"] = page.evaluate("appliedTranslation")
    (output / "checkpoint.json").write_text(json.dumps(checkpoint))
    return measurements


def verify_recovery(page: Page, checkpoint: dict) -> None:
    page.wait_for_function("() => csrfToken.length > 0")
    expect(page.locator("#stage-queue-review .stage-queue-item")).to_have_count(0)
    assert page.evaluate("reviewDocument === null && translationReview === null")
    assert page.locator("#review-result-path").input_value() == ""
    stage(page, "saved")
    page.locator("#workspace-directory").fill(checkpoint["catalog"])
    page.locator("#refresh-workspaces").click()
    page.wait_for_function(
        "key => [...document.querySelector('#workspace-list').options].some(o=>o.value===key)",
        arg=checkpoint["key"],
    )
    page.locator("#workspace-list").select_option(checkpoint["key"])
    page.locator("#load-workspace").click()
    expect(page.locator("#workspace-status")).to_contain_text("Workspace loaded:")
    expect(page.locator("#stage-queue-review .stage-queue-item")).to_have_count(2)
    assert page.evaluate("reviewDocument.result_path") == checkpoint["result"]
    assert page.evaluate("reviewDocument.review_path") == checkpoint["review"]
    assert page.locator("#review-result-path").input_value() == checkpoint["result"]
    expect(page.locator("#review-editor textarea").first).to_have_value(checkpoint["text"])
    assert page.evaluate("translationReview.review_path") == checkpoint["translation"]
    assert page.evaluate("translationReview.result_path") == checkpoint["translation_result"]
    expect(page.locator("#translation-review-editor textarea").first).to_have_value(
        checkpoint["target"]
    )
    if checkpoint.get("applied"):
        assert page.evaluate("appliedTranslation") == checkpoint["applied"]
        expect(page.locator("#export-translation-review")).to_be_enabled()
    assert not page.locator("#allow-empty-translation-units").is_checked()
    assert not page.locator("#translation-review-confirmed").is_checked()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument(
        "--recover", type=Path, help="Verify a saved checkpoint after server restart"
    )
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
            if args.recover:
                verify_recovery(page, json.loads(args.recover.read_text()))
                measurements = []
            else:
                measurements = exercise(page, args.output, args.baseline)
        except Exception:
            page.screenshot(path=str(args.output / "failure.png"), full_page=True)
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
