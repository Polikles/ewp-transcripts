# Requirements

The words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

## 1. Functional requirements

### A. Input and discovery

- **FR-A01** The application MUST accept a path to a single file or a directory.
- **FR-A02** For a directory, the application MUST inspect only files directly inside that directory by default.
- **FR-A03** Recursive discovery MUST require an explicit option.
- **FR-A04** The application MUST identify media content through FFmpeg/ffprobe rather than relying only on filename extensions.
- **FR-A05** The application MUST support audio files decodable by FFmpeg. Video files and audio-stream selection are deferred until stage 2.
- **FR-A07** The application MUST normalize Windows and WSL paths.
- **FR-A08** The application MUST NOT follow symbolic links by default.
- **FR-A08.1** No, --force nor any other command MUST NOT make symlink to be followed.
- **FR-A08.2** Symlinks found during batch processing MUST be omitted and result in warning. 
- **FR-A08.3** Symlinks pointing to one singular file MUST result in error.

### B. Episode grouping

- **FR-B00** The application MUST group files that share a base name and have a speaker suffix separated by the final hyphen, e.g. `S01E01_audio-john.mp3` recognizes `john` as the speaker name.
- **FR-B01** A speaker suffix in a single filename MUST be interpreted only when `speaker_count = 1`.
- **FR-B02** In `speaker_count = auto` mode or when the value is not 1, the suffix of a single file MUST NOT be used as a speaker label.
- **FR-B03** An unsuffixed base file and one or more suffixed files MAY form a group; the base file receives a default speaker label.
- **FR-B04** An explicitly supplied group MUST take precedence over automatic grouping.
- **FR-B05** Files in a group MUST have the same sample rate.
- **FR-B06** A duration difference of up to 100 ms is accepted, a difference above 100 ms produces a warning, and a difference above 500 ms blocks the group.
- **FR-B07** Bypassing the duration block MUST require a separate option; `--force` MUST NOT bypass it.
- **FR-B08** Separate episodes discovered in one batch that derive the same `job_id` MUST block dry-run/transcription before publication. The application MUST NOT silently prefer one source, treat result versions as source aliases, or change canonical identity based on neighboring files.

### C. Channels and speakers

- **FR-C00** The application MUST classify input as `mono`, `dual_mono`, `split_speakers`, `mixed_stereo`, or `ambiguous`.
- **FR-C01** Identical or nearly identical channels MUST be treated as one channel containing one or more speakers.
- **FR-C02** Confidently detected `split_speakers` input MUST be transcribed per channel without conventional diarization.
- **FR-C03** Ambiguous stereo MUST produce a warning and use one channel.
- **FR-C04** The user MUST be able to override `channel_mode`.
- **FR-C05** Speaker count MUST be optional and accept `auto` or a positive integer.
- **FR-C06** For `speaker_count = 1`, the application SHOULD skip diarization.
- **FR-C07** For separate files or split channels, each file/channel MUST represent one speaker.
- **FR-C08** Speaker-label priority MUST be: explicit parameter, filename, semantic track/channel metadata, then `SpeakerN`.
- **FR-C09** `Speaker1` MUST mean the first speaker encountered chronologically, independently of backend-specific identifiers.

### D. Transcription

- **FR-D00** The default language MUST be `pl`.
- **FR-D01** The application MUST support explicit `pl`, `en`, and `auto` language modes.
- **FR-D02** The MVP MUST NOT switch language or alignment model within a recording.
- **FR-D03** The application MUST generate transcription, word alignment, and diarization when required.
- **FR-D04** A missing word timestamp MUST NOT fail the entire job.
- **FR-D05** The source of every word timestamp MUST be recorded as `aligned`, `interpolated`, or `segment_fallback`.
- **FR-D06** Overlapping speech MUST be represented in JSON even when the second speaker's words cannot be reconstructed reliably.
- **FR-D07** The canonical transcript MUST preserve meaningful repetitions, self-corrections, and faithful wording; it MUST NOT be paraphrased by an LLM.

