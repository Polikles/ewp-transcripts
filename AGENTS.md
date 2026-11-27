# AGENTS.md

## Current work and authority — 2026-11-27

Read WORK_STATUS.md, TODO.md, WORK_POLICY.md, docs/99-roadmap-v2.md and the active checkpoint
before work. Product0.26.2 and prior owner UI/lifecycle acceptance remain qualified and immutable.
Owner plan revision2026-11-27 supersedes the mandatory-signing rule: early public releases MAY BE
UNSIGNED. Actual signing procedure/private instructions/keys stay outside Git; later free OSS
signing research may use owner-approved Actions, not a paid certificate commitment.
NEXT: SEC-01/PRIV-01 general local EN report/policy and REL-01 attestations. Owner confirmed BOTH
as first-release gates. All six policy answers settled: Release assets/index accepted; quick update
AFTER first release; Store model-free/cloud-first; shared EXE/Store hardware tiers, including
compatible6–8 GB/older NVIDIA experimental; publisher/contact approved in SECURITY_REVIEW_PLAN. General cybersecurity
report FIRST local EN OUTSIDE Git, including DEV VM authentication/permissions/credential lifecycle
and compromise tradeoffs (no secret values); then owner approval before publishing. Applicable frameworks
and separate mapping follow the general report. Existing technical docs are not a complete user
privacy policy. Required attestations are not yet implemented; current CI permissions unchanged.
Quick update is planned AFTER first release. Required GH Pages follows first release per latest owner sequencing.
MSIX/Store is an independent post-release research channel, preserving installed CLI and optional
model setup. Agreed shared EXE/Store tiers await HWPOL-01; they are not current installer code or qualification.
Remove highlighting, separate reader tests and benchmark programs old5.12–5.14. Bound audio prep;
separate poor-audio attempt with one-file repaired/composite export; sound detection experimental.
Profile transfer/200% zoom are upcoming-release scenarios. Physical AMD/other NVIDIA unavailable,
no tests planned; annotated-corpus accuracy deferred without date. Artist only blocks illustrated
docs after integration/test. GTX1070, slimming and local Scribe/MAI stay removed. Preserve pins,
brand/licenses/workbooks, immutable packages, zero paid budgets and provider spend USD0.0291461230985028369.

## 1. Project goal

A local-first transcript workflow sharing one application/domain core across native Windows and
Ubuntu/WSL/browser interfaces. Canonical results, revisions/translations, dictionaries, exports,
privacy and scoped provider consent retain their contracts in docs, schemas and tests.
Historical chronology is preserved byte-for-byte in archive/project-status; do not replay stale
NEXT instructions from those snapshots or old checkpoints. Approved terminology, asset/license
sources and sent artist/installer archives remain immutable unless the owner explicitly changes them.

## 2. Scope discipline

Implement only the current MVP unless a task explicitly says otherwise.

The selected feature set includes native Windows and browser GUI, local/optional cloud ASR,
manual/assisted correction, translation, dictionaries, managed lifecycle and offline help.
Outside current delivery: Docker, audio repair/advanced channels and other optional post-release
work, voice biometrics, cloning datasets, internal clock-drift correction and distributed/multi-GPU
processing. Preserve clean extension points without speculative infrastructure. Current owner
scope and cancellation decisions in the roadmap override historical proposals.

## 3. Architectural rule

The project is a **modular monolith**.

The primary dependency direction is:

```text
CLI or GUI
        |
        v
application.py
        |
        v
pipeline.py and domain services
        |
        +--> discovery.py
        +--> media/
        +--> engines/
        +--> speakers.py
        +--> storage.py
        +--> workdirs.py
        +--> exporters/
```

Mandatory boundaries:

1. `cli.py` is an adapter. It must not contain transcription, grouping, hashing, subtitle, or storage logic.
2. `application.py` is the stable application-facing API for both CLI and GUI.
3. `pipeline.py` orchestrates work but delegates implementation details to focused modules.
4. `domain/` must not import Typer, Rich, WhisperX, pyannote, torch, or FFmpeg adapters.
5. WhisperX may be imported only inside `engines/whisperx.py`.
6. pyannote may be imported only inside `engines/pyannote.py`.
7. Heavy ML imports must be lazy. `--help`, `doctor`, `inspect`, `dry-run`, and `export` must not initialize CUDA.
8. Exporters operate on the canonical internal result model, never directly on WhisperX output.
9. Final result files are written only through `storage.py`.
10. Temporary audio is managed only through `workdirs.py` and must never be placed in the final output directory.

## 4. Data contracts

- `*_results.json` is the canonical source of truth and is always produced after successful transcription.
- `*_segments.json` is optional and derived entirely from `*_results.json`.
- TXT, SRT, and VTT are derived exports and must be regenerable without running ASR again.
- All canonical models must remain compatible with the JSON Schemas under `schemas/`.
- Schema changes require explicit versioning and corresponding migration or compatibility notes.
- Store timestamps as integer milliseconds unless the existing schema explicitly requires another representation.
- Store SHA-256 for every source file and a deterministic episode signature for grouped sources.

