# Testing Strategy

Owner revision2026-11-27: [current roadmap](99-roadmap-v2.md) and [release checklist](RELEASE_CHECKLIST.md)
override older research proposals below. Comparative/human-vs-machine, translation/public-corpus/
universal-dictionary/model/hardware benchmark programs are removed from the active plan. Existing
tools/evidence remain; no new campaign is implied. Full profile transfer and actual browser200%
zoom enter upcoming-release scenarios. Physical AMD/other NVIDIA tests are unavailable/unplanned;
annotated-corpus quality is deferred without date. Screenshots await artist integration/interface tests.

Owner scope update (2026-11-20): the current [roadmap scope](99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20)
controls required work. The old comparative correction/translation/public-corpus/general-dictionary/model/hardware benchmark
programs are removed from the active plan by the owner revision2026-11-27. Existing tooling/evidence
remains; annotated-quality deferrals remain unscheduled, not project completion gates. Existing
unit/integration, security, data-lineage and packaging checks remain required; preserve all accepted
historical evidence. This is a practical podcast/recording workflow tool.

## 1. Goals

The testing system must validate four distinct concerns:

1. software correctness independent of ML quality;
2. integration with the local operating environment and FFmpeg;
3. functional correctness of the complete GPU pipeline;
4. retain existing quality evidence and explicit annotated-material deferrals; a new public-dataset
   benchmark program is not in the current owner plan.

Local quality checks and the documented standard public GitHub Actions Windows packaging/lifecycle checks have distinct roles; see GITHUB_ACTIONS.md. Production release attestations/enforcement are planned, not yet implemented.

## 2. Test environments

### Development WSL instance

Used for normal implementation and fast feedback. Contains the editable repository, local `.venv`, model cache, and optional local dataset checkout.

### Clean-room WSL instance or VM

Used periodically and before releases. It should:

- start from a documented base image;
- clone the repository from scratch;
- run `uv sync --locked`;
- use an independent virtual environment;
- install and test the built wheel, not only an editable checkout;
- use already authorized suitable reference material when a relevant regression needs it;
- validate offline operation after models are prepared.

This environment replaces the installation/reproducibility role normally covered by hosted CI.

## 3. Test categories

### 3.1 Static and repository checks

Purpose: catch cheap errors before runtime tests.

Scope:

- Ruff lint;
- Ruff formatting check;
- mypy type checking;
- TOML parsing;
- JSON parsing;
- JSON Schema validation of repository examples;
- package build;
- import smoke test;
- forbidden-file/secret checks when practical.

Command target:

```bash
make check
```

Expected runtime: seconds to a few minutes.

### 3.2 Unit tests

Purpose: validate deterministic logic without external processes or models.

Must not require:

- FFmpeg;
- CUDA;
- WhisperX;
- pyannote;
- network access;
- external dataset.

Coverage:

- configuration defaults, precedence, and validation;
- path normalization;
- file scanning and non-recursive defaults;
- episode grouping and speaker suffix rules;
- SHA-256 and episode signature;
- duration-threshold policy;
- version suffix allocation;
- speaker ID/label normalization;
- channel classifier logic using synthetic arrays or generated audio;
- sentence layout;
- subtitle cue generation;
- TXT/SRT/VTT/segments serialization;
- partial/failed/completed result transitions;
- atomic-write behavior where testable;
- controlled errors and warning codes.

Expected runtime: normally under one minute.

### 3.3 Integration tests without ML models

Purpose: validate real boundaries while keeping tests fast and deterministic.

Dependencies:

- FFmpeg/ffprobe;
- real temporary filesystem;
- fake transcription and diarization engines.

Coverage:

- inspect on actual fixture files;
- media stream and track detection;
- audio extraction and channel splitting;
- dry-run planning;
- output-directory defaults;
- existing-result detection;
- duration/sample-rate group validation;
- full mocked pipeline through canonical result and exports;
- cleanup behavior;
- cancellation handling where feasible.

Command target:

```bash
make test-integration
```

Expected runtime: a few minutes.

### 3.4 GPU smoke tests

Purpose: prove that the installed dependency stack works on the target workstation.

Coverage on one or more short files:

