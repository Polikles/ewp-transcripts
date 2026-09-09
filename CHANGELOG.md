# Changelog

All notable changes to EWP-transcripts are documented here.

## Unreleased

The next internal-beta version is `0.10.0`.

### Added

- Added GUI manual-review selected-text separation and adjacent-block merging. Each resulting
  editable block can be assigned independently to a known speaker while protected anchors and
  the canonical result remain unchanged.
- Added explicit named GUI workspace save/load for allowlisted non-secret fields and current-step
  context in an application-owned user-state catalog. Paths are revalidated, stale work is listed
  unavailable, and credentials, confirmations, transcript text, and unsaved edits are excluded.
- Added optional change-sensitive 60-second auto-save after an explicit workspace save or load;
  unchanged state produces no write.
- Added hash-validated restoration of staged GUI transcription jobs. Only unstarted jobs are
  persisted; restoration re-hashes each source and reproduces its dry-run plan before restaging.
- Saving a manual-review draft now also saves an active named GUI workspace. The filesystem
  browser hides unreadable and temporary desktop/session runtime directories from selection.
- Added a read-only, CSRF-protected local filesystem browser for GUI media, result, revision,
  dictionary, and output path fields. Navigation is constrained to explicit allowed roots, hides
  symlinks, filters expected file types, and retains direct entry for not-yet-created outputs.
- Added explicit transcription language and speaker-count controls to GUI inspection, exact
  dry-run authorization, staged jobs, and execution. A plan produced with different controls can
  no longer authorize queueing with stale settings.
- Added an OpenRouter correction-model chooser with three priced Gemini 2.5 presets, an explicit
  manual-ID mode, and opt-in live availability/list-price checks for only those bounded presets.
  Live checks disclose the external request, run only on button press, and send no transcript.
- Added completed-transcription handoffs for optional LLM correction and direct manual review.
  Each fills the exact canonical result and containing output root, scrolls smoothly, and starts
  no correction provider request or review preparation automatically.
- Added a gated `Proceed to translation` handoff after immutable transcript application. It
  fills canonical source, verified revision, shared output root, and opposite target language,
  then scrolls to translation without starting a provider request or changing provider settings.

### Changed

- Clarified that GUI-entered API keys are shared only within the active GUI server process and
  disappear when it stops; they are never saved in projects, workspaces, or browsers.
- Clarified the intentional single-user/single-organization credential boundary, aligned the
  auto-save checkbox with its label, and exposed distinct checked/saved/validation-failed status.
- Added immediate `Changes pending for auto-save` feedback for tracked workspace edits and
  visually subordinated the supplementary auto-save status line.

- Recorded successful Chrome/Firefox allowed-root browser qualification and clarified that roots
  are operator-granted capabilities rather than hardcoded work directories. Added roadmap work
  for persistent named roots and start-time source fingerprint revalidation/optional immutable
  snapshots instead of extension-only trust or fragile filesystem blacklists.
- Limited the 1–6 GUI speaker-count field to one typed or pasted character and recorded accepted
  browser evidence that dry-run summaries survive confirmation failures and clear after staging.
- Added roadmap contracts for separate, default-off punctuation-check and basic-editorial LLM
  correction modes with increased-usage/risk disclosure, versioned provenance, and mandatory
  manual review; the conservative lexical default remains unchanged.
- Replaced the fixed speaker-count list with a validated 1–6 number field plus explicit automatic
  detection, documented the expected accuracy tradeoff, and retained the last dry-run summary
  while queue confirmation or exact-plan validation fails.
- Clarified that dry-run already performs inspection, documented EWP Transcriber as part of a
  wider externally sourced model/API ecosystem, and made the current lexical-only LLM correction
  boundary explicit: punctuation and sentence boundaries remain manual-review responsibilities.
- Recorded future LM Studio connection/model discovery and explicit capability-gated loading,
  plus searchable broader OpenRouter model browsing, without expanding the accepted bounded
  preset slice prematurely.
- Require an explicit GUI dry-run output directory and highlight it when absent instead of
  later misreporting a missing matching plan. OpenRouter readiness now validates the key through
  authenticated `/api/v1/key` before checking the exact model catalog; public `/models` success
  can no longer produce a false green state for a fake key.
- Keep the connection light and a labeled `API check` result together below the buttons, allow
  long coded errors to wrap as one unit, and clarify that the informational key status means
  session-only use with no API-key storage.
- Added an explicit correction-provider connection check with a neutral/green/red indicator and
  distinct missing/rejected credential, unavailable connection, rejected HTTP response, and
  exact-model-unavailable errors; it sends no transcript text.
- Match confirmation error codes as well as legacy message wording when highlighting required
  controls, and clarify the OpenRouter spending-limit example as `USD $2`.
- Require an exact matching dry-run before reporting a missing transcription confirmation,
  explain the inspect/dry-run sequence, highlight the required queue checkbox, soften the Clear
  button, and collapse advanced correction provider/model/endpoint/reasoning controls.
- Added a password-masked OpenRouter dialog that transfers a key only to loopback server memory
  for the current process, clears the browser field immediately, exposes only configured/not-
  configured state, and never persists or returns the secret.
- Highlight required confirmation controls after transcript review, correction, translation,
  or semantic translation review rejects an operation for missing explicit confirmation; the
  highlight and accessibility-invalid state clear when the operator checks the control.

### Validated

- Qualified explicit dry-run output validation and coded credential/model readiness failures,
  including correct rejection precedence for fake keys and exact unavailable models.
- The first live readiness retest proved that OpenRouter `/models` accepts an arbitrary bearer
  value: both fake and real keys appeared green while exact fake models were correctly rejected.
  This result invalidated the original credential-check assumption and prompted `/key` validation.
- Qualified the collapsed correction provider settings, lower-emphasis Clear action, and
  password-dialog behavior including empty-on-reopen secret handling. The first queue-checkbox
  retest exposed and did not qualify the red outline because its matcher missed the coded error.
- Qualified shared confirmation highlighting in the browser: a rejected unchecked manual-review
  confirmation received the visible red outline, checking it cleared the outline, and applying
  the verified revision then succeeded normally.
- Qualified the verified-review handoff using an English example and revision 3: the button
  stayed gated until application, then filled exact canonical/revision/root lineage, selected
  Polish, preserved provider fields, scrolled smoothly, and started no translation request.
- Qualified dictionary catalog selection in the browser: correction and translation each
  discovered exactly one compatible Ethics in the Loop dictionary, displayed project/ID/
  version/language identity, reported local counts, and filled the exact selected path.
- Qualified the final dictionary evidence layout: list mode opens the first five examples,
  show-more opens the remainder, sequential mode shows one expanded example, and its inactive
  navigation controls disappear completely in list mode.
- Qualified browser dictionary publication against the 22-case private corpus: the previous
  dictionary restored all 41 decisions, and the GUI published a 4,438-byte immutable test
  dictionary plus its 58,616-byte reviewed proposal under a temporary root.
- Qualified browser semantic review through source/target editing, exact preview, manual child
  translation 3, audit reconstruction, and TXT/SRT/VTT/HTML/provenance export from the
  dictionary-backed 79-unit Bielik candidate.
- Qualified GUI LM Studio translation generation from the manually verified `s0e00` revision
  with the project PL→EN dictionary: 79 units, 867 source tokens, 1,051 target tokens, zero
  warnings, exact model/source/dictionary provenance, and an explicitly non-final candidate.
- Qualified disk-backed review restoration across browsers and confirmed that the bordered,
  labeled review-status surface is readable and correctly placed.
- Qualified the model-free browser review flow through editing, save/preview gating, two
  immutable revisions, and all six revision-backed export formats in WSL2.
- Passed formatting, lint, static typing, and all 640 tests for the current v0.9 GUI slices;
  verified that its bundled HTML/CSS/JavaScript assets are included in the built wheel.
- Built the `0.9.0` wheel and source archive and verified inclusion of the model-free browser
  review controller plus updated bundled review assets/help.
- Qualified the loopback shell on WSL2 with Firefox, LibreWolf, Chrome, and Brave, including
  exact allowed roots, health/about data, and rejection of an untrusted Host header.
- Qualified real WAV inspection, allowed-root rejection, cross-origin rejection, and the
  dry-run no-write invariant from WSL2; moved About into a compact footer and added explicit
  inspect/dry-run summaries plus a collapsible structured result.
- Qualified staged queue construction with two files, refresh and cross-browser persistence,
  staged removal, same-job-ID rejection, explicit execution, and canonical publication on
  WSL2. No GPU work began while items remained staged.
- Qualified the follow-up planning UI fix in the target browser: successful staging has no
  false API error, detail rows remain full-width, and automatic language is labeled clearly.
- Passed formatting, lint, static typing, and all 620 tests; the locked environment contains
  140 mutually compatible packages.
