# Queue percentage and ETA

Status: first implementation delivered after the 2026-11-19 assessment and owner's request for
an approximate indicator. It makes activity visible without changing inference or model pins.
Synthetic tests validate behavior; prediction accuracy on real target hardware remains to qualify.

## What the GUI displays

The queue shows the actual phase, animated gear, elapsed time and an approximate percentage.
Grouped work includes current stream/count. Cold/unknown runs use coarse phase weights: a long
opaque inference call can hold its percentage while elapsed time and the gear keep showing work.
The percentage describes estimated pipeline completion, not a measured fraction of recognized audio.

After comparable successful jobs, ETA appears as a broad remaining-time range and percent can
advance within the active phase using those measurements. Unknown profiles show calibration.
When a phase takes much longer than expected, ETA is withdrawn and a longer-than-estimated
message replaces it. The counter never silently counts down to zero while inference still runs.
Failure stays below 100%; completion reaches 100% after the application returns from required
publication, exports and cleanup. Optional API operations and human review are outside ASR ETA.

## Actual backend events

`progress.ProgressEvent` is an immutable optional observer event. Application events cover
inspection, planning, publication, exports and cleanup; pipeline events cover preparation, ASR,
word alignment, normalization, diarization/reconciliation when used, and source composition.
Independent streams carry their actual index/count. Events contain no transcript or audio data.

Callbacks default to None for CLI/other callers and failures are isolated. The single GUI worker
owns a live RuntimeProgress tracker; polling samples a monotonic clock for phase and total elapsed
time. API responses add runtime_progress without changing canonical schemas. A browser refresh
cannot restart a job or synthesize phase completion. Failed/interrupted runs keep their normal
queue diagnostics/restart behavior and do not contribute successful timing measurements.

Pinned adapters still call WhisperX/pyannote as before. Model loading inside the first inference
call is included in that phase's real timing. This increment does not consume engine-native chunk
callbacks or change CUDA/model settings. Finer native callbacks can improve cold-run progress
later, subject to actual GPU/E2E qualification.

## Local timing history

Successful complete runs record measured per-phase duration divided by media duration. The cache
keeps up to 12 samples/phase and 32 profiles. Its default file is runtime-timings.json alongside
the GUI workspace catalog, under XDG_STATE_HOME/ewp-transcripts (or the user's local state root).
The cache contains hashed profile keys, phase names and numeric timing factors only; no host
names, source paths, transcript text, audio or API credentials are stored.

Profiles separate host/CPU, available GPU identity/driver (queried without initializing torch),
OS/Python, exact model/runtime configuration, language, speaker/topology and actual stream phase
plan. Unknown/unavailable GPU discovery remains explicit in the hashed profile input. Different
hardware/configuration does not borrow another machine's speed. Cache read/write failure leaves
transcription unaffected. Deleting this cache simply resets calibration.

A median factor predicts each pending phase for the current recording duration. At least one
matching successful complete run is required for a numeric ETA. The initial range is deliberately
broad: 50–175% of predicted remaining time. This is a heuristic confidence display, not a measured
accuracy guarantee. More diverse completed jobs improve the evidence but do not make it exact;
cold load, system contention, silence and speaker topology still affect timing.

First-run phase weights are heuristics (ASR and alignment dominate; diarization is included only
when actually used). For a measured phase, estimated internal completion is capped at 90% until
its real completion event; the total stays monotonic and below 100%. If phase elapsed time exceeds
175% of its expected duration, the stale ETA disappears. Completed phase/time remain factual.
Late active phases retain a small remaining allowance and cannot consume time reserved for future
phases. Numeric active ETA is never rounded down to zero. Unknown profiles/phases omit ETA. A queue-wide ETA is not reported because pending work may
have unknown profiles; no incomplete sum is presented as a complete queue prediction.

## Evidence and further qualification

Fake-clock tests cover elapsed heartbeat, calibration, unknown/corrupt history, overdue fallback,
monotonic percent, incomplete/failed runs, observer failure and true completion. Queue tests check
live snapshots while the service is blocked and terminal state after it returns. Real FFmpeg with
fake engines verifies event order through publication/exports/cleanup, including observer failures.
Browser checks cover EN/PL labels and narrow queue cells. These tests do not calibrate GPU speed.

Next real-runtime checks: mono, mixed-speaker/diarization, grouped/split-channel, PL/EN, cold/warm
load and video extraction on RTX 3090/WSL and a slower supported machine. Compare each predicted
remaining range with actual remaining wall time at phase boundaries; record error/spread privately
without transcript data. Use that evidence to tune weights/ranges and decide on finer engine-native
callbacks. Do not infer quality or runtime accuracy from the synthetic artist-package simulation.
