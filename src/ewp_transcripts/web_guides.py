"""Fixed, packaged workflow documentation for offline GUI help."""

from __future__ import annotations

import html
import re
from importlib.resources import files

GUIDE_FILES = {
    slug: f"{slug}.md"
    for slug in (
        "transcribe",
        "optional-correction",
        "source-review",
        "optional-translation",
        "translation-review",
        "dictionaries",
        "saved-work",
        "settings",
        "ubuntu-upgrade",
        "windows-native",
    )
}


def _inline(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(text))


def render_guide(slug: str) -> bytes | None:
    """Render only allowlisted bundled guides; never resolve a requested filesystem path."""

    filename = GUIDE_FILES.get(slug)
    if filename is None:
        return None
    source = files("ewp_transcripts.web_assets").joinpath("guides", filename).read_text()
    title = source.splitlines()[0].removeprefix("# ")
    output = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(title)} · EwP Transcripts instructions</title>",
        '<link rel="stylesheet" href="/assets/app.css"></head><body class="gui-guide">',
        '<main><p><a href="/">Open EwP Transcripts</a> · '
        "Close this tab to return to your existing work.</p>",
    ]
    list_open = False
    code_open = False
    for line in source.splitlines():
        if line.startswith("```"):
            if list_open:
                output.append("</ol>")
                list_open = False
            output.append("</code></pre>" if code_open else "<pre><code>")
            code_open = not code_open
            continue
        if code_open:
            output.append(html.escape(line) + "\n")
            continue
        numbered = re.match(r"^\d+\. (.+)$", line)
        if numbered:
            if not list_open:
                output.append("<ol>")
                list_open = True
            output.append(f"<li>{_inline(numbered[1])}</li>")
            continue
        if list_open:
            output.append("</ol>")
            list_open = False
        heading = re.match(r"^(#{1,3}) (.+)$", line)
        if heading:
            level = len(heading[1])
            output.append(f"<h{level}>{_inline(heading[2])}</h{level}>")
        elif line:
            output.append(f"<p>{_inline(line)}</p>")
    if list_open:
        output.append("</ol>")
    if code_open:
        output.append("</code></pre>")
    output.append('<nav aria-label="Workflow instructions"><h2>Other workflow guides</h2><ul>')
    for name in GUIDE_FILES:
        output.append(
            f'<li><a href="/help/{name}">{html.escape(name.replace("-", " ").title())}</a></li>'
        )
    output.append("</ul></nav></main></body></html>")
    return "\n".join(output).encode()