- Built the `0.7.0` wheel and source archive, verified version and `AGPL-3.0-only` metadata,
  confirmed inclusion of `LICENSE` and `LICENSING.md`, and scanned archive names/content for
  runtime/private payloads and credential-shaped values.
- Installed the wheel into an external `/tmp` target and ran it outside the checkout. Version,
  help, coded framework errors, and model-free TXT/SRT/VTT/YTT/HTML/segments export passed.

### Added

- Added bounded allowed-root dictionary catalog discovery and project/ID/version/language
  selectors to correction and translation forms while retaining explicit custom paths.
- Added browser correction-dictionary proposal, contextual evidence review, optimistic decision
  saving, retained prior approved/rejected decisions, and immutable project dictionary
  publication with exact proposal/corpus provenance.
- Added browser semantic translation review with immutable source units, editable targets,
  save/preview/manual-verification gating, exact-parent manual apply, audit reconstruction,
  and deterministic TXT/SRT/VTT/HTML plus provenance export.
- Added the first browser translation workflow for explicitly consented LM Studio candidate
  generation from an exact canonical or revision-backed source, with bounded backend/model
  preflight, optional project dictionary provenance, readable source-verification status,
  private resume state, and explicit non-final semantic-review labeling.
- Matched browser Bielik translation to the accepted zero-context compatibility profile;
  adjacent context had caused the model to return both the owned and neighboring unit.
- Added the first browser correction workflow for explicitly consented LM Studio or
  OpenRouter generation, optional project dictionary provenance, private resume state,
  non-final candidate summaries, and direct handoff into candidate-backed manual review.
- Added a three-second provider/model/credential readiness check before correction chunk
  retries and prevented local correction from overlapping active transcription GPU work.
- Added a model-free browser review workspace: prepare structured editable drafts without
  exposing anchors, edit text/speaker attribution, save with optimistic hash conflict
  protection, preview exact saved content, explicitly apply an immutable manually verified
  revision, and export TXT/SRT/VTT/YTT/HTML/segments from that revision.
- Connected read-only GUI inspect and dry-run forms directly to existing application
  services, with structured results, bounded in-process operation history, explicit-root
  containment, symlink rejection, Origin validation, and bounded JSON requests.
- Added a GUI Clear control that resets input/output fields and all visible operation results
  without mutating server-side history or artifacts.
- Added the first state-changing GUI workflow: an explicitly confirmed, CSRF-protected,
  single-worker transcription queue for one allowed-root file, with refresh-safe polling,
  sanitized failures, and existing atomic application publication underneath.
- Split queue staging from execution. Users can collect files from different allowed roots
  into one shared output directory, review/remove staged rows in a table, then explicitly
  start the serialized queue. The readable planning/queue tables expose decisions, warnings,
  logical job IDs, and planned results; duplicate inputs and logical-output collisions stop
  before execution. Added expandable on-page guidance and bundled local help.
- Added the first executable local-browser GUI slice: `transcriber gui` serves a bundled,
  responsive offline shell on loopback with versioned health/about/allowed-root APIs,
  compatibility checking, security headers, Host validation, coded errors, and no ML load.
- Changed automatic browser opening under WSL2 to use the Windows PowerShell bridge quietly;
  launcher failure leaves the printed URL usable instead of emitting a misleading `gio` error.
- Accepted one self-contained local browser GUI architecture for WSL2, bare-metal Ubuntu,
  and the future Docker image, with normative workflow, allowed-root filesystem, security,
  privacy, accessibility, diagnostics, and staged implementation requirements.
- Added a guided, explicitly networked `scripts/setup-models.sh` that downloads exact
  pinned public snapshots and language data, privately reads the gated Hugging Face token,
  verifies every artifact, and runs readiness diagnostics without placing tokens in command
  arguments or files.
- Added a first-time Hugging Face guide covering gated pyannote terms, read-only token
  creation, hidden installer entry, revocation, and placeholders for future screenshots.
- Added candidate-aware manual review preparation. `revise prepare --revision` prefills
  from an exact compatible correction revision and protects its ID/number/hash plus
  automated-versus-manual verification label; preview/apply resolve that parent explicitly
  with `--revisions-dir` and publish an exact-lineage manual child.
- Added a complete warning/error-code catalogue with meaning, likely causes, safety impact,
  and operator actions. Automated coverage rejects undocumented codes emitted by domain,
  provider, batch, and CLI paths.

### Changed

- Fixed dictionary catalog scans aborting on valid proposal JSON encountered before project
  dictionaries; proposals and unrelated JSON are now ignored, and each picker reports local
  loading, empty, or coded failure status.
- Restyled translation review as numbered source/target cards with automatically sized target
  editors, consistent primary handoff actions, and a readable preview validation/publication
  summary instead of exposing only a technical status sentence.
- Reduced semantic-editor label emphasis so unit headings and target labels do not compete
  visually with the source and editable translation.
- Added dictionary candidate filters, a four-count proposal summary, five-example list
  truncation, list/sequential occurrence navigation, required-field highlighting, and
  visible post-publication feedback.
- Made visible dictionary evidence expanded by default and restored reliable hiding of
  inactive controls whose native `hidden` state had been overridden by shared flex styling.

- Strengthened the correction disclosure to state that API use is non-local and provider
  logging/retention/use/forwarding is outside application control; exposed dictionary
  provenance in the readable candidate summary and smoothed the manual-review handoff.
- Derived correction project identity from the selected dictionary's validated metadata,
  labeled the review identity, and retained explicit mismatch rejection for API callers.
- Clarified browser review state with readable validation/publication summaries and expandable
  JSON; protected open drafts from accidental Prepare replacement; visually distinguished
  disabled Apply/Export controls; and added persistent one-section/continuous review layouts.
- Restored the active saved review after refresh from its authoritative disk file, derived
  structured review/revision/export directories from one output root, guarded Clear with a
  confirmation, and disabled repeated publication of the same open review.
- Added an allowed-root-validated disk pointer for explicitly restoring the last review from a
  persistent output root across browsers and GUI restarts, plus a labeled status panel.
- GUI paths now reuse Windows/WSL/POSIX normalization before allowed-root authorization;
  Windows drive paths are convenient aliases, not a bypass around explicitly exposed roots.
- Compacted dry-run summaries to logical jobs, filenames, source decisions, and warning codes.
  Unchanged queue polling no longer replaces the table DOM, preserving text selection.
- Retained the submitted form across asynchronous staging so successful queue additions no
  longer display a false `GUI_API_UNAVAILABLE` message. Plan details now occupy a full-width
  row, and the implicit language is labeled `(auto)`.
- Dry-run and transcription now reject a batch containing separate episodes with the same
  derived job ID. They neither overwrite paths, misuse result versions as source aliases, nor
  silently prefer one format; explicit per-input aliases remain future work.
- Clarified the GUI footer as `EWP Transcriber v0.8.0` and `API v1.0`; license and warranty
  is now a direct link rather than an unhelpful plaintext disclaimer.
- Standardized repository and package licensing on `AGPL-3.0-only`, added the named author
  and licensing contact, and included the detailed licensing notice in distributions.
- Reconciled live status, roadmap, correction, and onboarding documentation with the
  completed fresh Ubuntu 24.04.4 WSL2 cross-workflow qualification and final YouTube YTT
  acceptance; retained intermediate ADR statements as historical test evidence.
- Expected application failures, policy warnings, command validation, batch records, and
  framework-generated usage errors now print stable diagnostic codes. Unexpected defects
  remain tracebacks rather than being mislabeled as expected failures.
- Added canonical public repository and issue-tracker links to package metadata. The separate
  project website remains intentionally unset until it is deployed.
- Clarified that internal beta versions remain untagged during requirements work and that the
  first public release is reserved for the checkpoint immediately before Docker-image work.
- Promoted the automated-correction traceability rows from implemented to verified using the
  already accepted provider, corpus, dictionary, privacy, and manual-review evidence.

- Expanded the primary README quick start, clarified that YTT/HTML are generated by the
  model-free export step, added post-installer uv PATH guidance, and refreshed the clean-WSL
  runbook.
- Changed fresh-transcription defaults to canonical JSON, machine-readable segments, and a
  clearly non-final TXT preview. Raw SRT/VTT remain explicit exports, while reviewed
  revisions are the recommended subtitle and translation source.
- Successful work-directory cleanup now also removes an empty per-run parent while
  preserving the configured work root and any sibling jobs.
- Automated correction now reports a concise canonical-input error when an empty shell
  variable or other mistake resolves to a directory, instead of exposing a Python traceback.
- Sanitized OpenRouter correction failures now retain the numeric HTTP status for diagnosis
  while continuing to discard provider bodies, request content, credentials, and arbitrary
  exception text.

## 0.4.0 - 2026-08-25

### Validated

- Passed the complete locked release gate: formatting, lint, static typing, and all 602
  tests.
