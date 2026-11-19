# Artist GUI review package — 2026-11-19

Related implementation: [mix/review/progress checkpoint](2026-11-19-review-mix-progress-artist.md).
Frontend source: `831dca4ee7a294eab1618f7df8788e2464b81ada`. Local-only delivery; no app release/tag.

## Retained artifact

- ZIP: `/home/linuch/project-ewp/deliveries/ewp-gui-artist-review-2026-11-19.zip`
- Size: 1135816 bytes; 43 files below ewp-gui-review/.
- SHA256: `1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1`
- Recipient: unzip the complete folder, double-click index.html in Chrome/Edge. No server,
  installation, API key or transcription runtime. README.md/README.html explain synthetic behavior.
- icon-inventory.html: previews, provenance, usage and replacement guidance. JSON inventory has
  14 entries: custom EwP identity/gear/patterns, seven Lucide assets, generic/CSS/Unicode states,
  native browser/OS controls, and fonts. Credits/identity terms/ISC/OFL/software license included.
- Only synthetic text/tone audio. No supplied MP4, private transcript, credentials, model or backend.

## Evidence

The exact ZIP manifest and source commit were verified. Current bundled frontend bytes (after
relative-URL rewriting) and mock adapter match the archive. Playwright/Chromium file:// test PASS,
HTTP(S) blocked and no server: all stages, mixed-source demo seek, source/translation editor,
save/apply/export simulations, palettes, correction demo, dictionaries, saved work, settings,
running/failed/completed controls, EN/PL/themes/full/half widths and inventory. No page errors or
external requests. Native controls remain browser-specific; Windows/artist visual approval is pending.

Builder: tools/build_artist_review.py. Optional verifier: tools/check_artist_review.py.
Development intermediates used mktemp and were removed. This ZIP is an explicitly requested
handoff artifact and remains under project-ewp/deliveries, outside Git. No message/artifact was sent
to the artist. Next work: owner downloads it; artist supplies replacement SVG/state/animation assets,
then integrate them without changing workflow semantics. Full Polish documentation follows the
existing terminology-approval gate.
