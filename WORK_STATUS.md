# EWP-transcripts work status

Last updated: **2026-08-28**.

## Checkpoint

Version `0.10.0` is the next internal beta on `main`; it is not tagged or published as a public
release. Development remains untagged while requirements work continues. The first public
release is reserved for the checkpoint immediately before Docker-image implementation; an
internal version number never implies publication. The repository is public and licensed
under `AGPL-3.0-only`.

The v0.1 transcription/export baseline, v0.2 immutable manual transcript revisions, and
v0.3 local/cloud automated correction are implemented and acceptance-audited. Automated
correction remains a non-final review candidate. The accepted v0.3 evidence, provider
problems, prompt history, local/cloud pilots, complete Gemini corpus run, costs, and
limitations are recorded in `docs/22-v0.3-automated-correction.md`.

The first v0.4 vertical slice—manual Polish/English translation—is implemented:

- exact canonical or compatible transcript-revision source lineage;
- deterministic speaker-safe timed translation units;
- immutable `EWP-TRANSLATION 1` review and translation artifacts;
- single-file and failure-isolated batch prepare, preview, apply, audit, and export;
- deterministic UTF-8 TXT, SRT, and VTT output without audio or models;
- English closing-quote and known abbreviation/domain boundary handling, including
  legal case names such as `Battle v. Microsoft`;
- a complete operator playbook in `WSL config/TRANSLATE_TRANSCRIPTS.md`.

The automated-translation and benchmark slices are also implemented on `main`:
provider-neutral single-owner unit requests, bounded read-only context, a
deterministic mock provider, retry/resume execution, immutable non-final candidates,
content-free operations reporting, exact-scope consent, and the first network-isolated LM
Studio adapter are present. Failure-isolated directory execution and explicit manual
acceptance as a new exact-parent manual translation are also implemented. In addition,
exact-hash automated candidates and compatible
manual references can be staged into
private per-unit assessments, and completed reviews produce content-free,
direction-specific semantic reports. Meaning fidelity is explicitly independent of
lexical overlap; names, project conventions, and selected-dictionary adherence are a
separate dimension. The corrected LM Studio baseline, manual acceptance, exact-lineage
semantic report, and project-dictionary comparison are complete.

The first real Bielik 11B v3 Q8 `s0e00` pilot completed operationally: 80 requests, zero
retries, 49,605 ms provider time, and complete resume reuse on publication. Its candidate
was rejected after review found JSON wrappers in 75/80 units, adjacent-context repetition,
an owned-unit omission, and a false numeric sentence split. Fixes are implemented for a
fresh zero-context rerun; no translation-quality claim is accepted from the failed pilot.
The rerun then showed Bielik's chat template adding a valid string `translator_notes`
and later `translation_notes` field. The adapter now discards only those two observed
aliases with an explicit per-unit warning; unknown provider metadata continues to fail
closed. Parser-version changes invalidate resume identity.
The resulting zero-context run completed 79 requests with zero retries in 28,854 ms and
fixed the numeric split, but manual review found 25 spurious outer-quote wrappers and three
`Szymon` to `Simon` anglicizations. Valid JSON-string responses are now unwrapped and the
prompt requires exact personal-name copying.
The fresh confirmation run completed 79 requests with zero retries in 26,833 ms, produced
1,051 target tokens, and emitted no provider warnings or spurious outer-quote wrappers.
Manual review found no omission, repetition, or ownership failure, but identified two clear
semantic errors and several minor wording/meaning issues. Bielik still anglicized `Szymon`
in three of four occurrences despite the prompt. The owner confirmed `Ethics in the Loop`
as the English title, `etykawpetli.pl` as the preferred Polish-domain spelling (both owned
spellings are valid), and initiator/catalyst as the intended sense of `aktywator`. The
candidate remained non-final until the exact-parent manual correction described below.
The first manual apply exposed that a separate accepted-output directory restarted child
numbering at one. Publication now allocates strictly after the recorded parent number;
the incorrectly numbered temporary artifact is rejected as qualification evidence.
After that fix, the corrected review published as exact-parent manual child translation 2,
its 79-unit audit published successfully, and deterministic TXT, SRT, and VTT exports were
written successfully. The automated candidate-to-manual-acceptance workflow is therefore
qualified end to end for this pilot. Its exact-lineage semantic assessment and content-free
benchmark report, described next, completed the gate.
That report is now complete for `pl -> en`: 79 units, 71 faithful, 6 minor errors,
2 major errors, no critical errors, semantic pass rate `0.89873418`, and 6 separately
counted convention failures. Issue totals are 1 addition, 5 mistranslations, and 2
tone/register errors; dictionary provenance is null. The Bielik no-dictionary baseline is
therefore complete and must not be merged with later dictionary-assisted or reverse-direction
runs.

