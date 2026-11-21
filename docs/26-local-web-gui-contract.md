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

Media files can be large and already exist on the server-visible filesystem. Direct server-side
path entry therefore remains available. Browser file controls deliberately hide the selected
absolute path, so a native-picker selection creates an explicit, session-only copy on the local
loopback server; it is deleted with the GUI process and is never sent off the machine.

The web adapter MUST:

- reject operating-system trees and symlink resolution, while accepting accessible ordinary
  user-space locations without a launch-time allowlist;
- normalize paths through the existing path policy before applying that denylist;
- show the resolved source and destination before a mutating or expensive operation;
- preserve Unicode and spaces, and normalize Windows drive, WSL-mounted Windows, and native
  Linux path forms before applying the same operating-system-path denial policy;
- require explicit Docker mounts rather than implying that host paths are automatically
  visible inside a container;
- never serve arbitrary source files as static web content.

Browser upload-style directory selection is not used: it returns the directory's files and
relative names, not the server-visible path needed by application services, and browsers warn
that the contents will be shared. `showDirectoryPicker()` instead returns a browser-owned handle;
it does not make that directory a Python/FFmpeg path and is not uniformly available. The frontend
therefore offers direct server-path entry plus an optional deployment adapter: a Windows host
dialog under WSL, Zenity/KDialog/Yad on desktop Linux, and direct paths inside explicit mounts for
headless or Docker operation. Lack of a desktop adapter MUST NOT block typed paths.

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
result where lineage and path-safety validation identify one unambiguously; otherwise the GUI
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

The GUI MAY expose editable display names for known speaker IDs and may add a revision-local
speaker ID for manually reassigned text. A changed or added name is stored only in the mutable
review and immutable child revision, is inherited by a review prepared from that revision, and
overrides that revision's exports. It MUST NOT rename canonical speaker IDs,
modify the canonical result, or create a reusable cross-recording identity.