## 5. Runtime behavior

- Default language: Polish (`pl`). English and automatic detection are optional modes.
- Default directory processing is non-recursive.
- Existing completed results with matching SHA-256 are skipped unless `--force` is present.
- `--force` creates the next free version suffix: `_v002`, `_v003`, and so on.
- `--force` must not bypass source-duration or sample-rate safety checks.
- Ambiguous stereo must produce a warning and fall back to one-channel transcription.
- Multiple files grouped as one episode must have matching sample rates and a shared timeline.
- Differences above 100 ms produce a warning; differences above 500 ms reject the group unless a dedicated mismatch override is used.
- A failed or interrupted file is restarted from the beginning on the next run.
- Temporary work files are deleted after success and retained after failure unless configuration says to retain them always.
- Model downloads must be explicit. Installation and normal transcription must not silently download gated models.

## 6. Coding standards

- Target Python 3.12 for the MVP.
- Use a `src/` layout.
- Use type annotations for all public functions and non-trivial internal functions.
- Prefer small typed data models over unstructured dictionaries.
- Use `pathlib.Path` for paths.
- Use `subprocess` argument lists and never `shell=True` for FFmpeg or ffprobe.
- Avoid global mutable state and module-level model initialization.
- Avoid hidden network access.
- Never log secrets or the Hugging Face token.
- Avoid logging full transcript text by default.
- Preserve meaningful repetitions and self-corrections in canonical text.
- Automated correction MUST remain faithful transcription repair. Do not add LLM-based
  rewriting, paraphrasing, or prose polishing.

## 7. Change strategy

Work in vertical slices. Use `WORK_STATUS.md` for the current resume point and
`docs/99-roadmap-v2.md` for post-MVP priorities.

For context recovery, also read `WORK_POLICY.md`, `TODO.md`, and the active task
checkpoint linked from `WORK_STATUS.md`. Leave a dated checkpoint under
`docs/checkpoints/` for each task and update its evidence, outstanding work and resume
steps before handoff. Keep the existing roadmap authoritative for product sequencing.

Before implementing a phase:

1. read the relevant existing product documentation and schemas;
2. identify the acceptance criteria for the phase;
3. add or update tests first when practical;
4. implement the smallest complete change;
5. run the local quality gate;
6. update documentation only when behavior or a public contract changed.

Do not create empty modules for future phases unless required by imports or packaging.

### Commit and pull-request naming

Use the standardized form `<type>(<scope>): <summary>` for every new commit and pull
request title. Use a short imperative summary and one of these types unless a later
repository rule expands the list:

- `docs` for documentation-only changes;
- `func` for a new functional requirement, normally scoped to its requirement ID;
- `fix` for defect corrections;
- `test` for test-only changes;
- `refactor` for behavior-preserving restructuring;
- `chore` for repository or dependency maintenance.

Examples: `docs(readme): add archive-pilot instructions`,
`func(FR-XXX): add corrected transcript import`, and
`fix(cli): normalize Windows paths before dispatch`.

Every user-visible behavior, CLI, installation, or workflow change must update
`CHANGELOG.md` in the same commit. Record ongoing work under `Unreleased`; move it into
a dated version section and apply the corresponding semantic-version bump when creating
an identifiable internal or public build. Historical version sections must not be
rewritten to include later changes.

## 8. Testing expectations

Follow `docs/TESTING_STRATEGY.md`.

Minimum local gate for normal changes:

```bash
make check
```

Changes touching FFmpeg, filesystem behavior, or pipeline orchestration must also run:

```bash
make test-integration
```

Changes touching WhisperX, alignment, pyannote, CUDA, model loading, or performance must run
relevant available GPU/E2E functional regression checks with authorized representative material.
Record unavailable hardware/material honestly; never claim qualification from model-free tests.
Broad comparative dataset/model/hardware benchmark campaigns are removed from the active owner
plan. Existing regression checks remain; do not impose a new project-completion campaign.

All disposable pilot outputs, provider resume state, generated candidates, temporary
exports, and intermediate benchmark bundles MUST be written under a dedicated `mktemp -d`
directory. Do not place pilot runtime artifacts inside the private corpus, repository, or
long-lived project directories. Persist only the reviewed, content-free test evidence that
the relevant contract or acceptance document explicitly requires, then remove the temporary
directory when the pilot is complete.

## 9. Definition of done

A change is complete only when:

- behavior matches the documented requirement;
- tests cover the normal case and relevant failure cases;
- lint, formatting, typing, and tests pass locally;
- no new secret, model, private audio, generated transcript, workdir, or cache file is committed;
- CLI behavior is non-blocking in non-interactive mode;
- public JSON and CLI contracts remain backward compatible or are explicitly versioned;
- no unrelated v2 feature was added.