### E. Results and exports

- **FR-E00** Every completed job MUST create a schema-valid `results.json`.
- **FR-E01** `segments.json` MUST be an optional export derived from `results.json`.
- **FR-E02** TXT MUST contain no timestamps, use one sentence per line, and group text by speaker.
- **FR-E03** SRT and VTT MUST be segmented using readability rules rather than raw backend segments.
- **FR-E04** Speaker labels in subtitles MUST appear at the first occurrence and after each speaker change.
- **FR-E05** For a single speaker, labels MUST be omitted by default.
- **FR-E06** TXT, SRT, VTT, and `segments.json` MUST be regeneratable without running ASR again.
- **FR-E07** All timestamps in JSON MUST be integer milliseconds.
- **FR-E08** All text formats MUST use UTF-8.

### F. Duplicates, versions, and state

- **FR-F00** The application MUST calculate SHA-256 for every source before transcription.
- **FR-F01** A grouped episode MUST receive a deterministic `episode_signature` that includes hashes, speaker assignments, and channel selections.
- **FR-F02** A completed result with the same signature MUST be skipped unless `--force` is supplied.
- **FR-F03** `--force` MUST create the first available `_vNNN` suffix, beginning with `_v002`.
- **FR-F04** All exports created during one run MUST use the same version number.
- **FR-F05** A source with the same name but a different signature MUST create a new version without overwriting existing files.
- **FR-F06** The final `_results.json` MUST be created only after successful completion.
- **FR-F07** In-progress and failed runs MUST use `.partial.json` and `.failed.json` files.
- **FR-F08** An incomplete file MUST be processed again from the beginning.
- **FR-F09** Failure of one job MUST NOT stop the remaining batch.

### G. CLI operations

- **FR-G00** `inspect` MUST analyze input without loading ASR models.
- **FR-G01** `dry-run` MUST show groups, decisions, skipped jobs, warnings, and planned outputs.
- **FR-G02** `transcribe` MUST execute the complete pipeline.
- **FR-G03** `export` MUST operate only on an existing JSON result.
- **FR-G04** `doctor` MUST verify the environment, CUDA, FFmpeg, and models without exposing secrets.
- **FR-G05** `clean` MUST remove only explicitly selected working files.
- **FR-G06** The application MUST provide a non-interactive mode with no prompts.

### H. Models and offline operation

- **FR-H00** Application installation MUST NOT automatically download gated models.
- **FR-H01** A missing required model MUST produce a clear error and setup instructions.
- **FR-H02** The Hugging Face token MUST be read from the `HF_TOKEN` environment variable.
- **FR-H03** After models have been prepared locally, transcription MUST work without network access.

### I. Audio diagnostics

- **FR-I00** The application MUST provide lightweight, non-destructive audio-quality diagnostics.
- **FR-I01** Diagnostics MUST be warning-only and MUST NOT modify or repair source audio.
- **FR-I02** MVP diagnostics MUST cover clipping, low level, channel-level imbalance, and high silence ratio.

### J. Transcript revisions (implemented for v0.2.0)

