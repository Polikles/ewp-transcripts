# Playback, video ingestion and progress analysis — 2026-11-19

Baseline: clean main e08a4102ee0d9e0dbe0457b3dc96e58185e13552.
Read AGENTS.md, WORK_POLICY.md, TODO.md, WORK_STATUS.md and the roadmap on resume.

## Scope and acceptance

1. Compact source-review audio player in the left rail; real segment-start seek buttons below
   speaker controls. Exact recording identity, grouped-track choice, secure seek/range access,
   navigation and independent recording state must work without changing transcript timing.
2. Video input including MP4: discover/upload/inspect/plan/transcribe via existing audio extraction;
   keep the original video source in provenance. Missing/ambiguous audio is explicit and actionable.
3. Analyse percentage/ETA using actual events and measurements. Document what is credible, avoid
   fabricated progress, implement only supported estimates. No model pin/performance changes.
4. Verify, document, commit and push together. Manual owner review follows all three tasks.

## Progress

- Full task list persisted before implementation. Immediate implementation is complete;
  final delivery verification is in progress.
- Source player is bound to canonical source ID/hash/stream/channel. Private 16 kHz mono
  WAV preparation uses workdirs, one cached source and opaque session URLs. GET/HEAD supports
  streaming/single ranges; switching cache revokes old URLs, server close removes workdirs.
- Block seek saves dirty drafts and uses existing deterministic anchored word alignment.
  Unchanged text uses a direct mapping; ambiguous/inserted blocks explicitly disclose a
  conservative real-source timestamp. No canonical/revision timestamp is invented.
- Browser memory retains source/position independently per recording. Stage/recording navigation
  pauses and restores playback. Late preparation/seek callbacks cannot target another recording.
- Native picker and discovery accept video formats; probe propagates actual video-stream type
  through inspection to existing canonical media_type. Attached cover art is excluded. Existing
  FFmpeg stream/channel extraction is reused; no codec/model dependency added.
- Percentage/ETA analysis completed in docs/30-queue-progress-and-eta.md: current polling has
  no live phase events; canonical durations are available only after stages finish. Recommendation
  defines events, robust per-runtime history, slow-phase fallback and GPU calibration. Numeric
  estimates stay deferred, not fabricated. This completes the requested analysis scope.
- First browser playback and all 144 EN/PL/theme/layout cases PASS. Real MP4 extraction through
  fake-engine pipeline and source playback PASS; missing/multiple audio errors PASS.
- Temporary verification root: /tmp/ewp-media-tasks.1hT0dM. Latest full browser run is
  delivery-check, adding native MP4 staging and switching recording state. Consult its logs
  before rerunning. make check final session 70958; browser session 82846.

## Verification

- `UV_CACHE_DIR=/tmp/ewp-uv-cache make check`: Ruff/format/mypy (100 files), 864 tests PASS.
- `make test-integration`: eight PASS, four deselected. Real synthetic MP4 goes through directory
  discovery, inspect, dry-run, FFmpeg extraction, fake-engine transcription, canonical video-source
  publication and private playback. Original bytes stay unchanged; work audio is not in outputs.
  Missing/multiple audio are explicit failures. Cover art classification has unit regression coverage.
- Chromium 159 / Playwright 1.65.2: 144 layout cases PASS, six stages × six viewports × EN/PL
  × two themes. No page errors, external requests, page overflow, feedback overlap or internal
  transcript overflow. Existing editing, cursor split, dictionary, palette, queue recovery and
  source/manual-translation export checks remain passing.
- Actual browser native MP4 selection/upload, FFprobe metadata, dry-run and durable queue
  staging PASS. Start requests are intercepted: no ASR/provider call is made in browser tests.
- Actual synthetic PCM decode, per-block word seek/play, grouped-source selection, per-recording
  source/position restoration, pause on stage navigation and HTTP 206/416 PASS. Screenshots
  reviewed at 960/1920px. HTTP HEAD/byte range/foreign-request and token invalidation tests PASS.
- Fresh-server saved-work source/translation recovery PASS. Re-preparing audio, missing-source
  notice with continued editing, restoring source/reloading and updated PL video help PASS.
  Final focused browser seek uses the exact review SHA; changed-review rejection has a unit test.
- Build wheel/sdist PASS. All 52 packaged frontend/guide files match source; nine help routes and
  video defaults work directly from wheel without ML imports. Bundled JS syntax PASS.
- Model-free checks do not establish real WSL/GPU ASR or provider quality, Windows zoom or
  YouTube color behavior. Prior owner-qualified local WSL source-export evidence remains valid.
- No canonical schema, locked ML dependency, engine inference behavior, version or tag changed.

## Delivery and resume

- Implementation/analysis complete; commit and push pending. Manual owner review follows delivery.
- Disposable root `/tmp/ewp-media-tasks.1hT0dM` must be removed after content-free evidence capture.
  Browser/server processes exit after each run; final successful runs: delivery-check, seek-final.
- Owner retest: pull and restart `uv run --locked transcriber gui`; select one-audio-track MP4,
  inspect/plan/stage/transcribe, review source using Go to this fragment, switch grouped sources
  and recordings, navigate away/back, then perform normal save/export. Existing audio still works.
- Progress/ETA analysis is complete. Its separately listed follow-up needs phase events plus
  real target-workstation measurements before percent/ETA can be enabled. No fake indicator ships.
- Full Polish user documentation and artist package remain in their existing deferred order.