- Built the 0.4.0 wheel and source archive, checked their metadata and contents for private
  benchmark or runtime material, and smoke-tested the installed wheel's import, CLI version,
  HTML export, and YouTube srv3 YTT export from an isolated target directory.

### Changed

- Added an explicit LM Studio translation `plain-text` mode for single-unit responses when
  a model translates successfully but emits malformed JSON around dialogue quotes. The
  complete response remains exact-operation-bound and is rejected when empty, fenced, or
  control-character-bearing; mode identity remains part of provenance and resume hashing.
- Added an explicit LM Studio translation `json-text` compatibility mode for models or
  backends that reject JSON Schema channels. It omits `response_format` while retaining a
  strict single-object prompt and local schema validation; mode changes prompt provenance
  and resume identity. Permanent HTTP failures now expose only the safe numeric status.
- Required disposable test and model-pilot outputs to use a dedicated `mktemp -d`
  directory under `/tmp`. Private corpora and repositories retain only reviewed,
  content-free evidence rather than resume state, candidates, exports, or intermediate
  benchmark bundles.

- Replaced the stale mid-v0.3 work status with a concise 2026-08-23 checkpoint: completed
  v0.1-v0.3 work, structurally accepted manual translation, the exact ordered remaining
  v0.4 workstreams, and explicitly deferred later work now have repository-resident resume
  instructions. Reconciled the completed v0.2 revision requirements from `planned` to
  `verified` and the manual translation roadmap from planned to implemented.
- Defined the initial v0.4 translation scope as one bidirectional Polish-English
  pipeline, led by Polish-to-English podcast translation. Source-faithful style is the
  default; optional provenance-recorded register (`preserve`/`formal`/`informal`) and
  discourse (`preserve`/`academic`/`general`) guidance cannot alter facts, intent,
  speaker identity, or sentence lineage.
- Made the latest manually verified transcript revision the preferred translation source.
  Raw ASR and automated-correction sources remain explicit comparison branches, while
  local translation models receive their own no-dictionary benchmark instead of
  inheriting correction-model rankings.
- Added Qwen 2.5 32B Q4, Bielik 11B Q8, Llama 3.3 8B Q8, MADLAD-400, and NLLB-200 as
  unvalidated local translation benchmark candidates. Polish-to-English and
  English-to-Polish will use separate gold sets, reports, and rankings, with `pl -> en`
  as the primary production gate.

### Added

- Added canonical result schema `1.1` timed-segment semantics with the closed `speech`, `music`,
  `laugh`, `cough`, and `note` vocabulary. Legacy results without `kind` load as `speech`;
  revised effective projection, segment JSON `1.1`, and subtitle cue planning retain kinds
  without inferring brackets, italics, colors, or other presentation.
- Added `dictionary correction propose` to derive repeated, consistent Polish correction
  candidates from exact canonical/manual-revision pairs, and `dictionary correction approve`
  to publish only a fully reviewed, project-scoped dictionary. Proposals retain corpus hashes
  and case scope; approved dictionaries retain proposal hash and never activate implicitly.
- Added explicit `revise correct --dictionary` integration for LM Studio and OpenRouter.
  Only source-present entries reach each editable chunk; dictionary ID/hash alter operation
  and resume identity, while immutable LLM revision provenance and audits record the selected
  project dictionary or `null`.
- Versioned Polish correction proposals to `1.1`. Every occurrence now includes marked
  source and corrected neighboring context for human decisions, while leading/trailing
  punctuation and quotation marks are removed from proposed lexical keys. Older context-free
  proposals therefore cannot be approved by the new command.
- Made correction dictionaries durable decision ledgers: approved and rejected mappings are
  both retained, only approved mappings reach providers, and `--previous-dictionary` carries
  exact prior decisions into later proposals instead of reopening them as pending. Added the
  versioned `dictionaries/<project>/<purpose>/<language-or-direction>/` repository catalog.
- Published the reviewed Ethics in the Loop Polish correction proposal and dictionary in that
  catalog: 19 approved and 22 rejected decisions across 22 compatible public podcast cases,
  with exact proposal lineage verified by the automated gate.
- Recorded the first dictionary-assisted Gemini 2.5 Flash correction smoke: four clean
  OpenRouter requests, exact dictionary provenance, no token/speaker drift or warnings, and
  `$0.023449` provider-reported cost. Quality claims remain gated on the matched no-dictionary
  control and manual-gold comparison.
- Reclassified correction dictionary `job_ids` as derivation lineage rather than a runtime
  allowlist, and required explicit matching `revise correct --project-id` selection. This keeps
  dictionaries project-scoped while allowing held-out and future episodes. Recorded the
  in-sample `s0e01` result: dictionary assistance removed 10/72 gold-relative errors versus
  2/72 without it, but no generalization claim is made because the case informed extraction.
- Recorded the held-out `s0e00` Gemini comparison. Dictionary assistance reduced raw WER by
  50% (22 errors to 11) versus 3 errors removed without a dictionary, with comparable runtime
  and cost and no token/speaker drift. Three exact edits unsupported by gold remain explicitly
  pending manual harm/style classification.
- Added `benchmark correction review`, which writes an exact-manifest-bound private `/tmp`
  artifact containing only unsupported edits, bounded normalized source context, and any
  overlapping gold edits for focused human classification. Content-free reports stay clean.
- Added an explicit normalization notice to private correction reviews so punctuation removed
  for lexical scoring is not mistaken for artifact corruption. Recorded owner review of the
  three held-out dictionary edits as supported ASCII domain conventions, with no harmful edit.
- Added strict, explicitly selected project translation dictionaries with direction/job
  scope, deterministic file hashes, request/resume identity, provider context, and immutable
  candidate provenance. Dictionaries remain disabled unless `translate automate --dictionary`
  names an exact JSON file.
- Added first-class dictionary provenance to translation snapshots and manual children,
  explicit dictionary-or-null declarations in audits, and deterministic export provenance
  sidecars so TXT/SRT/VTT remain clean while their dictionary version/hash stays auditable.
- Made semantic benchmark preparation inherit dictionary identity/hash directly from the
  immutable candidate, preventing dictionary-assisted runs from being reported as null.
- Added provider-neutral automated translation requests and responses with one exact owned
  sentence unit, bounded read-only context, deterministic operation identity, strict local
  response binding, and a network-free deterministic mock provider.
- Added bounded automated-translation execution, sanitized retry/permanent failure
  handling, private exact-operation resume entries, content-free operational summaries,
  and immutable LLM-provenance candidate construction without changing source artifacts.
- Added `translate automate` preview/publication for mock and LM Studio providers. The LM
  Studio adapter uses strict structured output, loopback-only endpoints by default, exact
  model/prompt provenance, usage capture, and separate exact-scope translation consent.
  Every CLI outcome warns that automated translation is non-final.
- Extended automated translation to deterministic failure-isolated directories with
  per-result resume state and latest-compatible source-revision selection. Added explicit
  manual acceptance through `translate prepare --parent-translation`: the protected review
  is prefilled only after exact candidate/source/style/unit validation, and apply publishes
  a new manual child with immutable parent ID, filename, number, and SHA-256 lineage.
- Added the first exact-lineage translation benchmark workflow. It stages automated
  candidates with compatible manual references, creates private per-unit human semantic
  assessments, and emits content-free direction-specific reports. Meaning fidelity is
  scored independently of lexical wording; names, explicit dictionary terminology, and
  project conventions use a separate compliance dimension. Pending review, artifact hash
  changes, source/style/unit mismatch, and mixed directions fail closed.

- Added the first strict v0.4 translation domain models for language direction, style,
  exact canonical/revision source identity, source verification status, parent lineage,
  manual/LLM provenance, speaker-safe timed units, statistics, warnings, and immutable
  complete snapshots. Contradictory verification, duplicate source ownership, invalid
  timing, and inconsistent statistics fail validation.
- Added deterministic translation source-unit planning that covers effective transcript
  tokens exactly once, treats speaker changes as hard boundaries, inherits integer
  timing, and reuses established abbreviation/domain non-ending rules.
- Added exact-lineage manual translation review preparation. It resolves raw or compatible
  revised text, records whether the source is raw, automated, or manually verified, and
  emits immutable source context with blank target-language fields as the only intended
  editor input.
- Added deterministic `EWP-TRANSLATION 1` rendering and strict parsing. Compact metadata,
  unit identity, speaker, timing, source hashes, and token ownership are machine-owned;
  only `> ` target lines are editable, and changed source text fails hash validation.
- Added pure manual-translation preview construction. Reviews with any blank target fail;
  complete reviews become unpublished immutable snapshots with normalized target text,
  exact source mappings, manual provenance, direction/style, and verified statistics.
- Added locked, non-destructive translation review publication and atomic language-qualified
  immutable translation numbering. Apply-time source validation reconstructs canonical or
  revised units and rejects changes to metadata, speakers, timing, hashes, or token ownership.
