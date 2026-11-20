# MVP requirements traceability

Current scope is governed by the [2026-11-20 owner decisions](99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20).
Broad research metrics, hardware presets and ETA accuracy studies are optional, not current
completion gates. Preserve earlier accepted results; current owner acceptance excludes a full
profile exchange and latest restart recovery, with browser/palette behavior accepted.

This matrix audits every normative requirement against production code, automated
tests, and accepted external evidence. It is a release-control document, not a claim
that the unchecked MVP gates are complete.

Status meanings:

- **verified** — implemented and covered by automated tests or accepted external evidence;
- **implemented** — implemented, but an explicitly listed external validation remains;
- **deferred** — intentionally moved beyond MVP by an accepted ADR;
- **gap** — the current implementation does not yet satisfy the literal requirement;
- **planned** — accepted target for the next MVP increment and intentionally not yet implemented.

## Functional requirements

| Requirement | Status | Implementation and evidence |
| --- | --- | --- |
| FR-A01, FR-A02, FR-A03 | verified | `discovery.py`; discovery and recursive CLI tests. |
| FR-A04 | verified | `media/probe.py`; media-probe tests and ADR-0015 format matrix. |
| FR-A05 | deferred | Direct files are content-probed regardless of suffix. Content-aware inclusion of arbitrary-extension directory entries is deferred by ADR-0017; configured standard audio formats remain supported and externally validated. |
| FR-A07 | verified | Windows/WSL/POSIX normalization tests in `test_discovery.py`. |
| FR-A08, FR-A08.1, FR-A08.2, FR-A08.3 | verified | Symlink rejection/skip tests across discovery, grouping, and CLI behavior. |
| FR-B00, FR-B01, FR-B02, FR-B03 | verified | `group_discovered_files`; grouping tests cover suffix and speaker-count semantics. |
| FR-B04 | verified | Explicit `--group` contract, tests, and ADR-0012 external validation. |
| FR-B05, FR-B06, FR-B07 | verified | `inspect_episode`; sample-rate and duration-threshold tests, including the dedicated override. |
| FR-B08 | verified | Application-level dry-run/transcription ambiguity guard, coded error, same-stem regression test, and real WSL MP3/WAV discovery evidence. |
| FR-C00, FR-C01, FR-C02, FR-C03, FR-C04 | verified | Channel analysis/classification tests and Phase 2/7/10 external matrices. Enum values use hyphens at the CLI boundary and correspond to the underscore names in this requirement. |
| FR-C05, FR-C06, FR-C07 | verified | Configuration, stream-planning, and pipeline tests; Phase 7/8 evidence. |
| FR-C08 | verified | `inspection.py` applies explicit, filename, selected-stream title, then default priority; focused provenance/signature tests. |
| FR-C09 | verified | Chronological reconciliation tests and ADR-0013 release evidence. |
| FR-D00, FR-D01, FR-D02 | verified | Language configuration/CLI tests and ADR-0011. English execution is supported; corpus accuracy remains deferred by ADR-0014. |
| FR-D03 | verified | ASR, alignment, diarization adapters and pipeline tests; Phase 7/8 production runs. |
| FR-D04, FR-D05 | verified | Canonical normalization tests cover aligned, interpolated, fallback, and untimed words. |
| FR-D06 | verified | Diarization reconciliation and canonical overlap tests; Phase 8 overlap evidence. |
| FR-D07 | verified | Canonical pipeline contains no LLM rewriting; lexical/manual reviews confirm faithful wording. |
| FR-E00 | verified | Canonical Pydantic model, JSON Schema validation, finalization tests, and all accepted production runs. |
| FR-E01, FR-E02 | verified | Segments and transcript exporters plus exporter/service tests. |
| FR-E03, FR-E04, FR-E05 | verified | Subtitle partition/label tests and accepted short/long YouTube reviews in ADR-0016. |
| FR-E06, FR-E07, FR-E08 | verified | Offline export service, canonical schema types, UTF-8 writers, and export tests. |
| FR-F00, FR-F01 | verified | Streaming fingerprints and deterministic signature tests. |
| FR-F02, FR-F03, FR-F04, FR-F05 | verified | Storage planning/version tests and duplicate/force external runbooks. |
| FR-F06, FR-F07, FR-F08 | verified | Reservation/finalization/state tests, including corrupt partial state and restart evidence. |
| FR-F09 | verified | Batch application tests and mixed-success Phase 6 evidence. |
| FR-G00, FR-G01, FR-G02, FR-G03 | verified | Application boundary and CLI tests; inspect/dry-run/export/transcribe runbooks. |
| FR-G04 | verified | Doctor tests and release readiness runbook, including secret scans. |
| FR-G05 | verified | Marker-verified workdir cleanup tests and Phase 9 privacy cleanup evidence. |
| FR-G06 | verified | Non-interactive CLI tests and unattended batch/interruption runs. |
| FR-H00, FR-H01 | verified | Packaging does not prepare models; missing-model tests and setup guidance validation. |
| FR-H02 | verified | `doctor.py` reads only `HF_TOKEN` and sanitizes its value. Runtime uses pinned local snapshots and does not pass a token. |
| FR-H03 | verified | Offline adapter tests and isolated installed-wheel transcription in ADR-0010. |
| FR-I00, FR-I01, FR-I02 | verified | Warning-only channel/quality analyzers and clipping, level, imbalance, and silence tests. |

