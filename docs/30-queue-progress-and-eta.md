# Queue percentage and ETA: implementation assessment

Status: analysis complete, 2026-11-19. No percentage or ETA is enabled by this assessment.
The current indeterminate gear remains the accurate signal until runtime evidence exists.
This closes the requested analysis task; implementation and GPU calibration are follow-up work.

## Finding

An approximate indicator is feasible. The present API cannot support a meaningful Running xx%
by itself: it only reports staged/queued/running/completed/failed. A browser timer would confuse
elapsed time with completed work and could reach 100% while a blocking model call still runs.
Use actual backend events first, then calibrate time estimates from comparable successful jobs.
No additional model, provider, cloud service or transcript upload is needed.

## Evidence in this repository

- `web_jobs.GuiTranscriptionQueue._run` marks running before calling `transcribe_one`; the
  browser polls `/api/v1/transcriptions` every two seconds. There is no live phase counter.
- `pipeline.py` measures `CanonicalStage.duration_ms` only once each stage has finished.
  The completed canonical result retains prepare_audio/transcribe/align/normalize timings;
  the diarization path also has diarize/reconcile_speakers. Source-speaker runs repeat stages
  per stream and retain source/channel details. These durations are real historical evidence.
- `application.transcribe_one` starts its elapsed timer before inspection; `_process_reservation`
  also allocates work, gathers environment, publishes results/exports and cleans workdirs.
  These costs are not all covered by canonical stage durations. They need their own events.
- Model factories create adapters before pipeline entry. WhisperX/pyannote lazily load models
  inside their first transcribe/align/diarize call. The currently recorded stage time therefore
  combines cold model load with inference. Equal phase weights or one global real-time factor
  would misrepresent single-speaker, diarized and grouped/split-channel recordings.
- Engine protocols return completed drafts/alignment/diarization results. They do not expose a
  stable per-chunk completion callback. Neither VAD logs nor audio timestamps in finished words
  establish live completion of the remaining pipeline. Instrumenting engine internals is a
  separate change requiring real GPU/E2E qualification.

## Recommended first increment

Add an optional observer at the application/pipeline boundary, defaulting to no observer for
existing CLI callers. Emit immutable, content-free events containing job/run ID, phase name,
phase started/completed, monotonic elapsed milliseconds, source/stream index and known count.
Emit inspection/planning, audio preparation, inference, alignment, diarization when used,
normalization/reconciliation, publication, exports and cleanup explicitly. Preserve the single
worker, cancellation/failure semantics, lazy ML imports and immutable canonical data.

The queue owns a thread-safe latest snapshot. Extend the existing polling response additively
with current phase, phase start/elapsed and known completed units. Do not write a canonical
result during processing. Persist only bounded successful timing summaries for future estimates;
exclude paths, names, transcript text, API credentials and failed/interrupted measurements.
A listener failure must not fail transcription. A restored running job must not resume a stale
percentage: it returns to the existing restart-from-beginning workflow.

Display immediately useful facts before introducing estimates: Running · Alignment, elapsed
12 min; grouped track 2/3 where the worker actually knows it. The gear is indeterminate within
an opaque phase. This can ship before an ETA and is more informative than a fabricated percent.

## Estimation model after calibration

Partition measurements by application/model revisions, device/runtime, compute type, batch size,
language, source topology/channel count, diarization/speaker-count mode and cold/warm model state.
Use source duration to normalize variable inference work; model load/publication are separate
fixed costs. Start conservatively with at least three comparable successful measurements, retain
a bounded history and use robust median plus a spread (for example lower/upper quantiles).
This sample minimum is a proposed product policy, not a measured accuracy guarantee.

For each remaining phase estimate its duration from matched historical measurements. At a real
phase boundary:

- estimated total = measured completed phase time + estimated remaining phase time;
- estimated progress = measured completed phase time / estimated total;
- ETA = a range covering remaining phases, rounded to whole minutes for long recordings.

Within an opaque call, keep phase progress unchanged; elapsed time can still increase. Do not
advance a percent just because a timer fired. If elapsed phase time exceeds its historical range,
show Running · taking longer than estimated and withdraw the stale ETA. Do not force time left
to zero. For known per-track units, a later increment can update when each track actually finishes.
Never move to 100% before successful publication/exports and required cleanup have completed.
Errors/interruption replace the estimate with their existing diagnostic state.

Where a remaining phase or runtime has no comparable data, omit numeric percent/ETA and show
Estimating after more completed recordings. Do not silently borrow another GPU or a synthetic
fixture's speed. Queue-wide ETA is the sum of credible per-job ranges, including queue wait;
if any pending job is unknown, display a partial estimate or no queue ETA. Human correction,
source verification, translation review and optional API response time are outside ASR queue ETA.

## Acceptance for a follow-up implementation

1. Fake-clock tests verify event order, sequential grouped tracks, skipped existing results,
   model-load failure, source mismatch, publication failure and observer failure isolation.
2. Browser tests verify EN/PL phase text, absent estimates on cold/unknown runs, slow-phase
   fallback, reload/recovery, terminal errors and 100% only after publication.
3. Real RTX 3090/WSL runs cover mono, mixed-speaker/diarization, grouped/split-channel,
   PL/EN, cold/warm load and video extraction. Record prediction error against actual remaining
   wall time at each phase boundary. Synthetic tone/fake-engine tests cannot calibrate ETA.
4. Agree acceptable error ranges with the owner using those measurements before enabling ETA
   by default. Keep a diagnostics explanation of estimate age/sample count and fallback behavior.

The current GUI task adds playback/video support and leaves this implementation in TODO.
No inference adapter, model pin, CUDA tuning or throughput change was made for this analysis.