- Added the first model-free `translate prepare`, `translate preview`, and `translate apply`
  CLI workflow for one Polish-English file. It exposes explicit target language and optional
  style guidance, requires the exact canonical/revision source at validation, and publishes
  only complete manual translations; later slices added batch operation and exports.
- Added a Draft 2020-12 translation JSON Schema and a validated English-to-Polish example
  snapshot. Schema validation and strict domain-model validation jointly cover portable
  structure plus cross-field source, direction, ownership, timing, and statistics rules.
- Documented the shipped single-file manual translation workflow in the complete operator
  runbook and CLI contract, including preferred verified input, exact source replay,
  protected review fields, style controls, immutable naming, and explicit pending slices.
- Added deterministic translation-review discovery plus exact batch source resolution.
  Revision-directory selection uses the highest compatible revision validated against the
  canonical SHA-256; applying prepared reviews resolves their recorded filenames, hashes,
  IDs, numbers, and methods rather than guessing from timestamps.
- Extended manual translation prepare, preview, and apply to deterministic directories
  with per-item failure isolation and exit-code-5 partial failure semantics. A revision
  directory selects each result's latest exact compatible revision; prepared reviews
  later resolve their recorded canonical and revision identities independently.
- Updated the complete runbook and CLI specification with copyable batch translation
  commands, the distinct `--revision` prepare and `--revisions-dir` validation roles,
  retry guidance, exact per-result selection, and current audit/export limitations.
- Added deterministic model-free TXT rendering from immutable translation snapshots.
  Multi-speaker output uses stable speaker IDs because display names remain presentation
  data; publication is locked, collision-safe, and idempotently skips identical output.
- Added `transcriber translate export` as the first translated-output command. It accepts
  one immutable translation JSON, normalizes Windows/WSL paths at the application boundary,
  writes deterministic UTF-8 TXT, and reports written versus identical skipped output.
- Added conservative SRT/VTT planning from translated sentence units. Target text is
  wrapped and, only when required, split inside its inherited unit interval; no target-word
  alignment is claimed. Overlapping source intervals remain explicit and render safely.
- Extended translated TXT/SRT/VTT export to directories with deterministic snapshot-only
  discovery, per-file failure isolation, recursive opt-in, idempotent skips, and exit-code-5
  partial failure reporting.
- Documented translated TXT/SRT/VTT single and batch export, including stable-ID speaker
  presentation, inherited sentence timing, the absence of target-word alignment claims,
  collision preflight, idempotent replay, and the remaining audit/provider scope.
- Added exact-source translation audit reconstruction and locked idempotent audit
  publication. Audits reopen the canonical and optional revision source, validate every
  unit's IDs, speaker, timing, token ownership, and hash, then pair reconstructed source
  text with target text for human inspection.
- Updated the complete runbook and CLI contract with translated batch export and exact
  source/revision audit commands, output semantics, non-mutating audit mode, and the
  sentence-timing precision boundary.
- Added the dedicated translation playbook covering corrected-Polish source selection,
  batch prepare/edit/preview/apply/audit/export, VS Code editing, external web-model
  privacy, `[cite: N]` removal, and fail-closed migration from legacy translated reviews.
- Reclassified the grammar-edited Polish private corpus as correction/translation source,
  not ASR ground truth, and the artistically translated English corpus as pipeline-only
  validation until a narrower translation-quality reference contract exists.
- Fixed English sentence boundaries ending in closing quotation marks while preserving
  both English `."` and Polish `”.` punctuation in sentence planning and exports.
- Prevented legal case names such as `Battle v. Microsoft` from splitting translation
  units after `v.`. Documented that sentence units improve subtitle timing, audit locality,
  and bounded retries without asserting one-to-one Polish-English syntax; bounded
  speaker-chunk unitization remains a versioned fallback if corpus evidence requires it.
- Added the v0.4 manual-first translation contract: exact source lineage, deterministic
  speaker-safe sentence units, immutable complete artifacts, staged batch review and
  export, and a shared validation boundary for future instruction and specialist models.

### Validated

- Prepared 24 English translation reviews from the private canonical corpus and each
  result's latest exact compatible corrected Polish revision: 24 prepared, 0 failed.
- Applied and exported the operator-mapped English corpus without errors; generated SRT
  and VTT were reported readable. This is structural pipeline evidence, not an accuracy
  score for artistically translated text.
- English sentence boundaries ending in closing quotation marks, Polish punctuation with
  a period after the closing quote, and preservation through translated TXT/SRT output.

## 0.3.0 - 2026-08-21

### Changed

- Promoted the provider-neutral local/cloud automated-correction, benchmarking, and
  fresh-install onboarding work to internal beta version 0.3.0. Automated output remains
  a non-final candidate requiring manual review.

- Accepted the fresh v0.2.1-era benchmark instance as sufficient current installation
  evidence and deferred redundant installation-only testing. Full clean-machine testing
  from installation through all functional workflows will run manually once those
  workflows exist, then become automated.
- Deferred private manual-gold errata publication until translation-pipeline testing,
  when the private benchmark will also gain manually approved translation examples and
  correction/translation manifests will be rebuilt together.
- Refined the v0.4 platform-export roadmap with a conservative YouTube-oriented TTML
  1.0-compatible profile, stable speaker styles and configurable ordered color defaults;
  made synchronized HTML explicitly a CSS/JavaScript-free embeddable fragment; and added
  a versioned canonical timed-event `kind` design task for speech and non-speech events.
  The reviewed agent-pack RSS material remains publishing policy rather than current
  exporter scope.

### Added

- Added opt-in raw, manually revised, and translated embeddable HTML transcript fragments with
  sentence-level seek buttons, explicit speaker turns, stable timing/speaker/kind data,
  escaped untrusted text, language metadata, and no embedded styling or behavior.
- Added a separate consuming-site HTML audio-player example with site-owned CSS/JavaScript,
  click and keyboard seeking, playback highlighting/following, accessible focus,
  reduced-motion handling, explicit theme and auto-follow controls, light/dark
  presentation, and readable unenhanced markup. Cross-browser seeking waits for media
  metadata and seek completion before playback, and the example includes a range-capable
  local server for Chromium media seeking. Real-media qualification passed Firefox,
  LibreWolf, Chrome, and Brave, including theme/auto-follow controls and a readable
  no-script fallback. Minor sentence-boundary acoustic spill remains an explicitly
  accepted inherited word-alignment limitation.

- Added an opt-in deterministic YouTube srv3 YTT export with one existing planned cue per
  paragraph, preserved planned line wrapping, millisecond timing, configurable stable
  speaker pens, bottom-center placement, structured non-speech italics, and parser-backed
  validation. This replaces the standards-based TTML profile after two accepted uploads
  discarded its wrapping, alignment, and colors. After a subsequent srv3 upload flattened
  `<br/>` elements, the renderer adopted the owner-supplied corrected template's literal
  in-paragraph newlines and near-white `#FEFEFE` default pen. The resulting bytes passed an
  unlisted YouTube upload with correct two-line wrapping, distinct speaker colors,
  centering, timing, turn labels, and Polish diacritics.

- Correction benchmark report v5 now derives exact normalized source-relative edit sets
  for candidate and manual gold, reporting per-case and aggregate true-positive,
  unsupported, and missed edits with precision, recall, and F1. Unsupported means absent
  from the exact hashed gold and still requires manual style/harm review.
- Added `benchmark correction operations` and persisted sanitized per-chunk execution
  metrics so private resume state can report attempts, retries, provider elapsed time,
  request/token volume, provider-reported cost, and legacy entries lacking those fields.
- Added `transcriber revise correct --revision PATH` so automated correction can start
  from an exact compatible immutable revision. The result is a complete standalone child
  snapshot that retains prior edits and records the parent's ID, number, filename, and
  SHA-256; incompatible lineage is rejected before provider execution.
- Added an explicit OpenRouter cloud-correction adapter with HTTPS-only uncredentialed
  endpoints, environment-only lazy bearer-key loading, structured-output capability
  requirements, disabled route fallback, sanitized retry handling, reported token and
  micro-USD cost capture, and network-isolated tests.
- Extended `transcriber revise correct` with explicit provider selection, `--allow-cloud`,
  and configurable API-key environment naming. Strict offline and reject consent stop
  before key lookup or request creation; cloud output remains a non-final candidate.
- LLM revision provenance now records effective non-secret adapter parameters while
  excluding credentials.
- Added explicit OpenRouter reasoning-token budgets, including `0` to disable supported
  model thinking. The setting affects request/resume identity and provenance so default,
  disabled, and enabled reasoning runs cannot be silently conflated.

### Fixed

- Required an exact-parent manual child to receive a translation number greater than its
  parent even when candidates and accepted translations use separate output directories.
