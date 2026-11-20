# Testing and Acceptance Criteria

Owner scope update (2026-11-20): the current [roadmap scope](99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20)
controls required work. Corpus/quality research, general dictionaries and hardware/preset benchmark
programs described here are optional nice-to-have, not current project completion gates. Existing
unit/integration, security, data-lineage and packaging checks remain required; preserve all accepted
historical evidence. This is a practical podcast/recording workflow tool.

Tests are divided into two matrices: application behavior and audio-material types.

Checked application items may be satisfied by deterministic automated tests, recorded WSL
integration gates, or both. Hardware-, player-, and corpus-dependent items remain open until
their corresponding external evidence is accepted.

## 1. Application tests

### Discovery and paths

- [x] Single Windows path with backslashes.
- [x] Windows path with forward slashes.
- [x] `/mnt/d` path.
- [x] Spaces, Polish characters, and general Unicode.
- [x] Directory without recursion.
- [x] Explicit recursion.
- [x] Symbolic link skipped by default.
- [x] File with a misleading extension detected by content.

### Grouping

- [x] `S01E01-jan` + `S01E01-anna`.
- [x] Base identifier containing underscores.
- [x] Single hyphenated file with `speaker_count=auto`.
- [x] Single hyphenated file with `speaker_count=1`.
- [x] Base file plus suffixed file.
- [x] Ambiguous names are not grouped.
- [x] Explicit group overrides automatic detection.

### Timeline validation

- [x] Difference of 0 ms.
- [x] Difference of 100 ms.
- [x] Difference of 101 ms produces a warning.
- [x] Difference of 500 ms produces a warning.
- [x] Difference of 501 ms blocks the group.
- [x] `--allow-duration-mismatch`.
- [x] Different sample rates block the group.

### Channels

- [x] Mono.
- [x] Identical dual mono.
- [x] Nearly identical dual mono.
- [x] Split speakers.
- [x] Mixed stereo.
- [x] Ambiguous input uses one channel and emits a warning.
- [x] Forced channel mode.
- [x] An implausible forced mode produces a visible warning.

### Hashing and versioning

- [x] Same SHA and same name results in SKIP.
- [x] Same SHA and different name results in SKIP.
- [x] Same SHA with `--force` creates `_v002`.
- [x] Existing `_v002` causes `_v003` allocation.
- [x] Same name with different SHA creates a new version.
- [x] A grouped signature changes when one source changes.
- [x] Every export in a run uses the same version.
- [x] Concurrent version allocation does not collide.

### State and failures

- [x] SIGINT during ASR.
- [x] Exception during alignment.
- [x] Exception during diarization.
- [x] Disk full.
- [x] Output write error.
- [x] Corrupt partial result.
- [x] Restart processes the file from the beginning.
- [x] One failed job does not stop the batch.
- [x] Temporary files are preserved after failure.
- [x] Temporary files are removed after success.
- [x] `--keep-temp`.
- [x] `clean --dry-run`.

### JSON

- [x] Conformance to JSON Schema.
- [x] `schema_version` and `application_version` present.
- [x] Monotonic timestamps.
- [x] No secrets.
- [x] Complete effective-configuration snapshot.
- [x] Correct `timestamp_source` values.
- [x] Overlap and active-speaker metadata.
- [x] Final JSON exists only for `completed` status.

### Exports

- [x] TXT contains no timestamps.
- [x] One sentence per line.
- [x] Speaker blocks.
- [x] No label for a single speaker.
- [x] SRT is syntactically valid.
- [x] VTT is syntactically valid.
- [x] No more than two lines per cue.
- [x] `on-change` labels.
- [x] Regeneration without source audio.
- [x] Optional `segments.json`.
- [x] Fast speech does not create unintended overlapping cues.

### Environment

- [x] `doctor` without a GPU.
- [x] `doctor` with RTX 3090.
- [x] Missing FFmpeg.
- [x] Missing model.
- [x] Missing `HF_TOKEN` before model download (not an application operation: installation
  never downloads gated models, and missing-model setup guidance is validated).
- [x] Complete offline readiness.
- [x] Token is not written to logs.

### Performance and resources

- [x] A 60-minute file completes without OOM on RTX 3090.
- [x] Peak VRAM is recorded or marked unavailable.
- [x] Stage timings are recorded.
- [x] VRAM usage does not grow across consecutive batch jobs.
- [x] Ten sequential files complete without stability degradation.

## 2. Audio-material matrix

- [x] Clean Polish podcast, one speaker.
- [x] Polish podcast, two speakers mixed to mono.
- [ ] Polish material with three speakers — quality validation deferred by ADR-0014.
- [x] Polish speech with English technical terms.
- [ ] Full English recording — quality validation deferred by ADR-0014.
- [x] Split-speaker stereo.
- [x] Audacity dual mono.
- [x] Two separate mono files.
- [x] Overlap on separate tracks.
- [x] Overlap in mixed mono.
- [x] Fast speech.
- [x] Long pauses.
- [x] Intro/outro music.
- [x] Light recorder noise.
- [x] Clipping.
- [x] Unequal channel levels.
- [x] WAV 44.1 kHz.
- [x] WAV 48 kHz.
- [x] MP3.
- [x] FLAC.
- [x] M4A/AAC.
- [x] Opus.