External structural evidence is complete for this slice: the owner mapped the private
English corpus into the current scheme, applied and exported all files without errors,
and reported readable SRT/VTT output. This corpus permits artistic translation freedom,
so it validates workflow structure, not translation accuracy.

The current v0.9 tree passes formatting, lint, type checks, and all **640 tests**. A fresh
Ubuntu 24.04.4 WSL2 installation on an RTX 3090 passed environment installation, pinned-model
setup, offline transcription, restart-safe canonical replay, Gemini 2.5 Flash correction,
candidate-backed manual-review preparation, verified-revision export, and LM Studio/Bielik
translation candidate, audit, and review preparation. Canonical results and accepted
revisions remain immutable. Private corpus content, API keys,
provider payloads, and runtime resume/lock files remain outside Git.

The cross-cutting diagnostic catalogue is implemented. Expected application exceptions,
direct privacy/non-final warnings, benchmark and dictionary command failures, explicit CLI
validation, and framework-generated usage errors now print stable codes. Batch failures reuse
the same application codes. `docs/25-warning-error-catalog.md` documents meaning, likely
cause, safety implications, and operator action, and tests reject undocumented emitted codes.

The GUI direction is now decided: one self-contained local browser application will use the
same frontend, versioned API, application services, and immutable artifacts on WSL2,
bare-metal Ubuntu, and the future Docker image. ADR-0021 and
`docs/26-local-web-gui-contract.md` define loopback-only initial deployment, configured
server-side path roots, direct service calls, single-GPU queueing, review/translation
coverage, privacy/security controls, and the pre-Docker implementation sequence. GUI
requirements remain planned; the existing exported HTML transcript player is not the GUI.

The first executable GUI slice was implemented in v0.8. `transcriber gui` starts a
loopback-only server with bundled offline HTML/CSS/JavaScript, versioned health/about/root
endpoints, frontend/API compatibility checking, explicit normalized allowed roots, Host
validation, restrictive browser security headers, coded failures, and About/license/source
information. It does not load ML models.

The owner qualified this shell from Ubuntu 24.04 WSL2 in Firefox, LibreWolf, Brave, and
Chrome. All browsers reported the v0.8/API-v1 compatibility state, exact configured roots,
license/source information, and consistent rendering. PowerShell requests confirmed the
security headers and the expected `421 GUI_HOST_REJECTED` response. WSL browser launching now
uses the quiet Windows bridge after the initial `gio` launcher proved unsupported.

The second GUI slice now connects inspect and dry-run directly to the existing application
services. The browser accepts only server-side paths contained by configured roots, rejects
symlinks and cross-origin POST requests, returns the existing structured inspection/plan
models, and retains a bounded read-only in-process operation history. These operations load
neither transcription models nor create final artifacts.

External WSL2 validation inspected the real `s0e00.wav`, returned the expected episode,
stream, channel, fingerprint, and quality evidence, rejected `/etc/hosts`, rejected a hostile
Origin with HTTP 403, and confirmed that dry-run created no output directory. The initial
report left the dry-run display unclear, so the interface now distinguishes inspection from
dry-run completion, shows compact summary cards, treats a missing result as a coded defect,
keeps full JSON in a disclosure panel, and places About in the page footer.

The owner subsequently confirmed the clarified dry-run display, structured direct-file plan,
ambiguous-directory error, and revised footer. A Clear control now resets both path fields and
all visible result state locally without deleting operation evidence or filesystem content.

The first transcription-queue slice is implemented: one worker serializes GPU jobs,
the browser requires an explicit post-dry-run confirmation and per-process CSRF token, input
and output remain confined to allowed roots, and polling reconstructs queue state after a
browser refresh. The worker invokes `transcribe_one` directly and reports the existing atomic
result path or a sanitized coded failure. Initial scope accepts one file per queued job.

Owner testing confirmed real GPU completion and that refresh preserved the active row. Based
on that review, adding an item no longer starts work: jobs remain `STAGED` in a table, may be
removed, share one enforced output directory, and begin only through a separate Start queue
action. The page now summarizes planned jobs for non-technical users, labels raw JSON as
technical detail, contains expandable brief instructions, and serves a bundled `/help` page
with a link to the complete repository runbook. Each staged row records its logical job ID
and planned result path; duplicate active inputs, output-directory changes, and colliding
logical job IDs are rejected before GPU work begins.

The staged-queue qualification then passed end to end on WSL2: two distinct files were
staged, survived refresh/browser replacement, one was removed, a same-job-ID source was
rejected with `GUI_QUEUE_JOB_ID_COLLISION`, and the remaining job published canonical JSON,
preview TXT, and segments. Follow-up usability work compacted dry-run paths to filenames,
stopped unchanged polling from replacing selectable table DOM, and extended GUI path
normalization to the Windows-drive forms already supported by the CLI. Repeated POSIX
separators such as `//input-b` are intentionally normalized by the filesystem.

