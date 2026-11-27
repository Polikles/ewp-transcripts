# Architecture and Coding Rules

## 1. Architectural style

The MVP is a modular monolith with explicit internal boundaries. The design optimizes for:

- maintainability by a small team or single maintainer;
- deterministic local execution;
- testability without loading GPU models;
- CLI and delivered browser/native Windows GUI using the same application API;
- deployment-independent core (Docker is outside selected scope);
- replaceable external ML engines.

It does not optimize for microservices, distributed execution, or multiple independently released packages.

## 2. Layers

### Interface layer

Current interfaces: CLI and the shared local GUI, embedded in WPF/WebView2 on managed Windows.

Responsibilities:

- collect user input;
- select interactive/non-interactive behavior;
- present progress and diagnostics;
- map application errors to human-readable messages;
- map outcomes to process exit codes or GUI state.

Interfaces must not implement domain behavior.

### Application layer

`application.py` exposes use cases and is the stable integration point for all interfaces.

Responsibilities:

- accept typed requests;
- resolve the effective configuration;
- invoke inspection, planning, transcription, revision, export, or cleanup;
- return typed outcomes;
- enforce use-case-level policy.

### Orchestration layer

`pipeline.py` coordinates processing stages. It owns sequence and branching, not the implementation details of each technical operation.

### Domain layer

`domain/` and `speakers.py` contain application concepts, invariants, and typed data independent from CLI, GUI, FFmpeg, WhisperX, and pyannote.

### Infrastructure/adapters

- `media/` wraps FFmpeg/ffprobe;
- `engines/` wraps WhisperX and pyannote;
- `storage.py` wraps canonical file persistence;
- `workdirs.py` wraps temporary filesystem lifecycle;
- `exporters/` wraps derived formats.

## 3. Dependency rules

Allowed direction:

```text
cli.py -----------> application.py
future gui/ ------> application.py
application.py ---> pipeline.py and domain services
pipeline.py ------> discovery/media/engines/speakers/storage/workdirs/exporters
adapters ---------> domain models
```

Forbidden dependencies:

- domain importing CLI or GUI code;
- exporters importing WhisperX or pyannote;
- CLI importing WhisperX or calling FFmpeg directly;
- engine adapters writing final output files;
- storage parsing raw WhisperX results;
- GUI invoking CLI commands as subprocesses;
- module-level model loading.

## 4. Canonical data flow

External engine output must be normalized immediately:

```text
WhisperX-specific result
        |
        v
engines/whisperx.py
        |
        v
domain Word/Segment models
        |
        v
speaker attribution and timeline merge
        |
        v
canonical Result model
        |
        +--> results.json
        +--> TXT
        +--> SRT
        +--> VTT
        +--> optional segments.json
```

No downstream module should depend on WhisperX or pyannote internal structures.

## 5. Processing modes

### Inspect

May use filesystem, hashing, ffprobe, and channel analysis. Must not load ASR/diarization models or modify source files.

### Dry run

May perform everything required to produce an execution plan, including existing-output detection and version selection. Must not create work audio or run ML engines.

### Transcribe

Runs the full pipeline and always produces a canonical result on success.

### Export

Reads an existing canonical result and produces selected derived outputs. Must not load models or reopen source audio.

### Clean

Operates only on known workdir locations and failed/partial job artifacts. Must never delete final results, configuration, model caches, or arbitrary user paths.

### Doctor

Diagnoses Python, FFmpeg, CUDA, GPU, model availability, token configuration, and writable paths. It must avoid model downloads and should avoid loading full models unless an explicit deep-check option is used.

## 6. Configuration

Use one resolved typed configuration object throughout a run. Avoid passing many unrelated primitive parameters.

Required properties:

- values from packaged defaults, optional user TOML, optional project TOML, and CLI overrides;
- deterministic precedence;
- full validation before expensive processing;
- effective configuration serialized into the canonical result;
- secrets excluded from serialization and logs;
- paths represented as `pathlib.Path` internally;
- environment variables supported for secrets and container-friendly paths.

## 7. Filesystem and persistence

- Original media is immutable.
- Work files live in a configured work root on the Linux filesystem.
- Final outputs go only to the resolved output directory.
- `*_results.partial.json` represents an active/incomplete run.
- `*_results.failed.json` represents a failed or cancelled run and retains diagnostics.
- The final canonical file is created through atomic rename only after successful completion.
- A matching completed result is identified by source SHA-256 values and episode signature, not filename alone.
- Version suffixes are allocated as one output-set version, not separately per format.

