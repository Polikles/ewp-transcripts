# Large cloud recording request splitting

Date 2026-11-21. Baseline ec6d8d8, clean main. Owner requires automatic splitting above 24 MB
and merged results. This supersedes B8a's initial single-request mixed-audio restriction; A stays
closed, B acceptance and task-10/documentation gates stay unchanged. Artist ZIP frozen.

## Plan / findings

Existing single-speaker/separate-track cloud input chunks at 120 seconds. Mixed audio instead
uses one request and rejects normalized WAV over 24 MiB. Correct this by bounding every complete
JSON request (including base64/header/metadata) below 24,000,000 bytes, plus the configured chunk
duration. Mixed requests overlap around core intervals. Shared timed words establish request-local
speaker-ID mappings without voice embeddings or persistent identities. Ambiguous/unmatched labels
stay distinct with a canonical review warning; never equate speaker_0 across independent calls.
Merge using word ownership and shared timed-word pairs to avoid boundary duplicates/gaps while
preserving real repeated words. Include overlap and per-request rounding in preflight charges.

Official OpenRouter STT docs reviewed: verbose word timestamps/speaker support varies by model;
no documented cross-request global speaker-ID guarantee. Existing four models/key/consent/local
pins remain. Private source/key and the unused portion of the original USD 2 budget remain
available for a narrowly relevant live boundary test if needed; historical spend
USD 0.0095832333762821113. Do not repeat the earlier broad functional pilot.

## Implemented and verified

- [x] Complete JSON/base64 requests stay below 24,000,000 bytes; long mixed audio no longer
  rejects above 24 MiB. Time/byte caps apply before sending; core intervals default to 120 s.
- [x] Mixed chunks share up to 5 s each side; shared timed-word pairs remap local speaker IDs,
  preserve intentional repetitions and transfer boundary ownership despite timestamp jitter.
  Original provider times plus absolute offsets remain canonical, with one merged result.
- [x] Unmatched/ambiguous speakers remain distinct (no guessed identities/biometrics) and produce
  CLOUD_SPEAKER_CONTINUITY_UNCERTAIN in canonical JSON plus a visible EN/PL source-review note.
- [x] Preflight includes every context/rounding reservation before the first upload; each request
  has size/offset/core/index/count/mapping/charge provenance. Cancellation/no automatic retry remain.
- [x] 982 tests in make check, Ruff/format/mypy 114 source files; 15 FFmpeg integrations pass /
  4 deselected. Regressions cover an 800 s / 25,600,044-byte normalized WAV, model label permutation,
  encoded-body cap, both boundary jitter directions, real repetitions, warning propagation,
  budget rejection before upload, cancellation and canonical/SRT/VTT/YTT publication.
- [x] Short live PL Scribe/MAI follow-up: each 45 s mix split into three requests using 15 s cores;
  six calls in total. Both pass schema, two canonical speakers, draft save/preview/apply and
  SRT/VTT/YTT exports. Both retain an uncertain-continuity note for human review. No accuracy claim.
- [x] New charge USD 0.0057777777777770557; cumulative original pilot + follow-up USD 0.0153610111540591670
  of the shared USD 2 limit, all charges reported and no automatic retries. EN live remains waived.
- [x] Necessary GUI/guide/checklist/roadmap/changelog/TODO updates. Prior B8a single-request
  restriction is historical and superseded by this follow-up, not an active input limit.

[Content-free evidence](../evidence/2026-11-21-cloud-chunking.json). No new native Windows/GPU
qualification or browser run is claimed. Source-review warning payload is covered by unit tests;
DOM synchronization reuses the existing source warning path. No local model loading introduced.
Artist ZIP unchanged. B acceptance/task-10/manual gates remain intact.

Disposable root /tmp/ewp-cloud-chunks.BKHH1C was removed after content-free evidence capture. Private originals,
models and the frozen artist ZIP are preserved. Delivery targets main; next is owner long-cloud
and full Windows/WSL acceptance using the updated B checklist.