- **FR-J00** Final canonical `results.json` MUST remain immutable during all transcript-revision operations.
- **FR-J01** `revise prepare` MUST accept one completed canonical result or a directory of completed results and create `EWP-REVIEW 1` work files without loading source audio or ML models.
- **FR-J02** Directory-based revision preparation and apply MUST use deterministic natural ordering, ignore subdirectories unless recursion is explicit, isolate per-item failures, and follow the existing batch continuation policy.
- **FR-J03** `revise apply` MUST create a separate schema-valid immutable full-snapshot revision linked to the exact base-result SHA-256. It MUST NOT store a delta as the only representation of corrected state.
- **FR-J04** A revision MUST preserve a mapping from corrected text tokens to canonical `word_id` anchors or an explicit insertion anchor.
- **FR-J05** Normal revision MUST support spelling/proper-name corrections, capitalization, punctuation, sentence-boundary changes, merge/split, insertion, deletion, and reassignment to an existing `speaker_id`.
- **FR-J06** Meaningful repetitions and self-corrections MUST NOT be removed implicitly by the revision engine.
- **FR-J07** Corrected punctuation MUST remain ordinary text; reviewers MUST NOT be required to maintain a separate punctuation-token or sentence-boundary structure.
- **FR-J08** Canonical word timestamps MUST remain unchanged by normal revision. Revised exports MUST inherit timing from mapped canonical words; inserted text MUST NOT receive fabricated canonical timestamps.
- **FR-J09** `revise preview REVIEW` and `revise apply REVIEW --no-apply` MUST execute the same parse/alignment/validation path and MUST NOT persist a revision or derived export.
- **FR-J10** `revise edit` MUST open an external editor and, after a successful editor exit, apply the saved review automatically unless `--no-apply` is supplied. This behavior MUST be documented in CLI help.
- **FR-J11** Review anchors MUST be validated against canonical word order and the exact base-result hash. Missing, modified, duplicate, overlapping, or out-of-order anchors MUST NOT be silently repaired.
- **FR-J12** Ambiguous text-to-word mappings MUST be reported rather than resolved arbitrarily when the choice can affect timing or speaker attribution.
- **FR-J13** Every revision MUST store provenance, alignment metadata, summary change statistics, and structured warnings.
- **FR-J14** Detailed audit output MAY be generated with `--audit`; a base-relative detailed audit MUST be reconstructable later from the immutable base result and full revision snapshot.
- **FR-J15** A revision MAY reference a parent revision for lineage, but the revision MUST remain exportable without replaying or loading the parent.
- **FR-J16** `transcriber export` MUST support selecting raw canonical text or a compatible revision. Omitting a revision selector MUST preserve raw v0.1 behavior.
- **FR-J17** TXT, SRT, VTT, and `segments.json` generated from a revision MUST be derived from one resolved `EffectiveTranscript` and MUST NOT require source audio or ML models.
- **FR-J18** Revision artifacts and revision-aware exports MUST use non-destructive allocation and atomic publication.

### K. Automated transcript correction (implemented for v0.3)

