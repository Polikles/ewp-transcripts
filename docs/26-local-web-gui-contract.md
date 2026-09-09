# Local browser GUI contract

## 1. Scope

The graphical interface is one local web application served by EWP Transcriber and opened
in a normal browser. The same frontend assets, versioned API contract, application services,
and persisted artifacts MUST be used on WSL2, bare-metal Ubuntu, and the future Docker image.
Environment-specific launchers, filesystem roots, and Docker mounts MAY differ; behavior and
appearance MUST NOT fork by deployment environment.

The initial GUI is a single-user local tool. Multi-user hosting, public Internet exposure,
remote administration, and account management are outside the first implementation slice.

## 2. Architectural boundary

The browser talks to a local Python web adapter through a versioned `/api/v1` interface. The
adapter MUST call the existing application services directly. It MUST NOT execute
`transcriber` CLI commands as subprocesses, maintain a second transcript/translation model,
or rewrite immutable artifacts in place.

The web adapter owns only presentation concerns, request validation, job orchestration, and
serialization. Canonical results, revisions, translations, dictionaries, audits, and exports
retain their existing schemas, lineage, allocation, validation, and atomic-publication rules.

The packaged frontend MUST be self-contained. Runtime CDNs, telemetry, remote fonts, and
externally hosted JavaScript or CSS are prohibited. Once models are explicitly installed,
local workflows MUST remain usable without Internet access.

## 3. Deployment parity

All supported environments MUST render the same bundled frontend and report the same
application and API versions:

- WSL2 runs the service inside Linux and opens it from a Windows browser;
- bare-metal Ubuntu runs the same service and assets locally;
- the future Docker image runs the same service and assets with explicitly mounted input,
  project, and output directories.

The server binds to loopback by default. The initial GUI MUST NOT offer an unauthenticated
remote-listen shortcut. Any later non-loopback mode requires a separate threat model,
authentication, transport-security, and deployment decision. Docker instructions MUST bind
published ports to loopback unless the later remote-access contract explicitly supersedes
this rule.

## 4. Filesystem interaction

Media files can be large and already exist on the server-visible filesystem. The primary GUI
workflow therefore selects or enters server-side files and directories within configured
allowed roots; it does not upload or duplicate media through the browser.

The web adapter MUST:

- expose only explicitly configured roots and never provide a general filesystem browser;
- normalize paths through the existing path policy and reject traversal or disallowed
  symlink resolution;
- show the resolved source and destination before a mutating or expensive operation;
- preserve Unicode and spaces, and normalize Windows drive, WSL-mounted Windows, and native
  Linux path forms before enforcing the same explicit allowed-root boundary;
- require explicit Docker mounts rather than implying that host paths are automatically
  visible inside a container;
- never serve arbitrary source files as static web content.

Browser upload MAY be designed later as an opt-in convenience, but it is not required for
the initial GUI.

## 5. Required workflow coverage

The GUI MUST eventually expose the same supported pipeline as the application core:

1. inspect and dry-run input selection, grouping, streams, warnings, and output plan;
2. transcribe and monitor a deterministic local job queue;
3. optionally create an LLM-assisted correction candidate;
4. manually review, preview, and apply a transcript revision;
5. export raw or verified transcript artifacts without rerunning ASR;
6. create a manual or LLM-assisted translation from an explicitly identified source;
7. manually review, preview, apply, audit, and export translation artifacts.

Planning controls SHOULD expose language and speaker count per selected file. Values inferred
or supplied by the GUI rather than explicitly chosen by the operator MUST be labeled as
automatic. A later auto-discovery option may use only ephemeral within-job speaker features,
as constrained by the roadmap; it must not create cross-recording identities.

The interface MUST clearly distinguish canonical ASR output, automated non-final candidates,
manually verified revisions, and final/manual translations. Translation from an unreviewed
candidate remains allowed only with the existing warning and exact source provenance.
After an immutable transcript revision is applied, the review surface SHOULD offer a named
next-step action that fills the canonical result, verified revision, shared output root, and
opposite target language in the translation form. It MUST NOT start translation automatically
or overwrite the operator's provider, model, endpoint, or dictionary choices.

