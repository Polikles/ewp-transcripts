# B8a OpenRouter ASR

Date 2026-11-21. Baseline cf20995; implementation and B9 verification complete.
A remains closed; artist ZIP untouched. Owner supplied private key/source paths and explicitly
waives live EN qualification because no EN sample is present. The HD06 MP4 is PL, not EN.

## Implemented

- Four fixed ASR IDs, shared key, local default, exact provider/model/budget plan identity.
- New explicit cloud consent at queue Start; never saved/restored or automatically retried.
- Live worst-endpoint duration pricing with explicit MAI hour versus other-model second units;
  conservative reservations for uncertain charges, per-job guard, no secret/raw response logs.
- Word-time/speaker normalization into existing canonical schema 1.1, cloud runtime/provenance,
  existing source hashes, workdir failure/cancellation, review/revision and immutable exporters.
- One-speaker/separate synchronized source tracks for Whisper; Scribe/MAI mixed diarization.
  Mixed requests stay whole (24 MiB normalized WAV limit) to avoid stitching unstable speaker IDs.
- PL ISO639-3 aliases and silent chunks handled; missing word times/speaker labels fail visibly.
- Provider same-speaker word overlaps stay within subtitle cues without changing canonical times.
- Portable staged speech options/IDs/streams retained, credentials and consent excluded.

## Live functional evidence

Owner-authorized synchronized PL s0e00 excerpts: two tracks, 30 s each, 30 s mixed derivative.
Four models on the separate tracks plus Scribe/MAI on the mix: 10 paid requests, all charged costs
reported, total **USD 0.0095832333762821113** of the shared USD 2 budget. No automatic retry.
The Scribe first response exposed `pol`; after fixing the alias, the already-paid response was
reused locally, with no duplicate paid upload. An initial pilot reporting typo occurred after
Whisper's canonical publication; the existing artifact was used rather than transcribing again.

All six cases pass canonical Pydantic + JSON Schema validation, draft save, review preview,
revision application and SRT/VTT/YTT exports. All have two canonical speakers. These are structural
functional checks, not human transcript/translation approval or an accuracy benchmark. No live EN
claim; owner explicitly accepts PL-only live scope. Private derived audio/text/raw responses were confined to /tmp/ewp-package-b.Yz9JAl and removed
after content-free evidence capture. No key/audio committed.

## Qualification / next

Final ordinary gate: 973 tests,
Ruff/format/mypy 113 source files. Real FFmpeg integrations: 14 pass / 4 deselected.
B9 full Chromium GUI: 144 EN/PL/light/dark/width/section cases pass, no page errors/external calls;
real server restart/editor/export recovery passes. Focused B HTTP/browser and 48 expanded panel cases pass. Wheel/sdist/installed CLI/resource/privacy
checks pass. B checklist/evidence/status/roadmap are current. Disposable root removed after evidence capture; commit/push delivery. Owner native Win11x64/GPU and full WSL
acceptance stay owner-run. Complete EN–PL approval file/manual rewrite remain after B acceptance.
