# Mixed playback, review sections, live progress and artist package — 2026-11-19

Baseline: clean main 5e025b42169455b545bdd50b88c8e6021f57d60c.
Read AGENTS.md, WORK_POLICY.md, TODO.md, WORK_STATUS.md and the roadmap after context reset.

## Scope

Outside-click/Escape language info dismissal; combined synchronized source playback and original
filename hints; bounded long-speaker review sections; evidence-based approximate progress/ETA;
then an offline clickable artist package with synthetic data and full artwork/icon inventory.
Keep original media/transcripts private, canonical timing/lineage immutable and ML pins unchanged.
Owner supplied /home/linuch/HD06 AI in Cybersecurity.mp4 as a private diagnostic reference.
Owner confirms its transcription completed. No provider call or implicit model download allowed.

## Findings

- Current player chooses one isolated source; this causes silence on other speakers' tracks.
- review_service._anchor_ranges uses speaker changes alone when speaker-block mode is enabled;
  target_words is then ignored, so one long speaker becomes one huge review anchor/block.
- Runtime only exposes running/completed, with completed-stage timings retained retrospectively.
- Owner-supplied logs need interpretation against installed dependency sources before conclusions.

## Implementation

- Default source_id=mix verifies the canonical sources, prepares their selected streams/channels
  in an owned workdir, and mixes at shared time zero. No concatenation or invented offset; longest
  timeline retained and summed gain normalized. Existing individual-source API remains compatible.
- Small file hints below Speaker use original canonical word references and speaker/source IDs,
  not edited display names. Ambiguous/legacy regions conservatively list their section sources.
- New anchors honor word/speaker limits. Old unchanged drafts are projected into bounded anchors,
  preserving speaker edits; edited legacy blocks are bounded while retaining original anchors.
  Projection validates base/coverage and changes saved draft bytes only on explicit Save.
  Unchanged-word alignment has a deterministic direct fast path; large legacy playback uses
  conservative exact references instead of dense quadratic alignment. Canonical timing is unchanged.
- Language help closes on outside pointer and Escape; Escape restores icon focus.
- Observer events cover actual application/pipeline phases, per-stream counters and completion.
  Monotonic snapshots provide elapsed heartbeat. First-run percentages use explicit coarse weights;
  matching successful local measurements enable ETA ranges with overdue/unknown fallbacks.
  Observer/cache failures are isolated, failed work remains below 100%, and true completion follows
  the returned service outcome after publication/exports/cleanup. No inference adapter/pin change.
- Artist reference uses the actual bundled frontend, synthetic data/audio and an in-memory mock.
  No transcription backend, model, private transcript/media or provider call. Gallery/JSON inventory
  separates custom EwP, Lucide ISC, generic/CSS/Unicode, browser/OS controls and OFL fonts.

## Verification

- make check: Ruff/format/mypy (101 files), 874 tests PASS. All three optional browser/build tools
  pass explicit Ruff checks. make test-integration: ten PASS, four deselected.
- Real alternating synthetic tracks: mixed WAV retains both speakers at 2s/5s, exact 8s duration,
  correct file hints and unchanged originals. Missing/hash-changed sources remain controlled errors.
- 501-word/one-segment/one-speaker fixture: 200/200/101 review sections, valid base coverage,
  unchanged canonical data, legacy read-only projection, explicit saved structure and original
  filename provenance after speaker reassignment. Large edited/empty playback uses real times.
- Fake-clock/history/queue tests: real event boundaries, elapsed heartbeat, calibrated/unknown ETA,
  slow-phase withdrawal, monotonic percent, failed/incomplete exclusion and terminal completion.
  Real FFmpeg/fake-engine video pipeline proves event order and observer-failure isolation.
- Chromium 159 / Playwright 1.65.2: 144 layout cases PASS (EN/PL, two themes, six stages/viewports),
  no page errors/external requests/overflow/feedback overlap/transcript internal scrolling.
  Outside click/Escape, source mix/seek, per-recording state, source hints, narrow progress/ETA,
  cursor/save/scroll preservation and source/manual translation export/recovery PASS.
  Final fresh-server recovery/mix/source-hint position test PASS. Queue starts are intercepted.
- Owner reference: H.264 + AAC stereo 44100 Hz, 2742.555 s, 153756479 bytes; full audio decode
  to mono PCM 16000 Hz PASS, duration preserved within 100ms, original SHA unchanged. No ASR run
  or transcript content was generated from that private reference. Outputs stayed in mktemp.
- Wheel/sdist build PASS: 53 frontend/guide files byte-match source, all nine help routes work
  directly from wheel without importing torch/torchcodec/whisperx/pyannote. Bundled JS parses.
- Artist ZIP test: file://, no server/network. All stages, synthetic audio seek, source/translation
  editor/save/apply/export, palettes, demo correction, dictionaries, saved work, settings, running
  states, EN/PL/themes/960px/1920px and 14 inventory entries PASS; no page errors/external calls.
- This VM lacks the target GPU, installed GPU/E2E suite and external dataset. These checks do not
  qualify real ASR/ETA accuracy on WSL/RTX 3090, Windows zoom or YouTube output. Earlier owner
  MP4/local workflow success stays qualified. No version, release tag or ML pin changed.

## Terminal messages

Pinned primary sources are linked in docs/32-runtime-log-notes.md. Transformers 4.57.6 creates
masked_spec_embed for training augmentation; its normal pretrained loading sets evaluation mode,
and WhisperX 3.8.6 alignment does not pass training masks. The exact reported parameter warning
therefore does not require user training in this workflow. ONNX Runtime 1.28.0 logs DRM sysfs
probe failure as a warning and continues; this line alone does not establish PyTorch CUDA failure.
VAD INFO is informational. No generic missing-weight/runtime warning filters were installed.

## Delivery and resume

- Implementation delivered to origin/main in `831dca4ee7a294eab1618f7df8788e2464b81ada`;
  final positive-ETA refinement in `6610e299e4890771dca589ebd70819b5d6d6f95f`.
- Artist ZIP: `/home/linuch/project-ewp/deliveries/ewp-gui-artist-review-2026-11-19.zip`; 1135816 bytes.
  SHA256 `1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1`.
  Its frontend bytes match the current frontend; the later refinement is backend-only.
- Disposable root /tmp/ewp-review-progress.BWiy2Q removed after final ZIP verification and
  content-free evidence capture. Browser/server processes stopped; owner original unchanged.
- Owner retest: pull/restart GUI; dismiss (i) outside/Escape; seek host/guest sections in a grouped
  episode with the default mix; inspect file hints; reopen one-speaker MP4 review; observe phase,
  elapsed and approximate percent. First completed comparable jobs calibrate ETA; slow phases
  withdraw ETA. Existing saved/applied sources and exports remain immutable.
- Artist: unzip complete archive and open index.html in Chrome/Edge; inspect icon-inventory.html
  and JSON. New custom icon integration waits for the artist's assets, not more generated artwork.

## Final artist artifact

The exact retained ZIP passed tools/check_artist_review.py from file:// with no server/network:
manifest verification, source/translation editing/save/apply/export, palette preview/apply/save,
mock correction, dictionary editing, saved work, dependency-demo states, all workflow stages,
EN/PL light/dark at 960/1920px and the 14-entry inventory. No page errors/external requests.
43 archive files; only the explicitly synthetic demo-audio.wav, no Python backend or model files.
SOURCE-COMMIT.txt is verified against the frontend source commit; transformed app.js/app.css
and the mock adapter match the current frontend/tool bytes. No package was sent to the artist
or published externally. Owner download/artist feedback and real WSL ETA accuracy remain pending.