Preview is a non-publishing validation step: it parses the exact saved review, verifies its
base hash and protected anchors, runs alignment, and reports revision statistics and warnings
without writing a revision. The GUI MUST label that state as unpublished and show a readable
summary before offering expandable technical JSON. Preparing another review while one is open
MUST require an explicit clear action so unsaved editor content cannot be replaced. Disabled
Apply and Export actions MUST be visually distinct and explain their prerequisite.
Semantic translation review MUST reject blank targets by default. A distinct, default-off
**Allow empty translation units** confirmation may permit them for an intentional omission; the
preview records the number of such units and Apply is valid only with the same setting. The
control is a per-preview confirmation and MUST NOT be restored from workspace or browser state.
The immutable translation and audit retain each omitted unit's source lineage and explicit
status, while derived TXT, HTML, SRT, and VTT exports omit that unit without a blank placeholder.
The active saved review and its non-secret filesystem identity MUST survive page refresh and
browser restart; restoration reloads content from the authoritative review file rather than
storing transcript text in browser storage. Clearing this pointer requires confirmation and
does not delete artifacts. One project output root SHOULD derive separate `reviews/`,
`revisions/`, and `exports/` directories, with manual paths available as an explicit option.
A small versioned, non-secret pointer file under that root SHOULD allow explicit restoration
across browsers and application restarts. It identifies the last review and applied revision;
it is not a transcript/revision artifact and MUST remain subject to path-safety validation.
A troubleshooting control MAY clear only EWP-owned browser-state keys after a clear warning that
it is not an HTTP-cache purge and does not delete server-side or on-disk artifacts. It MUST not
clear unrelated origin keys or browser-held credentials.
A later full-workspace state MUST allow the operator to deliberately save and restore all
non-secret workflow fields, staged artifact identities, open review identity, and current
step after the browser, GUI process, VM, or workstation has stopped. Restore revalidates every
path-safe artifact path and exact artifact hash; it never serializes API keys, transcript text, or
unsaved editor contents as casual browser preferences.
The first workspace-state slice MAY persist only allowlisted non-secret form fields and the
current step in an application-owned user-state catalog. It must mark entries with unavailable
paths, revalidate every path on save/load, and exclude confirmations as well as credentials.
GUI-owned temporary picker paths are session-only, so they MUST NOT invalidate saving otherwise
durable work state. The GUI clears such form paths and omits jobs whose only source/result is a
temporary picker copy, reporting the omission instead of promising impossible restoration.
Once a user chooses a durable output root and imports a completed canonical result, the GUI MUST
preserve a validated, content-addressed copy under that root before adding it to a resumable queue.
Browser-picked audio MUST likewise be preserved there when the user confirms staging. Source
copies must never overwrite different existing content, and workspace restore must verify their
recorded hashes. Explicit Save current work state MUST save dirty transcript/translation review
drafts to their authoritative output files before saving the non-secret workspace record;
periodic field-only auto-save does not claim to checkpoint unsaved editor text.
Changing the shared output directory updates default workflow output roots. Explicit workspace
save MAY clear unavailable dormant file fields and omit unavailable inactive queue rows rather
than rejecting unrelated recoverable state, but it MUST report both counts. It MUST still reject
malformed, changed, or prohibited paths and MUST NOT reinterpret an unavailable source as valid.
The help surface MUST explain that workspace JSON alone is not a complete backup: the output root,
including dot-directories, and any separate workspace catalog must be backed up together. Session
picker copies are removed when the GUI stops and atomic incoming files after their copy attempt.
Content-addressed sources are durable and MUST NOT be automatically deleted until a future cleanup
operation proves that no active queue, known workspace, or required artifact lineage references
them. In the current slice they remain until the operator archives or removes the whole project.
An active saved workspace MAY be auto-saved. The default GUI interval is 60 seconds and the
client MUST compare the allowlisted state before writing, so unchanged state causes no save
request. Auto-save begins only after an explicit save or load, remains optional, and never
broadens the persisted field set.
Auto-save MUST default off. Its control must explain that enabling it replaces the active saved
recovery point after tracked queue additions or removals; consequently, a removed queue item may
stop protecting its managed source through that workspace. Explicitly saved state remains stable
until the operator saves again or knowingly enables auto-save.
When a custom workspace catalog is selected, the visible workspace list MUST include both that
catalog and the private default catalog because managed-source cleanup audits both. Every entry
identifies its catalog, and load, overwrite, delete, import selection, and auto-save target the
entry's owning catalog. The same imported workspace ID may exist independently in both catalogs.
An unavailable workspace remains selectable for maintenance. The GUI disables restore and
auto-save because its referenced paths cannot be validated, but MUST still allow confirmed
deletion of that workspace JSON without touching any transcript or workflow artifact.
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
can be reassigned as a whole. The reviewer can also select complete words or a sentence inside
a visible block, isolate that selected text, and reassign it while retaining the original anchor
lineage. Merging one entire adjacent block into the previous block saves any dirty draft first,
creating a recoverable checkpoint before the visible merge; the merge itself remains editable
and must be saved again before preview. A selected leading `.`, `!`, or `?` immediately before
a new sentence remains with the preceding block when the new sentence is isolated. Empty blocks
and speakers not defined by the canonical result or the revision-local display-name map are
rejected. It supports project/revision-scoped speaker display-name replacement when canonical
speaker labels are absent or wrong, plus manually added revision-local speakers; neither feature
may silently rewrite canonical results.
The GUI MAY remove an unused revision-local speaker from the mutable review. It MUST refuse
removal while any visible block still references that identifier; the reviewer must reassign or
merge those blocks first.
Separating text or adding a revision-local speaker likewise saves a dirty draft before changing
block structure. The current editor maintains a bounded Undo/Redo history that never writes an
artifact; undoing or redoing a change makes the draft dirty and therefore still requires Save and
Preview before Apply.

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
Opening a different semantic-review queue item MUST save any dirty target edits before changing
the active source, then load or prepare that item's own exact draft. Preview saves dirty target
edits before validating the saved draft; Apply and export remain explicit separate actions.

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
Result-import queues MUST use the browser's native picker. A selected canonical JSON first enters
the same-machine loopback server's owned temporary work directory and is strictly parsed; the
picker never searches all user filesystems. Import requires an explicit durable shared output
root. The validated JSON is then preserved under that root in a hidden content-addressed source
folder before it enters the queue, and the session copy is deleted when the GUI server stops.
Review, revision, and export files also use the selected root. If the root is missing after file
selection, the browser retains that selection during the current page session and resumes
import when the root is supplied. Validated force-versioned canonical names
(`*_results_vNNN.json`) are accepted alongside `*_results.json`. Inspect and
plan likewise offers a native audio picker that makes an explicit, bounded session copy and shows
its temporary server-side path. When staged after a reviewed dry-run, that audio is copied into
the same durable content-addressed source folder and the queue uses the durable path. The picker
button must show Working and Done feedback. Output
directories allow direct path entry or a server-mediated, deployment-specific operating-system
folder dialog. WSL, desktop Linux, and headless/container adapters may differ without changing
the browser workflow or application API.
Browser directory selection causes an unavoidable browser-controlled sharing warning and is not
offered. Direct server-side result, transcript,
dictionary, and output path fields MAY retain typed entry while their native-picker replacements
are qualified.
Durable `.ewp-gui-sources` cleanup MUST begin with a fresh inventory of the chosen output root.
The GUI may select only copies with no reference from the current queue, the default workspace
catalog, the explicitly selected custom workspace catalog, or review/revision/translation lineage
under that output root. Referenced, hash-mismatched, unreadable, or structurally unsafe copies are
not selectable. Cleanup re-runs the audit immediately before deletion, requires an explicit
per-batch confirmation, removes only the selected exact files and empty managed-source parents,
and never deletes publication artifacts. The interface MUST disclose that custom workspace
catalogs stored elsewhere are unknown and must be audited separately.
The GUI does not use a launch-time filesystem allowlist. It rejects documented operating-system
directories and symlinks to prevent accidental system changes; this is an operator-safety policy,
not a security boundary against the local account that starts the loopback service. Optional
search roots optimize browser-picker lookup and do not grant or remove path access.
Unfamiliar controls, including non-loopback endpoint authorization, SHOULD have a compact
accessible information action with a plain-language explanation and an optional link to the
relevant bundled documentation. The local help surface SHOULD explain the intended stage-by-
stage workflow, not merely individual fields.