Correction controls MUST require exact provider/model/endpoint selection, explicit disclosure
consent, and an optional project dictionary whose embedded ID/version/hash are read and shown
automatically. Credentials stay at the server boundary. A short readiness check MUST reject
missing credentials, unreachable providers,
and unavailable exact models before bounded per-chunk retries. Successful candidates remain
non-final and SHOULD hand off directly into candidate-backed manual review.
Any later punctuation-check or basic-editorial correction mode MUST be separately selectable,
off by default, and identified in prompt/provenance evidence. The GUI MUST warn before execution
that either mode may increase API usage and unsupported changes; output remains a non-final
candidate requiring full manual review. These modes must not silently broaden the default lexical
correction contract.
The loopback GUI MAY accept a provider key into server-process memory for one run. Such a field
MUST be password-masked, cleared immediately after submission, protected by the same origin and
CSRF boundary, excluded from browser storage/logs/artifacts/configuration, and erased when the
server closes. Persistence across restarts requires a separately designed OS credential store;
plaintext project or settings files are prohibited.
Small tested model presets MAY show approximate separately labeled input/output cost evidence,
but MUST retain exact manual-ID entry. Mutable model availability and pricing MUST be fetched
only after an explicit external-request action, labeled with its disclosure, and never inferred
from stale bundled values. Searchable full-catalog browsing and saved favorites are later UI work.
LM Studio controls SHOULD offer the same explicit readiness check and may prefill the exact model
when the backend advertises one unambiguous loaded model. Any later backend model-load control must
use an explicit operator action and capability detection; discovery or selection must not silently
load, unload, or replace a local model.

Project dictionaries MUST be selectable by project, language, version, and hash. The GUI
MUST display the dictionary provenance recorded by an artifact, including `none`. Dictionary
proposal/review management may arrive after the first vertical slice, but must reuse the
existing project-scoped formats and retained approved/rejected decisions.
The initial correction-dictionary manager MUST compare exact canonical/manual-revision
directories, expose bounded before/after context, preserve mapping identity, retain both
approved and rejected prior decisions, and prevent publication while any candidate remains
pending. Published dictionaries remain immutable and include their exact proposal/corpus
provenance.

Each completed workflow stage SHOULD offer a clearly named next-step action that transfers
known canonical, revision, output-root, language, and project context without asking the user
to re-enter it. Selecting an existing revision SHOULD resolve and prefill its exact canonical
result where lineage and allowed-root evidence identify one unambiguously; otherwise the GUI
must request the source rather than guess. Common output roots, dictionary locations, and
other non-secret preferences may be persisted in explicit application settings.
Completed transcription jobs SHOULD offer both optional correction and direct manual-review
handoffs. Each fills the exact canonical result and containing output root, scrolls to the
chosen stage, and leaves candidate generation or review preparation under explicit user control.

## 6. Review and media interaction

The transcript editor MUST present human-readable speaker turns while preserving the same
machine-owned anchors and exact lineage used by `EWP-REVIEW 1`. Anchors and metadata may be
hidden visually, but the GUI MUST NOT discard or invent them. Applying changes requires a
preview produced by the existing revision validation/alignment path and an explicit user
action.