- **FR-K00** Automated correction MUST consume a completed canonical result or compatible immutable revision and MUST publish corrections through the existing revision engine.
- **FR-K01** Correction providers MUST implement one provider-neutral application protocol; provider-specific request/response objects MUST NOT enter the revision domain.
- **FR-K02** Every provider response MUST contain corrected editable text in the same ordered speaker blocks supplied by the application. Block count/order/identity MUST NOT change. The local application MUST derive an explicit change list with source span, before text, after text, and deterministic correction category before revision construction. Optional provider annotations are advisory evidence only.
- **FR-K03** The local application MUST independently align and audit provider output. Provider text or optional annotations MUST NOT be treated as an authoritative revision patch.
- **FR-K04** Prompts MUST restrict correction to obvious ASR lexical errors, proper-name spelling, conservative punctuation, capitalization, and sentence boundaries. They MUST prohibit paraphrasing, stylistic repair, grammar repair, summarization, and removal of meaningful repetitions or self-corrections.
- **FR-K05** Editable chunks MUST form an ordered, gap-free, non-overlapping partition of the selected effective transcript. Read-only context overlap MAY repeat surrounding tokens but MUST NOT create multiple owners for editable text.
- **FR-K06** Chunk target size, hard maximum size, and read-only overlap MUST be configurable and validated before any provider call.
- **FR-K07** Correction MUST preserve canonical word/speaker/timing anchors through the same deterministic alignment rules used by manual revision.
- **FR-K08** Cloud correction MUST require explicit scoped consent before transcript content leaves the machine. Rejecting consent MUST make no provider request.
- **FR-K09** Loopback/local API correction MUST display a distinct API-boundary privacy warning and require scoped consent; it MUST NOT be described as equivalent to in-process offline execution.
- **FR-K10** Strict offline mode MUST block cloud correction regardless of stored consent.
- **FR-K11** Non-interactive correction MUST require an explicit one-run consent flag or compatible stored consent and MUST never infer acceptance.
- **FR-K12** Consent persistence MUST be scoped to provider, non-secret endpoint identity, operation class, and warning-policy version. Secrets MUST NOT appear in configuration artifacts, revisions, audits, logs, or benchmark reports.
- **FR-K13** Provider provenance MUST record provider, model, endpoint kind, prompt identity/hash, and non-secret parameters in every LLM revision.
- **FR-K14** Provider failures MUST use bounded timeout/retry behavior, distinguish retryable from permanent failures, and MUST NOT create a revision for an incomplete correction.
- **FR-K15** Directory correction MUST be deterministic, resumable, failure-isolated, non-recursive by default, and governed by the existing batch continuation policy.
- **FR-K16** A deterministic mock provider MUST exercise the complete correction path without network access, credentials, or heavyweight model loading.
- **FR-K17** Benchmarking MUST support canonical-to-latest-gold and earlier-revision-to-latest-gold tasks selected by exact base hash and revision lineage, not timestamps.
- **FR-K18** Benchmark reports MUST measure lexical quality, harmful changes to already-correct text, locally derived change precision/recall, unsupported/stylistic changes, speaker preservation, audit completeness, latency, request/token volume, cost when applicable, and failure/retry outcomes. Provider-annotation precision/recall MUST be reported only for providers that emit such annotations.
- **FR-K19** Every automated correction artifact and CLI outcome MUST be described as a non-final review candidate. Manual acceptance MUST verify wording, speaker attribution, punctuation, quotation marks, and sentence boundaries before the artifact is treated as final publication text or benchmark gold.

### L. Local browser GUI (planned)

- **FR-L00** The GUI MUST be one local browser application with the same bundled frontend, versioned API, application services, and artifact contracts on WSL2, bare-metal Ubuntu, and the future Docker image.
- **FR-L01** The web adapter MUST call application services directly and MUST NOT invoke CLI subprocesses or maintain alternate transcript, revision, translation, or dictionary models.
- **FR-L02** The service MUST bind to loopback by default. Non-loopback or multi-user deployment requires a separate security contract and MUST NOT be enabled implicitly.
- **FR-L03** The primary media workflow MUST use server-visible user-space paths. The GUI MUST reject symlinks and documented operating-system directories; optional picker search roots optimize lookup but do not define path authority.
- **FR-L04** The GUI MUST expose inspect and dry-run evidence before transcription, including grouping, stream/channel choice, warnings, and resolved outputs.
- **FR-L05** The GUI MUST expose a deterministic job queue and initially run at most one GPU-intensive job at a time. Browser refresh or closure MUST NOT corrupt active work.
- **FR-L06** Transcript editing MUST preserve `EWP-REVIEW 1` anchors and lineage while allowing machine metadata to be hidden from the visible editor.
- **FR-L07** Transcript preview/apply and export MUST use the existing revision, resolution, validation, and export services and retain immutable publication rules.
- **FR-L08** Correction and translation screens MUST distinguish automated non-final candidates from manually verified artifacts and preserve exact source lineage.
- **FR-L09** Translation from an unreviewed candidate MAY be offered only with the existing warning and explicit candidate-source provenance.
- **FR-L10** Project dictionaries MUST be selected and displayed by project, language/direction, version, and hash; artifacts without a dictionary MUST display `none`.
- **FR-L11** Expected GUI warnings and errors MUST display a stable diagnostic code, readable message, and catalogue/action link.
- **FR-L12** Provider credentials MUST NOT be stored in URLs, browser history, local storage, logs, artifacts, or job records. Provider operations MUST preserve endpoint classification, explicit scoped consent, and strict-offline enforcement.
- **FR-L13** The packaged GUI MUST use bundled assets and MUST NOT require runtime CDNs, telemetry, remote fonts, or externally hosted scripts/styles.
- **FR-L14** The GUI MUST provide version, license/warranty, source-code, and issue-tracker information.
- **FR-L15** When media is available, transcript review SHOULD support synchronized playback, seeking, highlighting, keyboard operation, and user-controlled follow-playback and theme settings.
- **FR-L16** The frontend and backend MUST reject incompatible API versions rather than continuing with partial behavior.
- **FR-L17** The local server MUST validate browser host/origin, protect state-changing requests against cross-site request forgery, escape untrusted content, use a restrictive content-security policy, and serve only validated artifacts.
- **FR-L18** Planning SHOULD expose per-file language and speaker-count controls and MUST label values chosen by configuration or automatic inference as automatic rather than as explicit operator choices.