The follow-up retest accepted a Windows-form media path and confirmed stable text selection.
It also exposed a harmless frontend exception after successful staging: asynchronous access
to the expired DOM event target. The form reference is now retained before the request. The
plan detail table occupies its own full-width row, and the implicit language is labeled
`pl (auto)` pending later per-file language and speaker-count controls.

The owner confirmed the correction in the target browser: staging reports only `Added to
staged queue`, plan details render full-width below the summary cards, and language displays
as `pl (auto)`. This closes the current transcription queue and planning-presentation gate.

The v0.9 model-free GUI review slice passed its first external browser workflow test.
It prepares a non-destructive review from one canonical result, exposes only editable
speaker/text blocks, protects hidden anchors and lineage, rejects stale-tab saves by exact
review hash, requires Preview of the current saved hash before Apply, and requires explicit
manual-verification confirmation. Apply publishes through the existing immutable revision
service; verified TXT/SRT/VTT/YTT/HTML/segments export uses that exact revision. Review API
requests remain allowed-root constrained, Origin/CSRF protected, bounded, and model-free.
The test published two immutable revisions and all six export formats. Follow-up UI work now
labels preview as validation-only, summarizes it in a readable table with expandable JSON,
protects an open draft from accidental Prepare replacement, distinguishes disabled actions,
and offers both sequential and continuous section layouts. The supplied fixture was English;
an earlier instruction describing it as Polish was incorrect. Whole-block speaker reassignment
is available now. The GUI also supports isolating selected complete words or a sentence into an
independent block, assigning it to another known speaker, and deliberately merging adjacent
blocks without modifying the canonical result. Project/revision-scoped speaker display-name
editing remains a later editor requirement.
The same acceptance pass found that refresh discarded the active editor pointer and that
separate output-path entry was unnecessarily repetitive. The follow-up restores a saved review
from its authoritative disk file using only non-secret path pointers in browser storage,
derives `reviews/`, `revisions/`, and `exports/` from one output root by default, guards Clear
with confirmation, and prevents repeated Apply clicks from publishing the same open review
again. Collapsible section/table-of-contents navigation is retained for the larger GUI.
External acceptance confirmed automatic structured paths, same-browser refresh/restart
recovery, unsaved-edit warnings, applied-state recovery, guarded Clear, and clean output
structure. The next follow-up adds an explicit disk-backed last-session restore for another
browser or later GUI process and labels the bordered review status surface.

