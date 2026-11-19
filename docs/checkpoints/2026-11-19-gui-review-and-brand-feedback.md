# GUI review and brand feedback — 2026-11-19

Baseline: clean main ad49a48e384214d6a2e0d5a742129eafe5db2a33.
Read AGENTS.md, WORK_POLICY.md, TODO.md, WORK_STATUS.md and the roadmap before resuming.
Current implementation scope is the active TODO checklist. Owner-supplied /home/linuch/gear.svg
is the requested progress artwork; inspect and package original bytes with appropriate notices.
No provider calls, ASR, model downloads or canonical/ML changes are needed for these GUI fixes.

## Scope and sequencing

- Fix hint placement, two Polish labels, palette identity/default separation, language info,
  missing-verification feedback and all in-progress indicators.
- Preserve existing named custom profiles, saved work, historic colors and immutable exports.
- Audio playback plus real segment seeking is the next prioritized task before other deferred
  TODO work. Video ingestion and progress/ETA assessment are planned, not implemented in this slice.
- Keep the prior full Polish documentation task behind owner terminology approval.

## Progress

- Immediate scope implemented, VM-verified and delivered to origin/main in ef958dc83031900f2c9e82a7692ec8921f64812f.
- Audio, video and percentage/ETA items remain planned, with audio explicitly next.

## Implementation notes

- Path hint now sits immediately after input, before picker/list. Polish selection/review-ID
  labels updated. Accessible (i) language help records the reported EN-on-PL observation and
  explicitly requires review/correction; no translation mode or engine behavior was changed.
- Example default uses a distinct six-color example palette, first in the list. EwP Brand®
  keeps its original colors and stable brand ID. Legacy brand configuration names are accepted;
  explicit production settings remain selectable separately and saved-name collisions survive.
- Save actions now stop locally at missing human verification, outline the checkbox row and
  show an adjacent EN/PL message. Existing backend confirmation checks remain authoritative.
  Highlighting also reads the original source message rather than localized text.
- Owner gear.svg copied unchanged. Native circle animation removed; global, adjacent feedback,
  ongoing-status text and running queue/card indicators use the gear. Its exact inline SVG
  animation CSS is permitted with a fixed CSP hash, without enabling arbitrary inline styles.
- Planned video input is not currently enabled: InputConfig.supported_audio excludes MP4.
  Pipeline canonical stages record timings only after completion; live progress callbacks and
  measured stage/real-time-factor estimates are prerequisites for a meaningful percentage/ETA.
- Next audio task must bind a safe seekable media endpoint to actual canonical source identity,
  keep grouped-track choice explicit and seek to immutable start_ms / 1000. No fake audio/timing.

## Verification

- `UV_CACHE_DIR=/tmp/ewp-uv-cache make check`: Ruff, format, mypy (99 files), 834 tests PASS.
- `make test-integration`: five PASS, four deselected; browser tool Ruff PASS.
- Chromium 159 / Playwright 1.65.2: 144 layout cases PASS, six stages × six viewport widths ×
  EN/PL × light/dark. No page errors, external requests, page overflow, feedback overlap or
  transcript internal overflow. Existing cursor, draft, queue, dictionary, palette and export
  workflow checks remain passing. Queue start is intercepted; no ASR/provider calls are made.
- Focused checks PASS: hint placement, translated labels, first/default Example profile,
  distinct protected EwP Brand® and actual swatches, missing verification highlight/message in
  source and translation, cleared feedback after checking, fresh-server recovery and language
  popup bounds at 390/960px. Existing custom profile IDs and legacy aliases survive unchanged.
- Actual SVG ring transform changes with time; reduced-motion CSS stops the ring. Header,
  inline, inspection, correction, translation, doctor, dictionary/profile save and connection
  statuses use the gear. Completed/error feedback stays static. Final focused motion test PASS.
- Owner asset packaged byte-for-byte, SHA256
  `d8a890ff5f6c32407835ff8088c5c5f256e38c166dafdd27dc090bcc41f9c07a`.
  Exact inline SVG stylesheet CSP hash is
  `+ofmwl8C0LfVC0NWIY+m/gaSyXmSOBladdCFOJyIBis=`; no unsafe-inline/unsafe-eval added.
- Wheel and sdist builds PASS. All 51 frontend/guide resources match source; exact gear route
  and nine help routes work directly from the wheel without importing ML dependencies.
  Combined packaged JS syntax check PASS. No schema, lockfile, ML pin, version or tag changes.
- These checks do not establish new real WSL/GPU/provider, Windows zoom or YouTube behavior.
  The earlier owner-qualified local WSL transcription/source-export success remains valid.

## Delivery and resume

- Implementation delivered to origin/main in `ef958dc83031900f2c9e82a7692ec8921f64812f`; no release/tag created.
- Disposable verification root `/tmp/ewp-gui-brand.U1LSuG` removed after content-free evidence
  was recorded; local GUI server processes stopped.
- Owner retest after pull: restart `uv run --locked transcriber gui`, inspect path/language help,
  compare Example default / EwP Brand®, test Save before/after verification, and observe gear.
- Next implementation starts with the audio-player checklist in TODO.md. Do not enable video
  or percentage/ETA incidentally; implement source identity/seek safety and real progress evidence.