## 8. Speaker model

Keep internal identity separate from display text:

```text
speaker_id: stable technical identifier within the result
speaker_label: human-readable label
speaker_source: explicit, filename, channel metadata, diarization, or default
```

Rules:

- grouped source suffixes identify speakers only under the documented grouping convention;
- for a single file, a filename suffix is used only when speaker count is explicitly one;
- diarization clusters are normalized by chronological first appearance;
- multi-file and split-channel sources use deterministic source-based attribution;
- automatic voice recognition is not implemented.

## 9. Channel behavior

Supported classifications:

- mono;
- dual mono;
- split speakers;
- mixed stereo;
- ambiguous.

MVP policy:

- high-confidence dual mono: use one channel;
- high-confidence split speakers: transcribe channels independently and merge timelines;
- ambiguous stereo: warn and use one channel;
- explicit `channel-mode` overrides automatic classification;
- no automatic cross-channel transcript deduplication in the MVP.

## 10. External processes

For FFmpeg and ffprobe:

- always use `subprocess` with an argument sequence;
- never use `shell=True`;
- capture stdout/stderr;
- include the executable exit code and a sanitized error summary in controlled exceptions;
- support cancellation/termination;
- avoid exposing secrets in command lines;
- use deterministic working-format parameters.

## 11. External ML engines

- Import lazily.
- Keep engine configuration explicit.
- Record exact model identifiers and relevant library versions in canonical results.
- Keep model download/setup separate from transcription.
- Support offline execution after setup.
- Release model references and GPU memory between large stages when safe.
- Fail with actionable messages when required models are missing.
- Make engine adapters replaceable in tests through protocols or simple dependency injection.

## 12. Logging and diagnostics

- Use stable warning/error codes in domain results.
- Human-readable text may change; codes should remain stable.
- Do not log full transcripts by default.
- Do not log tokens or authentication headers.
- Include stage, source/episode identifier, and relevant sanitized metadata.
- Preserve enough diagnostics in failed results to reproduce the failure.

## 13. Public compatibility

Treat these as public contracts:

- CLI command and option names;
- exit-code meanings;
- JSON Schema and `schema_version`;
- result and export filename conventions;
- configuration keys;
- warning codes where documented.

Breaking changes require explicit documentation and versioning.

## 14. GUI readiness

The delivered GUI uses these existing boundaries:

- adding a `gui/` package;
- creating request objects for `application.py`;
- mapping typed progress/events to widgets;
- executing long-running operations outside the UI thread;
- displaying existing structured diagnostics.

GUI readiness does not require adding GUI abstractions to the MVP. It requires keeping terminal presentation out of the application and pipeline layers.

## 15. Historical Docker extension guidance (not selected work)

The future Docker image should be able to configure:

- input mounts;
- output mounts;
- model cache mount;
- workdir mount;
- Hugging Face token environment variable;
- non-interactive mode;
- GPU access.

Do not hardcode WSL-specific paths in core logic. WSL is the development/runtime baseline, but all paths must be configuration-driven.

## 16. Simplicity rule

Prefer the smallest module structure that preserves the boundaries above. Add a new package or abstraction only when it removes real duplication, isolates an optional dependency, creates a stable contract, or improves independent testability.


## 17. Transcript revision boundary (implemented for v0.2.0)

Transcript revision follows the same interface-independent rules as transcription. CLI,
GUI, and LLM adapters call application services; none may implement their
own correction model or token alignment.

Persisted data flow becomes:

```text
canonical Result -> results.json (immutable)
                         |
                         +--> raw TranscriptResolver --------+
                         |                                   |
                         +--> revision prepare/apply          v
                                  |                    EffectiveTranscript
                                  v                           |
                         revision_NNN.json -------------------+
                                                              |
                                                  TXT/SRT/VTT/segments
```

Rules:

- `results.schema.json` is not changed merely to support editorial correction;
- a revision is a complete immutable snapshot linked to the exact base-result SHA-256;
- `EffectiveTranscript` is runtime-only and must not become a third authoritative file;
- exporters consume one effective transcript interface instead of independently choosing
  canonical segment text versus word text;
- review parsing/alignment and revision persistence belong below the interface layer;
- normal revision does not load WhisperX, pyannote, alignment models, or source audio;
- revision and review schemas/formats are public compatibility contracts and require
  explicit versioning for breaking changes;
- external editors are executed without a shell;
- future cloud LLM correction is an explicit opt-in adapter and does not weaken the
  local-only v0.2.0 contract.
