# Architecture

## 1. Architectural style

The application core is a domain library. The CLI, delivered local browser GUI/web service and native Windows host
are adapters. Integrations with FFmpeg, WhisperX, pyannote, and the filesystem are
infrastructure ports. ADR-0021 and `26-local-web-gui-contract.md` define the web-adapter
boundary without changing the application core.

## 2. Processing pipeline

```mermaid
flowchart TD
    A[Input discovery] --> B[Path normalization]
    B --> C[ffprobe media inspection]
    C --> D[Grouping and source signature]
    D --> E[Existing result lookup]
    E -->|skip| Z[Batch summary]
    E -->|process| F[Channel classification]
    F --> G[Basic audio quality analysis - TODO]
    G --> H[Create WSL workdir]
    H --> I[Extract/decode working audio]
    I --> J{Source topology}
    J -->|single mixed channel| K[ASR]
    K --> L[Word alignment]
    L --> M{Diarization needed?}
    M -->|yes| N[Diarization + reconciliation]
    M -->|no| O[Assign one speaker]
    J -->|split channels/files| P[ASR + alignment per source]
    P --> Q[Assign speaker by source]
    N --> R[Canonical normalization]
    O --> R
    Q --> R
    R --> S[Write partial result]
    S --> T[Validate JSON schema]
    T --> U[Atomic finalization]
    U --> V[Optional exporters]
    V --> W[Cleanup workdir on success]
    W --> Z
```

## 3. Recommended modules

```text
src/ewp_transcripts/
  domain/
    jobs
    sources
    speakers
    transcript
    warnings
    versions
  application/
    inspect_service
    dry_run_service
    transcribe_service
    export_service
    clean_service
    doctor_service
  ports/
    media_probe
    audio_decoder
    asr_backend
    alignment_backend
    diarization_backend
    result_repository
    workdir_repository
  adapters/
    ffmpeg
    whisperx
    pyannote
    filesystem
  exporters/
    txt
    srt
    vtt
    segments_json
  cli/
  config/
  schemas/
```

These names are recommendations, not a public API contract.

## 4. Domain models

### Source

Represents specific input content, not merely a path. Identity is based on SHA-256 plus selected stream and channel information.

### EpisodeJob

One processing unit: either a single file or a group of files sharing one timeline.

### Speaker

Contains a stable `speaker_id` and a display label. They are separate because a label may later be edited without changing references in words and segments.

### Word

The smallest timestamped unit. It records timestamp provenance and optional confidence.

### Segment

A chronologically coherent piece of speech. Canonical segments do not have to match subtitle cues.

### Warning

A structured diagnostic with a code, severity, source, and context.

## 5. Separation of transcription and export

ASR produces a rich canonical model. Exporters are deterministic transformations:

```text
results.json + export_config → TXT/SRT/VTT/segments.json
```

An exporter must not require source audio. This avoids repeated expensive processing and permits subtitle regeneration after cue settings change.

## 6. GPU memory management

The pipeline should load models by stage and release them between stages when required for stable operation. The MVP processes one GPU job at a time.

The JSON result records:

- model identifiers;
- compute type;
- batch size;
- device;
- peak VRAM when available;
- duration of each stage.

## 7. Responsibility boundaries

- FFmpeg handles probing, decoding, and preparation of working audio.
- The channel classifier determines channel topology only; it does not identify people.
- WhisperX handles ASR and word alignment.
- pyannote handles diarization of mixed material.
- The normalizer translates backend output into the project's stable schema.
- Exporters do not depend on ML backends.


## 8. Transcript revision architecture (implemented for v0.2.0)

Transcript correction is a post-ASR application pipeline. It does not reopen source audio.

```mermaid
flowchart TD
    A[Immutable results.json] --> B[revise prepare]
    B --> C[EWP-REVIEW 1]
    C --> D[manual editor]
    D --> E[parse + anchored token alignment]
    E --> F[validate full revision snapshot]
    F --> G[atomic revision_NNN.json]
    A --> H[TranscriptResolver]
    G --> H
    H --> I[EffectiveTranscript]
    I --> J[TXT]
    I --> K[SRT]
    I --> L[VTT]
    I --> M[segments JSON]
```

`EffectiveTranscript` is an in-memory boundary between transcript source selection and
export. Raw canonical content and a corrected revision are resolved into the same runtime
shape. It is not another persisted source-of-truth artifact.

Recommended new internal responsibilities are revision/review models, review parsing and
rendering, deterministic anchored alignment, revision persistence, and transcript
resolution. Exact module names are not public API.

The v0.1 canonical models and `results.schema.json` remain unchanged. In particular, the
revision layer removes the need to mutate `CanonicalSegment.text` or `CanonicalWord.text`
when editorial text changes.

## 9. Revision responsibility boundaries

- the canonical reader verifies the completed base result and its hash;
- the review formatter converts an effective transcript into human-editable text plus
  machine-owned anchors;
- the revision aligner maps edited text back to canonical word anchors and reports
  ambiguity;
- revision storage validates and atomically publishes a full immutable snapshot;
- `TranscriptResolver` verifies revision/base compatibility and produces
  `EffectiveTranscript`;
- exporters consume effective text/timing and never call ASR/diarization backends;
- CLI and delivered GUI/LLM adapters invoke application services rather than implementing
  correction or alignment logic themselves.
