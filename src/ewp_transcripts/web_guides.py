"""Fixed, bilingual workflow documentation for offline GUI help."""

from __future__ import annotations

import html
import re
from importlib.resources import files
from urllib.parse import quote, urlsplit

GUIDE_FILES = {
    slug: f"{slug}.md"
    for slug in (
        "index",
        "installation",
        "transcribe",
        "optional-correction",
        "source-review",
        "optional-translation",
        "translation-review",
        "dictionaries",
        "saved-work",
        "settings",
        "outputs",
        "troubleshooting",
        "cli",
        "ubuntu-upgrade",
        "windows-native",
    )
}


def _source(slug: str, locale: str) -> str:
    directory = files("ewp_transcripts.web_assets").joinpath("guides")
    if locale == "pl":
        directory = directory.joinpath("pl")
    return directory.joinpath(GUIDE_FILES[slug]).read_text(encoding="utf-8")


def _link(target: str, locale: str) -> str | None:
    """Map known manual links; reject active schemes and arbitrary local paths."""

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return target if parsed.scheme == "https" and parsed.netloc else None
    if target.startswith("#"):
        return target
    if target.endswith("Instructions/README.md"):
        return "https://github.com/Polikles/ewp-transcripts/blob/main/Instructions/README.md"
    name = parsed.path
    if "/" in name:
        return None
    slug = "index" if name == "README.md" else name.removesuffix(".md")
    if slug not in GUIDE_FILES:
        return None
    fragment = f"#{quote(parsed.fragment)}" if parsed.fragment else ""
    return f"/help/{slug}?lang={locale}{fragment}"


def _inline(text: str, locale: str) -> str:
    output: list[str] = []
    end = 0
    # Interpret only a small, escaped subset. Raw HTML is always text, never markup.
    pattern = r"`([^`]+)`|\[([^\]]+)\]\(([^\s)]+)\)|\*\*([^*]+)\*\*"
    for match in re.finditer(pattern, text):
        output.append(html.escape(text[end : match.start()]))
        code, label, target, strong = match.groups()
        if code is not None:
            output.append(f"<code>{html.escape(code)}</code>")
        elif strong is not None:
            output.append(f"<strong>{html.escape(strong)}</strong>")
        else:
            href = _link(target, locale)
            escaped_label = html.escape(label)
            output.append(
                f'<a href="{html.escape(href, quote=True)}" rel="noreferrer">{escaped_label}</a>'
                if href
                else escaped_label
            )
        end = match.end()
    output.append(html.escape(text[end:]))
    return "".join(output)


def _markdown(source: str, locale: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    code_open = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{_inline(' '.join(paragraph), locale)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            output.append(f"</{list_kind}>")
            list_kind = None

    for line in source.splitlines():
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            output.append("</code></pre>" if code_open else "<pre><code>")
            code_open = not code_open
            continue
        if code_open:
            output.append(html.escape(line) + "\n")
            continue
        numbered = re.match(r"^\d+\. (.+)$", line)
        bullet = re.match(r"^- (.+)$", line)
        if numbered or bullet:
            flush_paragraph()
            kind = "ol" if numbered else "ul"
            if list_kind != kind:
                close_list()
                output.append(f"<{kind}>")
                list_kind = kind
            item = numbered or bullet
            assert item is not None
            output.append(f"<li>{_inline(item[1], locale)}</li>")
            continue
        close_list()
        heading = re.match(r"^(#{1,3}) (.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading[1])
            identifier = re.sub(r"[^\w -]", "", heading[2].lower()).replace(" ", "-")
            # Preserve the h1 shape used by the original fixed-help contract.
            attr = f' id="{html.escape(identifier)}"' if level > 1 else ""
            output.append(f"<h{level}{attr}>{_inline(heading[2], locale)}</h{level}>")
        elif line.strip():
            paragraph.append(line.strip())
        else:
            flush_paragraph()
    flush_paragraph()
    close_list()
    if code_open:
        output.append("</code></pre>")
    return "\n".join(output)


def render_guide(slug: str, *, locale: str = "en") -> bytes | None:
    """Render an allowlisted EN/PL resource, never a requested filesystem path."""

    if slug not in GUIDE_FILES:
        return None
    locale = "pl" if locale == "pl" else "en"
    source = _source(slug, locale)
    title = source.splitlines()[0].removeprefix("# ")
    open_label = "Otwórz EwP Transcripts" if locale == "pl" else "Open EwP Transcripts"
    return_label = (
        "Zamknij tę kartę aby powrócić do swojej pracy."
        if locale == "pl"
        else "Close this tab to return to your existing work."
    )
    navigation = "Instrukcje pracy z programem" if locale == "pl" else "Workflow instructions"
    other = "Inne instrukcje" if locale == "pl" else "Other workflow guides"
    output = [
        f'<!doctype html><html lang="{locale}"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(title)} · EwP Transcripts</title>",
        '<link rel="stylesheet" href="/assets/app.css">',
        "</head>",
        '<body class="gui-guide"><main>',
        f'<p><a href="/">{open_label}</a> · {return_label}</p>',
        f'<p class="guide-languages"><a href="/help/{slug}?lang=en" lang="en">English</a> · '
        f'<a href="/help/{slug}?lang=pl" lang="pl">Polski</a></p>',
        _markdown(source, locale),
        f'<nav aria-label="{navigation}"><h2>{other}</h2><ul>',
    ]
    for name in GUIDE_FILES:
        label = _source(name, locale).splitlines()[0].removeprefix("# ")
        output.append(f'<li><a href="/help/{name}?lang={locale}">{html.escape(label)}</a></li>')
    output.append("</ul></nav></main></body></html>")
    return "\n".join(output).encode()