- Restricted dictionary context to entries whose source form occurs in the owned unit. The
  first exploratory dictionary pilot sent every entry to every request and caused an
  invented speaker label, so that run is rejected as benchmark evidence.
- Tightened applicable dictionary matching to Unicode word/phrase boundaries. Entries are
  selected from source text only—`Szymon` never rewrites a source `Simon`—and are not
  post-translation substitutions.
  The versioned selection contract participates in operation/resume identity and candidate
  provenance so matcher changes cannot silently reuse older provider responses.
- Removed a contradictory JSON instruction from LM Studio `plain-text` translation mode.
  Raw prose is accepted directly; Bielik's valid one-field `target_text` or
  `translated_text` compatibility envelope is strictly parsed and unwrapped locally.
  Its observed optional string `translator_notes` or `translation_notes` field is discarded
  with a content-free per-unit artifact warning; malformed JSON, unknown fields, and
  non-string values fail. The versioned compatibility-envelope contract participates in
  prompt hashing, provenance, and resume identity.
- Unwrapped Bielik's observed valid JSON-string serialization in `plain-text` mode so
  transport quotation marks cannot become transcript punctuation. Strengthened the
  source-faithful prompt to copy personal names exactly without anglicizing or normalizing
  them; both changes participate in prompt/resume identity.
- Recorded the corrected 79-unit Bielik baseline: 79 requests, zero retries, 26,833 ms
  provider time, 1,051 target tokens, no provider warnings, and no remaining transport or
  ownership defects. Manual review still found semantic errors and three personal-name
  convention failures, so the candidate remains non-final pending exact-parent correction.
- Qualified the corrected Bielik candidate through exact-parent manual publication as
  translation 2, a successful 79-unit audit, and deterministic TXT/SRT/VTT export. The
  automated artifact remains non-final and distinct from its accepted manual child.
- Completed the first human semantic translation report for the no-dictionary Bielik
  `pl -> en` baseline: 71/79 faithful units, 6 minor errors, 2 major errors, semantic pass
  rate `0.89873418`, and 6 separately reported convention violations.
- Completed the paired general project-dictionary report. Semantic results were unchanged
  at 71/79 faithful, while convention violations fell from 6 to 2 without harmful insertion;
  remaining name failures confirm dictionary context is not an enforcement mechanism.
- Documented the planned production order: Gemini 2.5 Flash dictionary-assisted Polish review
  candidate, manual Polish acceptance, export, then translation from the accepted revision.
  Correction and translation dictionaries remain separate auditable artifacts.
- Warned whenever a single-file translation uses an unreviewed automated transcript
  revision. This remains supported, but artifacts retain exact `automated_candidate`
  verification rather than claiming manual source verification.
- Added explicit `--context-units` control and fixed Polish unit planning so a numeric
  period followed by a lowercase continuation, such as `6. rano`, does not create a false
  sentence boundary. This supports a zero-context rerun after the Bielik pilot showed
  adjacent-unit repetition and omission caused by context leakage.

- Automated correction alignment now treats canonical speaker boundaries as hard mapping
  constraints. Repeated or ambiguous text can no longer be mapped across speakers after a
  provider has returned the required immutable speaker blocks; manual review retains its
  explicit speaker-reassignment capability.
- Structured correction responses are now bound to the active synchronous request locally
  instead of trusting the model to echo an opaque operation hash exactly. Resume identity,
  text reconstruction, speaker blocks, and all safety gates remain strict.
- Invalid structured-response errors now include only content-free provider finish reason
  and response character count, allowing truncation to be distinguished from malformed
  stopped output without logging transcript or model-response text.
- Provider responses with `finish_reason=error` are now classified as sanitized retryable
  generation failures and use the existing bounded retry policy. Malformed content that
  finishes with `stop` or `length` remains a hard validation failure.

- Added the normative v0.3 automated-correction contract: provider-neutral adapters,
  faithful-repair policy, deterministic single-owner chunks with read-only overlap,
  locally derived change validation, scoped API consent, retry/resume/batch behavior, immutable
  revision provenance, private-corpus benchmark requirements, and acceptance checklist.
- Added the first provider-neutral correction primitives: strict request/response/change
  models, deterministic gap-free editable chunking with bounded read-only context, stable
  operation/content hashes, and a network-free deterministic mock provider.
- Added local provider-response verification that rejects wrong operation identities and
  deterministically derives exact insert/delete/replace changes from corrected editable
  text before revision construction.
- Connected validated mock responses to ordinary review anchors and the existing
  deterministic revision aligner, producing immutable LLM-provenance snapshots without
  letting providers construct mappings or artifacts. Added explicit `mock` endpoint
  provenance for network-free test revisions.
- Added strict `[correction]` configuration for target, maximum editable, and read-only
  context token counts, including packaged/example defaults and invalid-order rejection.
- Added application-facing mock correction preview and atomic apply operations that use
  resolved configuration, preserve the canonical result, and publish through the existing
  locked revision allocator.
- Added deterministic non-recursive mock correction batches with natural result ordering,
  preview/apply modes, per-result failure isolation, aggregate counts, and the existing
  continue-or-stop batch policy.
- Hardened resumable correction operation identities with provider, model, prompt,
  language, editable/context bounds, chunk index, and content hash.
- Added private, mode-restricted, immutable per-chunk resume entries. Only fully validated
  responses with an exact provider/model/prompt/operation identity are reused; corrupt or
  stale entries fail before another provider call.
- Added strict hash-bound automated-correction benchmark manifests and lexical reports
  for canonical-to-gold and earlier-revision-to-gold tasks, with exact base-lineage
  validation and no transcript text in reports.
- Wired an explicit resume directory into single and batch correction operations so
  validated chunk responses can be reused without repeating provider calls; preview
  remains write-free when no resume directory is supplied.
- Added a provider-independent correction API consent policy with distinct local/cloud
  warnings, strict-offline cloud blocking, reject/accept-once/persist choices, exact-scope
  reuse, mock bypass, and non-interactive denial by default.
- Added an atomic private consent store containing only exact non-secret scopes, with
  missing-store denial semantics, strict corruption handling, and duplicate suppression.
- Added bounded provider execution with adapter-enforced per-attempt timeouts, explicit
  retryable/permanent failure classes, retry counts, and sanitized latency metrics.
- Provider execution now replaces adapter exception details with stable sanitized errors,
  preventing request text, endpoint details, or credentials from escaping through failures.
- The provider-neutral response contract now carries optional token and micro-USD usage;
  execution outcomes combine it with request, retry, and latency measurements.
- Added the first real provider adapter for LM Studio's OpenAI-compatible loopback API,
  with a faithful-transcript structured prompt, strict JSON parsing, usage capture,
  injectable network-free tests, and rejection of remote or credential-bearing URLs.
- Added disabled-by-default LM Studio correction configuration for exact model/endpoint,
  prompt, chunking, timeout/retry policy, temperature, and private consent-store location.
- Added the production correction application boundary: exact-scope consent is resolved
  and optionally persisted before request construction, configured timeout/retry policy
  is applied, and local/mock provenance records the provider's actual endpoint kind.
- Added `transcriber revise correct` for single-result LM Studio correction with exact
  model/endpoint selection, warning and reject/once/persist consent, preview/apply modes,
  private resumable chunk state, and zero-call rejection behavior.
- Prompt provenance and resume identity now hash the adapter's actual system prompt and
  structured-response schema, preventing stale response reuse after prompt-contract edits.
- Added `transcriber benchmark correction build|report` to create private exact-hash
  bundles, select the latest compatible manual gold, and report separate
  canonical-to-gold, canonical-to-LLM, and gold-to-LLM lexical comparisons without
  transcript text.
- Added correction-specific lexical normalization that excludes balanced parenthetical
  and square-bracket review annotations, preventing manual speaker notes from being
  counted as ASR or LLM errors.
- Tightened the LM Studio correction prompt to v11 after the Qwen 14B v10 pilot scored
  worse than raw ASR against manual gold. Copying is now the default; grammar repair,
  stylistic rewriting, ambiguous edits, and dictionary-free terminology normalization
  are explicitly forbidden.
- Added a provider-independent numeric-literal safety gate: automated correction must
  preserve recognized digit-based values exactly, preventing factual mutations such as
  `5.2` to `4.0` while allowing punctuation changes around the same value.
- Added a short/long fixture matrix covering repeated words, punctuation, speaker changes,
  chunk boundaries, gap-free ownership, and bounded read-only overlap. Updated acceptance
  status for the already-tested exact-scope consent matrix without closing the remaining
  revision-child or comprehensive artifact-scan work.
- Added an explicit fresh-Ubuntu installer/verifier. Read-only verification is the default;
  `--install` confirms before Ubuntu package changes and locked-environment setup. The
  script never clones/pulls Git, installs an NVIDIA display driver, or downloads gated
  models. Root README onboarding now has concise installation and usage examples.
