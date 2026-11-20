# Batch planning, sentence-aware review and portable user profiles

Date: 2026-11-20. Baseline: clean main aa70f4d00c74cd23740dcace55c597d58fa707ac.

## Scope and acceptance

See the complete active checklist in ../../../TODO.md. The owner confirms mixed playback,
MP4 ASR and progress work. Current defects: Inspect batches but planning/staging only selects
one episode; metadata summary omissions/English counts; mid-sentence review boundaries;
browser-native speed controls missing for mixed audio. Requested additions: optional calibrated
ETA, second-by-second elapsed rendering, portable single-file user profiles and independent
dictionary exchange, framed credit/favicon, review guidance/action alignment.

## Boundaries

English repository, bilingual GUI. Preserve canonical schemas/timing, qualified inference/pins,
immutable dictionaries/artifacts and exact dry-run confirmation. Profiles must exclude API keys,
media, transcripts and in-flight state; workspace manifests reference external paths and cannot
make unavailable media portable. No release/tag/version bump. Disposable tests under dedicated
/tmp directory. Owner steering: the artist ZIP has already been sent for review. Do not alter or rebuild it; all current work concerns the application.

## Evidence and resume

Repository policies, TODO, WORK_STATUS, roadmap and GUI contract read; baseline clean.
Next: inspect workflow batch handling, review preparation and persisted state boundaries,
then implement and verify vertical slices. No new work qualified yet.

## Implementation checkpoint

- Batch controls now share one full pending episode list, preserve per-episode language/count,
  and require an unchanged reviewed request snapshot. Every staged item still passes existing
  server plan/hash/confirmation checks. Inspect fallback values are starred and localized.
- Review preparation chooses a nearby conservative EN/PL sentence end rather than a strict word
  cutoff; speaker attribution/timing stay original. Bounded unpunctuated fallback is disclosed.
  Edited legacy anchors are retained; unchanged legacy text can be repartitioned without writes.
- Explicit speed select applies to mixed/single media. Artwork credit framed; favicon original
  vector on framed light tile. Three block actions fit one row, guidance/warning localized.
- ETA off by default; at least 3 successful comparable complete runs, independent of track count,
  are required. Browser elapsed refreshes locally at 1 second with bounded poll interpolation.
- Single JSON profile API/UI and independent immutable dictionary import/export implemented.
  Profiles include current fields, default/selected workspace catalogs, selected/referenced
  dictionaries and custom palettes. No queue execution or automatic editor replacement on import.
  Missing path references remain visible/unavailable rather than silently dropped. Dictionary
  bytes (including CRLF), hashes, provenance and visibility survive transfer.
- Initial Ruff/mypy pass, full 888-test run passes. Focused profile transfer, invalid-input/no-write,
  dictionary collision, missing media, profile idempotency and CSRF tests pass.
- Browser check found only test expectations needing adjustment for batch planning and default
  automatic speaker mode so far; profile export/import and dictionary byte round-trip already pass.

Next: finish fresh browser workflows/layout, add calibration/elapsed regression assertions, run
final required gates/integration/package checks, update guides/contracts/changelog and deliver.
Artist ZIP remains unchanged at the owner's explicit instruction; no artist tools or package
rebuild are part of this work.

## Final verification

- Final application gate: make check PASS (896 tests, Ruff/format, mypy 102 source files).
  make test-integration PASS (10 passed, 4 deselected). No inference/model changes or downloads.
- Browser Chromium 159.0.8154.6 / Playwright 1.65.2: 144 layout cases in EN/PL × light/dark ×
  six widths × six stages; no page errors/external requests, page/textarea overflow or feedback
  overlap. Normal desktop queues stay within the viewport; mobile queues retain local scrolling.
- Synthetic two synchronized WAV tracks + MP4 are inspected/planned/staged as two episodes with
  PL/2 and EN/1 settings. Changing count after planning rejects staging until replanned. Both jobs
  appear after one Add action. Completed/staged guards and existing start/recovery/export flows pass.
- Profile save/export/import/load and independent dictionary transfer pass in the real browser.
  Unit tests verify CRLF byte/hash equality, immutable IDs, malformed profile/no-write rejection,
  unavailable paths, idempotency, credential/consent exclusion, CSRF and palette collision isolation.
- ETA requires 3 successful jobs, not 3 tracks; first/unknown/overdue/failure behavior remains tested.
  Elapsed reaches the next second between server polls. ETA hidden by default, opt-in UI persists.
- Sentence-aware review: 581 canonical words form 210/220/151 word sections at actual sentence
  ends; unpunctuated fallback displays the red note above the first section. Both themes/locales
  pass; advisory and all three block actions are visible and correctly aligned. Explicit manual
  same-speaker splits survive Save; parent-revision anchors remain protected. Canonical files unchanged.
- Fresh process/browser restores the saved source/manual translation and export state successfully.
- GUI evidence under /tmp/ewp-batch-profiles.jCbW8c/fifth (complete browser) and recovered-final
  (fresh-server recovery and sentence guidance). Fixtures/logs/screenshots were removed at handoff after this content-free evidence capture.

## Delivery and resume

Implementation delivered to origin/main in 7cfddb4 (func(gui): add portable profiles and refine
batch review). All authorized application work and verification are complete. No app version,
release or tag was changed. The dedicated temporary root /tmp/ewp-batch-profiles.jCbW8c, including
synthetic recordings, private browser state, wheels, test exports, reports and browser binaries,
was removed after recording the evidence above. Test servers were closed.

Owner retest: git pull, then uv run --locked transcriber gui. Check the complete mixed selection
through Inspect / Dry-run / Add once, per-episode settings, sentence-aware presentation, mixed
playback speed and Settings & About profile/ETA controls. Profile transfer includes settings and
workspace references; media/results move separately. Real GPU/ETA accuracy and full Polish manuals
remain owner-dependent follow-ups. The already sent artist package stays out of scope until new
owner instructions; no further package work is queued for this task.

Package gate: wheel and sdist build PASS. All 56 packaged resource files byte-match the source;
nine help routes render from the extracted wheel and no torch/torchcodec/WhisperX/pyannote import
is initialized. New favicon is registered and served as SVG with no inline style dependency.
The supplied original logo and gear remain unchanged. Framing is recorded in the asset notice.
Artist ZIP SHA256 remains 1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1.
No artist package files, demo adapter or builder were modified; the ZIP was only hash-checked.