- torch sees the NVIDIA GPU;
- WhisperX model loads;
- Polish transcription runs;
- English mode runs on an English sample;
- word alignment runs;
- pyannote model loads when needed;
- offline model loading works after setup;
- canonical result passes schema validation;
- TXT/SRT/VTT generation succeeds;
- GPU memory is released sufficiently for subsequent cases.

Marker:

```text
gpu
```

Suggested command:

```bash
make test-gpu
```

Expected runtime: several minutes.

### 3.5 End-to-end functional tests

Purpose: validate the real application behavior against representative inputs.

These tests use the external public dataset and the full CLI/application pipeline.

Required cases:

- one Polish speaker in mono;
- multiple Polish speakers in mixed mono;
- one speaker with occasional English terms;
- English recording;
- dual mono;
- split speakers in stereo;
- multiple synchronized mono files, one speaker per file;
- optional overlap case;
- existing matching SHA skip;
- forced `_v002` generation;
- failed/partial restart behavior;
- non-recursive and recursive directory modes;
- optional segments export;
- export regeneration without ASR.

Markers:

```text
e2e
gpu
```

Suggested command:

```bash
make test-e2e
```

### 3.6 Quality evaluation tests

Purpose: compare models and settings, not merely check that code runs.

Reference data must be manually corrected. A cloud transcription model may be recorded as a comparison baseline, but it is not ground truth.

Metrics:

#### Text quality

- Word Error Rate (WER);
- Character Error Rate (CER);
- optional normalized WER;
- separate error counts for names, numbers, technical terms, and English insertions.

#### Speaker quality

Where manually annotated:

- Diarization Error Rate (DER);
- speaker confusion rate;
- missed speaker changes;
- false speaker changes;
- overlap detection quality.

#### Timestamp quality

For selected manually aligned words/segments:

- mean absolute start-time error;
- mean absolute end-time error;
- median and 95th-percentile timing error;
- percentage within 50 ms, 100 ms, 250 ms, and 500 ms;
- cue coverage and ordering validity.

#### Subtitle quality

Automated checks:

- no invalid or overlapping cue ordering unless deliberately supported;
- maximum line count;
- maximum configured line length;
- characters-per-second violations;
- cue duration violations;
- speaker-label placement;
- valid SRT/VTT syntax.

Manual review:

- natural linguistic breaks;
- readability at normal playback speed;
- no orphan words;
- no misleading speaker attribution.

#### Performance

- wall-clock time;
- real-time factor;
- peak GPU VRAM;
- peak system RAM;
- temporary disk usage;
- model-load time;
- per-stage timing;
- success of sequential jobs without process restart.

These tests may generate reports rather than pass/fail on every metric during early development. Before MVP release, acceptance thresholds should be fixed for the reference preset.

### 3.7 Long-duration and soak tests

Purpose: validate technical stability for realistic and extreme durations.

Dataset durations should include approximately:

- several minutes;
- 30–60 minutes;
- 90 minutes;
- up to 3 hours.

Coverage:

- no unbounded memory growth;
- acceptable temporary-disk use;
- successful final atomic result;
- correct cleanup after success;
- retained workdir after failure;
- interruption and restart from the beginning;
- multiple sequential episodes;
- stable output ordering;
- no corruption of previous results;
- offline execution.

Marker:

```text
long
```

Suggested command:

```bash
make test-long
```

These tests are not part of the normal edit-run loop.

## 4. External public dataset

The dataset should be maintained outside the application repository and made available publicly under a clear license.

The application test suite locates it through:

```bash
export EWP_TRANSCRIPTS_TEST_DATASET=/path/to/ewp-transcripts-testdata
```

Recommended dataset layout:

```text
ewp-transcripts-testdata/
├── README.md
├── LICENSE
├── manifest.toml
├── audio/
├── references/
└── cases/
```

The manifest should describe for each case:

- stable case ID;
- source files;
- SHA-256 values;
- language;
- expected channel mode;
- expected speaker count when known;
- expected grouping;
- reference transcript path;
- optional speaker/timestamp annotation path;
- expected warnings;
- recommended test markers;
- approximate runtime;
- licensing/provenance notes.

The test suite must not depend on arbitrary filename discovery inside the dataset. It should read the manifest.