The v0.10 GUI correction slice is implemented and externally qualified with Gemini 2.5 Flash,
including dictionary-assisted generation and smooth candidate-backed review handoff. The first
GUI translation-candidate slice is implemented pending external LM Studio qualification. It
accepts an exact canonical source plus optional revision, records source verification and
dictionary provenance, performs a bounded exact-model preflight, and labels every result as
non-final pending semantic manual review. It
builds on the correction slice, which accepts an exact canonical result, structured
candidate/resume output root, LM Studio or
OpenRouter provider/model/endpoint, optional exact project dictionary and project ID, and an
explicit disclosure/non-final confirmation. Credentials remain in the server environment.
A short readiness check rejects missing credentials, unreachable backends, and unavailable
exact models before chunk retries. Successful immutable LLM candidates are labeled non-final
and can be opened directly as the parent of the existing manual-review workflow. Local-model
correction is rejected while transcription GPU work is queued or running.
The first external OpenRouter/Gemini 2.5 Flash GUI run succeeded with 855 tokens, three
substitutions, two punctuation-only changes, no warnings, and a non-final candidate. Its
reported dictionary provenance was `none`, so it is operational evidence but not yet the
intended dictionary-assisted gate. The follow-up makes dictionary selection visible in the
readable summary, strengthens cloud-data wording, and uses a smooth review handoff.
The repeated dictionary-assisted run then passed with exact v1.1 ID/project/hash/proposal
provenance, 17 substitutions, one punctuation-only change, zero drift/warnings, and smooth
handoff to a `pl` review labeled `source: automated_candidate`. The GUI now derives project ID
from the dictionary rather than requiring redundant typing and labels the review identity.
The first GUI translation qualification reached exact-model preflight after a clean machine
restart. LM Studio advertised `bielik-11b-v3.0-instruct`, so the deliberately exact request for
the older `bielik-11b-v3.0-instruct@q8_0` ID was correctly rejected as
`TRANSLATION_MODEL_UNAVAILABLE`; candidate generation remains pending with the advertised ID.
The advertised-model retry reached generation but reproduced Bielik's known adjacent-context
leakage: the final response contained two separately quoted translations for one owned unit
and was correctly rejected as `INVALID_TRANSLATION_RESPONSE` after bounded retries. The GUI
had mistakenly requested one context unit; it now uses the previously qualified zero-context
Bielik profile.
The zero-context GUI retry then passed end to end with the advertised
`bielik-11b-v3.0-instruct` model: one non-final `pl -> en` candidate from the exact manually
verified revision, 79 units, 867 source tokens, 1,051 target tokens, zero warnings, and exact
`ethics-in-the-loop-pl-en-v1` dictionary ID/project/hash provenance. Translation generation is
therefore externally qualified. Browser semantic review/apply/audit/export is the next GUI
slice; this candidate is not accepted publication text.
That next model-free browser slice is now implemented pending external qualification. A
generated candidate opens as an exact parent with immutable source units and editable target
text; save invalidates preview, apply requires the exact preview hash plus explicit semantic
verification, and the resulting manual child can be reconstructed into an audit and exported
as deterministic TXT/SRT/VTT/HTML with provenance. Transcript review remains a separate
workspace and is unchanged.
External qualification passed on the 79-unit `s0e00` candidate: immutable sources and all
editable targets rendered, one target edit saved and previewed, manual child translation 3
published, its audit reconstructed, and TXT/SRT/VTT/HTML plus provenance exported. The first
presentation was functionally correct but cramped and exposed unit IDs prominently; the
follow-up uses readable numbered source/target cards, auto-sized target areas, consistent
primary handoff buttons, and a preview table explaining validation and non-publication.
The owner accepted the revised card layout and Preview table, with two final hierarchy
adjustments: target labels are regular weight and unit headings use the subdued source-label
color. Resume reuse was also observed to perform backend readiness only and send no transcript
excerpt. Named non-secret workspace save/load now survives workstation or VM shutdown; exact
artifact-backed restoration remains distinct from provider resume state and saved-review pointers.
The first project correction-dictionary GUI slice is implemented pending external
qualification. It compares canonical-result and exact manual-revision directories, supports
minimum-occurrence filtering and an optional previous dictionary, renders bounded contextual
examples, saves explicit pending/approved/rejected decisions with conflict protection, and
publishes a new immutable project/version dictionary only after no pending decisions remain.
External qualification passed with the private 22-case corpus and the previous v1 dictionary:
all 41 candidates/decisions rendered and an immutable 4,438-byte test dictionary was published
with its 58,616-byte proposal under `/tmp`. The first layout was too long and publication
feedback remained below the fold. The follow-up adds approved/rejected/pending filters, a
compact count summary, five-example truncation, list or previous/next evidence navigation,
required-field highlighting, and scroll-visible publication confirmation.
The retest accepted the summary, filters, five-item limit, show-more behavior, confirmation
highlight, and visible publication message. It found that evidence still required redundant
manual expansion and inactive sequential controls remained visible because shared `.actions`
CSS overrode `hidden`. Visible evidence now opens automatically in both layouts, and a global
author-level hidden rule keeps inactive controls out of the layout.
The final retest accepted all four corrections: initial and expanded list evidence is open,
sequential evidence is open one at a time, and sequential controls are absent in list mode.
The correction-dictionary proposal/review/publication GUI slice is therefore externally
qualified. Installed/custom dictionary discovery and selection is the next functional slice.
That selection slice is now implemented pending external qualification. Correction and
translation forms scan one explicit allowed-root catalog (bounded to 1,000 JSON files), ignore
unrelated invalid JSON, list valid dictionaries by project/ID/version/language or direction,
and fill the exact path while preserving direct custom-path entry.
The first external catalog test returned empty lists because scanning encountered the retained
correction proposal, correctly rejected it as a correction dictionary, then allowed an
unwrapped translation-schema validation error to abort the whole scan. Catalog discovery now
isolates every invalid/proposal JSON file and each picker exposes local loaded/empty/error
feedback instead of sending failures only to the distant dictionary-management status.
The corrected browser retest passed: correction and translation each found one compatible
project dictionary, showed project/ID/version/language or direction plus a local count, and
filled the exact direct path on selection. Dictionary catalog discovery/selection is therefore
externally qualified.
The next browser slice now connects verified transcript review to translation: only an applied
immutable revision enables the handoff, which fills exact source lineage and the shared project
root, selects the opposite target language, and scrolls to translation without starting it.
The browser retest passed all of those conditions with English example revision 3, including
preservation of model, endpoint, and dictionary fields. This handoff is externally qualified.
That retest also exposed a missing visual cue when transcript application rejected an unchecked
manual-verification confirmation. Required confirmation errors now highlight and mark the
relevant checkbox accessibly across transcript review, correction, translation, and semantic
translation review; external visual qualification of this shared behavior remains pending.
The browser retest confirmed the red required-field outline, immediate clearing after checking,
and successful transcript application. Shared confirmation highlighting is externally qualified.
Completed transcription rows now expose two explicit next steps: optional LLM correction or
direct manual review. Both transfer the exact canonical result and containing output root and
scroll to the chosen stage without starting work. External browser qualification is pending.
The browser handoff retest passed both paths and confirmed that the two actions fit the queue
table. It also exposed queue guidance and confirmation affordance problems. Queue staging now
reports inspect/dry-run first, highlights the exact confirmation only after a matching plan,
and renders Clear as a lower-emphasis action. Advanced correction provider settings are now
collapsed with defaults retained. A password-masked OpenRouter dialog can set a key for the
current loopback server process without browser/file persistence; durable restart persistence
remains blocked on a future OS credential-store design and must never use plaintext settings.
An end-to-end MP4 transcription run is retained as a later acceptance task.
The follow-up browser test accepted the subdued Clear action, collapsed provider defaults, and
session-key dialog including empty-on-reopen behavior. Queue confirmation still lacked its red
outline because the shared helper matched old prose rather than `GUI_CONFIRMATION_REQUIRED`;
the helper now recognizes coded confirmation errors. A new transcript-free `Check connection`
action reports a green `API OK` state or a red coded error and distinguishes rejected keys,
unreachable/rejecting endpoints, and unavailable exact models. Both require external retesting.
Live testing showed that OpenRouter's public model catalog answered identically for fake and real
bearer values, so `/models` cannot authenticate a key. Readiness now first calls the documented
authenticated current-key endpoint, then separately validates the exact model. Empty dry-run
output is rejected directly and highlighted. The API-check light/status now form one labeled row
below the buttons, and the informational secret status explicitly says the key is session-only
and not stored. These corrections require external retesting.
The next retest accepted output validation and clear fake/empty credential/model failures.
Correction model choice now offers Gemini 2.5 Flash (recommended), Flash Lite, and Pro with
separate approximate listed input/output tokens per USD plus an explicit manual-ID mode. A
collapsed, opt-in model/pricing check refreshes availability and listed rates for those three
models only and sends no transcript. Saving custom selections and searchable browsing across
the provider catalog remain later settings/UI work. External testing accepted all bounded preset,
manual-ID, disclosure, and opt-in pricing behaviors. A later LM Studio control should check the
connection, prefill one unambiguous advertised loaded model, and—only if supported—offer explicit
model loading without silently changing backend state.
Per-job transcription language and speaker-count controls now flow through inspect, exact dry-run
identity, staged queue evidence, and execution. Changing either setting invalidates the prior
dry-run authorization. External testing accepted the settings summary, stale-plan rejection, and
staged queue evidence. Follow-up replaces the fixed count list with a validated 1–6 number field,
retains automatic detection, and preserves dry-run evidence across queue-validation failures.
The accepted browser retest confirmed the 1–6 range, exact dry-run summary retention across a
confirmation error, and summary clearing only after successful queue staging. The numeric input
now also refuses more than one typed or pasted character.
The first allowed-root Browse slice now covers media, canonical results, revisions, dictionaries,
and workflow/output directories. Its read-only CSRF-protected API stops navigation at configured
roots, hides symlinks, bounds listings, and filters file types. Direct entry remains available for
new output directories. External cross-browser qualification remains pending.
Chrome and Firefox qualification passed root-only navigation, media/JSON filtering, symlink
hiding, file selection, directory selection, close-without-change, and disabled upward traversal.
The roots are launch-time capabilities rather than hardcoded work directories. Later settings
work should make named media/project roots persistent without allowing a browser request to expand
server authority. Start-time exact fingerprint revalidation and optional immutable input snapshots
remain explicit TOCTOU-hardening work; media already undergoes FFprobe decoding and structured
artifacts undergo strict schema parsing, so extension alone is not accepted as valid content.
The first application-owned workspace-state slice now explicitly saves and loads a named set of
allowlisted non-secret GUI form fields plus the current workflow step. It works across browser and
server restarts through the user state directory, revalidates all paths, lists stale entries as
unavailable, and excludes API keys, confirmations, transcript text, and unsaved editor content.
External qualification passed in Chrome, Brave, and Firefox: fields and last-step scrolling
restore across browsers and a stopped/restarted GUI, while confirmation controls remain cleared.
Exact staged-job reconstruction and open-review/artifact hash restoration remain required before
the full workspace contract is met. The staged-job slice now persists only unstarted jobs with
source SHA-256 and exact dry-run output identity; restoration re-hashes and replans them before
they return to the queue. Open-review/artifact identity remains the next recovery gap. API credentials remain process-local,
shared by browsers connected to that process, excluded from workspaces, and erased on GUI stop.
The first auto-save qualification correctly rejected a nonexistent saved input path and resumed
saving after the path was repaired, but exposed poor checkbox alignment and ambiguous silence when
no tracked change was written. The follow-up aligns the control and reports inactive, unchanged,
validating, saved, and retry states separately. Confirmations and editor text remain intentionally
outside workspace tracking. Process-wide credentials are an intentional single-user or
single-organization deployment boundary; multi-user support is not currently planned.
External retesting accepted checkbox alignment, unchanged-state reporting, tracked saves,
confirmation exclusion, and invalid-path retry behavior. The remaining presentation follow-up
subordinates the supplementary status and reports pending tracked edits immediately rather than
waiting silently for the next interval.
The staged-queue recovery retest then passed: one unstarted job reappeared after a GUI restart
without beginning execution, while a deliberately modified temporary source was rejected with
`GUI_WORKSPACE_REQUEST_INVALID`. A final full-workflow qualification from mixed input directories
to one output root is deferred until GUI functions are nearly complete; branding alignment follows
that functional acceptance run.
The review-workspace retest restored its saved paths, draft, and review section correctly. Draft
saves now also update the active named workspace. The filesystem browser additionally hides
unreadable and `/tmp` desktop/session runtime directories, rather than advertising them as normal
output choices.
The follow-up accepted draft-to-workspace synchronization and the safer `/tmp` browser listing.