Preview is a non-publishing validation step: it parses the exact saved review, verifies its
base hash and protected anchors, runs alignment, and reports revision statistics and warnings
without writing a revision. The GUI MUST label that state as unpublished and show a readable
summary before offering expandable technical JSON. Preparing another review while one is open
MUST require an explicit clear action so unsaved editor content cannot be replaced. Disabled
Apply and Export actions MUST be visually distinct and explain their prerequisite.
The active saved review and its non-secret filesystem identity MUST survive page refresh and
browser restart; restoration reloads content from the authoritative review file rather than
storing transcript text in browser storage. Clearing this pointer requires confirmation and
does not delete artifacts. One project output root SHOULD derive separate `reviews/`,
`revisions/`, and `exports/` directories, with manual paths available as an explicit option.
A small versioned, non-secret pointer file under that root SHOULD allow explicit restoration
across browsers and application restarts. It identifies the last review and applied revision;
it is not a transcript/revision artifact and MUST remain subject to allowed-root validation.
A later full-workspace state MUST allow the operator to deliberately save and restore all
non-secret workflow fields, staged artifact identities, open review identity, and current
step after the browser, GUI process, VM, or workstation has stopped. Restore revalidates every
allowed-root path and exact artifact hash; it never serializes API keys, transcript text, or
unsaved editor contents as casual browser preferences.
The first workspace-state slice MAY persist only allowlisted non-secret form fields and the
current step in an application-owned user-state catalog. It must mark entries with unavailable
paths, revalidate every path on save/load, and exclude confirmations as well as credentials.
An active saved workspace MAY be auto-saved. The default GUI interval is 60 seconds and the
client MUST compare the allowlisted state before writing, so unchanged state causes no save
request. Auto-save begins only after an explicit save or load, remains optional, and never
broadens the persisted field set.
An API key entered through the GUI is scoped to the active GUI server process rather than one
browser. Browsers connected to that process share the in-memory credential. It MUST NOT be
included in workspace state, project files, or browser storage, and stopping the server erases it.
This is an intentional single-user or single-organization pipeline boundary. Multi-user accounts,
tenant isolation, and per-user credentials are outside the current roadmap.
Open-review identity remains incomplete until its exact artifact hashes are included.
The first staged-queue recovery slice stores only jobs still in the `staged` state, with source
SHA-256, resolved planned result path, language, and speaker-count settings. On restoration the
server MUST re-hash the source and reproduce the model-free dry-run plan before restaging it.
Queued, running, completed, and failed work is never replayed automatically.
When a workspace restores an output root with an existing review-session pointer, the GUI MAY
reopen it only through the existing review-session validator. That validator confirms the review's
canonical source lineage before rendering; unsaved browser editor text is never reconstructed.
Saving a review draft SHOULD also update an active named workspace so its disk-backed review
pointer and workspace state do not diverge.
A later recovery surface SHOULD discover a bounded list of recent pointer files without
requiring the operator to remember an output root. Entries SHOULD be sortable/identifiable by
optional project name, job ID, and source filename. Missing temporary roots are shown as stale
or unavailable and never prevent the rest of the GUI from loading.

Long reviews MUST support both a sequential previous/next-section view and a continuous
all-sections view, with the presentation preference retained locally. A visible speaker block
can be reassigned as a whole. The reviewer can also wrap complete words or a sentence inside a
visible block in `[[double brackets]]`, isolate that marked text, and reassign it while retaining
the original anchor lineage; the transient brackets are removed before a review is saved. An
explicit confirmation is required before merging one entire adjacent block into the
previous block. Empty blocks and unknown speakers are rejected. It MUST later permit
project/revision-scoped speaker display-name replacement when canonical speaker labels are
absent or wrong; neither feature may silently rewrite canonical results.

Equivalent rules apply to translation units: source text remains visible, target text is
editable, source ownership is immutable, and apply uses the existing translation service.
Automated translation generation MUST identify the exact canonical result and optional source
revision, exact provider endpoint/model, target language, compatibility mode, and optional
project dictionary. The candidate summary MUST expose source verification and dictionary
identity/hash. Raw-ASR and automated-candidate sources remain permitted, but MUST be visibly
distinguished from manually verified revisions. Every automated translation is non-final and
requires semantic—not lexical-overlap—manual review before acceptance.
The semantic editor MUST keep source text and ownership immutable, invalidate preview after
every saved target change, and require explicit checks for meaning, omissions, additions,
uncertainty, names, conventions, register, and style. Only the exact-parent manual child may
be presented as final; audit reconstruction and translated export operate on that child.

Where source media is available, the GUI SHOULD provide synchronized playback, seeking from
a transcript unit, active-unit highlighting, keyboard operation, and independently persistent
follow-playback and light/dark preferences. Minor source timing inaccuracies are evidence for
later timing work, not permission for the GUI to silently alter canonical timing.

