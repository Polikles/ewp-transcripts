# Product Scope

## 1. Purpose

EWP-transcripts generates accurate local transcripts, word timestamps, speaker assignments, and readable subtitles from edited podcast and training recordings.

The application is a post-production tool. Input material is expected to follow this workflow:

```text
audio recording
        ↓
editing all tracks on a shared timeline
        ↓
exporting one or more audio files
        ↓
EWP Transcriber
        ↓
results.json → TXT / SRT / VTT / segments.json
```

## 2. Target user

A technical user working locally on Windows with WSL2 running Ubuntu and an NVIDIA GPU. The MVP version is a CLI application; a potential GUI will use the same application core. There is a plan of creating a containerized version for less technical users. Same stack should also work under bare-metal Ubuntu

## 3. MVP scope

The MVP includes:

- a single audio file;
- directory processing (by default without recursion);
- explicitly enabled recursion;
- grouping several mono files that represent one episode;
- classification of mono, dual mono, split-speaker stereo, mixed stereo, and ambiguous stereo;
- WhisperX transcription;
- word-level forced alignment;
- diarization of mixed recordings;
- speaker labels from explicit parameters, filenames, or track/channel metadata;
- canonical `results.json` output;
- optional `segments.json` export (word/phrase-level timestamps, e.g. for creation of voice-clone and voice-recognision dataset);
- TXT, SRT, and VTT exports;
- skipping completed duplicates using SHA-256-based signatures;
- versioned results when `--force` is used;
- offline operation after models have been downloaded explicitly;
- working files stored in the WSL filesystem;
- `inspect`, `dry-run`, `transcribe`, `export`, `doctor`, and `clean` operations.

## 4. Outside the MVP scope (potentially in later versions)

- interactive audio-track selection for video with multiple audio streams (single-audio-stream
  video ingestion is implemented in the current GUI increment);
- biometric identification of people from their voices (after extracting enough samples from previously analyzed recordings);
- automatic audio repair based on diagnostic warnings;
- automatic denoising, normalization, or audio repair;
- LLM-based transcript correction;
- GUI transcript editing;
- colored or burned-in subtitles;
- parallel jobs on one GPU;
- dockerized version of the app;
- presets to run the app on lower-tier PCs [including CPU-only transcripts];
- adding other language versions of the program (default is English).

## 5. Input assumptions

- Files belonging to one episode are exported from a shared timeline.
- Files in one group have the same sample rate and practically identical duration.
- Each separate file in a group contains one speaker.
- Crosstalk between separate speaker tracks has been removed or is minimal.
- Input is usually denoised and normalized before transcription.
- Most recordings are in Polish with occasional short English phrases.
- The typical speaker count is one or two; three speakers are uncommon.
- A typical file is no longer than 60 minutes, but this is a recommendation rather than a technical limit.

## 6. Quality priorities

In descending order:

1. no data loss or overwriting;
2. text accuracy;
3. timestamp accuracy;
4. correct speaker assignment;
5. subtitle readability;
6. result reproducibility;
7. performance.

The application may run more slowly when this improves quality, provided the reference "quality" preset remains within 24 GB of VRAM on the reference hardware.


## 7. Implemented v0.2.0 MVP increment

The next internal MVP increment adds manual transcript revision while preserving the
v0.1 transcription contract. Implemented additions are:

- immutable full-snapshot transcript revisions linked to canonical results;
- human-readable `EWP-REVIEW 1` manual correction;
- single-file and batch prepare/apply workflows;
- preview and external-editor workflows;
- correction of text, punctuation/sentence boundaries, and existing-speaker attribution;
- revision-aware TXT/SRT/VTT/segments regeneration without ASR;
- provenance, summary statistics, and optional detailed audit.

LLM-based correction, translation, automated translation, and GUI remain outside v0.2.0.
They are sequenced in `99-roadmap-v2.md`.
