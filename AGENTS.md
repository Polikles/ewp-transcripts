# AGENTS.md

This file defines implementation rules for coding agents working on **ewp-transcripts**.

## 1. Project goal

`ewp-transcripts` is a local-first transcription application for edited podcast and training recordings. The MVP runs under Ubuntu in WSL2, uses an NVIDIA GPU through CUDA, and produces a canonical `*_results.json` plus optional TXT, SRT, VTT, and `*_segments.json` exports.

The existing files under `docs/`, `examples/`, and `schemas/` are the product and data-contract source of truth. Read them before changing application behavior.

Current owner scope (2026-11-20) is authoritative in the opening section of
`docs/99-roadmap-v2.md`: a practical podcast/recording workflow tool. GUI is authorized and
native Windows remains planned convenience work. General-corpus research, universal dictionaries,
broad model/hardware preset benchmarking and accurate percentage/ETA calibration are optional,
not current completion gates. Preserve accepted results and ordinary regression/security checks.
Generate the complete editable EN–PL string-pair approval file only after functional additions
finish, then owner approval before the full English-manual revision and Polish manuals.
Keep only necessary changed-step/raw-output instructions current before that approval. Documentation screenshots wait for custom icons;
waiting for the artist has no deadline and blocks no other work. Do not modify the sent artist ZIP.

Latest owner sequencing: follow TODO and the roadmap package table. Package A (1–4) is followed
by an owner checklist/fix/retest gate, then package B (5–8, 8a cloud ASR, 9 full native-Windows/WSL
workflow test), then 10 complete EN–PL approval. The owner explicitly authorized A1–A4 and its
verification/checklist. On 2026-11-21 the owner passed the complete focused retest and accepted A,
with a final source-review action layout adjustment that needs no new owner retest. That adjustment
is implemented/verified and A is closed. Next: B5 preparation for Windows 11 x64; agent changes/checks
on this Linux VM and pushes to GitHub, owner pulls and tests natively.
Do not reopen the accepted A gate. B features/cloud calls are not part of the A closure task.
Previously declined proposals must not return as requirements. Explicit owner B8a scope now selects
OpenRouter (one key shared with correction/translation), the four ASR presets in the B plan and
short supplied PL/EN functional samples with USD 2 total including retries. Retain that permission
for B8a without asking again; no broader provider/media/spending scope is implied. B implementation
has not started; the current request records planning decisions.

## 2. Scope discipline

Implement only the current MVP unless a task explicitly says otherwise.

The following are outside the MVP:

- GUI;
- Docker images and deployment;
- automatic denoising or audio repair;
- LLM-based text correction before v0.3 (provider-neutral correction work is now
  explicitly authorized by the accepted v0.3 contract);
- voice-cloning dataset generation;
- automatic speaker recognition from voice biometrics;
- internal drift correction between independently recorded files;
- distributed or multi-GPU processing.

Code should leave clean extension points for these features, but must not introduce speculative infrastructure for them.

## 3. Architectural rule

The project is a **modular monolith**.

The primary dependency direction is:

```text
CLI or future GUI
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
2. `application.py` is the stable application-facing API for both CLI and the future GUI.
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
Broad external-dataset/model/hardware benchmark campaigns are optional under the current owner
scope and must not be imposed as a new project-completion gate.

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