## Non-functional requirements

| Requirement | Status | Implementation and evidence |
| --- | --- | --- |
| NFR-001 | verified | Local adapters, offline tests, and network-disabled production runbooks. |
| NFR-002 | verified | Locked dependencies and effective configuration stored in canonical results. |
| NFR-003 | verified | P9-04 processed 151 minutes without OOM on RTX 3090; ADR-0009. |
| NFR-004 | verified | Atomic state/finalization tests, ENOSPC/EIO coverage, and interruption recovery. |
| NFR-005 | verified | Deterministic grouping/version/export tests and duplicate replay evidence. |
| NFR-006 | verified | CLI-independent application boundary; ADR-0006. |
| NFR-007 | verified | Protocol-backed FFmpeg/ASR/alignment/diarization test doubles. |
| NFR-008 | verified | Structured logging, summaries, stage timing and VRAM evidence; ADR-0013. |
| NFR-009 | verified | Secret sanitization tests and doctor/missing-model external scans. |
| NFR-010 | verified | Unicode, spaces, Windows and WSL path tests. |
| NFR-011 | verified | Versioned outputs, source immutability, safe cleanup, and replay tests. |
| NFR-012 | verified | Versioned canonical schema and strict compatible-reader tests. |

## Open release work resulting from this audit

1. Keep dataset-dependent English, three-speaker, timestamp, and DER/JER accuracy gates deferred under
   ADR-0014 until annotated archive-derived references exist.


## v0.2.0 implemented transcript-revision requirements

Their normative definitions are in `02-requirements.md` and `13-transcript-revisions.md`.

| Requirement | Status | Planned implementation/evidence |
| --- | --- | --- |
| FR-J00, FR-J03, FR-J15, FR-J18 | verified | Revision domain/storage, ADR-0020, immutable full snapshots, and atomic allocator tests. |
| FR-J01, FR-J02 | verified | `EWP-REVIEW 1`, prepare/apply services, deterministic discovery, failure-isolated batch tests, and the accepted private-corpus workflow. |
| FR-J04, FR-J05, FR-J06, FR-J07, FR-J11, FR-J12 | verified | Anchored alignment tests cover supported edits, repetition preservation, anchor integrity, and ambiguity warnings. |
| FR-J08 | verified | `EffectiveTranscript` inherits canonical timing without canonical timestamp mutation. |
| FR-J09, FR-J10 | verified | Preview equivalence and external-editor lifecycle tests; staged VS Code editing is the preferred operator path. |
| FR-J13, FR-J14 | verified | Revision provenance/statistics and reconstructable or published detailed audit. |
| FR-J16, FR-J17 | verified | Revision resolution and TXT/SRT/VTT/segments export use one `EffectiveTranscript` without audio or models. |
| NFR-013, NFR-014 | verified | Determinism fixtures and shared CLI/correction/translation application boundaries; the future GUI must reuse them. |

## v0.3 automated-correction requirements

| Requirement | Status | Planned implementation/evidence |
| --- | --- | --- |
| FR-K00, FR-K01, FR-K03, FR-K07 | verified | Provider-neutral mock, LM Studio, and OpenRouter paths correct canonical or explicitly selected compatible revision text through the existing aligner and immutable revision storage. Child revisions retain exact parent lineage and remain complete standalone snapshots. |
| FR-K02, FR-K04 | verified | Strict speaker-block text response validation, locally derived exact per-block change lists, and the hashed LM Studio faithful-repair prompt prohibit paraphrase, style/grammar repair, summary, translation, and meaningful deletion. |
| FR-K05, FR-K06, NFR-015 | verified | Deterministic gap-free editable chunks, bounded read-only overlap, operation hashes, configuration validation, and boundary tests. |
| FR-K08, FR-K09, FR-K10, FR-K11, FR-K12, NFR-016 | verified | Local/cloud consent policy, strict-offline rejection, exact-scope private persistence, CLI warning/choice behavior, zero-call rejection, and sanitized failures are tested. |
| FR-K13 | verified | LLM revisions record provider/model/endpoint kind and prompt ID/content hash; operation and resume identity include the actual prompt/schema hash. |
| FR-K14, FR-K15 | verified | Adapter timeout budgets, bounded explicit retries, validated resume entries, deterministic batches, failure isolation, and stop policy tests. |
| FR-K16 | verified | The in-process deterministic provider exercises request, validation, alignment, and revision publication without network or models. |
| FR-K17, FR-K18 | verified | Exact-lineage canonical/revision cases report lexical outcomes, exact normalized gold-relative edit precision/recall, revision activity, warnings, alignment warnings, and speaker preservation. Private resume evidence now aggregates attempts, retries, provider latency, requests, tokens, cost, and legacy-entry coverage; unsupported/style interpretation remains an explicit manual review task. |
| FR-K19 | verified | CLI and operator documentation label automated output as a non-final candidate and require manual wording/speaker/punctuation/quotation review before final or gold use. |