That directory-level evidence also exposed two different sources (`s0e00.mp3` and
`s0e00.wav`) deriving the same job ID and initially receiving colliding planned output paths.
The initial attempt to allocate the next result version was rejected after owner review:
versions represent successive results for one logical job, not simultaneous source aliases.
Dry-run and transcription now fail before publication with `AMBIGUOUS_JOB_ID`; they do not
guess that the formats are interchangeable or make canonical identity depend on neighboring
directory content. Users select one source directly until explicit per-input aliases exist.

The `0.7.0` package candidate passed the 620-test locked gate and the 140-package environment
compatibility check. Its wheel and source archive contain the expected license metadata/files
and no runtime/private payload filenames or credential-shaped values. An external `/tmp`
target installation proved wheel provenance outside the checkout, version/help, coded usage
errors, and all six model-free export formats. Exact candidate hashes are recorded in the
ADR-0010 follow-up; this targeted artifact smoke complements rather than repeats the earlier
full isolated locked-dependency installation.

## v0.4 delivered work

These are the delivered v0.4 workstreams; details and acceptance criteria live in
`docs/23-v0.4-translation-contract.md` and `docs/99-roadmap-v2.md`.

1. **Automated translation.** The provider-neutral request/response, mock, LM Studio,
   exact-scope consent, retry/resume, immutable candidate, and single-file CLI slice is
   implemented. The verified-Polish `pl -> en`, `preserve/preserve`, no-dictionary Bielik
   baseline is complete, including exact-parent manual acceptance, audit, export, and the
   semantic assessment/report. Keep `en -> pl` separate.
   Local LLM translation is operationally usable, but it is not recommended for
   publication-quality output on current evidence: Bielik remains noticeably mechanical
   and requires comprehensive human semantic/convention review. This gate primarily
   qualified LM Studio compatibility, failure handling, provenance, resume, review, and
   export—not a broad model-quality ranking. Additional local models and settings were
   intentionally not exhaustively tested.