## 10. Initial implementation sequence

The smallest acceptable vertical slices are:

1. loopback server, bundled shell, health/version compatibility, local path-safety policy,
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

## Integrated preview 0.20.0 compatibility

The stage-focused shell reuses the existing controls and application services. PL/EN and explicit
system/light/dark are browser preferences, independent of processing languages. Multi-audio selection
retains inspect/exact-plan/stage/start. Cursor splitting stays within protected anchors and requires
Preview alignment; selection isolation remains a separate command. Optional export speaker-color maps
are validated at the web boundary and version new exports without changing saved production settings.
Workspace v2 adds allowlisted semantic-review paths and display preferences, restoring through existing
exact-lineage validators. See [the detailed preview contract/evidence](28-integrated-gui-preview.md)
and [the consolidated owner plan](../Instructions/GUI_PREVIEW_TEST_PLAN.md).

## Source playback and video increment (2026-11-19)

Stage 3 has a compact left-rail audio player and a per-block Go to this fragment action below
the speaker selector. The existing model-free anchored alignment maps saved blocks to real
source-word starts. Insertions/ambiguous matches show a nearest-known-timestamp notice and
never invent canonical timing. A dirty draft is saved first; seeking publishes no revision.
Stage changes pause audio. Source/position are kept independently per recording in memory.

Review documents add playback_sources metadata (source ID, filename, speaker and channel).
POST /api/v1/reviews/playback accepts result_path/source_id through existing Host/Origin/CSRF
checks, validates the completed canonical result and selected original source sizes/SHA-256, then decodes
the canonical stream/channel to a private mono 16 kHz PCM workdir. One cached preview is kept;
source/mix changes revoke prior opaque tokens. No arbitrary filesystem URL is exposed. GET/HEAD
/api/v1/review-audio/<opaque-session-token> streams in bounded chunks with audio/wav, no-store,
Accept-Ranges and single byte ranges (206/416). Unknown tokens/foreign requests are rejected.
The exact media-src self policy permits local playback only. Cache/workdir cleanup runs when
the source changes or the server closes; an open stream retains its own descriptor.

