# Documentation Index

Start ongoing work with [TODO](../TODO.md), [WORK_STATUS](../WORK_STATUS.md) and the
[owner scope/current roadmap](99-roadmap-v2.md).
Older milestone procedures and checkpoints retain evidence, not competing current priorities.

## Normative documents

| Document | Scope |
|---|---|
| [01 - Product scope](01-product-scope.md) | Purpose, users, MVP, and exclusions |
| [02 - Requirements](02-requirements.md) | Functional and non-functional requirements with identifiers |
| [03 - Architecture](03-architecture.md) | Modules, pipeline, and responsibility boundaries |
| [04 - Input and grouping](04-input-and-grouping.md) | Files, directories, episode groups, channels, and SHA-256 |
| [05 - CLI specification](05-cli-specification.md) | Commands, options, exit codes, and interactive behavior |
| [06 - Configuration](06-configuration.md) | TOML, presets, and configuration precedence |
| [07 - Results data model](07-results-data-model.md) | Canonical output and partial-state files |
| [08 - Export formats](08-export-formats.md) | TXT, SRT, VTT, and optional segments JSON |
| [09 - State, errors, and logging](09-state-errors-and-logging.md) | Versioning, atomicity, retries, and warnings |
| [10 - WSL2 installation](10-wsl2-installation.md) | Reference environment, CUDA, models, and offline setup |
| [11 - Security and privacy](11-security-and-privacy.md) | Privacy, tokens, temporary files, and network use |
| [12 - Testing and acceptance](12-testing-and-acceptance.md) | Application and audio-material checklists |
| [13 - Transcript revisions](13-transcript-revisions.md) | v0.2.0 manual correction, review format, revision snapshots, and effective transcript |
| [14 - Dependency baseline](14-dependency-baseline.md) | Verified environment starting point |
| [15 - Glossary](15-glossary.md) | Standardized terminology |
| [16 - Risk register](16-risk-register.md) | Technical risks and mitigations |
| [17 - Definition of Done](17-definition-of-done-mvp.md) | MVP completion criteria |
| [18 - Quality evaluation](18-quality-evaluation.md) | Manifest-driven WER/CER reports and review diffs |
| [20 - MVP requirements traceability](20-mvp-requirements-traceability.md) | Requirement-by-requirement implementation, test, evidence, and deferral status |
| [21 - v0.2.0 transcript revision plan](21-v0.2.0-transcript-revision-plan.md) | Consolidated implementation plan and future-compatibility decisions |
| [22 - v0.3 automated correction](22-v0.3-automated-correction.md) | Provider-neutral correction, consent, chunking, provenance, benchmark, and acceptance contract |
| [23 - v0.4 translation contract](23-v0.4-translation-contract.md) | Bidirectional manual-first translation artifact, workflow, and benchmarks |
| [25 - Warning and error catalogue](25-warning-error-catalog.md) | Stable diagnostic meanings, safety implications, and operator actions |
| [26 - Local browser GUI contract](26-local-web-gui-contract.md) | Shared native Windows/browser interface, security, workflows, and implementation slices |
| [29 - Guided workflow and prototype comparison](29-guided-workflow-and-prototype.md) | Numbered stage guides, review usability and prototype reconciliation |
| [GUI step instructions](gui/README.md) | Full instructions for every workflow stage and supporting tool |
| [99 - Post-0.1 roadmap](99-roadmap-v2.md) | Current owner release, security/privacy, distribution and bounded post-release backlog |
| [Sources](SOURCES.md) | Official technical sources used by the specification |

## Current installation and platform guidance

- [Installer size review](INSTALLER_SIZE.md): measured payload inventory, compression and online-bootstrap boundary.
- [Hardware recommendations](HARDWARE.md): tested NVIDIA reference, practical VRAM/RAM guidance,
  exact pinned-library/driver compatibility and cloud guidance for unsupported/low-VRAM cards.

- [AMD acceleration (experimental)](AMD_EXPERIMENTAL.md): implemented Windows ASR adapter,
  CPU alignment/diarization, detection/acknowledgement, pinned dependencies and untested GPU boundary.
- [Native Windows application](NATIVE_WINDOWS_APP.md): window preferences, owned processes,
  safe closing and platform qualification.