2. **Translation pipeline benchmark.** The exact-lineage human semantic assessment and
   content-free reporting boundary is implemented. The first narrower Bielik reference and
   complete candidate/correction/apply/audit/export/report path are qualified. Optional
   post-functional quality work may compare local candidates Qwen 2.5 32B Q4, Bielik 11B Q8,
   Llama 3.3 8B Q8, MADLAD-400, and NLLB-200 separately from cloud models once semantic
   assessment can scale without whole-corpus manual review.
   Record model artifact, backend, prompt, chunking, latency, resource use, request/token
   volume, cost, retries, and reviewer effort. Do not claim translation accuracy from the
   artistically free English corpus; first define a narrower manually approved reference.
3. **Project-scoped dictionaries.** The first strict, explicit, hashed translation-context
   slice is implemented. Extend the same contract to Polish automated correction, using
   Gemini 2.5 Flash because evaluated local models did not improve ASR error rate, and add
   operator examples
   and dictionary-assisted benchmark evidence. Candidate extraction from accepted audits
   requires human approval. Benchmark raw, LLM-only, dictionary-assisted LLM, and manual
   gold; reject dictionaries that create harmful confident replacements.
   The first exploratory translation-dictionary run demonstrated such harm: the complete
   dictionary was sent to every unit and Bielik invented an unrelated speaker label. Request
   planning now exposes only entries whose source form occurs in the owned unit. That run is
   rejected; the next pilot must use only durable names/titles/addresses, not episode-specific
   mistranslation fixes. The subsequent scoped pilot is described below.
   Dictionary provenance is first-class and inherited by exact-parent manual children;
   audits declare the dictionary object or null, while exports publish a provenance sidecar.
   The accepted general project-dictionary pilot preserved semantic performance at 71/79
   faithful (`0.89873418`) while reducing convention failures from 6 to 2. It produced the
   same 6 minor and 2 major semantic errors as the no-dictionary baseline. Per-unit source
   filtering caused no harmful insertion, but Bielik still anglicized 2/4 `Szymon`
   occurrences, so dictionaries are context assistance rather than enforcement.
   The intended stage order is `transcript -> Gemini-assisted Polish review candidate ->
   manual Polish review -> export -> translation (manual or LLM-assisted)`. Translation
   normally starts from the accepted Polish revision. Explicit translation from an
   unreviewed candidate remains supported with a prominent warning and exact
   `automated_candidate` source lineage. Correction and
   translation dictionaries remain separately versioned and hashed even when they share
   approved identifiers.
   Polish correction-dictionary proposal and approval are now implemented: exact compatible
   manual revisions yield pending repeated/consistent mappings, every item must be manually
   approved or rejected, and the published project dictionary retains proposal and corpus
   lineage. The initial context-free private proposal was rejected after ambiguous short
   forms and punctuation-bearing keys were observed. Proposal v1.1 adds marked source/target
   context per occurrence and strips only boundary punctuation from lexical keys. A fresh
   `/tmp` pilot found 41 pending candidates across 22 compatible cases with context on every
   item and no punctuation-bearing boundary keys. Explicit Gemini/OpenRouter selection,
   per-chunk source matching, resume identity, revision provenance, and audit reporting are
   implemented. The subsequent manual proposal review and controlled dictionary comparisons
   are recorded below.
   The owner reviewed proposal v1.1: 19 mappings were approved and 22 rejected. Both decision
   classes are retained so rejected mappings remain suppressed in later proposals; only
   approved entries are provider context. The redistributable proposal and dictionary are
   published in the versioned `dictionaries/` catalog with exact SHA-256 values
   `7556eb83...43152` and `5d1bb1c5...15db`; automated tests verify their lineage and counts.
   A dictionary-assisted Gemini 2.5 Flash `s0e01` smoke then completed four requests with no
   retries in 25,442 ms for `$0.023449`, preserving all 2,411 tokens and speaker attribution
   while proposing 17 substitutions with no warnings. This proves operation and provenance,
   not quality; an identical no-dictionary control and exact manual-gold comparison are next.
   That comparison is complete but in-sample: no-dictionary Gemini removed 2/72 errors
   (`0.02926421` WER), while dictionary-assisted Gemini removed 10/72 (`0.02591973` WER),
   with exact-edit precision/recall improving from `0.66666667`/`0.05882353` to
   `0.76470588`/`0.38235294`. Because `s0e01` contributed to dictionary derivation, this proves
   adherence rather than generalization; four unsupported exact edits also need manual review.
   Runtime scope is being corrected so derivation job IDs remain audit evidence while explicit
   matching project selection permits a genuinely held-out/future-episode comparison.
   The held-out `s0e00` comparison now supplies generalization evidence: dictionary-assisted
   Gemini halved raw WER from `0.02561118` (22 errors) to `0.01280559` (11), versus
   `0.02211874` (19) without a dictionary. Exact-edit precision/recall/F1 were
   `0.82352941`/`0.7`/`0.75675676`, versus `1.0`/`0.15`/`0.26086957` for the conservative
   control. Runtime/cost were nearly equal and both preserved tokens/speakers without warnings.
   Manual classification of three dictionary-assisted edits unsupported by gold is the final
   acceptance gate before expanding the dictionary-assisted correction benchmark.
   The owner classified all three as supported convention edits: ASCII `etykawpetli.pl` is the
   preferred spelling of the owned address, while the diacritic spelling is also valid. No
   harmful held-out edit was identified. The dictionary-assisted held-out pilot is therefore
   accepted, with 14 exact-gold plus 3 owner-supported convention edits. Review output now
   explains that lexical normalization may visually separate domain punctuation without
   changing the candidate artifact.