- Added a network-isolated full-path cloud privacy test covering consent persistence,
  private resume state, immutable revision, reconstructable audit, exact-hash benchmark,
  and content-free report. The bearer credential must appear only in the captured request
  header, never in any persisted artifact; consent, manifest, and report also reject
  transcript payload exposure.
- Added an explicit LM Studio `json-text` compatibility mode for model/chat-template
  combinations that fail grammar-constrained structured output. JSON Schema remains the
  default; the fallback omits only `response_format`, retains strict whole-response schema
  parsing and all correction safety gates, and has a distinct prompt/resume identity.
- Plain-JSON compatibility requests now include an initialized response template and
  explicitly distinguish immutable task input from the only allowed response keys. This
  prevents unconstrained models from echoing request fields as their response contract.
- Removed the redundant opaque operation ID from the synchronous plain-JSON fallback
  response after Bielik copied it with a one-character mutation. The application binds the
  response locally while retaining exact block count, order, speaker, text, and drift gates.
- Added the correction `output_mode` setting to the editable example configuration and a
  parity regression test; it was already present in packaged defaults and the CLI.
- Removed obsolete per-token metadata from LM Studio requests after a 120-token Qwen 32B
  chunk exhausted an 8K context before completing its JSON response. Speaker-block text and
  bounded context remain provider-visible; exact token identity stays local. The versioned
  wire contract now participates in prompt/resume identity.

### Validation

- Completed the reasoning-disabled Gemini 2.5 Flash baseline on the full 24-episode,
  77,607-word private corpus. All 24 revisions and audits were produced; WER against manual
  gold improved from `0.01077914` to `0.00889891` (17.44% relative reduction), with
  canonical-to-candidate WER `0.00338242`, zero speaker changes, and 19 retained alignment
  warnings. Report v3 measured 146 net lexical errors removed across 21 improved, 2
  unchanged, and 1 regressed episode. The 395 audited operations remain review candidates
  rather than final edits.
- Targeted review of the nominally regressed `S2E1` case found two genuine corrections
  (`postanowiamy` to `postanawiamy` and `króciczkami` to `króliczkami`) that exposed errors
  remaining in manual gold, plus one newly wrong numeric change. The hashed report remains
  reproducible but its quality interpretation is provisional until a later corrected gold
  revision is benchmarked. Recurring `na biało` and spoken-email forms were recorded as
  project-dictionary candidates.
- Review of nominally unchanged `S0E08` found another manual-gold error (`urodzin` rather
  than `rodzin`). `S0E10` exposed a valid Latinized/diacritic proper-name equivalence that
  exact WER cannot represent. Project-dictionary alias equivalence is now planned without
  unsafe global diacritic folding.
- Recorded a six-item pending private-gold errata table after high-improvement sample
  review found three further missed manual corrections in `S2E4v2_part2`. The sampled
  Gemini output was predominantly useful but retained near-corrections such as `Oba`
  instead of `obaj` and `IDEAS` instead of the project name `AIDEAS`; automatic
  finalization remains rejected.
- Deferred the corrected-gold Gemini rerun on the roadmap; the current 24-case report is
  the settled provisional baseline for near-term implementation work.
- Recorded about 25m21s operator wall time for the complete run including retries. Validated
  resume state accounted for 651 requests and `$1.218604`; the provider dashboard showed
  about `$1.34`, correctly remaining authoritative for billed malformed/rejected responses.
- Correction benchmark report v3 now records net and relative lexical error reduction,
  candidate edit distance, net correction efficiency, and improved/unchanged/regressed
  case counts without exposing transcript content.
- Correction benchmark report v4 adds content-free per-case and aggregate immutable
  revision statistics, total change activity, warning/alignment-warning counts, and
  speaker changes. Gold-relative edit-quality and provider runtime/usage aggregates remain
  explicitly open rather than being inferred from WER.

- Completed the authorized three-case OpenRouter pilot under prompt v11 and 120/160/30
  chunks. DeepSeek V3 0324 reduced 76 raw word errors to 67 (`0.00659124` WER) in about
  19m31s for `$0.088462`; manual review retained deletion/context caveats.
- Gemini 2.5 Flash with reasoning explicitly disabled reduced 76 raw errors to 63
  (`0.00619774` WER) in about 3m01s for `$0.155583`. Gold-context review accepted all
  audited edits. It is the leading pilot but remains a non-final review candidate.
- Stopped the preliminary OpenRouter Qwen 2.5 72B run after its short case deleted a spoken
  token. The rejected larger-chunk smoke cost `$0.004423`; no longer paid cases were run.
- Stopped the Gemini 2.5 Flash 1,024-token reasoning branch after its short case delivered
  the same lexical repairs as reasoning-disabled Gemini while taking 2.34 times longer and
  costing 1.84 times more. Disabled reasoning remains the cloud baseline.

- The three-case private Bielik 3.0 11B Q8_0 pilot passed the explicit plain-JSON adapter
  contract with no speaker changes. It remained deliberately conservative but scored
  `0.00767339` WER against manual gold versus `0.00747664` for raw ASR, so it does not yet
  pass the correction-quality gate. Private transcript text and artifacts remain outside
  the repository.
- Manual audit classified Bielik's five affected tokens: one correct repair, one still-wrong
  plausible repair, one newly wrong substitution, and a harmful two-word deletion. The
  resulting net two additional word errors exactly account for the measured regression.
- The compact-contract Qwen 2.5 32B three-case pilot completed without warnings and
  improved lexical WER by 1.3% over raw ASR, but took about 36 minutes 41 seconds. Manual
  audit found five useful repairs, two harmful changes, and two context-dependent
  punctuation edits, so a larger-chunk performance/quality pilot is required before any
  full-corpus run.
- Clarified that correction scoring excludes complete balanced round/square editorial
  annotations, whereas quotation marks alone are normalized away and all quoted words
  remain scored. Manual review accepted both Qwen 32B punctuation-only edits.
- Automated correction is now explicitly labelled in CLI output, help, requirements, and
  operator instructions as a non-final review candidate. Manual acceptance must verify
  wording, speakers, punctuation, quotation marks, and sentence boundaries before final
  publication or benchmark-gold use.
- Added planned unattended local benchmark orchestration through verified model
  load/readiness and optional unload APIs, with exact model/quant/backend/prompt/chunk/sampling/hardware
  matrix identity and no automatic paid-cloud authorization.
- Recorded the Qwen 32B 400/500/60 preview timing: 33 minutes 19 seconds across the same
  three cases, only 9.1% faster than 120/160/30. Quality remains pending publication and
  manual audit because the medium case lost one token.
- Rejected the Qwen 32B 400/500/60 optimization after publication and audit: it matched raw
  ASR WER, made 11 rather than nine changes, deleted a source token, repeated an incorrect
  proper-name edit, and introduced unsupported grammatical-form changes for only a 9.1%
  runtime reduction.
- Rejected the Bielik 11B F16 control: at 21.7 GB VRAM it took about 56 minutes 29 seconds,
  exactly matched the earlier Q8 lexical scores and harmful substantive edits, and added
  only unscored capitalization changes. It demonstrated no quality benefit over Q8.
- Completed the fair current-contract Bielik Q8 control at about 20.9 GB VRAM: 12 minutes
  15 seconds, roughly 4.6 times faster than F16, but one correct lexical repair was offset
  by a harmful two-word deletion and the result remained 1.3% worse than raw ASR.
- Added the consolidated local three-case comparison with exact prompt/contract identity,
  WER, runtime, manual audit outcome, and observed provider/runtime failures. No local
  candidate currently justifies an unattended full-corpus correction run.

### Documentation

- Updated v0.3 traceability and acceptance status to distinguish implemented neutral
  infrastructure from provider-dependent prompt, CLI, benchmark, and review work.

- Documented exact LM Studio model discovery, explicit local consent, safe preview/apply
  and resume paths, initial local benchmark candidates, and the deferred OpenRouter stage.
- Updated implementation status after completing LM Studio CLI/consent wiring and exact
  prompt-content provenance; the first real local smoke run remains an operator gate.
- Added benchmark-gated correction preset targets: GTX 1070 as the lowest planned GPU
  validation floor, optional CPU-only operation with 16 GB recommended RAM, and a later
  separate Apple Silicon build with 16 GB unified memory. Recorded candidate model and
  quantization matrices plus rented MacinCloud/Scaleway CLI/GUI validation provenance.
- Made non-loopback LM Studio endpoints explicitly configurable for LAN/VPN/Tailscale-like
  use while retaining loopback by default, exact-scope consent, and an additional network
  warning. Recorded the Qwen 14B Q8_0 32K/18.5 GB VRAM observation and planned Bielik
  Q8_0 versus CPU-offloaded F16 comparison as configuration-specific evidence.