## 3. Text-quality evaluation

### Ground truth

Every representative sample must have a manually verified reference transcript.

Procedure:

1. Select 5–15 minutes from each material type.
2. Produce a manually verified reference transcript.
3. Define one normalization policy for numbers, capitalization, punctuation, and fillers.
4. Run the local pipeline.
5. Optionally run a recognized online model.
6. Compare both systems independently against the same ground truth.
7. Calculate WER and CER.
8. Manually assess proper names, numbers, technical terminology, and English insertions.

### Regression criterion

After the first baseline is approved, no dependency or parameter change may worsen mean WER by more than one percentage point without an explicit project decision.

## 4. Timestamp evaluation

On a manually aligned subset, measure:

- word-start MAE;
- word-end MAE;
- P50, P90, and P95 error;
- percentage of words without alignment;
- number of cues that cut through words incorrectly.

Initial absolute thresholds are set after the reference corpus exists. The release gate requires no regression against the approved baseline.

## 5. Diarization evaluation

Measure separately:

- DER/JER for mixed mono;
- source-based speaker assignment for separate files/channels, expected to be 100%;
- correctness of normalized `SpeakerN` numbering;
- overlap errors.

## 6. Subtitle review

Perform a manual review in the target player or a private YouTube upload:

- readability;
- no excessively long lines;
- speaker labels;
- timing;
- fast speech;
- speaker transitions;
- Polish characters.


## 7. Transcript revision acceptance (implemented for v0.2.0)

### Review and alignment

- [x] `EWP-REVIEW 1` round-trip with no text edits.
- [x] Punctuation-only edit.
- [x] Proper-name/spelling substitution.
- [x] Sentence-boundary change through punctuation only.
- [x] One-to-one substitution.
- [x] N-to-1 merge.
- [x] 1-to-N split.
- [x] Insertion with adjacent canonical anchors.
- [x] Deletion.
- [x] Legitimate repeated words remain duplicated when not edited.
- [x] Short span reassigned to another existing speaker.
- [x] Ambiguous alignment is reported rather than silently selected.

### Review integrity

- [x] Modified anchor is rejected.
- [x] Missing anchor is rejected.
- [x] Duplicate/overlapping/out-of-order anchors are rejected.
- [x] Nonexistent canonical word ID is rejected.
- [x] Base-result SHA mismatch is rejected.
- [x] Unknown speaker ID is rejected.
- [x] Insert across configured long gap emits a structured warning.

### CLI and batch

- [x] Single-file `revise prepare`.
- [x] Directory `revise prepare` in deterministic natural order.
- [x] Single-file `revise apply`.
- [x] Directory `revise apply` with per-item failure isolation.
- [x] `revise preview` writes no revision.
- [x] `revise apply --no-apply` writes no revision and matches preview outcome.
- [x] `revise edit --no-apply` retains review edits without creating a revision.
- [x] Successful editor close without `--no-apply` automatically applies the saved review.
- [x] Non-zero editor exit creates no revision.

### Persistence and provenance

- [x] Base `results.json` bytes remain unchanged.
- [x] Every revision is a full standalone snapshot.
- [x] Sibling revisions can reference the same base result.
- [x] Parent revision metadata does not make child export depend on parent replay.
- [x] Provenance, alignment metadata, statistics, and warnings are always present.
- [x] `--audit` produces detailed diagnostics without becoming reconstruction state.
- [x] Base-relative detailed audit can be regenerated later from base + revision.
- [x] Concurrent revision allocation cannot collide.

### Revision-aware exports

- [x] Omitted `--revision` is behaviorally equivalent to raw v0.1 export.
- [x] `--revision none` selects raw canonical text.
- [x] `--revision latest` selects only a revision matching the exact base-result hash.
- [x] Explicit revision path is validated against the selected base result.
- [x] Revised TXT uses corrected punctuation and one-sentence-per-line output.
- [x] Revised SRT and VTT use corrected text with inherited canonical timing.
- [x] Revised segments JSON is generated from the same effective transcript.
- [x] Revision prepare/apply/export do not require source audio, GPU, ASR, alignment, or
  diarization models.

Automated evidence is concentrated in `test_review_format.py`,
`test_revision_service.py`, `test_revision_models.py`, `test_revision_storage.py`,
`test_revision_application.py`, the revision CLI/batch tests, and the revision-aware
export tests. Concurrency is exercised with two separate processes contending for the
same output lock and allocating distinct immutable revision numbers.

Operator evidence covers the complete private 24-episode workflow: deterministic batch
prepare/apply, isolated repair of one malformed review, two revision generations with
audits, and successful model-free batch regeneration of TXT/SRT/VTT/segments. The private
corpus itself is not repository test data and is not required by the automated gate.