4. **Timed-event semantics.** The additive schema `1.1` foundation is implemented with segment
   kinds `speech`, `music`, `laugh`, `cough`, and `note`; legacy omissions default to speech.
   Raw/revised effective projection, derived segment JSON, and subtitle cue planning preserve
   kind without changing SRT/VTT presentation. Explicit non-speech authoring remains separate;
   YTT and HTML may now consume the shared semantic field without inferring it from text.
5. **YouTube srv3 YTT export.** Two standards-based TTML uploads were accepted and verified
   timing, turn labels, language, and Polish diacritics, but YouTube discarded wrapping,
   centering, and colors even when encoded inline. The failed profile has been replaced by
   deterministic YouTube srv3 timed-text XML based on the owner-supplied accepted example.
   It reuses planned cues/line breaks, numeric speaker pens, centered bottom placement, and
   a separate non-speech pen. The first srv3 upload correctly centered cues and preserved
   text/timing, but YouTube flattened `<br/>` line elements. The owner-supplied corrected
   template uses literal in-paragraph newlines and near-white `#FEFEFE`; the renderer now
   matches that structure byte-for-byte. The final unlisted upload fully passed: two-line
   wrapping, distinct speaker colors, centering, timing, turn labels, and Polish diacritics
   all rendered correctly. YTT remains opt-in because it is platform-specific, not because
   qualification is pending.