## 7. Jobs, diagnostics, and recovery

The initial scheduler runs at most one GPU-intensive job at a time. Queued work has an
explicit state, operation identity, progress summary, cancellation behavior, and recoverable
resume location. Refreshing or closing the browser MUST NOT corrupt an active operation.

Every expected warning and error displayed by the GUI MUST include its stable diagnostic
code, readable message, and an action/help link into the warning and error catalogue. Provider
availability SHOULD be checked before a long operation so an unreachable backend fails within
a short bounded preflight budget rather than exhausting per-unit retries.

## 8. Privacy and security

The GUI MUST preserve the CLI privacy boundary and consent model:

- transcript content crosses a local-API or cloud boundary only after endpoint
  classification and explicit scoped consent;
- audio is never sent to correction or translation providers;
- credentials are accepted as password-like session input or inherited from the server
  process environment;
- credentials MUST NOT enter URLs, browser history, local storage, logs, artifacts, job
  records, or rendered exception details;
- strict-offline mode blocks all provider calls regardless of UI state;
- provider and non-final-candidate warnings are displayed before execution, not only after.

The server MUST validate host/origin for browser requests, protect state-changing requests
against cross-site request forgery, escape all transcript/provider text, use a restrictive
content-security policy, and expose downloads only through validated artifact identities.
The frontend and backend MUST reject incompatible API versions rather than operating
partially.

## 9. Accessibility and presentation

The interface MUST support keyboard navigation, visible focus, semantic labels, sufficient
contrast, browser zoom, and light/dark presentation. Status MUST NOT be conveyed by color
alone. Destructive or irreversible-looking actions require plain-language scope and outcome,
even when the underlying operation is non-destructive.

The interactive GUI may require JavaScript. If scripts are unavailable, the served page MUST
remain safe and readable and explain that the application requires JavaScript; this does not
weaken the separate no-script readability requirement for exported HTML transcripts.

The About surface MUST show application and API versions, license/warranty information, and
the canonical source-code and issue-tracker links.

As workflow coverage grows, top-level workflow sections MUST be collapsible and reachable
through a table-of-contents navigation near the start of the page.
After functional coverage is complete, the primary workflow MUST become numbered, separate
tabs or equivalent routed views—transcribe, optional correction, review/export, translation,
semantic review/export—while dictionary and settings management live in their own clearly
separate views. Navigation must preserve current saved state and must not imply that optional
stages are mandatory.
Server-side result, transcript, dictionary, and output path fields SHOULD offer an allowed-root
Browse control in addition to direct entry. It must use the constrained GUI filesystem API,
not the browser's upload picker or an unrestricted server filesystem explorer.
Allowed roots are operator-granted capabilities, not application-hardcoded work directories.
Production usability SHOULD support persistent named media/project roots and a local launch or
settings workflow for managing them. Browser requests MUST NOT silently broaden server authority;
blacklisting a few operating-system directories is not an adequate replacement for allowlisting
across Windows, WSL, Linux, and containers.
Unfamiliar controls, including non-loopback endpoint authorization, SHOULD have a compact
accessible information action with a plain-language explanation and an optional link to the
relevant bundled documentation. The local help surface SHOULD explain the intended stage-by-
stage workflow, not merely individual fields.

## 10. Initial implementation sequence

The smallest acceptable vertical slices are:

1. loopback server, bundled shell, health/version compatibility, allowed-root configuration,
   coded diagnostics, About/license/source surfaces, and automated security tests;
2. inspect/dry-run plus a persistent-in-process job view without GPU execution;
3. transcription scheduling and result discovery;
4. transcript review/preview/apply and model-free export;
5. correction and translation provider workflows with consent and credential handling;
6. dictionary proposal/review management and remaining operator conveniences;
7. package/install qualification on WSL2 and Ubuntu, followed later by the same application
   inside the Docker distribution.

Docker packaging is intentionally downstream. GUI behavior is qualified before container
construction so the container does not become a separate product implementation.