Once multiple manually verified transcripts exist, add a corpus comparison runner to the local test suite. It should execute selected presets against manifest cases, apply the documented normalization policy, produce machine-readable per-case and aggregate WER/CER, and retain a human-readable word-diff report for error review. Candidate output must always be compared with an independent manually verified reference, never with another model's uncorrected transcript.

The manifest-driven lexical evaluator is documented in
[`18-quality-evaluation.md`](18-quality-evaluation.md). Its JSON report records strict
reference and hypothesis provenance plus per-case, macro, and micro results. The
error-only word diff remains external because it contains transcript-derived content.

The Phase 0 lexical scorer is [`../tools/phase0_score_transcript.py`](../tools/phase0_score_transcript.py). Its `ewp-phase0-lexical-v1` normalization joins line-wrapped sentences, applies Unicode NFC and case folding, replaces Unicode punctuation with spaces, and collapses whitespace. It preserves Polish diacritics, filler words, repetitions, symbols, and the original digit-versus-written-number form. Primary WER/CER therefore ignores capitalization, punctuation, and sentence layout without erasing lexical differences. For a `.json` hypothesis, the scorer concatenates ordered `segments[].text` values and ignores timestamps, words, confidence values, and speaker metadata. The scorer never prints normalized or source transcript text.

## 5. Synthetic repository fixtures

Small generated fixtures remain inside the application repository for deterministic mechanics testing.

Generate fixtures for:

- mono silence;
- mono tone;
- dual mono;
- clearly distinct stereo channels;
- near-identical channels;
- mismatched durations around 100 ms and 500 ms thresholds;
- mismatched sample rates;
- clipping;

Synthetic tones cannot validate ASR quality and must not be used for quality metrics.

## 6. Test markers

Recommended pytest markers:

```text
unit
integration
gpu
e2e
quality
benchmark
long
offline
slow
```

Marker behavior must be documented in `pyproject.toml` and `tests/e2e/README.md`.

Default `pytest` should exclude tests requiring external models, the external dataset, or long runtimes.

## 7. Local commands

Recommended targets:

```bash
make check              # static checks, unit tests, schemas, build
make test               # unit tests
make test-integration   # FFmpeg/filesystem tests without ML
make test-gpu           # short GPU dependency/pipeline smoke tests
make test-e2e           # full representative dataset cases
make test-quality       # metrics and comparison report
make test-long          # 60-minute to 3-hour stability cases
make release-check      # complete release gate
```

`make release-check` should accept options to skip long tests during development, but a final MVP candidate must run the full required matrix.

## 8. Test doubles

Use fake engine implementations conforming to `engines/protocols.py`. They should return deterministic words, timestamps, speakers, and overlaps.

Do not mock internal pure functions unnecessarily. Mock only expensive or external boundaries:

- transcription engine;
- diarization engine;
- subprocess execution in unit tests;
- time or failure injection when testing partial/failed states.

Integration tests should use real FFmpeg.

## 9. Acceptance gates by change type

### Documentation-only change

- documentation links/format validation where available.

### Pure domain/config/export change

- `make check`.

### Filesystem, discovery, FFmpeg, storage, or pipeline change

- `make check`;
- `make test-integration`.

### Engine, CUDA, alignment, diarization, or model configuration change

- all previous gates;
- `make test-gpu`;
- affected E2E cases;
- quality comparison if output may change.

### Release candidate

- clean-room installation;
- full `make release-check`;
- required E2E matrix;
- long-duration tests;
- offline test;
- manual subtitle review on selected cases;
- results and metric report archived with the release notes.

## 10. MVP test completion criteria

Testing is sufficient for MVP only when:

- all static, unit, integration, and schema tests pass;
- the full target GPU pipeline runs from a clean environment;
- every required input topology has at least one E2E case;
- skip/force/versioning behavior is verified;
- partial/failed/cancelled behavior is verified;
- exports regenerate from canonical JSON without ASR;
- long files complete without corruption or unbounded resource growth;
- offline transcription works after explicit model setup;
- quality metrics are measured against manually corrected references;
- subtitle output passes automated constraints and manual readability review;
- the default accurate preset has documented time, VRAM, RAM, and quality results on the target RTX 3090 workstation.
