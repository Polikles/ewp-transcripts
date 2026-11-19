"Build a portable file:// GUI review ZIP with synthetic data and no Python/ML runtime."

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import shutil
import struct
import subprocess
import tempfile
import wave
import zipfile
from pathlib import Path

from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.gui_library import GuiLibrary
from ewp_transcripts.web_guides import GUIDE_FILES, render_guide
from ewp_transcripts.web_reviews import GuiReviewController
from ewp_transcripts.web_server import WebConfiguration, dispatch_get
from ewp_transcripts.web_translation_reviews import GuiTranslationReviewController
from ewp_transcripts.web_workflows import GuiWorkflowController

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/ewp_transcripts/web_assets"
LUCIDE = ("book-open", "download", "file-music", "languages", "list-ordered", "settings-2", "split")


def asset(name: str) -> bytes:
    return dispatch_get(
        WebConfiguration.create(port=8765),
        server_port=8765,
        host="localhost:8765",
        target=f"/assets/{name}",
    ).body


def page(title: str, body: str) -> str:
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width"><title>'
        + html.escape(title)
        + '</title><link rel="stylesheet" href="review-docs.css">'
        + "<h1>"
        + html.escape(title)
        + "</h1>"
        + '<p><a href="index.html">Open clickable GUI</a> · '
        + '<a href="icon-inventory.html">Artwork and icon inventory</a></p>'
        + body
        + "</html>"
    )