POST /api/v1/reviews/playback-position accepts result/review paths, expected review SHA-256 and anchor/block indices,
validates their lineage and returns a real start_ms plus an approximate flag. It uses the
existing deterministic alignment, with a fast path for unchanged words, and writes no artifacts.
Editing/export remains available when original media has moved; playback asks to restore it.

Video input accepts MP4/MKV/MOV/WebM/AVI/M4V in native picker/directory discovery and follows
the same inspect/plan/queue/application pipeline. Canonical source metadata already permits
video; no schema migration is required. Only audio is decoded. Missing/multiple audio is an
explicit error with guidance; interactive stream selection and video-frame playback are deferred.

The percentage/ETA analysis is [recorded separately](30-queue-progress-and-eta.md). Approximate
progress is implemented through actual phase events; precise GPU percentage/ETA accuracy qualification is no longer required by owner.

## Episode mix, review bounds and live progress increment

Default source playback requests source_id=mix, verifies all original source records and mixes
their selected streams/channels at shared time zero. The longest timeline is retained; amplitudes
are normalized in the preview to avoid summed clipping. Individual source API identifiers remain
backward compatible, but the regular UI always plays the complete episode. Each block adds a muted
source-filename hint from canonical word/speaker/segment provenance, independent of edited labels.

New review anchors use word/speaker targets and prefer nearby EN/PL sentence ends. A bounded
unpunctuated fallback is disclosed above the first review section. These are presentation sections,
not subtitle boundaries. The GUI can project
unchanged oversized legacy drafts into bounded anchors, preserving text/assignments; edited legacy
blocks are bounded without changing their existing anchors. Projection is read-only until explicit
Save. Server-owned projected anchors are re-derived at save/seek boundaries. Derived provenance
metadata updates do not discard the caret or scroll position. Canonical timing remains unchanged.

Transcription API responses add runtime_progress with phase, approximate percent, monotonic
elapsed/phase time, stream counters, optional ETA range and calibration/overdue flags. Optional
application/pipeline observers report actual phase starts/completions. Only successful completed
runs update bounded content-free local timing history. Queue polling provides the elapsed heartbeat;
unknown estimates remain explicit, slow phases withdraw ETA, failures stay below 100%, and true
completion follows publication/exports/cleanup. Saved-work history never revives a live job.

The [artist package](31-artist-review-package.md) uses a separate in-memory mock adapter and never
changes production request/authentication/provider behavior. Its state/progress are synthetic.


## Portable user profiles and batch planning (2026-11-20)

Native selected-media Inspect, dry-run and staging share one ordered list of all pending episodes.
Each episode retains language/count independently. Combined planning is an explicit request snapshot;
any changed selection/output/options requires replanning. Staging calls the existing exact-plan,
confirmation and source-hash boundary per item; a partial error retains earlier staged items and
requires planning the remaining list again. Completed matches retain normal skip behavior.
Inspect summaries mark processing selections with * when metadata lacks those values; no ASR language
or speaker detection is claimed. Batch counts, settings and actions are localized EN/PL.

POST /api/v1/profile/save accepts name, explicit display preferences, allowlisted current workflow
fields, selected workspace-storage and dictionary-directory values. It writes a version-1 user profile
under the private state root and returns its JSON. /load restores the saved profile; /import accepts
that profile JSON. All profile routes require same-origin and the active CSRF session, permit at most
16 MiB and validate the complete structure before imports. They do not execute jobs or replace editors.
The single file includes selected/default workspace manifests, selected/referenced available dictionary
editions and custom palettes; it excludes credentials, confirmations, transcripts, media and timing
history. Missing external paths remain unavailable, with normal workspace validation required at Load.
Imported workspace identities are content-derived and distinct; repeated identical imports are idempotent.
Existing records/editions are not deleted. Dictionary bytes/hashes survive transfer; private imported
copies use digest directories. Custom palette name conflicts allocate distinct names.