- Added the post-functional public benchmark plan: BIGOS, FLEURS, Common Voice, and
  Multilingual LibriSpeech for lexical evaluation; VoxConverse and AMI for diarization;
  strict split/license/provenance rules; an optional separate general Polish dictionary;
  and a later licensed three-or-more-speaker public-podcast evaluation tier.
- Revised the LM Studio faithful-correction prompt to v2 after the first synthetic smoke
  response failed strict validation. The prompt now defines zero-based half-open token
  spans, verbatim `before` text, exact reconstruction, sorted changes, context exclusion,
  and the required no-change response without weakening local validation.
- Revised the prompt to v3 after Qwen returned a contradictory lexical edit and unchanged
  corrected text. Added deterministic category semantics, explicit final reconstruction,
  and conservative uncertainty rules; punctuation/capitalization/sentence-boundary labels
  can no longer conceal lexical changes.
- Recorded the successful public synthetic LM Studio preview under
  `faithful-correction-v3`: 8 revision tokens, zero warnings, and no publication. Cached
  response reuse and immutable apply subsequently passed without another provider request;
  all generated state and revision artifacts were mode `0600`.
- Added the operator runbook for the local Qwen correction benchmark: private path setup,
  exact input evidence, a short/medium/long pilot, resume-backed immutable publication,
  manual faithfulness review, and gated sequential full-corpus candidate generation.
  Final scoring remains blocked on the operator-facing manifest/report slice.
- Added content-free correction-span mismatch diagnostics (span, token counts, and
  character counts, alternate source positions, and truncated hashes) so private provider
  failures can be investigated without logging transcript text. Documented that Bash
  requires WSL paths even though the application
  accepts Windows paths, and that LM Studio developer logs expose full transcript payloads.
- Recorded the safely rejected three-case Qwen pilot and its observed RTX 3090 load of
  approximately 23.3 GB VRAM at 95%+ utilization; full-corpus execution remains blocked.
- Made both pilot loops stop at the first failed preview or apply instead of proceeding to
  later private-corpus cases.
- Replaced model-counted numeric spans in the LM Studio wire contract with copied stable
  first/last editable token IDs after the private pilot proved a six-position indexing
  error. Prompt v4 maps IDs deterministically back to core half-open spans and still rejects
  unknown/context/reversed IDs, non-verbatim before text, and inconsistent reconstruction.
- Replaced the ambiguous inclusive start/end token-ID pair with an explicit ordered list of
  every changed token ID after Qwen treated the end ID as exclusive. Prompt v5 requires
  non-empty, unique, contiguous editable IDs before the adapter derives a core span.
- Added content-free LM Studio schema diagnostics that report only failing field paths and
  validation error types, never raw response values or transcript payloads.
- Clarified in prompt v6 that every proposed-change object represents one contiguous source
  replacement and that non-adjacent corrections require separate objects. Content-free
  failures now include only the referenced numeric positions and count.
- Added prompt-v7 minimal-span and copy-only-before rules with a concrete generic example
  after Qwen removed punctuation from otherwise correctly addressed source evidence. Exact
  local before-text validation remains unchanged.
- Simplified prompt v8 to one stable start token ID plus verbatim `before` after Qwen copied
  an exact 11-token span but listed only four IDs. The adapter derives one unique contiguous
  end locally and rejects unknown/context starts or unmatched source text.
- Redesigned prompt v9 after both default and 120/160-token pilots proved redundant model
  patch metadata unreliable. LM Studio now returns corrected editable text; the application
  deterministically derives exact insert/delete/replace spans, before/after text, categories,
  speaker mapping, alignment, and audit. Optional provider annotations are advisory only.
- Added prompt-v10 speaker-block round-tripping after a text-only local diff crossed a
  speaker boundary. Block count/order/IDs are immutable and correction changes are derived
  independently inside each block.
- Clarified that review of the official `uv` installer is optional unless local policy
  requires it, replaced the clone placeholder with the public repository URL, and added
  current dependency/model download and free-space estimates to installation guidance.
- Added a root Requirements section covering the validated WSL2/Ubuntu/RTX 3090 baseline,
  expected but unvalidated Ubuntu deployment shapes, and future per-preset requirements.
- Added a v0.3 backlog item for a reviewable installation and verification script.
- Scoped the v0.3 installer to fresh installations, kept existing-installation updates
  separate, and specified future README Prerequisites, How to install, and How to use
  sections. Standardized storage guidance at a recommended 20 GB minimum (preferably
  SSD) while deferring RAM/VRAM qualification to preset validation.
- Recorded acceptance of the second model-free fresh-WSL installation and postponed
  redundant full model/runtime revalidation until later functional changes require it.
- Assigned automated local/cloud correction and fresh-install onboarding to v0.3; moved
  translation, synchronized HTML export and its acceptance tests, and optional
  project-scoped dictionaries to v0.4. Kept advanced 3+ channel handling in the later
  roadmap without assigning a release.

### Fixed

- Added model-independent automated-correction safety gates: LM Studio speaker blocks
  cannot exceed conservative token-count drift, and revision alignment cannot publish
  any automated speaker reassignment.
- Replaced the quadratic pure-Python lexical scorer with RapidFuzz's exact optimized
  Levenshtein edit operations, allowing long podcast transcripts to produce WER/CER
  correction reports in seconds rather than stalling on character-level comparison.

## 0.2.0 — internal release candidate — 2026-08-19

### Added

- Expanded the future GUI backlog with explicit About, License, and Source Code sections,
  including a direct link to the public repository.
- Included the full GNU AGPL v3 license in source
  and distribution artifacts, and documented contribution and warranty terms.
- Added the first v0.2.0 implementation slice: strict immutable transcript-revision
  domain models, artifact loading, and exact canonical-base compatibility validation.
- Added locked revision-number allocation and atomic, no-overwrite publication with
  base-result-version-aware filenames.
- Added strict `EWP-REVIEW 1` parsing and deterministic rendering with directive escaping,
  extension-header preservation, and stable base/anchor/speaker validation errors.
- Added model-free review preparation from completed canonical results, with complete
  segment-boundary anchors and speaker-turn preservation.
- Added locked, non-destructive review-file publication and an application-facing
  single-file review preparation operation.
- Added deterministic non-recursive result discovery and isolated batch review
  preparation with the configured continue/stop policy.
- Added strict transcript-revision configuration and the model-free `revise prepare`
  CLI for single canonical results and deterministic directory batches.
- Added deterministic per-anchor review alignment with merge, split, insertion, deletion,
  punctuation, speaker-reassignment, ambiguity, statistics, and provenance handling.
- Added non-mutating `revise preview` and atomic single-file `revise apply`, with
  `apply --no-apply` using the same validation and alignment path as preview.
- Added deterministic directory preview/apply, recursive opt-in, per-review failure
  isolation, and runtime-configured continue/stop behavior.
- Added safe external-editor review workflow with config/`VISUAL`/`EDITOR` resolution,
  automatic apply after a successful close, and a revision-free `--no-apply` path that
  retains the edited review.
- Added the shared effective-transcript resolver and revision-aware TXT/SRT/VTT/segments
  export through `--revision none|latest|PATH`, with inherited timing, corrected speakers,
  distinct filenames, and revision provenance in segments JSON.
- Added reconstructable base-relative revision audits, standalone `revise audit`, and
  optional `revise apply --audit` publication without making audit data authoritative.
- Added exact parent-revision identity verification, standalone child snapshots, and
  sibling revision behavior that shares a base without implying false lineage.
- Added deterministic revision-aware directory export with compatible revision
  selection, natural result ordering, per-result failure isolation, recursive opt-in,
  safe duplicate replay, aggregate/JSON reporting, and mixed-batch exit code 5.
- Defined future LLM correction as conservative transcription repair rather than prose
  editing, with mandatory proposed-change lists and independently reconstructed audits.
- Defined explicit multichannel topology handling, scoped cloud/local API privacy
  consent, and the complete future `Instructions/` operator-runbook release requirement.
- Defined the input preference order: synchronized mono files per speaker first,
  split-speaker stereo second, and reviewed diarization for mixed program audio. The
  future 3+ channel fallback is automatic only for recognized layouts and uses a
  dedicated topology confirmation—not `--force`—when layout evidence is insufficient.
- Recorded that advanced 3+ channel implementation is deferred to V2 or later. The
  completed 24-episode audio/corrected-transcript corpus remains a private benchmark
  outside Git until all episodes are public and a separate publication review passes.
- Expanded post-0.2 goals for local/cloud correction benchmarks, manual review of model
  revisions, manual/automatic translation lineage, approved project-dictionary candidate
  mining, and synchronized accessible HTML player testing. Added an explicit v0.2.0
  release-closure checklist without importing those later features into its scope.
- Defined private-corpus gold selection: the highest compatible revision is accepted
  gold, while earlier revisions remain intermediate inputs for raw-to-gold and
  revision-to-gold correction benchmarks.