def build(output: Path) -> None:
    if output.exists():
        raise ValueError("Choose a new ZIP filename; previous delivery is preserved")
    with tempfile.TemporaryDirectory(prefix="ewp-artist-build-") as temporary:
        temp = Path(temporary)
        package = temp / "ewp-gui-review"
        (package / "assets").mkdir(parents=True)
        shutil.copytree(ASSETS / "brand", package / "assets/brand")
        (package / "review-docs.css").write_text(
            "body{font:16px/1.5 system-ui;max-width:1000px;margin:2rem auto;padding:1rem}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.6rem}"
            "img{width:64px;height:64px;object-fit:contain}code{overflow-wrap:anywhere}"
        )
        (package / "assets/app.css").write_text(asset("app.css").decode().replace("/assets/", ""))
        javascript = asset("app.js").decode().replace("/assets/", "assets/")
        (package / "assets/app.js").write_text(javascript)
        shell = ASSETS.joinpath("index.html").read_text().replace("/assets/", "assets/")
        shell = shell.replace(
            '<script src="assets/app.js"',
            (
                '<script src="demo-data.js" defer></script><script src="demo-runti'
                'me.js" defer></script><script src="assets/app.js"'
            ),
        )
        (package / "index.html").write_text(shell)
        shutil.copyfile(ROOT / "tools/artist_review/demo-runtime.js", package / "demo-runtime.js")
        shutil.copyfile(ROOT / "LICENSE", package / "LICENSE.txt")
        source_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        (package / "SOURCE-COMMIT.txt").write_text(source_commit + "\n")
        config = ApplicationConfig()
        paths = GuiWorkflowController()
        base = temp / "DEMO01_results.json"
        document = json.loads((ROOT / "examples/results.example.json").read_text())
        document["job_id"] = document["episode"]["episode_id"] = "DEMO01"
        base.write_text(json.dumps(document))
        reviews = GuiReviewController(config=config, resolve_path=paths.resolve_allowed_path)
        review = reviews.prepare(str(base), str(temp / "reviews"))
        for index, block in enumerate(review["anchors"][0]["blocks"]):
            block["text"] = (
                (
                    "This is a fictional recording for visual interface review. Check "
                    "the speaker names, colors, spacing and editing controls. "
                )
                if index == 0
                else (
                    "The guest responds in this synthetic example. These words illustr"
                    "ate a transcript paragraph and do not come from any private recor"
                    "ding. "
                )
            ) * 2
        review["playback_sources"] = [
            {
                "source_id": "source_001",
                "filename": "demo-host.wav",
                "speaker_label": "Host",
                "channel_selection": "mono",
            },
            {
                "source_id": "source_002",
                "filename": "demo-guest.wav",
                "speaker_label": "Guest",
                "channel_selection": "mono",
            },
        ]
        review["anchors"][0]["block_sources"] = [["demo-host.wav"], ["demo-guest.wav"]]
        review["speaker_labels"] = {"speaker_001": "Host", "speaker_002": "Guest"}
        translation = GuiTranslationReviewController(
            config=config, resolve_path=paths.resolve_allowed_path
        ).prepare(
            result=str(base),
            revision="",
            parent="",
            output=str(temp / "translations"),
            target_language="pl",
        )
        for unit in translation["units"]:
            unit["target_text"] = "Przykładowe tłumaczenie do wizualnego przeglądu interfejsu."
        profiles = GuiLibrary(
            state_directory=temp / "library",
            resolve_path=paths.resolve_allowed_path,
            subtitles=config.subtitles,
        ).profiles()
        data = {
            "review": review,
            "translation": translation,
            "profiles": profiles,
            "guides": json.loads((ASSETS / "guides/index.json").read_text()),
        }
        text = json.dumps(data, ensure_ascii=False).replace(str(temp), "/demo")
        (package / "demo-data.js").write_text("window.EWP_ARTIST_DATA = " + text + ";\n")
        with wave.open(str(package / "demo-audio.wav"), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            frames = [
                int(1600 * math.sin(2 * math.pi * (440 if n < 64000 else 660) * n / 16000))
                for n in range(128000)
            ]
            audio.writeframes(struct.pack(f"<{len(frames)}h", *frames))
        guides = package / "guides"
        guides.mkdir()
        for slug in GUIDE_FILES:
            rendered = render_guide(slug)
            assert rendered is not None
            (guides / f"{slug}.html").write_text(
                rendered.decode()
                .replace("/assets/", "../assets/")
                .replace('href="/"', 'href="../index.html"')
            )
        (guides / "index.html").write_text(
            page(
                "GUI guides",
                "<ul>"
                + "".join(f'<li><a href="{slug}.html">{slug}</a></li>' for slug in GUIDE_FILES)
                + "</ul>",
            )
            .replace('href="index.html"', 'href="../index.html"')
            .replace('href="icon-inventory.html"', 'href="../icon-inventory.html"')
            .replace('href="review-docs.css"', 'href="../review-docs.css"')
        )
        inventory = [
            {
                "asset": "logo.svg",
                "origin": "Custom EwP identity",
                "usage": "Header logo",
                "replacement": "Preserve EwP identity; owner approval for replacement",
            },
            {
                "asset": "gear.svg",
                "origin": "Owner-supplied custom animated SVG",
                "usage": "Every in-progress status/request/queue marker",
                "replacement": "Stationary center, moving ring; include reduced-motion treatment",
            },
            {
                "asset": "web-pattern-light.svg",
                "origin": "Custom EwP identity",
                "usage": "Light-theme background",
                "replacement": "Tileable pattern with sufficient contrast",
            },
            {
                "asset": "web-pattern-dark.svg",
                "origin": "Custom EwP identity",
                "usage": "Dark-theme background",
                "replacement": "Tileable dark-theme counterpart",
            },
        ]
        uses = {
            "file-music": "Transcribe",
            "list-ordered": "Optional correction",
            "book-open": "Source review / Dictionaries",
            "languages": "Optional translation",
            "download": "Translation review / export",
            "settings-2": "Settings / Saved work",
            "split": "Included handoff asset; reserved, not currently rendered",
        }
        inventory.extend(
            {
                "asset": f"{name}.svg",
                "origin": "Lucide 1.71.0, ISC license",
                "usage": uses[name],
                "replacement": "Provide matching custom SVG, 20×20 viewBox; dark/light contrast",
            }
            for name in LUCIDE
        )
        inventory.extend(
            [
                {
                    "asset": "CSS / Unicode",
                    "origin": "Generic shapes and text glyphs",
                    "usage": (
                        "Workflow circles, ✓ completed, × error, pending/skipped outlines;"
                        " selection arrows; numbered stage badges; speaker color dots; con"
                        "nection lights; (i) help"
                    ),
                    "replacement": "Map each semantic state; retain text/aria equivalents "
                    "and readable small sizes",
                },
                {
                    "asset": "Browser controls",
                    "origin": "Browser / OS native",
                    "usage": (
                        "Audio play/pause/volume/seek/menu, checkboxes, select arrows, num"
                        "ber steppers, file/folder dialogs, native progress bars"
                    ),
                    "replacement": (
                        "Not SVG assets; custom replacements require implementation and ke"
                        "yboard/accessibility behavior"
                    ),
                },
                {
                    "asset": "montserrat.woff2 / mono.woff2",
                    "origin": "Montserrat / Noto Sans Mono, OFL",
                    "usage": "Interface / technical text",
                    "replacement": "Fonts, not icons; licenses included",
                },
            ]
        )
        (package / "icon-inventory.json").write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
        )

        def inventory_row(item: dict[str, str]) -> str:
            image = ""
            if item["asset"].endswith(".svg"):
                image = f'<img src="assets/brand/{html.escape(item["asset"])}" alt=""><br>'
            cells = [image + html.escape(item["asset"])]
            cells.extend(html.escape(item[key]) for key in ("origin", "usage", "replacement"))
            return "<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"

        rows = "".join(inventory_row(item) for item in inventory)
        gallery = page(
            "Artwork, icons and indicators",
            (
                "<p>This is a private visual review reference for the owner and ar"
                "tist. Identity assets retain their existing restrictions; inclusi"
                "on grants no new public redistribution license.</p><table><tr><th"
                ">Asset / preview</th><th>Origin</th><th>Where used</th><th>Replac"
                "ement notes</th></tr>"
            )
            + rows
            + (
                "</table><p>Custom artwork credit: Cyryl; rights holder: Damian Sz"
                "częch / Etyka w Pętli. Gear supplied by the owner; no additional "
                "artist credit was invented. See assets/brand/NOTICE.txt and LICEN"
                "SE-ASSETS.txt. Lucide ISC and both OFL font notices are bundled.<"
                "/p><p>Suggested delivery: named SVG files, matching viewBox sizes"
                ", light/dark variants where needed, state variants (pending/runni"
                "ng/completed/failed/skipped/disabled/hover), animated and reduced"
                "-motion gear variants, attribution/licensing file and a contact s"
                "heet. Do not rely on color alone.</p>"
            ),
        )
        (package / "icon-inventory.html").write_text(gallery)
        readme = """# EwP GUI artist review package

Unzip the complete folder, then double-click index.html in Chrome or Edge. No installation,
Python, transcription backend, account, API key or network connection is needed. Keep assets
beside index.html. Reset demo restores the sample state. Choose EN/PL and light/dark in the header.

This is the current frontend with an in-memory demo adapter. It is a visual review reference,
not a transcription tool: all recordings/text/jobs/progress/provider responses are synthetic.
File selection does not transcribe or upload media; entered API keys are ignored and never sent
or stored. Exports and dictionary/workspace edits are simulated in this tab; reload resets them.
The demo audio is an explicitly synthetic test tone. Browser-native controls vary by OS/browser.

Try the queue, all five workflow stages, source and translation editors, split/undo/draft controls,
speaker names/colors, palette preview/apply/save, dictionaries, saved work, settings and dialogs.
The demo toolbar offers queue state presets for running/failed/completed visual states. Read
icon-inventory.html for custom / Lucide / generic / native elements and replacement guidance.
Review at full and half desktop widths in both themes. Short instructions and bundled guides work.

Software: AGPL-3.0-only (LICENSE.txt). Frontend source is assets/app.js, assets/app.css,
demo-runtime.js and demo-data.js. Original repository: https://github.com/Polikles/ewp-transcripts.
Identity artwork remains restricted under assets/brand/LICENSE-ASSETS.txt; artist review is
owner-authorized. Included third-party icon/font notices remain applicable. This package is not
a release of the transcription application and contains no models, private transcripts or media.
"""
        (package / "README.md").write_text(readme)
        (package / "README.html").write_text(
            page(
                "Artist review — start here",
                "<pre style='white-space:pre-wrap'>" + html.escape(readme) + "</pre>",
            )
        )
        manifest = {
            str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in package.rglob("*")
            if path.is_file()
        }
        (package / "manifest-sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(package.rglob("*")):
                if path.is_file():
                    archive.write(path, Path("ewp-gui-review") / path.relative_to(package))
    print(f"Artist review ZIP: {output}")
    print(f"SHA256: {hashlib.sha256(output.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output.resolve())