6. **Embeddable HTML transcript.** Raw and manually revised `--format html` export is
   implemented as an escaped deterministic fragment with a BCP 47 language, explicit
   speaker turns, sentence-level native buttons, integer timing/speaker/kind metadata, and
   no CSS, JavaScript, inline styles, or event handlers. Immutable translation artifacts
   now export the same HTML contract using target language/text and inherited unit timing.
   The separate mock player site is implemented with its own CSS/JavaScript and contract
   tests for highlighting, seeking, native keyboard activation, reduced-motion-aware
   following, light/dark presentation, and readable no-script structure. A manual browser
   pilot passed Firefox/LibreWolf audio, mouse/keyboard seeking, highlighting, following,
   and light/dark rendering, but Chromium-family clicks restarted at zero. The retry waits
   for metadata and seek completion; explicit theme and auto-follow controls were added.
   A second Chromium retry isolated the remaining failure to Python's basic static server;
   the example now includes a range-capable server and byte-range calculation tests. The
   final retry returned valid `206 Partial Content` and passed seeking in Chrome and Brave;
   Firefox and LibreWolf had already passed. Theme/auto-follow controls and the no-script
   fallback also passed. The HTML slice is accepted. Minor acoustic spill across an
   occasional sentence boundary is inherited from word alignment and explicitly deferred;
   the renderer must not apply heuristic timestamp shifts.
7. **v0.4 closure.** Requirements, traceability, operator documentation, changelog,
   schemas/examples, and package version are reconciled. The full locked gate passes with
   603 tests, and the 0.4.0 wheel/source archives pass metadata, privacy-content, and isolated
   installed-wheel CLI/HTML/YTT smoke checks. The later beta-line clean-machine
   installation-through-workflow qualification also passed manually; repeatable automation
   may be added after the evidence format stabilizes.

## Explicitly deferred, not lost

- Sentence units remain the v1 translation timing/audit boundary. A separately versioned
  bounded speaker-chunk mode is added only if further corpus evidence shows repeated
  cross-sentence translation problems; existing artifacts never change interpretation.
- Correct and expand private benchmark references when a narrow translation-quality
  benchmark is designed. The grammar-edited Polish corpus is not ASR ground truth.
- Public-corpus WER/translation/diarization qualification, preset/hardware matrices,
  Apple Silicon support, CPU-only and GTX 1070 tiers, and automated model load/unload
  benchmarking remain later roadmap work.
- Research ephemeral per-job speaker fingerprinting/clustering for unknown meeting speaker
  counts. It must never become persistent cross-recording identity or a general people base.
- After the conservative lexical correction workflow is stable, evaluate two separately enabled
  non-final LLM modes: `check also punctuation` and `try basic editorial fixes`. Each must be an
  explicit unchecked GUI option with a clear warning that it can increase API usage and error
  risk, preserve exact provenance/prompt identity, and still require complete manual review.
- Manually review the complete instruction set with less-technical readers after workflows
  stabilize, then add screenshots and revise unclear terminology.
- After all GUI functions work, align the frontend's visual language with the owner's other
  projects and complete the final responsive styling pass.
- Add an explicit light/dark mode switch during that frontend pass; system color preference
  remains the temporary default until the functional GUI is complete.
- Content-aware arbitrary-extension discovery, audio repair/comparison, advanced 3+
  channel and surround handling, GUI, and additional subtitle/platform formats remain
  in `docs/99-roadmap-v2.md`; they are not v0.4 checkpoint blockers unless explicitly
  promoted.

## Operator and design entry points

- Complete CLI use: `Instructions/README.md`
- Manual transcript revisions: `WSL config/REVISE_TRANSCRIPTS.md`
- Manual translations and legacy migration: `WSL config/TRANSLATE_TRANSCRIPTS.md`
- v0.3 correction evidence: `docs/22-v0.3-automated-correction.md`
- v0.4 translation contract: `docs/23-v0.4-translation-contract.md`
- Complete prioritized/deferred roadmap: `docs/99-roadmap-v2.md`

Do not hand-edit canonical JSON. Preserve each original result and publish accepted text
only through immutable revision or translation artifacts.
