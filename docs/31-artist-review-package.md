# Frontend-only artist review package

The owner requested this package for the artist who supplied the interface artwork.
It is a private visual reference, not a transcription application release.

Unzip the complete package and open `ewp-gui-review/index.html` in Chrome or Edge. No Python,
server, transcription runtime, account, API key, model or network connection is required. Keep
`assets/`, `demo-data.js`, `demo-runtime.js` and the other bundled files beside the entry page.
Use EN/PL and light/dark choices in the header. The yellow demo toolbar offers synthetic
running/failed/completed states and Reset demo. The toolbar is not part of production UI.

The package uses the actual bundled frontend and an in-memory adapter. Queue actions, stage
navigation, source and translation editors, speaker colors, palettes, dictionary management,
saved work, settings and dialogs are available for visual review. Save/export/provider/diagnostic
responses are simulated, not evidence that transcription or dependencies work. The audio is a
synthetic test tone; no private recording or transcript is included. Picked files are not uploaded
or processed. API keys are ignored, never sent or retained. Demo edits reset on page reload.

Open `icon-inventory.html` for previews and `icon-inventory.json` for the machine-readable list:

- Custom: EwP logo, animated gear and light/dark background patterns.
- Third-party: seven Lucide 1.71.0 SVGs, with each file and interface use listed. The unused split
  SVG is identified as a reserved handoff asset, not falsely claimed to be a visible control.
- Generic/CSS/text: workflow pending/complete/error/skipped states, status glyphs, selection
  markers, numbered stages, speaker dots, connection lights and language-information indicator.
- Browser/OS native: audio play/pause/volume/seek/menu, selects, checkboxes, number steppers,
  progress bars and file dialogs. Replacing these also requires behavior/accessibility code.
- Fonts: Montserrat and Noto Sans Mono, separately identified and licensed under OFL.

The artist should provide named SVG files, suitable viewBox sizes, light/dark and semantic-state
variants, animated and reduced-motion gear behavior, a contact sheet and attribution/license
notes. Preserve readable small sizes, keyboard/focus semantics and a text equivalent for every
state. Custom assets will be integrated as a separate task when supplied.

Code is AGPL-3.0-only. Identity artwork retains `assets/brand/LICENSE-ASSETS.txt` restrictions;
no new public redistribution license is granted. Original credits and Lucide ISC/font OFL notices
are included. The owner authorized sharing this reference with the artist; it is not published.

## Rebuild

From the repository's locked development environment:

```bash
uv run --locked python tools/build_artist_review.py --output /new/path/ewp-gui-artist-review.zip
```

The builder refuses an existing ZIP path, uses a dedicated temporary directory for intermediate
synthetic reviews, and includes a SHA-256 manifest. The recipient only needs the resulting ZIP.
The checked-in adapter lives in `tools/artist_review/demo-runtime.js`; it is never bundled into
the real application. Production `fetch`, authentication, file handling and provider calls are
unchanged by this package.

The optional Playwright check is `tools/check_artist_review.py --package /unpacked/ewp-gui-review
--output /dedicated/mktemp/check`. It verifies the manifest and offline interactions while blocking
HTTP(S). `SOURCE-COMMIT.txt` identifies the checkout used to create the package; the ZIP SHA is
recorded in the delivery checkpoint. This package does not send artwork or messages to the artist.