## v0.4 translation and platform-export acceptance

The v0.4 contracts are defined in `23-v0.4-translation-contract.md`,
`24-v0.4-timed-event-semantics.md`, and the corresponding roadmap gates.

| Capability | Status | Implementation and evidence |
| --- | --- | --- |
| Manual and automated translation | verified | Exact source lineage, speaker-safe sentence units, immutable manual/non-final artifacts, prepare/preview/apply/audit/export, retry/resume providers, and accepted Bielik end-to-end pilot. |
| Semantic translation benchmark | verified | Exact-lineage private human assessments and content-free direction-specific reports; semantic fidelity is separate from dictionary convention adherence. |
| Project dictionaries | verified | Explicit versioned/hashed translation and correction dictionaries, retained approval/rejection decisions, source-aware provider context, audit provenance, Gemini comparison, and accepted held-out `s0e00` result. |
| Timed-event semantics | verified | Canonical/derived schema `1.1`, legacy speech default, revision/effective inheritance, closed kind vocabulary, and YTT/HTML consumption. |
| YouTube srv3 YTT | verified | Deterministic parser-tested exporter and successful unlisted real Polish upload covering wrapping, colors, centering, timing, labels, and diacritics. |
| Embeddable HTML | verified | Escaped sentence-level raw/revised/translated fragments plus separate player; real-media Firefox, LibreWolf, Chrome, and Brave qualification covers range seeking, keyboard/mouse interaction, highlighting/following, theme controls, and no-script fallback. |
| Privacy and reproducibility | verified | `/tmp`-only pilots, no committed private payloads or secrets, content-free benchmark evidence, deterministic exports, immutable source artifacts, the 620-test locked gate, archive-content inspection, and isolated installed-wheel CLI/HTML/YTT smoke checks. |

## Local browser GUI requirements

ADR-0021 and `26-local-web-gui-contract.md` define the common WSL2, bare-metal Ubuntu, and
future-Docker interface. The application GUI is implemented separately from the exported HTML transcript player.
The evidence below distinguishes delivered functions from retained proposals.

| Requirement | Status | Planned implementation/evidence |
| --- | --- | --- |
| FR-L00, FR-L01, FR-L02, FR-L13, FR-L16 | implemented | `transcriber gui`, bundled offline assets, loopback-only adapter, `/api/v1` health/about/root endpoints, and frontend compatibility rejection. All workflow stages call the application services directly. |
| FR-L03, FR-L17, NFR-020 | partial | Windows/WSL/POSIX paths normalize before ordinary-user-space/system-denylist validation; Host/Origin/CSRF validation, restrictive CSP, safe fixed routing, and negative tests are implemented. Safe file selection rejects symlinks/system trees. General verified export-download identities remain retained proposal E02. |
| FR-L04, FR-L05 | implemented | Browser inspect/dry-run calls existing services; an explicitly confirmed single-worker queue invokes atomic transcription, survives browser refresh, and waits safely on server shutdown. Explicit cancellation and richer persisted GUI history remain later operational enhancements. |
| FR-L06, FR-L07 | implemented | Structured browser transcript editor hides/protects anchors, saves with hash conflict detection, requires exact saved preview before immutable manual apply, and exports the selected verified revision through existing services. The owner accepts the current workflow; latest restart recovery and full profile exchange remain unchecked. |
| FR-L08, FR-L09 | verified | Correction and translation candidate generation, structured manual editors, exact-lineage preview/apply, translation audit/export, and direct handoffs passed external browser qualification. |
| FR-L10 | verified | Compatible correction/translation dictionaries are catalogued and selectable; proposal review retains approved/rejected decisions and publishes immutable project dictionaries with exact provenance. |
| FR-L11, FR-L12 | implemented | Coded failures cover startup, routes, paths, credentials, providers, models, and confirmations. Provider workflows require explicit disclosure/consent and keep optional OpenRouter credentials only in server-process memory. |
| FR-L14, FR-L15, NFR-018 | partial | Version, license/warranty, source, and issue information is implemented in the responsive keyboard-native shell. Synchronized mixed/single media review, seeking, playback speed, PL/EN and explicit themes are implemented and owner-accepted. Any automatic audio-follow enhancement remains a separate proposal. |
| FR-L18 | implemented | Inspect, exact dry-run authorization, staged queue evidence, and execution carry an explicit per-job language and speaker count. The owner accepts the current workflow; latest restart recovery and full profile exchange remain unchecked. |
| NFR-017, NFR-019 | planned | Shared contract tests across WSL2-compatible/native launch modes, then the identical packaged application in Docker; offline acceptance after model setup. |