POST /api/v1/dictionaries/export returns filename, original UTF-8 JSON payload and SHA-256;
/import validates/publishes those exact bytes under the chosen catalog and accepts an existing ID
only when bytes match. These routes retain the library's origin/CSRF/path policy and immutable editions.
Editing/importing a dictionary are distinct actions.

ETA is a persisted display opt-in, off by default. Numeric ETA requires three matching successful
complete runs, counted per job rather than per source track. Runtime snapshots add calibration_runs
and calibration_required. Browser elapsed interpolates every second, capped between existing two-second
polls; no extra requests. Machine timing history never enters portable profiles. Playback speed uses
an explicit local selector for both single media and mixed previews, retaining native audio controls.


## Owner acceptance and documentation sequence (2026-11-20)

The owner accepts current GUI/workflow changes with the summary/navigation polish in the current
checkpoint. Full profile exchange and the latest full-restart recovery are not owner-tested;
automated success does not upgrade those claims. Browsers and palette are accepted. Actual 200%
page zoom is not established, and remains an optional layout check rather than a blocking gate.
Progress primarily demonstrates continued activity; no accurate ETA study is required.

Finish the selected functional work before generating one editable complete EN–PL pair list for
all labels/messages, errors, statuses, hints, tooltips, numbered guide copy and dynamic templates.
Owner correction/approval precedes full Polish manuals; documentation screenshots additionally
wait for custom icons/final GUI. Artist waiting has no deadline and does not block development.
The sent artist ZIP/demo remains unchanged. Native Windows is planned as a separate target.
See the roadmap's retained/recovered inventory; research benchmarks and presets are optional.

Inspect and Dry-run display language * and speaker-count ** as selected processing values, with
two full-width wrapping explanations below all summary tables. The plural queue confirmation
still authorizes the exact reviewed request snapshot. Source section counters are vertically
centered against navigation buttons; no workflow/API semantics change.

## Package A additions — 2026-11-20

The current owner package adds cooperative cancellation to the single ASR worker. Waiting work
becomes `cancelled`; running work first becomes `cancel_requested`. Safe checkpoints occur between
inspection/preparation, ASR, alignment, normalization, diarization/composition and final publication.
The active native call may finish first; no thread/GPU is killed. An atomic token gate rejects late
requests once publication begins. Cancelled attempts retain terminal job state/workdirs according to
configuration, publish no incomplete final canonical result, and retry under a new queue-attempt ID
from the beginning with source hashes rechecked. Completed history never re-enters the worker.
Cancelled history joins completed/failed saved-work history; running/requested work never resumes
as an in-flight operation. Completed history recovery no longer requires original audio, but still
requires its validated canonical result/output. Playback independently requires its source media.