## 2. Non-functional requirements

- **NFR-001 Local-first privacy:** transcription, alignment, diarization, manual review, and
  export MUST operate locally after explicit model setup. Transcript text MAY cross a separate
  local-API or cloud boundary only for an explicitly selected automated correction or
  translation operation governed by scoped consent, strict-offline enforcement, disclosure
  warnings, and credential sanitization. Audio MUST NOT be uploaded by those operations.
- **NFR-002 Reproducibility:** dependencies use a lockfile, and the effective configuration is stored in JSON.
- **NFR-003 Stability:** a 60-minute file must complete without OOM on an RTX 3090 using the `accurate` preset.
- **NFR-004 Atomicity:** the application must not leave a final result with an incomplete status.
- **NFR-005 Operational determinism:** identical sources and configuration must produce identical grouping, versioning, and export decisions.
- **NFR-006 Extensibility:** the core must be independent of the CLI and reusable by a future GUI.
- **NFR-007 Testability:** FFmpeg, ASR, alignment, and diarization adapters must support test doubles.
- **NFR-008 Observability:** structured logs, warning codes, batch summaries, and time/VRAM metrics are required.
- **NFR-009 Security:** tokens MUST NEVER appear in logs, JSON, or exception output.
- **NFR-010 Path compatibility:** Unicode, spaces, and Windows/WSL path forms must be supported.
- **NFR-011 Non-destructive behavior:** source files and existing results must not be deleted or overwritten.
- **NFR-012 Documentation and compatibility:** a JSON schema change requires a `schema_version` update and either migration support or a compatible reader.

- **NFR-013 Revision determinism:** for the same base result, review content, configuration, and alignment-strategy version, revision mapping and preview classification must be deterministic.
- **NFR-014 Revision extensibility:** the manual revision core must be reusable by future LLM and GUI adapters without introducing another corrected transcript model.
- **NFR-015 Correction determinism:** identical selected input, chunk configuration, prompt, and deterministic provider responses MUST produce identical chunk ownership, alignment classification, and audit content apart from allocated identity and creation time.
- **NFR-016 Correction privacy:** no transcript content or credential may cross a provider boundary until endpoint classification and applicable consent have succeeded.
- **NFR-017 GUI deployment parity:** automated acceptance MUST run the same frontend/API behavior against WSL2-compatible and native Linux service configurations; Docker later MUST reuse that application rather than fork it.
- **NFR-018 GUI accessibility:** the interface MUST support keyboard navigation, visible focus, semantic labels, sufficient contrast, browser zoom, and status communication that does not depend on color alone.
- **NFR-019 GUI offline operation:** all local GUI workflows MUST remain functional without network access once explicitly selected models and application assets are installed.
- **NFR-020 GUI security:** filesystem exposure, browser-origin controls, credential handling, and rendered untrusted text MUST be covered by automated negative tests before GPU or provider workflows are exposed.
