# GUI-34a responsive access verification

Base: `9117d7f6bf72feb8afe4e024f801669790c8a95a`, `main`, application `0.19.0`.
This is an intermediate product increment, not acceptance of the complete new GUI.

Reference inputs: private UI handoff 0.1.0 / accepted brandbook 0.4.0, including its
workflow, acceptance, technical verification T01–T08, responsive T09 and owner decisions
O029–O031, O037/O038, O053, O076/O078. Only product-specific changes and content-free
evidence are retained here; no private bundle, transcript examples or brand assets are copied.
The owner's current task narrows adoption to responsive access. It supersedes the package's
broader integration sequence: audio import, cursor splitting, locale/theme controls, branding,
palette/renderer migration and playback remain outside this slice. The graphic creator URL
remains an unverified placeholder; TODO: replace it when the owner supplies the real URL.

## Implemented scope and compatibility

| Existing surface | Change | Preserved boundary |
| --- | --- | --- |
| Transcription queue | Correct six column widths; wrap markers inside their cells; labeled focusable local scroll region and keyboard hint | Existing table, removal selection, per-job status/settings, full filenames and actions |
| Correction/review/translation/semantic queues | Stack action under identity below 48rem; constrain checkbox width | Existing selection sets, item actions, active editor and stage states |
| Source review | Stack speaker/text below 48rem; allow grid children to shrink | Same control IDs/bindings, selection isolation, speakers, anchors, timing, dirty draft, Preview/Apply/export |
| Review recovery | Fit control groups to available width | Prepare/Preview, Save/Restore, Undo/Redo and Clear remain available |
| Translation/provider/workspace actions | Allow wrapped buttons, growing feedback space and connection-status wrapping | Same actions, source/target ownership, consent, credentials, recovery and cleanup |

No JavaScript workflow, application-service, schema, export-renderer or palette changes.
No navigation shell or right-context panel is introduced. Future shell work must retain these
functions when columns reflow. No page-level horizontal clipping is added.

## VM evidence

Ubuntu 26.04.1, Python 3.12.13; separate temporary Playwright **1.65.2** environment,
Chromium Headless Shell **159.0.8154.6**, browser revision **1255**.
The current stable package was resolved from PyPI; official
[release notes](https://playwright.dev/python/docs/release-notes) and
[headless browser installation guidance](https://playwright.dev/python/docs/browsers)
were consulted. No production dependency or lockfile changes were needed. Downloads and
local browser/server execution required sandbox approval; no desktop/system packages were installed.

`tools/check_gui_layout.py` uses the real bundled frontend and API, two generated canonical
fixtures based on the repository example, real mutable reviews and immutable exports. No audio,
ML initialization or provider calls are involved. Baseline and after screenshots use the same
fixtures, viewport sizes and system light/dark media preferences. Screenshots and runtime data
are disposable; only this content-free record is retained.

Measured source-textarea widths (CSS pixels, rounded):

| Viewport | Before | After |
| --- | ---: | ---: |
| 1440 × 1000 | 837 | 837 |
| 960 × 1080 | 645 | 645 |
| 768 × 1024 | 453 | 654 |
| 720 × 1000 | 405 | 606 |
| 900 × 1440 | 585 | 585 |
| 390 × 844 | 110 | 276 |

The baseline already contained horizontal table overflow locally; that alone did not justify
cards. Rendered inspection also found five-column CSS applied to a six-column table.
After correction, stage markers wrap rather than intrude into neighboring cells.

Acceptance record:

- PASS: `make check` (Ruff, format, mypy; 764 tests in 2.06s), `make test-integration`
  (2 passed, 4 deselected in 0.24s), separate Ruff lint/format for the browser tool, and
  `git diff --check`. Checks used offline uv and disposable caches under the temporary root.
- PASS: keyboard focus/arrow scrolling and access to the queue's rightmost actions;
  mixed failed/skipped stage annotations remain independently visible. The failure is an
  explicitly synthetic queue annotation, not evidence of a real-provider run.

- PASS: all six viewports in existing system light/dark styles; no page overflow, off-page
  controls outside the local table, marker bleed across table cells, or feedback/button overlap.
- PASS: resize retains source identity, dirty text, selection range and independent batch selection.
- PASS: keyboard selection isolation, speaker reassignment, Preview, explicit verified Apply,
  source export, another source review, and a separate manual semantic review.
- PASS: workspace save, page reload and restoration from the exact saved catalog; canonical
  fixture hashes remain unchanged. This is not a GUI-process restart test.
- PASS: no browser JavaScript errors or attempted external frontend requests.
- Pending: actual Windows/WSL browser acceptance, actual browser zoom to 200%, GUI-process
  restart, and deployment-specific picker/dialog behavior. Resizing is not proof of browser zoom.
- Not run: real transcription, providers, YouTube upload, English audio, native Windows,
  bare-metal Ubuntu or Docker. Current YTT/color acceptance is retained unchanged.

## Repeating the optional browser check

Use an isolated Playwright environment and dedicated `mktemp -d` root. Run a separate disposable
`LocalGuiServer` using `WebConfiguration.create(port=8765)`, default `ApplicationConfig` with
its work root inside that temporary directory, and `XDG_STATE_HOME` there. Never point this
check at an operator's active GUI: it clears inactive queue state and writes test artifacts.
Keep the server running while executing, with the browser binaries outside the application env:

```bash
PLAYWRIGHT_BROWSERS_PATH="$gui_tmp/browsers" "$gui_tmp/browser-env/bin/python" \
  tools/check_gui_layout.py --url http://127.0.0.1:8765 --output "$gui_tmp/after"
```

`--baseline` captures measurements without imposing new geometry requirements or publishing a
revision. Run it against the base checkout for comparison. Each output directory must be new.
After recording content-free outcomes, stop the disposable server and remove the temporary root.
The regular quality gate remains `make check`; the optional browser tool has its own Ruff check.

## Owner acceptance in WSL and a Windows browser

1. Pull `main` through GitHub and record the delivered full `git rev-parse HEAD`, Windows/browser
   version, WSL distribution, launch command and URL. No new 24-episode transcription run is needed.
2. Use two completed canonical results with a dedicated temporary output root. Import both;
   inspect queue identity/status and batch selection independently of the open editor.
3. Check desktop, 960 × 1080 half-screen, 768/720px, 900 × 1440 portrait, and actual browser zoom
   through 200%. At about 390px check monitoring/simple actions. Scroll the table locally and
   reach rightmost actions by keyboard; check focus, status text and wrapped feedback.
4. Edit source text, isolate selected words, reassign a speaker, Preview, explicitly Apply and
   export. Source exports must remain usable before translation. Check the other file independently.
5. Open a separate semantic review, edit a target, and confirm its source remains unchanged.
6. Save work, stop/restart the GUI, select the saved catalog and restore. Confirm the queue,
   saved source/target drafts and prior immutable exports remain intact. Record PASS/FAIL and SHA.

GUI-55 is closed based on the owner's confirmation; no additional dedicated gate is required.