Settings & About offers configured-root temporary inventory, reason/creation-age filters, selected
cleanup preview and explicit confirmation within five minutes. Version-2 owner markers preserve
UTC allocation time and terminal retention reason. Current queue/default/selected workspace catalog
references, active owners, symlinks, special/unknown artifacts and legacy-unknown owners protect
workdirs. Revalidation covers the whole selection before deletion and reports partial I/O removal
honestly. See [the marker contract](09-state-errors-and-logging.md#9-workdir-cleanup-metadata).
This is separate from durable managed-source copies; catalogs outside the selected/default roots
remain unknown and must be checked separately. No automatic deletion or final-artifact cleanup.

Both review stages expose existing-export downloads for applied manual revisions/translations.
A CSRF-protected POST lists validated export records; opaque 30-minute session URLs serve only
registered artifacts. Records bind canonical/revision/translation identities plus file SHA-256/size.
GET/HEAD enforce local Host, reject foreign Origin/cross-site fetches, reread bounded regular files,
reject symlink ancestors/hash changes, and serve exact bytes as attachment/octet-stream with the
original UTF-8 filename and security/no-store headers. No user-supplied filesystem download URL
exists. HTML is downloaded, never executed inline. Refresh does not run ASR or write exports.

Private `export-downloads.json` under the application state root preserves verified file/version
records across server restarts, without credentials or transcript text. New trusted GUI exports are
registered after publication; compatible older files are verified read-only against the same renderers.
Older custom palette files without records may need their original settings, rather than guessed
provenance. Missing/changed files are withheld; older registered palette/version hashes stay exact.
Public canonical/revision/translation schemas and pinned ML packages remain unchanged.

## Owner A closure — 2026-11-21

The owner passed the complete focused A checklist. The final source-review adjustment needs no
new owner retest: step 4 uses one action panel with Undo, Redo, Save draft and Restore saved draft
above Apply and Clear current draft. The redundant Prepare text for review button is removed;
queue review/export and correction-candidate actions still prepare/load the draft automatically.
Validation, explicit manual-verification consent and immutable publication are unchanged.
Package A is closed. B preparation targets Windows 11 x64: agent implementation/checks/push on
the Linux VM, owner pull and native execution/full-workflow testing.

## Owner A acceptance corrections — 2026-11-20

The public GUI has one checking/planning action, Dry-run, which performs the existing inspection
and creates exact hash/settings-bound plans. CLI/API Inspect is retained. Missing human staging
confirmation does not invalidate an otherwise unchanged plan; source/settings changes still do.
Before ASR completes, the recording rail identifies transcription as the next stage. Canonical
imports and completed ASR are labelled ASR completed; only all finished/skipped stages indicate
workflow completed. Successful manual source-review actions infer the unused optional correction
skip; existing downstream immutable artifacts provide the same inference after restart.

Saved-work load has a session-local progress identity, serialized restore ownership and real
loaded/total queue counts. A modal/backdrop/gear remains until server queue and browser editor
restoration finish. No ASR or confirmation is restored. Immediate save/load busy text replaces stale
success messages. Failed/cancelled terminal history validates safe file locations even if originals
have moved or its planned result was later published; staged work still requires exact live source
hashes and plans, and completed history still requires its canonical artifact.

Retry uses a fresh attempt ID and replaces the selected old terminal row rather than duplicating
it in the visible queue. Source/publication/workdir retention is independent. Existing older duplicate
history is not silently migrated/deleted. The native audio player has stable space for browser
controls during source review; overflow and playback-speed UI are supplied by the browser. Native
rate preferences (0.25–4x) persist in the existing profile field. The permanent duplicate rate select
is removed. Raw output/source provenance and shared-timeline playback are unchanged.

Temporary inventory refresh disables stale rows and ignores superseded responses; selection/filter
changes invalidate pending previews before confirmation. Cleanup continues to target only eligible
temporary workdirs, not durable media. Whole-interface EN–PL approval and final EN/PL manuals
remain sequenced after feature completion; only necessary changed-stage instructions are updated.

## Owner Windows feedback clarification — 2026-11-21

The main recording picker and Add audio in the rail accept audio, video and canonical result JSON
through the same flow. The input-directory convenience/discovery buttons and per-episode selection
buttons are removed; output browsing and direct paths remain. Each pending recording exposes its
language/count. Local ffprobe metadata is read automatically; only multi-stream media reveals a
warning and explicit stream choice. This supersedes earlier deferral of interactive stream selection.
Duplicate planned IDs reveal ID fields only when required. One Dry-run table combines sources,
decisions, warnings and processing settings for the batch.

Explicit POST /api/v1/speech/check uses the shared process/environment OpenRouter key for a GET
/key readiness check, without returning account information. POST /api/v1/speech/estimate validates
local media paths/stream choices, probes durations and reads the public transcription model catalog
and endpoint prices for the four existing presets. Both local routes require the current CSRF token
and same-origin policy. Neither uploads audio/text; price discovery does not require a key and is
never triggered automatically. The UI marks an estimate stale after input/settings changes.

Endpoint duration rates are normalized to USD/audio hour (MAI's prompt price is per hour; the other
three vetted presets use seconds). Estimates account for chunk overlap/rounding and a stereo-mode
range. They are mutable estimates, not billing promises. New GUI speech requests use
speech.cost_mode=estimated and derive an internal job-wide reserve from actual track durations,
chunk plan and refreshed maximum endpoint price, with a USD100 safety ceiling. Existing fixed
speech.max_cost_usd jobs remain compatible. Consent is still fresh and excludes saved work.

Unexpected queue failures expose exception type, errno/winerror and basename/line/function frames,
without arbitrary exception text, source lines, locals, credentials or transcript content. The same
safe locations are logged to the local terminal. Each failed job has one collapsed error disclosure,
with technical JSON nested inside. Storage retains file fsync and atomic publication on Windows;
it skips POSIX directory-descriptor flushing there, without claiming directory-metadata power-loss
durability. See the Windows feedback checkpoint and owner retest checklist.

## B native workflow feedback clarification — 2026-11-21

Add files names the rail's mixed media/canonical-result picker. Plan headers preserve word boundaries;
phone widths can scroll that table locally. The source/translation review main row starts with Apply,
then Undo/Redo/Save draft/Restore saved draft; Clear current draft is a secondary row aligned right.
Source export progress recognizes any supported verified export format, including subtitle-only sets,
and the actual exporter version suffix order. Existing accepted translations remain complete when
an older generated candidate is retained. Assisted generation completion and manual semantic review
are distinct; generating a candidate does not approve its content. Single generation refreshes the
queue immediately and blocks repeat submission for that source until explicit Reopen translation.

Missing cloud-upload or correction/translation disclosure is rejected in the frontend before requests,
with an accessible focused/highlighted checkbox and explanatory text. Server checks remain required.
The OpenRouter dialog exposes explicit Close/×/Escape and a read-only API-key check. A nonempty
api_key in POST /api/v1/speech/check tests that value without replacing the active session key or
saving it; no value is echoed, stored in workspaces, or unlocked from OS storage automatically.
With no supplied key, check uses the existing shared session/environment key. After restart, users
enter or explicitly load the saved key. Session activation leaves the dialog open for save/check/use.

Review audio treats BrokenPipeError, ConnectionResetError and ConnectionAbortedError as client
request termination during headers or body transfer, closing the source descriptor. Ordinary JSON
responses also tolerate those disconnected writes. General media/OS errors still propagate. No
claim is made about which native host/browser component caused a particular Windows10053 event.

### Restored cloud consent and saved-work layout follow-up — 2026-11-21

HTTP cloud starts require a one-use grant in addition to `cloud_confirmed: true`. On a trusted
checkbox change the frontend posts the exact staged cloud job IDs to
`POST /api/v1/transcriptions/cloud-consent` with the usual Origin/CSRF checks. The queue returns
an opaque `cloud_consent_token` bound to all staged job IDs. `/transcriptions/start` consumes and
checks it under the same queue lock before queuing workers. Missing/null/stale tokens, changed
staged IDs and false consent are rejected with `GUI_CLOUD_CONSENT_REQUIRED`. Loading a workspace
revokes the grant even in the same process. A retry gets a new job identity and needs new consent.
Unchecked input revokes the frontend's token; restoring fields/profiles clears it. No token or
consent is serialized. Explicit trusted in-process `queue.start(allow_cloud=True)` remains an
application API; HTTP cannot select that bypass by omitting or nulling its token.

Blank optional GUI catalog paths resolve to the shared output directory for new saves, imports,
profile workspace storage and cleanup audits. Existing selected saves retain their catalog, including
the legacy private default catalog, which remains listed. Saved-work entry auto-refreshes the list;
name validation highlights/focuses its field. Optional catalog hint precedes its input, name label
stays with its input, Refresh is below Save and removal controls are secondary/right-aligned.

The application is centered and bounded to 100rem, with main reading content bounded to 64rem.
The engine disclosure never encloses planning actions/headings. Key-check feedback follows its
button. The derived favicon uses visible-artwork bounds instead of the original SVG's stray
registration mark; the main logo and sent artist package remain unchanged.