- [EN installation/update/removal](gui/installation.md) and [PL instructions](gui/pl/installation.md).
- [Per-version release policy](RELEASE_POLICY.md) and [release checklist](RELEASE_CHECKLIST.md).
- [Security/privacy review plan](SECURITY_REVIEW_PLAN.md): local EN report and owner approval first, then framework applicability/mapping; privacy policy gap.
- [Independent MSIX/Store research plan](MSIX_STORE_PLAN.md) and [versioned release index](../releases/README.md).
- [Version and delivery policy](VERSIONING.md), [distribution plan](DISTRIBUTION_PLAN.md)
  and [GitHub Actions usage/costs](GITHUB_ACTIONS.md).
- [Current documentation audit](DOCUMENTATION_AUDIT.md) and [0.26.1 qualification](checkpoints/2026-11-26-release-readiness-evidence.json) and
  [remaining action plan/backlog](99-roadmap-v2.md).

## Architecture Decision Records

- [ADR-0001: WSL2 as the reference environment](adr/0001-wsl2-reference-environment.md)
- [ADR-0002: Canonical results JSON](adr/0002-canonical-results-json.md)
- [ADR-0003: Conservative channel classification](adr/0003-channel-classification.md)
- [ADR-0004: SHA-256 and non-destructive versioning](adr/0004-hashing-and-versioning.md)
- [ADR-0005: No audio repair in the MVP](adr/0005-no-audio-repair-in-mvp.md)
- [ADR-0006: Interface-independent application core](adr/0006-interface-independent-core.md)
- [ADR-0007: Accurate-preset ASR model selection](adr/0007-accurate-preset-asr-model.md)
- [ADR-0008: Mixed-source speaker diarization](adr/0008-mixed-source-diarization.md)
- [ADR-0009: Long-duration operational baseline](adr/0009-long-duration-operational-baseline.md)
- [ADR-0010: Isolated wheel installation procedure](adr/0010-isolated-wheel-installation.md)
- [ADR-0011: Language-specific offline alignment selection](adr/0011-multilingual-alignment-selection.md)
- [ADR-0012: Explicit group identity and validation contract](adr/0012-explicit-group-contract.md)
- [ADR-0013: Release observability and speaker order](adr/0013-release-observability-and-speaker-order.md)
- [ADR-0014: Dataset-dependent quality gates](adr/0014-dataset-dependent-quality-gates.md)
- [ADR-0015: MVP input format matrix](adr/0015-input-format-matrix.md)
- [ADR-0016: Subtitle readability and correction boundary](adr/0016-subtitle-readability-and-correction-boundary.md)
- [ADR-0017: Content-aware directory discovery after MVP](adr/0017-content-aware-directory-discovery.md)
- [ADR-0018: Synthetic fast-speech and recorder-noise acceptance](adr/0018-fast-noisy-audio-acceptance.md)
- [ADR-0019: Fresh Ubuntu 24.04 WSL installation](adr/0019-fresh-wsl-installation.md)
- [ADR-0020: Versioned full-snapshot transcript revisions](adr/0020-versioned-transcript-revisions.md) — accepted for v0.2.0
- [ADR-0021: One local browser GUI across deployment environments](adr/0021-local-browser-gui.md)

## Implementation guidance

- [Architecture and coding rules](ARCHITECTURE_AND_CODING_RULES.md)
- [Archived MVP planning documents](../archive/mvp-planning/README.md)
- [Testing strategy](TESTING_STRATEGY.md)
- [WSL setup and verification](../WSL%20config/README.md)

## Machine-readable artifacts

- `schemas/results.schema.json` - JSON Schema for canonical results.
- `schemas/segments.schema.json` - JSON Schema for the derived segment export.
- `schemas/revision.schema.json` - v0.2.0 JSON Schema for immutable transcript revisions.
- `schemas/ewp-review.schema.md` - `EWP-REVIEW 1` text-format grammar and validation contract.
- `examples/config.example.toml` - complete example configuration.
- `examples/results.example.json` - minimal valid result.
- `examples/segments.example.json` - example sentence-level export.
- `examples/revision.example.json` - revision snapshot example.
- `examples/review.example.txt` - human-editable review example.

- [Queue progress and ETA assessment](30-queue-progress-and-eta.md) — current evidence, event design and calibration gates.

- [Artist review package](31-artist-review-package.md) — offline frontend and asset inventory.
- [Runtime log notes](32-runtime-log-notes.md) — exact reported ONNX/VAD/Wav2Vec2 messages.
