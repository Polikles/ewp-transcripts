# Definition of Done — MVP

Owner scope update (2026-11-20): the current [roadmap scope](99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20)
controls required work. Corpus/quality research, general dictionaries and hardware/preset benchmark
programs described here are optional nice-to-have, not current project completion gates. Existing
unit/integration, security, data-lineage and packaging checks remain required; preserve all accepted
historical evidence. This is a practical podcast/recording workflow tool.

The MVP is complete when the following conditions are met.

## Functionality

- [x] All FR requirements are implemented or explicitly deferred through an ADR.

The requirement-by-requirement evidence and the narrow FR-A05 directory-discovery
deferral are recorded in the [MVP requirements traceability matrix](20-mvp-requirements-traceability.md).
- [x] `doctor`, `inspect`, `dry-run`, `transcribe`, `export`, and `clean` work.
- [x] A results JSON is always generated after successful transcription.
- [x] TXT, SRT, VTT, and optional segments JSON are generated without running ASR again.
- [x] Single file, directory batch, grouped files, dual mono, and split speakers work.
- [x] Diarization works for mixed mono/stereo.
- [x] SHA-256/signature-based skipping and versioning work.

## Quality

- [x] All examples pass JSON Schema validation.
- [x] The complete application-test checklist passes.
- [x] The representative audio matrix has been executed for available MVP material.

Fast/noisy derived fixtures and the long-form archive cases close the available material
rows. Full-English and three-speaker quality remain explicitly deferred by ADR-0014
until representative archive-derived inputs exist.
- Optional research backlog: additional WER/CER/timestamp/DER baselines (not a completion checkbox).

The lexical WER/CER portion has an accepted three-case Polish baseline. Timestamp,
DER/JER, English, and statistically representative thresholds are explicitly deferred by
[ADR-0014](adr/0014-dataset-dependent-quality-gates.md) until annotated archive-derived
references exist; the combined checkbox therefore remains open.
- [x] A 60-minute file completes on RTX 3090 without OOM.
- [x] A batch of at least ten files shows no accumulating VRAM use.
- [x] SRT and VTT have been reviewed manually in a private YouTube upload.

The accepted P2-03 compatibility review and complete 34.7-minute P9-02 YouTube timing
review, iterative cue-readability evidence, and final hashes are recorded in
[ADR-0016](adr/0016-subtitle-readability-and-correction-boundary.md).

## Security and reliability

- [x] Offline tests perform no network requests.
- [x] Tokens do not occur in logs or results.
- [x] Failed jobs do not create final results JSON files.
- [x] Existing files are never overwritten.
- [x] `clean` does not remove final results or models.
- [x] Locking prevents concurrent output collisions.

## Distribution

- [x] A clean installation on WSL2 Ubuntu 24.04 is documented and tested.
- [x] The lockfile is approved.
- [x] CLI documentation matches `--help`.
- [x] Known limitations are listed in README or release notes.
- [x] Application version and schema version are defined.
