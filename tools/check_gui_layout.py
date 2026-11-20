"""Optional model-free browser check; run with an isolated Playwright installation.

Point --url at a disposable GUI server and --output at a dedicated temporary directory.
This clears that server's inactive queue and writes synthetic reviews/exports/workspaces.
It never starts transcription or calls a provider. See docs/28-integrated-gui-preview.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
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
                    ("translation", "#translation-workflow"),
                    ("correction", "#correction-workflow"),
                    ("dictionary", "#gui-dictionary-library"),
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
    page.locator("#workflow-speaker-auto").uncheck()
    page.locator("#workflow-speaker-count").fill("2")
    files = []
    for filename in ("S01E01-a.wav", "S01E01-b.wav"):
        path = output / filename
        with wave.open(str(path), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b"\x00\x00" * 16000)
        files.append(path)
    video = output / "presentation.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=s=32x32:r=10:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=sample_rate=16000:duration=1",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            str(video),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    files.append(video)
    page.locator("#workflow input[type=file]").set_input_files(files)
    expect(page.locator("#gui-audio-choices li")).to_have_count(2)
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(0)
    page.locator("#workflow-language").select_option("pl")
    page.locator("#gui-audio-choices li").last.locator("button[aria-pressed]").click()
    page.locator("#workflow-language").select_option("en")
    page.locator("#workflow-speaker-count").fill("1")
    page.locator("#workflow-speaker-count").dispatch_event("change")
    page.locator("#gui-audio-choices li").first.locator("button[aria-pressed]").click()
    assert page.locator("#workflow-language").input_value() == "pl"
    inspections = []
    page.on(
        "request",
        lambda request: (
            inspections.append(request.post_data_json)
            if request.url.endswith("/api/v1/inspect")
            else None
        ),
    )
    page.locator("#workflow button[value=inspect]").click()
    expect(page.locator("#operation-status")).to_contain_text("Inspection completed")
    expect(page.locator("#operation-summary")).to_contain_text(
        "* Recording language: selected processing value"
    )
    assert page.locator("#workflow-speaker-count").input_value() == "2"
    assert [item["language"] for item in inspections] == ["pl", "en"]
    page.locator("#workflow button[value=dry-run]").click()
    expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
    plans = json.loads(page.locator("#operation-result").text_content())
    assert len(plans) == 2 and sum(len(plan["jobs"]) for plan in plans) == 2
    # Changing an option invalidates the entire confirmed snapshot.
    page.locator("#workflow-speaker-count").fill("3")
    page.locator("#workflow-speaker-count").dispatch_event("change")
    page.locator("#workflow input[name=confirmed]").check()
    page.locator("#workflow button[value=transcriptions]").click()
    expect(page.locator("#operation-status")).to_contain_text("GUI_DRY_RUN_REQUIRED")
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(0)
    page.locator("#workflow-speaker-count").fill("2")
    page.locator("#workflow-speaker-count").dispatch_event("change")
    page.locator("#workflow button[value=dry-run]").click()
    expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
    page.locator("#workflow input[name=confirmed]").check()
    page.locator("#workflow button[value=transcriptions]").click()
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(2)
    jobs = page.evaluate("guiQueueJobs")
    assert {(job["language"], job["speaker_count"]) for job in jobs} == {("pl", 2), ("en", 1)}
    for index in (0, 1):
        expect(
            page.locator("#gui-audio-choices li").nth(index).locator("button[aria-pressed]")
        ).to_be_disabled()
    expect(page.locator("#start-queue")).to_be_enabled()
    expect(page.locator("#workflow button[value=inspect]")).to_be_disabled()
    expect(page.locator("#workflow button[value=dry-run]")).to_be_disabled()
    expect(page.locator("#transcription-jobs input[type=checkbox]")).to_have_count(0)
    expect(
        page.get_by_role("button", name="Remove selected queue items", exact=True)
    ).to_have_count(0)
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(2)
    assert page.locator("#transcription-jobs tbody").inner_text().count("STAGED") == 2
    check_runtime_feedback(page, output)
    expect(page.locator("#gui-audio-choices li")).to_have_count(2)
    page.locator("#gui-audio-choices li").first.get_by_role(
        "button", name="Remove from list"
    ).click()
    expect(page.locator("#gui-audio-choices li")).to_have_count(1)
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(2)
    # Add real completed history alongside staged work. Intercept only Start so no ASR runs.
    history_document = json.loads((ROOT / "examples/results.example.json").read_text())
    history_document["job_id"] = "QUEUE_HISTORY"
    history_document["episode"]["episode_id"] = "QUEUE_HISTORY"
    history_path = output / "QUEUE_HISTORY_results.json"
    history_path.write_text(json.dumps(history_document), encoding="utf-8")
    stage(page, "correction")
    page.locator('#stage-queue-correction input[type="file"]').set_input_files(history_path)
    expect(page.locator("#stage-queue-review .stage-queue-item")).to_have_count(1)
    stage(page, "workspace")
    expect(page.locator("#start-queue")).to_be_enabled()
    page.route(
        "**/api/v1/transcriptions/start",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body='{"queued":2}'
        ),
        times=1,
    )
    page.locator("#start-queue").click()
    expect(page.locator("#operation-status")).to_contain_text("Started 2 queued job(s)")
    expect(page.locator("#start-queue")).to_be_enabled()
    page.route(
        "**/api/v1/transcriptions/start",
        lambda route: route.fulfill(
            status=409,
            content_type="application/json",
            body='{"error":{"code":"GUI_QUEUE_ACTIVE","message":"Synthetic start rejection"}}',
        ),
        times=1,
    )
    page.locator("#start-queue").click()
    expect(page.locator("#operation-status")).to_contain_text("GUI_QUEUE_ACTIVE")
    expect(page.locator("#start-queue")).to_be_enabled()
    page.evaluate("queuePost('/api/v1/transcriptions/clear-current', {confirmed:true})")
    page.evaluate("refreshJobs()")
    expect(page.locator("#start-queue")).to_be_disabled()


def check_runtime_feedback(page: Page, output: Path) -> None:
    """Keep progress/ETA readable in the real narrow queue cell and both locales."""
    page.evaluate("""() => {
      const cell=document.querySelector('#transcription-jobs tbody td');
      guiPreferences.showEta=true;
      const widget=renderRuntimeProgress({job_id:"runtime-synthetic",status:'running',
        runtime_progress:{phase:'align',percent:67,
        elapsed_seconds:845,eta_seconds:120,eta_min_seconds:60,eta_max_seconds:240,
        stream_index:2,stream_count:3,calibrated:true,overdue:false}});
      widget.id='runtime-test';cell.append(widget);
    }""")
    expect(page.locator("#runtime-test .gui-runtime-elapsed")).to_contain_text(
        "14:06", timeout=1800
    )
    for locale in ("en", "pl"):
        page.locator("#gui-locale").select_option(locale)
        for width in (720, 960):
            page.set_viewport_size({"width": width, "height": 1080})
            widget = page.locator("#runtime-test")
            widget.scroll_into_view_if_needed()
            expect(widget.locator("progress")).to_have_attribute("value", "67")
            assert widget.evaluate(
                "e=>e.getBoundingClientRect().right <= "
                "e.closest('td').getBoundingClientRect().right+1"
            )
            assert not geometry(page)["overflow"]
            page.screenshot(path=str(output / f"runtime-{locale}-{width}.png"))
    page.locator("#runtime-test").evaluate("e=>e.remove()")
    page.evaluate("guiPreferences.showEta=false")
    assert page.evaluate(
        """() => !renderRuntimeProgress({job_id:'hidden-eta',status:'running',
          runtime_progress:{phase:'align',percent:50,elapsed_seconds:20,eta_seconds:40,
          eta_min_seconds:20,eta_max_seconds:70}}).textContent.includes('ETA')"""
    )
    page.locator("#gui-locale").select_option("en")
    page.set_viewport_size({"width": 1440, "height": 1000})


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


def check_localized_interface(page: Page) -> None:
    """Audit static states and source copy without changing user text or calling providers."""
    import ast
    import re

    page.locator("#gui-locale").select_option("pl")
    stage(page, "workspace")
    expect(page.locator("#compatibility")).to_have_text("Stan: usługa lokalna gotowa")
    expect(page.locator("#gui-active-context .gui-path")).not_to_contain_text("Choose a recording")
    # The initial dictionary catalog is populated automatically; no Refresh click is needed.
    expect(page.locator(".library-item")).not_to_have_count(0)
    assert page.locator("#input-path").evaluate(
        "e=>e.nextElementSibling.id==='gui-input-path-hint'"
    )
    assert page.locator("#gui-audio-choices").evaluate(
        "e=>Boolean(document.querySelector('#gui-input-path-hint')"
        ".compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING)"
    )
    assert page.locator("#gui-export-palette").input_value() == "configured"
    assert page.locator("#gui-export-palette option").first.inner_text() == "Example default"
    assert page.locator('#gui-export-palette option[value="brand"]').inner_text() == "EwP Brand®"
    page.locator(".gui-language-info summary").click()
    expect(page.locator(".gui-language-info p")).to_contain_text(
        "nie jest gwarantowany tryb tłumaczenia"
    )
    page.locator("#output-path").click()
    assert not page.locator(".gui-language-info").evaluate("e=>e.open")
    page.locator(".gui-language-info summary").click()
    page.keyboard.press("Escape")
    assert not page.locator(".gui-language-info").evaluate("e=>e.open")
    expect(page.locator(".gui-language-info summary")).to_be_focused()
    assert page.locator("#output-path").evaluate(
        "e=>Boolean(e.compareDocumentPosition(document.querySelector('#input-path')) "
        "& Node.DOCUMENT_POSITION_FOLLOWING)"
    )
    literals = set()
    for file in (ROOT / "src/ewp_transcripts/web_assets").glob("*.js"):
        if file.name.startswith("ui_locale"):
            continue
        for match in re.finditer(
            r"\.(?:textContent|title)\s*=\s*(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')",
            file.read_text(),
        ):
            try:
                value = ast.literal_eval(match[1]).strip()
            except (SyntaxError, ValueError):
                continue
            if re.search(r"[A-Za-z]{3}", value):
                literals.add(value)
    missing = page.evaluate("texts=>texts.filter(text=>guiUiText(text)===text)", sorted(literals))
    assert set(missing) <= {"EwP Transcripts", "Model"}, missing
    # Include conditional messages and confirmation dialogs, not only direct assignments.
    all_literals = set()
    for file in (ROOT / "src/ewp_transcripts/web_assets").glob("*.js"):
        if file.name.startswith("ui_locale"):
            continue
        for match in re.finditer(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'", file.read_text()):
            try:
                value = ast.literal_eval(match[0]).strip()
            except (SyntaxError, ValueError):
                continue
            if re.search(r"[A-Za-z]{3} [A-Za-z]{2}", value) and not any(
                char in value for char in "<>#{=}"
            ):
                all_literals.add(value)
    missing = page.evaluate(
        "texts=>texts.filter(text=>guiUiText(text)===text)", sorted(all_literals)
    )
    non_ui = {
        "Example default",
        "Configured palette",
        "EwP Brand®",
        "Configured production",
        "EwP Transcripts",
        "EwP brand",
        "actions dictionary-evidence-navigation",
        "confirmation is required",
        "connection-light connection-unknown",
        "example misspelling",
        "inline-working inline-done",
        "inline-working inline-error",
        "noopener noreferrer",
        "preferred spelling",
        "queue-table library-comparison",
        "queue-table plan-table",
        "review-bottom-navigation actions",
        "review-control-line review-prepare-line",
        "use strict",
    }
    assert set(missing) <= non_ui, missing
    original_error = "GUI_API_UNAVAILABLE: Synthetic original backend explanation"
    page.locator("#operation-status").evaluate(
        "(element,text)=>{element.textContent=text}", original_error
    )
    expect(page.locator("#operation-status")).to_contain_text(
        "GUI_API_UNAVAILABLE: Lokalny serwer GUI"
    )
    expect(page.locator(".gui-error-diagnostic pre")).to_have_text(original_error)
    page.locator("#operation-status").evaluate("element=>{element.textContent=''}")
    expect(page.locator(".gui-error-diagnostic")).to_have_count(0)
    samples = {
        "Planning…": "Planowanie…",
        "Selected for inspection": "Wybrano do sprawdzenia",
        "Review identity:": "ID weryfikacji:",
        "Dry-run completed": "Plan gotowy",
        "Adding…": "Dodawanie…",
        "Added to staged queue": "Dodano do kolejki oczekującej na uruchomienie",
        "Correction is running; do not close the server.": "Korekta trwa; nie zamykaj serwera.",
        ("Translation is running; do not close the server."): (
            "Tłumaczenie trwa; nie zamykaj serwera."
        ),
        "Review: pending": "Weryfikacja: oczekuje",
        "ASR: completed_results.json": "ASR: completed_results.json",
        (
            "WARNING: source is raw, not manually verified. The non-final translation "
            "requires semantic manual review."
        ): "OSTRZEŻENIE: źródło to surowe",
        "Queue finished": "Kolejka ukończona",
        (
            "GUI_DRY_RUN_REQUIRED: Run and review dry-run for this exact input, output, "
            "language, and speaker count before adding it to the queue."
        ): ("GUI_DRY_RUN_REQUIRED: Najpierw zaplanuj"),
    }
    for source, expected in samples.items():
        assert page.evaluate("source=>guiUiText(source)", source).startswith(expected)
    stage(page, "correction")
    expect(page.locator("#generate-correction")).to_have_text("Wygeneruj wstępną korektę")
    expect(page.locator("#generate-translation")).to_have_text("Wygeneruj propozycję tłumaczenia")
    expect(page.locator("#review-translation")).to_have_text("Przejdź do przeglądu tłumaczenia")
    page.locator("#correction-workflow .provider-settings").evaluate("e=>e.open=true")
    page.get_by_role("button", name="Ustaw klucz API OpenRouter", exact=True).click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_contain_text("Klucz trafia wyłącznie do tego lokalnego serwera")
    expect(dialog.get_by_role("button", name="Ustaw klucz na tę sesję", exact=True)).to_be_visible()
    dialog.get_by_role("button", name="Anuluj", exact=True).click()
    stage(page, "review")
    expect(page.locator("#preview-review")).to_have_text("Zatwierdź")
    expect(page.locator("#prepare-review")).to_have_text("Przygotuj tekst do sprawdzenia")
    expect(page.locator("#apply-review")).to_have_text("Zapisz i przygotuj do eksportu")
    assert page.locator("#gui-review-step-5").evaluate("e=>e.tagName==='H3'")
    page.locator("#gui-locale").select_option("en")
    expect(page.locator("#preview-review")).to_have_text("Apply")
    expect(page.locator("#prepare-review")).to_have_text("Prepare text for review")


def check_motion_feedback(page: Page, output: Path) -> None:
    """Use the owner asset for real status/feedback hooks, including reduced motion."""
    page.wait_for_function("() => guiPendingRequests === 0")
    page.evaluate("setGuiWorking(true, document.querySelector('#prepare-review'))")
    for selector in ("#gui-working", "#prepare-review + .inline-working"):
        marker = page.locator(selector)
        assert marker.evaluate(
            "e=>getComputedStyle(e,'::before').backgroundImage.includes('/assets/brand/gear.svg')"
        )
        assert marker.evaluate("e=>getComputedStyle(e,'::before').borderTopWidth==='0px'")
    page.evaluate("setGuiWorking(false, document.querySelector('#prepare-review'))")
    assert page.locator("#prepare-review + .inline-working").evaluate(
        "e=>getComputedStyle(e,'::before').backgroundImage==='none'"
    )
    for selector, message in [
        ("#operation-status", "Inspecting…"),
        ("#correction-status", "Correction is running; do not close the server."),
        ("#translation-status", "Translation is running; do not close the server."),
        ("#operation-status", "Status: connecting"),
        ("#doctor-status", "Running doctor…"),
        ("#library-status", "Saving new dictionary version…"),
        ("#gui-palette-status", "Saving custom profile…"),
    ]:
        node = page.locator(selector)
        node.evaluate("(e,text)=>{e.textContent=text}", message)
        expect(node).to_have_attribute("aria-busy", "true")
        assert node.evaluate(
            "e=>getComputedStyle(e,'::before').backgroundImage.includes('/assets/brand/gear.svg')"
        )
        node.evaluate("e=>{e.textContent=''}")
        expect(node).to_have_attribute("aria-busy", "false")
    svg = page.context.browser.new_page()
    svg.goto(page.url.rstrip("/") + "/assets/brand/gear.svg")
    ring = svg.locator("#gear--gear-ring")
    assert ring.evaluate("e=>getComputedStyle(e).animationName") == "gear-gear"
    initial_transform = ring.evaluate("e=>getComputedStyle(e).transform")
    svg.wait_for_timeout(150)  # Observe the asset's own animation without unsafe-eval polling.
    assert ring.evaluate("e=>getComputedStyle(e).transform") != initial_transform
    svg.screenshot(path=str(output / "gear-animation.png"))
    svg.emulate_media(reduced_motion="reduce")
    expect(ring).to_have_css("animation-name", "none")
    svg.close()


def check_source_playback(page: Page, output: Path) -> None:
    """Decode real synthetic source audio, seek exact words and retain grouped-track state."""
    expect(page.locator("#gui-source-playback")).to_be_visible()
    page.wait_for_function("() => playbackAudio.readyState >= 1")
    expect(page.locator("#gui-playback-source option")).to_have_count(1)
    assert page.locator("#gui-playback-source").input_value() == "mix"
    for speed in ("1.5", "2", "1"):
        page.locator("#gui-playback-speed").select_option(speed)
        assert page.evaluate("playbackAudio.playbackRate") == float(speed)
    expect(page.locator(".review-source-files").first).to_contain_text("playback-")
    seek = page.locator(".review-seek").nth(1)
    assert seek.evaluate(
        "e=>e.getBoundingClientRect().top >= "
        "e.previousElementSibling.getBoundingClientRect().bottom"
    )
    seek.click()
    page.wait_for_function("() => playbackAudio.currentTime >= 4.32 && !playbackAudio.paused")
    page.evaluate("playbackAudio.pause()")
    assert page.evaluate("playbackAudio.currentTime") < 5.5
    url = page.locator("#gui-playback-audio").get_attribute("src")
    response = page.request.get(page.url.rstrip("/") + url, headers={"Range": "bytes=0-43"})
    assert response.status == 206 and response.body()[:4] == b"RIFF"
    assert response.headers["content-range"].startswith("bytes 0-43/")
    response = page.request.get(page.url.rstrip("/") + url, headers={"Range": "bytes=99999999-"})
    assert response.status == 416
    page.evaluate("playbackAudio.currentTime=2; rememberPlaybackPosition()")
    stage(page, "workspace")
    expect(page.locator("#gui-source-playback")).not_to_be_visible()
    assert page.evaluate("playbackAudio.paused")
    stage(page, "review")
    page.wait_for_function(
        "() => playbackAudio.readyState >= 1 && Math.abs(playbackAudio.currentTime - 2) < .1"
    )
    assert page.locator("#gui-playback-source").input_value() == "mix"
    current = page.evaluate("reviewDocument.result_path")
    other = page.evaluate(
        "stageQueueJobs.find(job=>job.result_path && "
        "job.result_path!==reviewDocument.result_path).result_path"
    )
    for result in (other, current):
        page.evaluate(
            "path=>openManualReviewForResult(path, document.querySelector('#output-path').value)",
            result,
        )
        page.wait_for_function("() => playbackAudio.readyState >= 1")
    assert page.locator("#gui-playback-source").input_value() == "mix"
    assert abs(page.evaluate("playbackAudio.currentTime") - 2) < 0.1
    page.locator("#gui-locale").select_option("pl")
    expect(page.locator(".review-seek").first).to_have_text("Przejdź do tego fragmentu")
    for width in (960, 1920):
        page.set_viewport_size({"width": width, "height": 1080})
        page.screenshot(path=str(output / f"playback-{width}.png"))
    page.locator("#gui-locale").select_option("en")
    page.set_viewport_size({"width": 1440, "height": 1000})


def check_video_staging(page: Page, output: Path) -> None:
    """Exercise the native video picker through real FFprobe and durable queue staging."""
    stage(page, "workspace")
    while page.locator("#gui-audio-choices li").count():
        page.locator("#gui-audio-choices li").first.get_by_role(
            "button", name="Remove from list"
        ).click()
    video = output / "video-input.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=s=32x32:r=10:d=2",
            "-f",
            "lavfi",
            "-i",
            "sine=sample_rate=16000:duration=2",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            str(video),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    picker = page.locator("#workflow input[type=file]")
    assert ".mp4" in picker.get_attribute("accept")
    picker.set_input_files(video)
    expect(page.locator("#gui-audio-choices li")).to_have_count(1)
    with page.expect_response("**/api/v1/inspect") as response:
        page.locator("#workflow button[value=inspect]").click()
    inspected = response.value.json()["result"]["episodes"][0]["sources"][0]
    assert inspected["media_type"] == "video" and inspected["stream"]["index"] == 1
    page.locator("#workflow button[value=dry-run]").click()
    expect(page.locator("#operation-status")).to_have_text("Dry-run completed")
    page.locator("#workflow input[name=confirmed]").check()
    page.locator("#workflow button[value=transcriptions]").click()
    expect(page.locator("#transcription-jobs tbody tr")).to_have_count(1)
    source = Path(page.evaluate("stageQueueJobs[0].input_path"))
    assert source.suffix == ".mp4" and source.read_bytes() == video.read_bytes()
    page.evaluate("queuePost('/api/v1/transcriptions/clear-current', {confirmed:true})")
    page.evaluate("refreshJobs()")
    expect(page.locator("#start-queue")).to_be_disabled()


def check_dictionary_library(page: Page, output: Path) -> None:
    stage(page, "dictionary")
    catalog = output / "edited-dictionaries"
    page.locator("#library-directory").fill(str(catalog))
    page.locator("#library-example").click()
    page.locator("#library-save").click()
    expect(page.locator("#library-status")).to_contain_text("New dictionary version saved")
    original = catalog / "example-pl-v1.json"
    digest = hashlib.sha256(original.read_bytes()).hexdigest()
    page.locator("#library-entries input").nth(1).fill("Preferred revised term")
    page.locator("#library-save").click()
    expect(page.locator("#library-status")).to_contain_text("New dictionary version saved")
    edition = catalog / "example-pl-v2.json"
    assert edition.exists() and hashlib.sha256(original.read_bytes()).hexdigest() == digest
    page.locator("#library-select").select_option(str(original))
    page.locator("#library-compare").select_option(str(edition))
    page.locator("#library-diff").click()
    expect(page.locator("#library-comparison")).to_contain_text("Preferred revised term")
    expect(page.locator("#library-status")).to_contain_text("1 differences")
    row = page.get_by_text("example-pl-v1 · correction", exact=True).locator("..")
    row.get_by_role("button", name="Remove from list", exact=True).click()
    expect(page.locator(".library-item")).to_have_count(1)
    assert original.exists()
    page.locator("#library-show-hidden").check()
    expect(page.locator(".library-item")).to_have_count(2)
    page.get_by_role("button", name="Restore to list", exact=True).click()
    expect(page.get_by_role("button", name="Restore to list", exact=True)).to_have_count(0)
    page.locator("#library-select").select_option(str(original))
    page.locator("#library-open").click()
    expect(page.locator("#library-status")).to_contain_text("Dictionary loaded")
    page.locator("#library-id").fill("example-pl-v1")
    page.locator("#library-save").click()
    expect(page.locator("#library-status")).to_contain_text("immutable")
    assert hashlib.sha256(original.read_bytes()).hexdigest() == digest
    page.locator("#library-show-hidden").uncheck()


def check_user_profiles(page: Page, output: Path) -> None:
    """Round-trip one-file profiles and exact dictionary exports through real local APIs."""
    stage(page, "settings")
    expect(page.locator("#gui-show-eta")).not_to_be_checked()
    page.locator("#gui-show-eta").check()
    expect(page.locator("#gui-user-profile")).to_contain_text("3 successful transcriptions")
    page.locator("#user-profile-name").fill("Portable browser profile")
    with page.expect_download() as pending:
        page.locator("#user-profile-export").click()
    profile_file = output / "portable-profile.json"
    pending.value.save_as(profile_file)
    exported = json.loads(profile_file.read_text())
    assert exported["preferences"]["showEta"] is True
    assert len(exported["dictionaries"]) == 2
    assert "api_key" not in exported and "confirmed" not in exported["fields"]
    page.locator("#gui-show-eta").uncheck()
    page.locator("#gui-locale").select_option("pl")
    page.locator("#gui-theme").select_option("dark")
    page.locator("#user-profile-file").set_input_files(profile_file)
    expect(page.locator("#user-profile-status")).to_contain_text("Profile loaded")
    assert page.locator("#gui-locale").input_value() == "en"
    expect(page.locator("#gui-show-eta")).to_be_checked()
    expect(page.locator("#library-select option")).to_have_count(3)
    page.locator("#user-profile-load").click()
    expect(page.locator("#user-profile-status")).to_contain_text("Profile loaded")
    page.locator("#gui-show-eta").uncheck()
    stage(page, "dictionary")
    chosen = page.locator("#library-select option").nth(1).get_attribute("value")
    page.locator("#library-select").select_option(chosen)
    with page.expect_download() as pending:
        page.locator("#library-export").click()
    dictionary = output / "exported-dictionary.json"
    pending.value.save_as(dictionary)
    assert dictionary.read_bytes() == Path(chosen).read_bytes()
    destination = output / "independent-dictionary-import"
    page.locator("#library-directory").fill(str(destination))
    page.locator("#library-file").set_input_files(dictionary)
    expect(page.locator("#library-status")).to_contain_text("Dictionary imported")
    assert next(destination.glob("*.json")).read_bytes() == dictionary.read_bytes()
    stage(page, "settings")
    assert (
        page.locator(".gui-artwork-credit").evaluate(
            "e=>parseFloat(getComputedStyle(e).borderTopWidth)"
        )
        >= 1
    )
    assert page.locator('link[rel="icon"]').get_attribute("href").endswith("/favicon.svg")
    stage(page, "workspace")


def check_workflow_polish(page: Page) -> None:
    page.locator("#gui-locale").select_option("en")
    for name in ("correction", "review", "translation", "semantic-review"):
        stage(page, name)
        assert page.locator(f"#stage-queue-{name}").evaluate("""e =>
          [...e.children].at(-1).classList.contains('workflow-progress')""")
    stage(page, "correction")
    assert not page.locator("#correction-dictionary").evaluate("e=>e.closest('details').open")
    stage(page, "translation")
    page.locator("#stage-queue-translation .stage-queue-item button").first.click()
    expected = page.evaluate("translationSourceJob().language === 'pl' ? 'en' : 'pl'")
    expect(
        page.locator(f'#gui-translation-directions button[data-target="{expected}"]')
    ).to_have_attribute("aria-pressed", "true")
    assert not page.locator("#gui-translation-inputs").evaluate("e=>e.open")
    assert not page.locator("#translation-dictionary").evaluate("e=>e.closest('details').open")
    expect(page.locator("#gui-manual-translation")).to_have_count(0)
    assert page.locator("#skip-translation").evaluate("""e =>
      e.getBoundingClientRect().top >=
      document.querySelector('#stage-queue-translation').getBoundingClientRect().bottom""")
    other = "pl" if expected == "en" else "en"
    page.locator(f'#gui-translation-directions button[data-target="{other}"]').click()
    expect(page.locator("#gui-direction-warning")).to_be_visible()
    assert page.locator("#translation-target").input_value() == expected
    page.get_by_role("button", name="Accept direction change", exact=True).click()
    expect(
        page.locator(f'#gui-translation-directions button[data-target="{other}"]')
    ).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#generate-translation")).to_be_disabled()
    page.locator(f'#gui-translation-directions button[data-target="{expected}"]').click()
    page.get_by_role("button", name="Accept direction change", exact=True).click()
    expect(page.locator("#generate-translation")).to_be_enabled()
    # Recording cards follow the recording's progress, independent of the screen being viewed.
    stage(page, "dictionary")
    page.locator("#gui-recordings button").first.click()
    expected_stage = page.evaluate("""() => {
      const next=nextWorkflowStage(guiKnownJobs[0]);
      return next==='original-export'?'review':
        ['translated-export','finished'].includes(next)?'semantic-review':next;
    }""")
    expect(page.locator(f'[data-gui-stage="{expected_stage}"]')).to_have_attribute(
        "aria-current", "step"
    )
    stage(page, "review")
    for width in (960, 1920):
        page.set_viewport_size({"width": width, "height": 1080})
        measured = page.locator(".review-control-groups").evaluate("""e => {
          const a=e.children[0].getBoundingClientRect(), b=e.children[1].getBoundingClientRect();
          const boxes=['#undo-review','#redo-review','#clear-review']
            .map(id=>document.querySelector(id).getBoundingClientRect());
          return {height:Math.abs(a.height-b.height),
            row:Math.max(...boxes.map(r=>r.top))-Math.min(...boxes.map(r=>r.top))};
        }""")
        assert measured["height"] <= 1 and measured["row"] <= 2, measured
    # Export the already verified source revision of the translated recording as well.
    page.evaluate("""async () => {
      const job=stageQueueJobs.find(item=>item.result_path===translationReview.result_path);
      await postReview('export', {result_path:job.result_path,
        revision_path:job.workflow.review.path,
        export_output_directory:`${job.output_directory}/exports`, formats:['txt']});
      await refreshJobs();
    }""")
    # Completed cleanup is checked with real server annotations/artifacts, never a fake UI flag.
    jobs = page.evaluate(
        "stageQueueJobs.map(job=>({id:job.job_id,path:job.result_path,workflow:job.workflow}))"
    )
    finished = next(
        job
        for job in jobs
        if all(
            job["workflow"][key]["state"] == "complete"
            for key in ("review", "original_export", "translation", "translated_export")
        )
    )
    for optional in ("correction", "assisted_translation"):
        page.evaluate(
            "([path,stage])=>reportWorkflowSkip(path,stage)", [finished["path"], optional]
        )
    page.evaluate("refreshJobs()")
    stage(page, "workspace")
    expect(page.locator("#remove-completed-queue-items")).to_be_visible()
    page.locator("#remove-completed-queue-items").click()
    page.wait_for_function("id=>!stageQueueJobs.some(job=>job.job_id===id)", arg=finished["id"])
    assert page.evaluate("stageQueueJobs.length") == len(jobs) - 1
    assert Path(finished["path"]).exists()


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
    check_localized_interface(page)
    check_motion_feedback(page, output)
    check_maintenance_controls(page)
    check_dictionary_library(page, output)
    check_user_profiles(page, output)
    stage(page, "workspace")
    page.evaluate("document.fonts.ready")
    assert page.evaluate('document.fonts.check("16px Montserrat")')
    assert page.evaluate("""document.fonts.check('16px "Noto Sans Mono"')""")
    page.evaluate("queuePost('/api/v1/transcriptions/clear-current', {confirmed:true})")
    page.locator("#output-path").fill(str(output / "project"))
    page.locator("#output-path").dispatch_event("change")
    stage_audio_without_models(page, output)
    check_video_staging(page, output)
    fixtures = []
    for number in (1, 2):
        document = json.loads((ROOT / "examples/results.example.json").read_text())
        document["job_id"] = f"S01E0{number}"
        document["episode"]["episode_id"] = document["job_id"]
        for source in document["sources"]:
            audio_path = output / f"playback-{number}-{source['source_id']}.wav"
            with wave.open(str(audio_path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(16000)
                audio.writeframes(b"\0\0" * 16000 * 8)
            source.update(
                input_path=str(audio_path),
                normalized_path=str(audio_path),
                filename=audio_path.name,
                sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
                size_bytes=audio_path.stat().st_size,
                duration_ms=8000,
            )
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
    check_source_playback(page, output)
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
    assert panel.locator(".review-add-speaker").evaluate("""button => {
      const last=button.parentElement.querySelector('.review-speaker-label-row:last-of-type');
      return !last || button.getBoundingClientRect().top >= last.getBoundingClientRect().bottom;
    }""")
    page.locator("#gui-export-palette").select_option("brand")
    expect(page.locator("#gui-profile-swatches span")).to_have_count(6)
    assert page.locator("#gui-profile-swatches span").nth(2).get_attribute("title") == "#F2C55B"
    expect(page.locator('input[aria-label="Speaker color speaker_001"]')).to_have_value("#f5f7fa")
    page.locator("#gui-export-palette").select_option("configured")
    configured_color = "#ffe8a3"
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
    page.locator("#gui-palette-name").fill("Browser custom profile")
    page.locator("#gui-save-palette").click()
    expect(page.locator("#gui-palette-status")).to_contain_text("Custom profile saved")
    page.locator("#gui-apply-palette").click()
    assert page.evaluate("guiExportPreferences().speaker_colors.speaker_007") == "#123456"
    page.locator("#gui-export-palette").select_option("brand")
    expect(page.locator('input[aria-label="Speaker color speaker_007"]')).to_have_value("#f5f7fa")
    # Preview changes swatches while leaving applied export colors untouched.
    assert page.evaluate("guiExportPreferences().speaker_colors.speaker_007") == "#123456"
    page.locator("#gui-export-palette").select_option("Browser custom profile")
    expect(page.locator('input[aria-label="Speaker color speaker_007"]')).to_have_value("#123456")
    page.locator("#gui-export-palette").select_option("configured")
    page.locator("#gui-apply-palette").click()
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
    page.locator("#gui-locale").select_option("pl")
    page.locator("#apply-review").click()
    expect(page.locator('#review-workflow input[name="verified"]')).to_have_attribute(
        "aria-invalid", "true"
    )
    expect(page.locator('#review-workflow input[name="verified"]').locator("..")).to_have_class(
        "confirmation field-error"
    )
    expect(page.locator("#review-status-verification-feedback")).to_contain_text(
        "Zaznacz „Ręcznie sprawdziłem treść…”"
    )
    page.locator('#review-workflow input[name="verified"]').check()
    expect(page.locator("#review-status-verification-feedback")).to_be_hidden()
    page.locator("#gui-locale").select_option("en")
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
    page.locator("#apply-translation-review").click()
    expect(page.locator("#translation-review-confirmed")).to_have_attribute("aria-invalid", "true")
    expect(page.locator("#translation-review-status-verification-feedback")).to_be_visible()
    page.locator("#translation-review-confirmed").check()
    expect(page.locator("#translation-review-status-verification-feedback")).to_be_hidden()
    page.locator("#apply-translation-review").click()
    expect(page.locator("#export-translation-review")).to_be_enabled()
    # Reopening optional translation clears a transient candidate while the saved review remains.
    page.evaluate("""async () => {
      const job=stageQueueJobs.find(item=>item.result_path===translationReview.result_path);
      await openStageQueueItem(job,'translation');
    }""")
    assert page.evaluate("translationCandidate === null && translationReview !== null")
    stage(page, "semantic-review")
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
    check_workflow_polish(page)
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


def check_sentence_guidance(page: Page, output: Path) -> None:
    """Real model-free preparation renders sentence-aware sections and fallback warnings."""
    for punctuated in (True, False):
        document = json.loads((ROOT / "examples/results.example.json").read_text())
        document["job_id"] = "BOUNDARIES" if punctuated else "UNPUNCTUATED"
        document["episode"]["episode_id"] = document["job_id"]
        segment = document["transcript"]["segments"][0]
        template = segment["words"][0]
        segment["words"] = [
            dict(
                template,
                word_id=f"word_{index + 1:06d}",
                text=f"word{index}" + ("." if punctuated and index + 1 in (210, 430, 581) else ""),
                start_ms=index * 10,
                end_ms=(index + 1) * 10,
                speaker_id="speaker_001",
            )
            for index in range(581)
        ]
        segment.update(
            text=" ".join(word["text"] for word in segment["words"]), start_ms=0, end_ms=5810
        )
        document["transcript"]["segments"] = [segment]
        result = output / f"{document['job_id']}_results.json"
        result.write_text(json.dumps(document))
        payload = page.evaluate(
            """async data => {
          const payload=await postReview('prepare',
            {result_path:data.result,review_output_directory:data.reviews});
          renderReview(payload);showGuiStage('review');return payload;
        }""",
            {"result": str(result), "reviews": str(output / "boundary-reviews")},
        )
        warning = page.locator("#review-sentence-warning")
        assert payload["sentence_boundary_warning"] is not punctuated
        if punctuated:
            assert [len(anchor["blocks"][0]["text"].split()) for anchor in payload["anchors"]] == [
                210,
                220,
                151,
            ]
            expect(warning).not_to_be_visible()
        else:
            expect(warning).to_be_visible()
            assert warning.evaluate(
                "e=>Boolean(e.compareDocumentPosition("
                "document.querySelector('#review-editor .review-anchor')) & "
                "Node.DOCUMENT_POSITION_FOLLOWING)"
            )
            for locale in ("en", "pl"):
                page.locator("#gui-locale").select_option(locale)
                for theme, color in (("light", "rgb(180, 35, 24)"), ("dark", "rgb(255, 155, 145)")):
                    page.locator("#gui-theme").select_option(theme)
                    expect(warning).to_have_css("color", color)
            page.set_viewport_size({"width": 960, "height": 1080})
            warning.screenshot(path=str(output / "sentence-warning.png"))
            buttons = page.locator("#review-editor .review-block-controls").first
            assert (
                buttons.evaluate(
                    "e=>new Set([...e.querySelectorAll('button')]"
                    ".map(button=>Math.round(button.getBoundingClientRect().top))).size"
                )
                == 1
            )


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
                check_sentence_guidance(page, args.output)
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