- Closed the v0.2.0 manual-revision acceptance checklist against automated and private
  24-episode operator evidence. Added explicit regression coverage for proper-name and
  sentence-boundary edits, ambiguous alignment, long-gap insertion warnings, repeated
  words, anchor integrity, base immutability, and concurrent revision allocation.
- Added the top-level `Instructions/` operator entry point covering installation links
  and every shipped CLI workflow. Clarified root/revision help discovery and corrected
  batch-capable `export`, `revise preview`, and `revise apply` argument help.
- Added a concise WSL operator runbook for preparing, editing, previewing, applying,
  auditing, exporting, retaining, and recovering transcript revisions.
- Added optional audit publication to the automatic `revise edit` apply path.
- Clarified editor setup with exact project/user configuration paths, a copy-pasteable
  nano workflow, and errors that distinguish editor commands from environment variables.
- Prevented automatic revision creation when an external editor exits without changing
  the review, and documented staged Windows-editor review for long transcripts.
- Clarified that revisions intentionally store corrected token mappings, while corrected
  phrase/speaker segments are materialized as revision-aware derived exports.
- Made staged prepare, manual Windows Notepad editing, apply, and export the primary
  correction runbook; retained `revise edit --editor nano` as an optional shortcut.
- Documented the complete bulk correction workflow: directory preparation, manual
  editing, batch preview/apply with audits, partial-failure handling, safe targeted
  retries, and the current one-result-at-a-time export limitation.
- Made Windows VS Code the preferred manual review editor because its search and
  change-all-occurrences tools accelerate repeated corrections; retained Notepad as a
  small-edit fallback and documented why GUI editors must be opened outside `revise
  edit`.
- Recorded archive-review evidence for incorrect generated-review speaker boundaries
  and a missing review sentence, while distinguishing a log-only alignment hallucination
  from canonical transcript content.
- Accepted the planned v0.2.0 manual transcript-revision contract, including immutable
  full snapshots, `EWP-REVIEW 1`, revision-aware export, schema/example artifacts, and
  the implementation acceptance plan, with automated contract-artifact validation.
- Prioritized the 24-episode corrected corpus, later local/cloud LLM correction, separate
  manual/automated translation pipeline, synchronized HTML export, and optional
  project-scoped dictionaries in the post-0.1 roadmap.

### Validated

- Built the internal 0.2.0 wheel and sdist with synchronized metadata, console entry
  point, packaged defaults, AGPL license, and current source instructions. An isolated
  wheel-provenance smoke test passed prepare, preview, apply, audit, and revised
  TXT/SRT/VTT/segments export without audio or models.
- Passed the first real-episode staged revision pilot using Windows Notepad: review
  preparation, validation, immutable apply, audit, and corrected export completed
  without modifying the canonical result.
- Passed revision-aware bulk export on 24 manually corrected podcast results: all TXT,
  SRT, VTT, and segments outputs were generated (96 artifacts), and duplicate replay
  skipped all 96 without creating new versions.

### Changed

- Export failures now identify the failing format and a fixed allowlist of safe renderer
  invariants while continuing to suppress arbitrary internal or transcript details.
- Invalid review-body directives and text placement now report the exact review-file line
  number, making isolated batch failures directly repairable without reapplying
  successful reviews.
- Source filenames containing whitespace now emit a structured warning and remain
  accepted unchanged when their complete CLI paths are quoted.

### Fixed

- Preserved canonical and timing-derived overlap metadata while projecting corrected
  revision tokens, sorted reconstructed overlapping speaker groups chronologically, and
  interpolated consecutive inserted tokens across bounded canonical gaps. This prevents
  revised subtitle overlap and line-limit failures without changing accepted text or
  canonical timing anchors.
- Restored chronological ordering after final subtitle repartitioning so explicitly
  overlapping speaker cues cannot make SRT/VTT export fail after long silent intervals
  or fallback alignment.
- Prevented plain-text sentence splitting after common abbreviations including `m.in.`,
  `np.`, `tzw.`, and `vs.`.
- Prevented plain-text sentence splitting after `tys.` and address tokens ending in
  `.pl`, `.eu`, `.com`, or `.edu`, including the project domains `etykawpetli.pl` and
  `ethicsintheloop.eu`.

## 0.1.1 — internal release candidate — 2026-08-14

Backward-compatible operator and transcription fixes found during the fresh-WSL archive
pilot.

### Changed

- Replaced the implementation-era work status with the current internal-candidate
  status and V2 agenda.
- Consolidated live WSL documentation around fresh installation, current MVP operation,
  and actionable V2 feedback; historical validation material now lives under
  `archive/`.
- Top-level CLI help now points users to `transcriber COMMAND --help` for
  command-specific options.
- Standardized commit and pull-request titles as `<type>(<scope>): <summary>`.

### Fixed

- Missing-model diagnostics now point directly to `WSL config/MODEL_SETUP.md`.
- Windows drive paths are normalized before CLI file/directory dispatch and output-path
  planning, so directory transcription correctly uses the batch workflow.
- An omitted `--speaker-count` now preserves the configured `auto` default instead of
  silently forcing one speaker; `--speaker-count 1` remains the explicit fast path.
- Accepted Lightning checkpoint-migration, pyannote TF32-reproducibility, and pyannote
  short-window pooling notices are narrowly suppressed across the operations that emit
  them; unrelated backend warnings remain visible.

### Validated

- 289 automated formatting, linting, typing, unit, integration, schema, documentation,
  and traceability checks.
- Windows-path directory batch dispatch and output placement.
- Automatic and exact-count speaker selection, including a real two-speaker mono rerun.

## 0.1.0 — internal release candidate — 2026-08-05

Initial functional MVP release candidate.

### Added

- Local-first `doctor`, `inspect`, `dry-run`, `transcribe`, `export`, and `clean`
  commands with a CLI-independent application boundary.
- Deterministic single-file, natural-order directory, filename-derived, and explicit
  collision-safe group discovery.
- Conservative mono, dual-mono, split-speaker, mixed-stereo, and ambiguous-channel
  classification with explicit overrides and warning-only audio diagnostics.
- Offline pinned WhisperX large-v2 ASR, Polish/English alignment selection, pyannote
  diarization, chronological speaker normalization, and overlap provenance.
- Schema-versioned canonical JSON with integer-millisecond timestamps, timestamp-source
  provenance, source hashes, model revisions, effective configuration, stage timing,
  VRAM metrics, structured warnings, and sanitized failures.
- Regeneratable TXT, sentence-level segments JSON, and readability-balanced SRT/VTT.
- Atomic partial/failed/final state transitions, signature-based duplicate skipping,
  versioned forced reruns, output locking, interruption recovery, sequential batch
  isolation, and marker-verified privacy cleanup with age filtering.
- Manifest-driven WER/CER reports and error-only review diffs.
- Reproducible locked CUDA 12.8 dependency graph and Python 3.12 wheel/sdist packaging.

### Validated

- 279 automated formatting, linting, typing, unit, integration, schema, documentation,
  and traceability checks.
- WAV at 44.1/48 kHz, MP3, FLAC, M4A/AAC, Ogg/Opus, dual mono, split speakers,
  separate mono sources, mixed overlap, clipping, imbalance, long silence, fast speech,
  light recorder noise, and repeated intro/outro material.
- Polish recordings from 95 seconds through 151 minutes on an RTX 3090 under Ubuntu
  24.04 WSL2, including ten-job batch stability and real SIGINT restart.
- Short and complete 34.7-minute YouTube SRT/VTT readability and timing reviews.
- Offline installed-wheel transcription and locked installation in a fresh Ubuntu
  24.04.4 WSL2 distribution.

### Known limitations and deferrals

- Quantitative English, Polish/English code-switch, and three-speaker quality remains
  deferred until representative archive-derived references exist. The `pl`, `en`, and
  `auto` execution modes are implemented.
- Timestamp accuracy and DER/JER lack manually annotated reference data; provenance and
  structural behavior are covered, but quantitative thresholds are deferred.
- The lexical corpus contains only three manually verified Polish cases and is not yet
  statistically representative.
- Arbitrary FFmpeg-decodable extensions work as direct files; content-aware discovery of
  arbitrary-extension files inside directories is deferred to V2.
- Transcription correction, synchronized HTML, speaker-colored web presentation, and
  source-aware subtitle editing are V2 workflow items.
- The accurate preset is validated only on the reference RTX 3090; lower-memory GPUs do
  not yet have supported presets or performance claims.

### Distribution note

This version is for internal use and is not a public release. No public license is
declared in this release candidate. The private
`LICENSE_SKETCH.TXT` draft is deliberately excluded from both wheel and source
distribution artifacts. Do not create or push a public version tag, publish a hosted
release, or distribute artifacts for third-party use until the owner decides the
application is ready and chooses and commits the intended license terms.
