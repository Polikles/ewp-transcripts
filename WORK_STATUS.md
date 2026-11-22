# EWP-transcripts work status

Last updated: **2026-11-22**.

## Active task and resume pointers

Current handoff: [Windows startup/live queue correction](docs/checkpoints/2026-11-22-windows-startup-refresh.md).
Baseline mainb0c2ddf. Reproduced win32 bootstrap null href after help-language query insertion:
About stayed Loading and backend completed while UI stayed running. Stable help ID plus early
idempotent polling fixes it; optional UI/restore errors get a distinct initialization code.
Document-level modal Escape/Tab containment, label-row language info and requested EN/PL subtitle
are corrected; stable-ID language reference updated.1056 tests/mypy115,17 integrations,216 layouts
and focused Windows-session/synthetic queue phases/completion/queued+active cancellation pass.
Eight modal entry/locale cases and3 caption widths pass. No real GPU/provider qualification claimed.
Next owner step: Instructions/GUI_WINDOWS_REFRESH_RETEST.md; preserve accepted wording/workflow
passes and do not reinstall models or repeat paid ASR. One-off output mismatch not reproduced;
shared-output guard unchanged and all7 status eligibility cases pass. Root cleanup/evidence is in
the checkpoint. Delivery targets main. After owner approval: EN docs → complete PL docs → NEW
artist package. Original artist ZIP/returned workbooks unchanged; prior spend unchanged.

Earlier handoffs below are historical.

Current handoff: [owner terminology integration](docs/checkpoints/2026-11-22-terminology-application.md).
Baseline maince9ddfc.106 owner-reviewed rows integrated (18 EN /105 PL); three rows include noted
spelling/actual-queue-target adjustments and one quick-guide title is synchronized. XLSX/CSV and
submitted/applied provenance are in docs/ui-language. Original local workbooks remain unchanged.
Full-message translations precede generic code fallbacks; help navigation follows interface locale,
while full manuals remain English.1050 tests/mypy115,17 integrations,216 full browser layouts and36
focused copy layouts pass;102 static pairs,2 templates,2 reviewed guide edits,1 derived guide and4
help labels checked across locale roundtrips. No page errors/external requests/paid calls.
Next: owner interface approval using Instructions/GUI_TERMINOLOGY_APPROVAL.md. After that approval:
EN documentation review/update → complete PL user documentation → NEW updated artist package.
Original artist ZIP unchanged. Source/spend/privacy qualifications retained; no reinstall/GPU test.
Temporary-root cleanup/evidence recorded in checkpoint; delivery targets main. Do not start later
documentation/package stages before owner approval or overwrite returned/delivered workbooks.

Earlier handoffs below are historical and superseded by the current gate above.

Current handoff: [final B polish and EN–PL review](docs/checkpoints/2026-11-22-terminology-review.md).
Baseline main8475723. Duplicate Save as new names now reject across known catalogs, preserving
updates/legacy records; short two-line key feedback sits to button right. Owner requested no manual
retest.1047 tests/mypy115,17 integrations,12 focused EN/PL/theme/width browser cases pass; screenshot
inspected. Local editable workbook2218 rows (all984 effective exact catalog entries plus templates,
diagnostics/guide copy) is ready at project deliveries/ewp-ui-en-pl-review-2026-11-22.xlsx, outside Git.
See Instructions/UI_LANGUAGE_REVIEW.md. Roundtrip EN/PL/ID/placeholder/source-snapshot validation
passes. Await owner's edited workbook; never overwrite/regenerate that delivered file.
Next: apply EN/PL edits and commit approved reference → owner interface approval → update EN docs
→ full PL docs → NEW updated artist package. Original ZIP unchanged. No paid ASR/reinstall; old
pending-function-freeze gates are superseded for task10 by owner's explicit request. Temporary
verification root cleanup is recorded in the checkpoint/evidence; delivery targets main.

Latest follow-up implemented/verified: [recent locations / named saves / key preflight](docs/checkpoints/2026-11-22-b-locations-key-preflight.md).
Baseline main 5d60f7f. Last directories/catalog list return automatically; name-prefixed manifests
preserve UUID/legacy compatibility. Key dialog rows/short labels/secondary clear-delete/bottom-right
Close are fixed. Missing/rejected keys stop the entire cloud/mixed queue before workers/media;
fresh consent is rechecked and no OS key is loaded implicitly. Supplied terminal chain is one
missing-key exception.1046 tests/mypy115,17 integrations,216 browser layouts,12 dialog cases and
actual process-restart directory/preflight/source/translation/export recovery pass. Changed-step
checklist/docs/evidence updated; dedicated root removed and artist ZIP unchanged. No paid calls;
cumulative USD0.0291461230985028369. Delivery main; next is the focused owner update check. Preserve
new owner save/load/cloud/export/progress passes; retained-failure native retest was not repeated
(old files gone). A closed, full B acceptance/task10 terminology/manual gate remain separate.

Previous delivery records below are historical.

Current task: [B recovery / pending media / cloud timing](docs/checkpoints/2026-11-22-b-recovery-cloud-timing.md),
baseline main 7a1c2da. Fixes implemented; pending-browser Save/restart/Load passes with completed+
failed rows, restored media paths/deduplication, stable saved-name identity and visible manifest path.
Async refresh could undo Save as new; revision counters and captured Save identity fix that race.
Whisper's missing-word issue reproduced on a supplied full track: Together dropped word timing after
9 DeepInfra chunks. Restrict route/price subset to DeepInfra/Groq; original tail now returns real
words for Whisper and Scribe. All10 responses replay successfully (777 words), no fabricated times.
Scribe's original native failure remains unproven; content-free diagnostics added for future defects.
No more paid calls; cumulative USD0.0291461230985028369. Disposable servers stopped and root
/tmp/ewp-b-recovery.nTxlJ0 removed after saving content-free evidence and exact spend totals.
1043 tests/mypy115,17 integrations, full GUI216 cases, fresh-consent48 and full review restart pass.
Changed-step docs/checkpoints/evidence saved. Delivered on main; next is the owner update-only retest.
A stays closed, artist ZIP frozen; task10 local ID/EN/PL draft waits for functional acceptance.

Current follow-up is implemented/verified: [restore consent / workspace / layout](docs/checkpoints/2026-11-21-b-restore-consent-layout.md).
Baseline main dee74cd. Fresh exact-queue one-use consent now gates HTTP cloud starts; load revokes it,
retry/changed queues invalidate it, and manifests/profiles never restore it. Original native bypass
cause remains unproven; tests preserve OpenRouter Whisper identity and reject unchecked/stale state.
Favicon visible-artwork centering, bounded desktop/editor width, key feedback, planning disclosure,
short cloud copy and saved-work controls/default output-root storage are corrected. 1034 tests,
17 integrations, mypy115, 216 full browser cases through 4K, focused/restart recovery pass.
Use [update-only checklist](Instructions/GUI_UPDATE_TEST_CHECKLIST.md); no model reinstall or fresh
setup check. Those wait for uninstall/installer milestones. Evidence is saved and disposable
servers/root removed. Delivered on main; owner B update-only retest remains; A closed, artist ZIP frozen, no paid calls.
Full B/terminology/manual gates stay separate.

Latest B native feedback is implemented/verified: [checkpoint](docs/checkpoints/2026-11-21-b-workflow-state-polish.md).
Owner confirms native local ASR, source export, cloud ASR and OS-key save/use actions work. Source
status now recognizes subtitle-only/versioned exports; generated translation refreshes assisted
progress and blocks duplicate generation until explicit reopen. Manual translation status remains
complete after publication despite retained candidates. Cloud/correction/translation disclosures
highlight missing consent; key dialog has Close/×/Escape/API check and clearer enter/load guidance.
Review rows/copy/plan labels and optional native picker placement are fixed. Expected Windows
aborted playback requests no longer log stack traces; unrelated I/O failures remain visible.
1031 tests / 17 integrations / mypy115, full/focused Chromium and actual restart/recovery pass.
Evidence is recorded; delivery targets main. Next is the focused owner B retest. A closed, artist ZIP frozen;
no paid calls/model/uninstall changes. Task10/manual approval remains after functional B acceptance.

Windows queue/GUI fixes delivered: [checkpoint](docs/checkpoints/2026-11-21-windows-queue-gui-feedback.md).
Baseline 761109f. Shared Windows-safe publication fixes the reproduced directory-descriptor defect;
unexpected failures now retain safe OS/frame diagnostics. Single media/results picker, per-recording
settings, conditional stream/ID controls, one plan table and explicit OpenRouter key/pricing estimates
are implemented. make check: 1008 tests / mypy115; integration: 17 passed / 4 deselected. Full Chromium
144 layouts, focused owner-feedback checks and actual restart/editor/export recovery pass.
Next: owner pulls/restarts/refreshes Windows GUI and retries grouped audio + MP4, then publication.
No model reinstall for this storage fix. Native full workflow/B acceptance remains pending.
Later uninstall/model removal and standalone GUI EXE installer/desktop/Add-Remove Programs/uninstaller
are TODO only. A stays closed, artist ZIP frozen; full ENPL terminology/manual gate unchanged.

Windows owner step-4 defect fixed: setup-models.py isolates NLTK language-data preparation in a
child with -I and neutral cwd, preserving its security hook and caller paths. Locked NLTK import
regression passes without downloads. [Fix checkpoint](docs/checkpoints/2026-11-21-windows-model-setup-nltk.md).
987 tests / 15 integrations and explicit script Ruff/format pass; model/dependency pins unchanged.
Owner subsequently confirms model preparation/install/GUI/doctor pass. Native ASR/publication
acceptance continues with the current queue/GUI fix above, not another model-preparation cycle. Disposable test root /tmp/ewp-nltk-setup.AScITi removed after evidence capture; no paid calls, models, private audio or artist package changes in this fix.

Owner requested installation/run/test instructions; [handoff checkpoint](docs/checkpoints/2026-11-21-owner-b-test-handoff.md).
Next: owner native Windows 11 x64 installation/doctor and the B checklist, then full WSL comparison.
No product change or new qualification is implied by this instructions-only handoff.


Latest owner follow-up delivered: cloud recordings split automatically into requests below 24 MB
and merge on one timeline. [Chunking checkpoint](docs/checkpoints/2026-11-21-cloud-chunking.md).
Shared timed context remaps local speaker IDs; ambiguous identities stay distinct with a visible
source-review note. 982 tests / 15 integrations, Ruff/format/mypy 114 files pass. Live Scribe/MAI
3-request PL cases pass schema/review/SRT/VTT/YTT. Cumulative live cost USD 0.0153610111540591670
within the original USD 2 budget. Prior single-request mixed limit is superseded. B owner acceptance
is next; EN live waived, artist frozen. Disposable root /tmp/ewp-cloud-chunks.BKHH1C removed after evidence capture. Delivery targets main; next is the owner B checklist.

Current request: B5–B9 agent implementation and delivery complete; owner acceptance next.
[Execution checkpoint](docs/checkpoints/2026-11-21-package-b-execution.md),
[B9 verification](docs/checkpoints/2026-11-21-b9-verification.md),
[full owner Windows/WSL checklist](Instructions/GUI_PACKAGE_B_TEST_CHECKLIST.md).
B5 native support, B6 OS credentials, B7 project/profile references, B8 media/IDs and B8a
four-model OpenRouter ASR are delivered. 973 unit tests / 14 FFmpeg integrations pass; Ruff/format/
mypy 113 files pass. Chromium full 144-case GUI, real server restart and focused B HTTP tests pass;
wheel/sdist resource/privacy and installed CLI smoke pass with model-free dependencies.
10 live PL calls cost USD 0.0095832333762821113 total; all four models and Scribe/MAI mixed cases
pass schema/review/SRT/VTT/YTT. EN live waived by owner (no sample; HD06 MP4 is PL).
Actual native Windows11x64/GPU/OS store and full owner Win/WSL acceptance remain pending.
No tag/release or artist ZIP changes. Task 10 full EN–PL approval file follows B acceptance;
manuals follow terminology approval. Disposable root /tmp/ewp-package-b.Yz9JAl and its test outputs were removed after evidence capture;
servers stopped and frozen artist ZIP hash verified unchanged. B delivery targets main; the
owner acceptance checklist is the next resume point.

Previous planning-only statements are historical and superseded. Preserve the USD 2 total
cloud-ASR test scope and the owner Windows 11 x64 execution arrangement.

Current request: [package B execution plan and remaining questions](docs/checkpoints/2026-11-21-package-b-plan.md).
Baseline clean main 56f597e. Planning only; no product implementation/provider calls. Order remains
B5 native Windows → B6 OS keys → B7 projects/profiles → B8 media selection → B8a cloud ASR →
B9 integrated qualification and the owner's full Win/WSL checklist. Windows 11 x64 execution
split is confirmed: agent changes/checks/push on Linux VM; owner pulls/tests natively.
Owner cloud decisions are resolved: OpenRouter with the same API key for ASR/correction/translation;
four ASR dropdown IDs `openai/whisper-large-v3`, `openai/whisper-large-v3-turbo`, `elevenlabs/scribe-v2`,
`microsoft/mai-transcribe-2`. Owner permits short supplied podcast/English samples (PL two speakers,
EN one) for B8a functional canonical/downstream tests, USD 2 total including all calls/retries/models.
This is not a corpus/accuracy benchmark. Public official pages/STT response docs verified; no key
read, upload or paid call performed. Locate actual files/recheck live capabilities/costs at B8a;
retain this authorization without asking again. B implementation still waits for a start instruction.
A stays closed; EN–PL approval follows B acceptance/function freeze; manuals follow terminology
approval and artist package remains frozen.

Earlier closure/delivery records below are historical.

Current request: [A closure and B preparation](docs/checkpoints/2026-11-21-package-a-closure.md).
Baseline clean main edda543. Owner passed the entire focused retest and accepts A on 2026-11-21.
Final no-owner-retest adjustment: remove redundant source-review preparation, merge action panels
into two rows and use Restore saved draft / Clear current draft. Implemented and verified; A closed.
make check PASS: 928 tests, Ruff/format, mypy 106 source files. Focused Chromium check PASS:
24 EN/PL/theme/width cases, queue/correction-candidate opening, Undo/Redo/Save/Apply/Clear/Restore
and custom gear; zero page errors/external requests. Ordinary checks suffice; no owner retest needed.
Next is B5 preparation, with the execution arrangement confirmed by the owner: Windows 11 x64;
agent implements/checks on this Linux VM and pushes to GitHub, owner pulls/tests natively.
No B feature implementation/cloud calls in this closure task.
Complete EN–PL approval and full manuals remain after B/function freeze; artist ZIP stays frozen.

Earlier A feedback/execution records below are historical; their pending-owner-acceptance wording
is superseded by the 2026-11-21 acceptance above.

Current request: [package A acceptance fixes](docs/checkpoints/2026-11-20-package-a-feedback.md).
Baseline clean main abe9ed2. Reported A acceptance fixes are implemented and verified; use the
[focused owner retest](Instructions/GUI_PACKAGE_A_RETEST.md). B remains gated on A acceptance.

Queue rail correctly distinguishes pre-ASR / ASR complete / workflow complete. Saved-work loading
has a blocking loaded/total modal through queue/editor restoration. Retry / Ponów replaces its old
row. Valid failed/cancelled history survives missing media and a later published planned path;
actual staged/retried source hashes remain strict. Missing confirmation preserves the unchanged
batch plan. Public GUI inspection/planning is merged; CLI/API Inspect remains compatible.
Manual review implies skipping unused LLM correction. PL cleanup/status/omission text and stale
inventory/preview selection are corrected. Native audio controls have sufficient width, with no
permanent duplicate rate selector; native speed persists, including profiles.

Evidence: make check PASS (928 tests, mypy 106 source files), 12 integration tests; 144 browser
layout/workflow cases and mixed 3-job progress pass, plus 12 maintenance layouts/PL feedback and
native overflow/speed at four widths across three reloads. Wheel/sdist and 57 resources/help/CLI
smoke pass with existing model-free base dependencies; full clean ML install is not claimed.
Owner's real WSL cancellation/recovery/export successes are retained; agent GPU/Windows/provider
qualification is not claimed. See checkpoint for final restart/download, evidence and cleanup.

Current scope is A feedback/retest only. Complete EN–PL two-column approval still follows feature
completion; final EN revision/PL manuals wait for approval. Only necessary changed-stage/raw-output
instructions are updated now. Artist ZIP/demo remain unchanged, no paid calls or model pin changes.

Previous implementation checkpoint: [package A execution](docs/checkpoints/2026-11-20-package-a.md).
Baseline clean main 6322a4a. Package A is implemented and automatically verified; owner testing
and fix/retest acceptance are next. The earlier planning-only hold was revoked for A.
Use [the concrete checklist](Instructions/GUI_PACKAGE_A_TEST_CHECKLIST.md). Package B is not started.

A1 restores saved queue/drafts/applied pointers and allows completed review without original audio.
A2 cancels waiting work or waits for safe running-stage checkpoints, refuses late publication
cancellation and stages fresh retries. A3 adds v2 creation/retention metadata and protected preview-
bound temporary cleanup. A4 serves exact hash/version-bound existing export downloads after restart.
Public schemas/model pins are unchanged. No paid calls or artist ZIP/demo changes.

Verification and limits are recorded in the active checkpoint. Real pinned-model cancellation on
owner WSL/GPU, full profile exchange and native Windows remain unqualified here. Ordinary
model-free regressions, real FFmpeg tests, actual browser recovery/downloads and package/resource
checks passed. Resume with owner checklist feedback, fix/retest A, and wait for explicit acceptance
before B. Task 10 complete EN–PL approval remains after feature completion/B acceptance.

Previous planning/delivery records below are historical; the no-start instruction there no longer
applies to package A.

Current request: [accepted package sequencing, planning only](docs/checkpoints/2026-11-20-package-sequencing.md).
Baseline clean main 90768eb. Read TODO.md and the opening roadmap package table.
**Product implementation must not start yet.** The owner explicitly requested planning only.
No source/test/runtime/asset/model/installer changes or provider calls were made in this turn.

Accepted order: package A tasks 1–4 (restart recovery, cancellation, retained-workdir cleanup,
verified GUI export downloads), then a concrete owner test checklist and fix/retest gate. Package B
waits for A fixes to pass: tasks 5–8 (native Windows, OS key store, project/profile and media
conveniences), then 8a cloud ASR, then 9 full native-Windows/WSL workflow qualification and fixes.
After B acceptance/function freeze: task 10 complete editable EN–PL list and owner approval, then
consistent textual documentation. Artist remains non-blocking/no-deadline; screenshots wait for
custom GUI/icons and the sent package remains frozen.

No extra decision blocks the later start of A. Before B confirm native-Windows test execution/
environment; before B8a choose the initial cloud provider/model and explicit spending/media scope.
Do not turn those deferred decisions into prerequisites for A. Do not start paid/media cloud calls.

Roadmap classifications now reflect the owner choices: cancellation/downloads/key-store/cleanup
selected; cloud ASR inserted 8a; non-speech/channels/audio repair/extra subtitle formats are nice-to-
have; model catalog/favorites/loading, manual timing editing, alternate translation chunking,
input snapshots, whole-block audio-follow, new correction modes, speaker-count research, bilingual
HTML and Docker are outside selected scope. Word/phrase highlighting, Ollama, timing refinements,
less-technical instruction review and earlier research/preset work remain only nice-to-have.

Next action: report readiness and wait for an explicit product-start instruction. Package-A
acceptance checklist is a future implementation deliverable, not already completed.

Previous deliveries below are historical evidence, not current work authorization.

Current request: [summary footnotes and scope reconciliation](docs/checkpoints/2026-11-20-scope-and-summary-polish.md).
Baseline clean main 8b64329. Read TODO.md, WORK_POLICY.md and the opening owner-scope section
of docs/99-roadmap-v2.md. Implementation/audit/verification complete; delivered to origin/main
in 159cb1f (fix(gui): align summary notes and reconcile owner scope).

Language * and speaker-count ** notes span the full summary width below all Inspect/Dry-run
tables; queue confirmation is plural in EN/PL and error guidance matches it. Top/bottom source
section counters center against actual buttons rather than padded feedback wrappers. No request,
plan-confirmation, inference, model pin or canonical-data behavior changed.

Owner accepts the current GUI/workflow and browsers/palette. Current full restart recovery remains
unchecked by owner; full profile exchange is provisionally accepted without a complete owner test.
Actual 200% browser page zoom is optional/unchecked. Percentage primarily indicates ongoing work;
accurate ETA/calibration studies are no longer required. Existing approximate ETA stays opt-in.

Project scope is the owner's podcast and similar workflows. Broad research benchmarks, private/
public corpus expansion, universal dictionaries, model benchmark automation and hardware presets
are nice-to-have outside delivery gates. Ordinary functional/security/packaging checks still apply.
Docs record tested RTX 3090 24 GB and an unqualified >=8 GB VRAM expectation without a guarantee.
Native Windows remains planned convenience work; current WSL success does not qualify it.

Roadmap R01–R15 retain existing product proposals; E01–E13 recover additional items from contracts,
ADRs, traceability and feedback guides. No implementation order was assigned and the whole backlog
is not automatically authorized for immediate implementation. The dated milestone/history text
below does not override these decisions. Work policies, handoff, scope, quality/testing/traceability
and installation entry points now link or repeat the current status.

At feature completion, generate one complete editable EN–PL file for labels/messages/errors/
states/hints/tooltips/guide copy/dynamic templates. Owner correction and approval precede full
Polish manuals. Documentation screenshots wait for final custom GUI/icons. Artist waiting has no
deadline and does not block other work; sent ZIP/demo stays unchanged.

Verification: make check PASS (896 tests, Ruff/format/mypy 102 source files), optional browser-helper
lint PASS. Real model-free browser checks: 24 summary variants (Inspect/Dry-run × EN/PL × themes ×
1440/960/390 widths), eight top/bottom counter-alignment cases; zero page errors/external requests
or page overflow. Wheel/sdist PASS offline; all 56 resources match source and nine help routes work
from the wheel without eager ML imports. No new GPU/provider/ETA-accuracy qualification claimed.
Dedicated temporary verification root /tmp/ewp-scope-summary.d3btur was removed after recording
content-free evidence. Test servers were closed. Artist ZIP
SHA remains 1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1.

Previous deliveries below are historical evidence, not current tasks.

Current request: [batch planning, sentence-aware review and portable user profiles](docs/checkpoints/2026-11-20-batch-sentences-profiles.md).
Baseline clean main aa70f4d00c74cd23740dcace55c597d58fa707ac. Start with TODO.md.
Implementation and verification complete; delivered to origin/main in 7cfddb4
(func(gui): add portable profiles and refine batch review).

Inspect, dry-run and Add to queue share all pending selected episodes. Per-episode language/count
survive selection changes; Inspect discloses chosen values with * and localized counts. Batch staging
retains the existing exact-plan/hash/confirmation boundary and stops honestly on partial errors.
Review sections choose nearby sentence ends; red fallback guidance, explicit mixed/single playback
speed, row-aligned block actions, framed artwork credit and framed-logo favicon are implemented.
Manual same-speaker splits and parent-revision protected anchors survive presentation normalization.

ETA is opt-in/off by default and requires three comparable complete successful jobs. Track count
does not multiply the run count. Elapsed renders once per second without more API polling. Portable
profiles contain preferences, current settings, workspace manifests, palettes and exact dictionary
editions; no media/transcripts/keys/consents/in-flight jobs/timing calibration. Missing external paths
remain visibly unavailable. Independent dictionary import/export preserves bytes/hash/provenance,
including CRLF; imports do not overwrite different editions or conflicting palette names.

Verification: make check (Ruff/format/mypy, 102 typed source files, 896 tests) and ten integration
tests PASS. 144 EN/PL/theme/viewport/stage layout cases PASS, zero page errors/external requests.
Actual browser batch uses two synchronized WAV tracks plus MP4, two independent language/count
settings, unchanged-plan invalidation, one-click batch staging and source/translation export.
Profile JSON export/import/load, dictionary byte transfer, second-by-second elapsed, ETA opt-in,
explicit mixed playback speed and responsive block controls PASS. Fresh-server saved-work recovery
and model-free 581-word sentence/fallback warning checks PASS in EN/PL and both themes.
Wheel/sdist PASS; 56 packaged resources match source and nine help routes render from the wheel
without eager ML imports. Artist ZIP SHA remains unchanged. Dedicated temporary verification root
/tmp/ewp-batch-profiles.jCbW8c was removed after content-free evidence capture.
Owner-qualified WSL/GPU ASR is not rerun here; no engine/pin/canonical schema changed. Real ETA
accuracy still needs target-machine observations. Full Polish manuals follow terminology approval.

The artist package was already sent for review. The owner explicitly removed it from current scope:
do not change/rebuild its ZIP or work on its demo adapter. Previous deliveries below are history.

Current request: [mixed playback, review bounds, live progress and artist package](docs/checkpoints/2026-11-19-review-mix-progress-artist.md).
Baseline clean main 5e025b42169455b545bdd50b88c8e6021f57d60c. Implementation and verification
are complete; delivered in 831dca4ee7a294eab1618f7df8788e2464b81ada, with the final ETA refinement in 6610e299e4890771dca589ebd70819b5d6d6f95f. Start with TODO.md.
Owner confirms actual MP4 transcription succeeded; no ASR/video-ingestion blocker was reopened.

Language info closes on outside pointer/Escape. Default audio is a synchronized all-source mix,
with normalized preview gain and longest timeline. Filename hints below Speaker follow canonical
word provenance, independent of edited names. New one-speaker sections honor the 200-word cap;
old draft presentation is bounded without replacing saved bytes until explicit Save. Canonical
text/timing/lineage is untouched. Provenance metadata updates retain caret/scroll.

Optional application/pipeline events now drive actual phase/elapsed/stream feedback and approximate
percentage. First runs use coarse completed-phase weights; successful local timings calibrate an
ETA range. Unknown/overdue estimates withdraw numeric ETA; completion reaches 100% only after
publication/exports/cleanup and terminal success. Content-free bounded timing cache; observer/cache
failures cannot fail transcription. Engine calls, ML pins and canonical schemas stay unchanged.
Real GPU accuracy needs owner qualification; this VM has no GPU/E2E suite/target dataset installed.

Verification: Ruff/format/mypy (101 files) and 874 tests PASS; ten integration tests PASS.
Alternating real synthetic tracks are audible in the mixed preview at both speakers' times.
501-word single-speaker reviews split 200/200/101; legacy projection preserves saved bytes and
speaker edits. Fake-clock/worker tests cover calibration, heartbeat, overdue/failure/terminal behavior.
144 browser layout cases PASS, EN/PL × themes × six viewports/stages, zero page errors/external
requests; popup dismissal, narrow progress/ETA, source hints/seek, editing/export and recovery PASS.
Fresh-server recovery and final mixed playback/source-hint placement PASS. Wheel/sdist PASS;
53 assets/guides byte-match source, nine help routes work from wheel without ML imports; JS parses.
Owner's 45-minute H.264/AAC video decoded to 16 kHz mono, duration/bytes preserved, without ASR.

Artist build is documented in docs/31-artist-review-package.md and tools/build_artist_review.py.
An offline file:// test passes source/translation editing/save/apply/export, palettes, demo correction,
dictionaries, saved work, settings, running states, EN/PL/themes/full/half widths and asset inventory,
with zero page errors/network requests. Custom EwP / Lucide / generic/native indicators and font
credits/licenses are included. No backend/models/private media/transcripts enter the ZIP.
Final ZIP: /home/linuch/project-ewp/deliveries/ewp-gui-artist-review-2026-11-19.zip
(1135816 bytes, SHA256 1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1).
Its frontend source is 831dca4ee7a294eab1618f7df8788e2464b81ada; the later backend-only ETA refinement does not alter those frontend bytes.
See docs/checkpoints/2026-11-19-artist-review-package.md for recipient/rebuild checks.
Reported terminal warnings are explained with pinned primary sources in docs/32-runtime-log-notes.md;
no model training, weight change or broad warning suppression was introduced.

Disposable verification root /tmp/ewp-review-progress.BWiy2Q removed after content-free evidence capture.
Full Polish documentation follows terminology acceptance. Artist icon integration follows receipt.
Earlier current-request summaries below are delivery history.

Current request: [playback, video ingestion and progress analysis](docs/checkpoints/2026-11-19-playback-video-progress.md).
Baseline: clean main e08a4102ee0d9e0dbe0457b3dc96e58185e13552. Implementation and verification
are complete; delivered to origin/main in 1864900c0928d910df8bb30cafda1d4554dd4cc2. Start from TODO.md. The owner will manually review
these three tasks after delivery. English repo and guides; new GUI copy is localized EN/PL.

Stage 3 has a compact source player in the left rail, grouped-track/channel choice and per-block
seek buttons below speaker selection. Seek saves dirty drafts and checks the exact review hash;
it maps through the existing anchored word alignment, discloses fallback timing and never changes
canonical times. Navigation pauses and retains positions independently per recording in browser
memory. Private previews are hash-bound to originals and streamed with opaque URLs/byte ranges.
Missing original audio does not block editing; restore it and reload audio to recover playback.

Video picker/discovery supports MP4/MKV/MOV/WebM/AVI/M4V. Existing FFmpeg preparation extracts
one audio stream; actual video type (excluding attached cover art), source path/hash/container and
stream are preserved in canonical provenance. Missing/multiple audio errors explain recovery;
interactive multi-audio-stream selection remains deferred. No ML pin or canonical schema changed.

Percentage/ETA analysis is complete in docs/30-queue-progress-and-eta.md. Real phase events,
comparable GPU history and calibration are needed before numeric estimates; the indeterminate gear
remains. This closes the requested analysis; the implementation is a follow-up, not a hidden estimate.

Verification: Ruff/format/mypy (100 files) and 864 tests PASS; eight integration tests PASS.
144 browser layout cases PASS in EN/PL and both themes, no page errors/external requests.
Native MP4 upload/inspect/plan/durable staging, real audio decode/seek/range handling, grouped-source
and per-recording state, missing-source editing/retry, saved-work recovery after server restart,
existing source/manual-translation publication/export and packaged help checks PASS.
Wheel/sdist build PASS; 52 frontend/guide resources match source, nine wheel help routes work
without ML imports, combined JS parses. Tests use synthetic media and fake engines; they do not
qualify real GPU ASR, provider calls, Windows zoom or YouTube output. Disposable verification artifacts were removed after
content-free evidence was recorded. Release/version/tag unchanged.

Full Polish documentation follows owner terminology acceptance; artist package remains deferred.
Earlier current-request summaries below are delivery history.

Current request: [review confirmation, palette identity and motion feedback](docs/checkpoints/2026-11-19-gui-review-and-brand-feedback.md).
Implementation and VM verification are complete; delivered to origin/main in ef958dc83031900f2c9e82a7692ec8921f64812f.
Start from TODO.md. Path help and Polish labels are corrected. Example default is first and
visibly distinct from EwP Brand®; explicit configured palettes and saved custom colors survive.
Language information explains the observed EN-on-PL behavior without changing engine settings.
Source/translation Save highlights missing human verification and shows a nearby EN/PL message.
The original owner-supplied gear animates pending/status/queue feedback with reduced-motion support.

Verification: Ruff/format/mypy and 834 tests PASS; five integration tests PASS; 144 browser
layout cases PASS across six stages/viewports, EN/PL and both themes, with no page errors or
external requests. Focused checks cover missing-confirmation/recovery, legacy profiles, actual SVG
motion, reduced motion and connecting/doctor/save statuses. Wheel/source builds PASS; all 51
frontend/guide resources match source, all nine help routes work from the wheel without ML imports,
and bundled JS parses. Disposable verification material was removed after recording content-free evidence.
These model-free checks do not qualify real GPU/provider, Windows zoom or YouTube behavior.

Next priority before other deferred TODO work: a source-review audio player with real segment
seeking. Video input/audio extraction and evidence-based queue percentage/ETA are planned.
Full Polish documentation follows owner terminology approval; the artist package stays deferred.
No canonical schema, ML pin, approval requirement, release tag or version changed.
Earlier current-request summaries below are delivery history.

Current request: [Polish UI audit and queue/translation recovery](docs/checkpoints/2026-11-18-gui-localization-and-recovery.md).
Read the active TODO checklist first. Implementation and VM verification are complete;
delivered to origin/main in af1b771872a1ed511f37dec4f3f9ea031d0413cc.
Owner terminology approval and WSL retest remain pending.
Full Polish user documentation is explicitly deferred until approval. English remains the
repository's primary language. The artist package is a separate deferred TODO.

Start queue now follows live job state, recovers after asynchronous success/failure and can
start later staged work alongside terminal history. Translation Apply/export use the active
saved review's output root, so visiting optional translation cannot break an applied export.
Selected recordings retain their own language; multi-Inspect uses each setting. Dictionary
catalog loads on session initialization and output is placed before input paths.

The EN/PL UI audit covers direct/conditional copy, running/restored statuses, summaries,
plan decisions, dialogs, hover text, stable error codes and original technical diagnostics.
Source/translation action names and guides match Apply / Save and prepare for export / Save
and export. Export subtitles is a regular section heading; technical text and speaker spacing
are corrected. Exact translations take precedence over parameterized patterns; actual paths,
recording/speaker names, transcript text and dictionary terms remain protected.

Verification: 831 tests, Ruff/format/mypy PASS; five integration tests PASS; 144 browser layout
cases PASS with no page errors or external requests. Focused copy, exact label, error-original,
modal, mixed-queue start/rejection, per-recording language, Add speaker and translation-navigation
export checks PASS. Backend worker test executes later staged work and skips terminal history.
Browser Start requests are intercepted so no ASR runs. Wheel/source builds PASS: 49 assets/guides
match source, nine help routes work from wheel without ML imports, combined JS parses.
This does not qualify new real provider/GPU/Windows zoom/YouTube behavior. Earlier entries are history.

Current request: [GUI workflow polish](docs/checkpoints/2026-11-18-gui-workflow-polish.md).
Implementation and VM verification are complete. Delivered to origin/main in
`2422d721d213f1403f33e8068f744156b97801c7`; the documentation follow-up records delivery.
Start with TODO.md after a context reset. The owner's latest WSL retest remains pending;
the earlier local-only ASR/source-export success remains qualified.

The GUI now inspects all selected unqueued episodes, advances after staging, follows each
recording's workflow and offers per-row/finished-only cleanup. Dictionary management supports
view/compare/create/import, immutable edits and reversible hiding. Configured/custom palettes
have full preset swatches and separate Preview / Apply / Save actions. Direction controls show
source-derived defaults and accepted-change warnings. Optional details collapse; diagnostic
hierarchy, header, Quick steps, legends and source/translation review controls are updated.

Final gates: Ruff/format/mypy and 830 tests PASS; five integration tests PASS. All 144 browser
layout cases PASS across six stages/viewports and both locales/themes with zero page overflow,
feedback overlap, internal transcript overflow or desktop queue scroll. Focused dictionary,
palette, grouped staging, direction, sidebar, cleanup, cursor and export/recovery checks PASS.
Fresh-server workspace recovery and final prototype comparison PASS; all source review buttons
share one row at 1920px, with Undo/Redo/Clear aligned at 960px. Wheel/source builds PASS; all
48 frontend/guide files match source and nine help routes work from the wheel without ML imports.
The frontend-only artist review package is saved as deferred follow-up in TODO and the roadmap.
Provider calls, real Windows zoom and YouTube palette qualification remain separate. The
completed guided-workflow delivery below is historical context for this request.

Current work: [guided workflow and prototype comparison](docs/checkpoints/2026-11-18-guided-workflow.md).
Start with [TODO.md](TODO.md) after every context reset. Implementation and VM verification
are complete; the new UI needs the owner's WSL retest. The owner already confirmed real
local-only transcription through source subtitle export on WSL/RTX 3090. The native ASR
blocker is resolved; API-assisted stages remain unqualified by that report.

The installer automatically runs native audio setup after locked sync; new tests also prove
failure propagation. Upgrade-specific doctor/queue guidance links the bundled Ubuntu recovery
guide. All stages have numbered EN/PL Quick steps, matching controls and offline per-stage docs.
Review panels are compact and below the transcript, Preview retains position, source/target
text grows, real caret splits have adjacent feedback, and newer edits survive a pending save.
Speaker profiles update swatches while preserving custom overrides. The prototype comparison
is [recorded here](docs/29-guided-workflow-and-prototype.md): recording rail, numbered stage
strip, responsive task context and compact queues retain the real backend/approval contracts.

Final gates: Ruff/format/mypy and 810 tests PASS; five integration tests PASS; 72 browser
locale/theme/stage/viewport cases PASS with no page errors/external requests, no text-box
overflow and no desktop queue overflow. Focused pointer/keyboard/concurrent-save, live context
colors and untranslated speaker names PASS. Wheel/source builds PASS; all 47 packaged asset/
guide files match source; all nine help routes render directly from the wheel without ML imports.
No ML pins, canonical schema, public release or tag change. Actual Windows zoom, provider calls
and new-palette YouTube qualification remain separate. The earlier summaries below are history.

Current task: [GUI dependency repair and settings/layout feedback](docs/checkpoints/2026-11-18-gui-dependency-repair.md).
Implementation and VM verification are complete; the owner must run the repair and retry a
short episode on WSL. The supplied pyannote failure is caused by unavailable TorchCodec
FFmpeg 4–7 shared libraries; WSL CUDA/GPU and pinned models already passed. The repair script
installs private compatible FFmpeg 7.1.5 audio libraries, preserving the system FFmpeg and
ML pins. Settings contains Test, post-test Doctor and repair instructions. Ubuntu 24.04/26.04
are accepted, Remove from list is renamed, and queue sizing is compact.

Current verification: `make check` PASS (793 tests, Ruff/format/mypy), integration PASS
(five tests, four deselected), real TorchCodec and pyannote prepared-WAV decoding PASS,
default locked-package repair and native-repair idempotence PASS, wheel/source build PASS.
Chromium passed all 72 layout cases, zero queue overflow at 720–960px in EN/PL and both
themes, post-test maintenance controls, removal, keyboard scrolling at 390px, and existing
source/translation/recovery workflows. Real WSL/GPU transcription and actual browser zoom
remain unqualified by this VM. See the task checkpoint for the exact repair/retest sequence.

Earlier launch diagnosis from baseline `a1a2460` is complete; WSL launch is owner-confirmed.
Read [work policy](WORK_POLICY.md), [immediate todo](TODO.md), and the
[task checkpoint](docs/checkpoints/2026-11-18-gui-launch.md) before resuming.
The existing [roadmap](docs/99-roadmap-v2.md) remains the product/acceptance authority.
The owner is preparing the consolidated WSL retest of the integrated 0.20.0 preview;
the supplied launch error ran in `~/waveform/ewp-waveform`, whose environment lacks
`transcriber`. Launch from the existing `ewp-transcripts` checkout. Local CLI/server
startup passes; `make check` passes 781 tests and integration passes five tests.
The later dependency-repair checkpoint above now contains the actual WSL queue exception.
Do not reopen GUI-55 or treat the historical 0.19.0 handoff snapshot as the next task.

## Owner feedback follow-up (unreleased)

The first owner workflow attempt stopped at failed transcription. Local fixes add compact
content-sized shell rows, larger identity/title, smaller subtitle, local light/dark EwP patterns,
service status above navigation, clear episode selection and missing-plan focus, exact grouped
speaker-track staging/recovery with every source hash, cleanup protection for all group copies,
and visible queue failure details plus an explicit native dependency test. Windows dialog DPI and
visual styles are requested; the host runtime still determines legacy versus upgraded appearance.

VM verification: `make check` passes 781 tests with Ruff/format/mypy; `make test-integration`
passes 5 tests (4 deselected), including real synthetic two-track inspect/plan/stage, durable
recovery, hash-change rejection, cleanup protection and timeline/sample-rate guards. Changed JS
parses in V8; selection grouping cases run in V8. Browser layout verification could not be rerun:
Chromium/Playwright are absent and the sandbox cannot resolve PyPI to install them. No GPU/device,
pinned model snapshots or external corpus are available for a GPU/E2E run. No real transcription
success is claimed. The new native check reproduces missing FFmpeg 4–7 shared libraries under this
VM's FFmpeg 8; bundled WhisperX VAD loads on CPU despite that warning, so the owner's terminal
failure still requires its actual backend exception. No model pins, public release or tag change.

## Integrated GUI preview 0.20.0

The clean GUI-34a baseline was `3ce1caa5f73eb89fa0f2e6e831f90ededf43ea17` on main.
The integrated untagged preview includes stage navigation, active-recording/draft context,
PL/EN UI, explicit system/light/dark, local branded assets/notices, multi-file audio selection
through the existing exact-plan contract, separate cursor split/isolation, dynamic speaker colors,
production/brand YTT choice, direct manual translation and exact source/semantic workspace recovery.
Source export still precedes any need for translation; dictionaries/providers remain optional.

Use [GUI quick start](Instructions/GUI_QUICKSTART.md) and the single
[consolidated owner plan](Instructions/GUI_PREVIEW_TEST_PLAN.md). Implementation/compatibility and
content-free evidence are in [the preview record](docs/28-integrated-gui-preview.md).
No per-slice owner acceptance is required. Windows/WSL, real 200% browser zoom, real GPU/provider
execution and new-palette YouTube validation remain unverified until the owner runs that session.
GUI-55 remains closed. No public release or tag is created.

Executed VM outcomes: `make check` PASS (769 tests; Ruff/format/mypy), `make test-integration`
PASS (2 passed, 4 deselected), browser-tool Ruff/format and JavaScript syntax checks PASS.
Headless Playwright 1.65.2 / Chromium 159.0.8154.6 passed 72 stage/viewport/locale/theme cases,
actual local font loading, real model-free audio inspect/plan/staging, cursor/isolation/Undo,
additional speaker/custom color, source and manual translation approval/export, mixed states,
and stale-source presentation. Recovery from an empty browser/server queue passed exact path,
identity and saved source/target value assertions. A separate actual Linux GUI-process restart
plus a fresh browser also passed those assertions, including the prior applied translation path.
This does not qualify Windows/WSL, real zoom, GPU/provider execution or YouTube colors.

The 0.20.0 wheel and source archive build passed; all 33 packaged frontend files match source,
both owner guides are in the source archive, and resource serving directly from the wheel works
without importing torch/WhisperX/pyannote. Only the project version changes in uv.lock; ML pins
are unchanged. Runtime/build/browser evidence stays disposable under the temporary test root.

## Earlier GUI-34a increment (historical context)

The first bounded responsive slice is implemented; Windows/WSL visual acceptance and actual
browser zoom to 200% remain pending. The existing table is retained with local keyboard scrolling,
correct six-column sizing and wrapped status markers; review speaker/text controls stack at narrow
desktop widths, and action/feedback groups reflow without hiding functions. Services, schemas,
JavaScript workflow bindings, palette and exporters are unchanged. PL/EN, explicit theme preferences,
branding and new navigation remain later slices. See [verification](docs/27-gui-34a-verification.md).
GUI-55 is closed on the owner's confirmation; another dedicated acceptance test is not required.

## Earlier 0.19.0 checkpoint

Version `0.19.0` is the next internal beta on `main`; it is not tagged or published as a public
release. Development remains untagged while requirements work continues. The first public
release is reserved for the checkpoint immediately before Docker-image implementation; an
internal version number never implies publication. The repository is public and licensed
under `AGPL-3.0-only`.

Correction dictionaries now distinguish evidence-backed lexical entries from immutable,
human-documented project conventions. The latter remain source-bound LLM context, not automatic
text replacement; Ethics in the Loop correction v2 uses that narrow path for the quoted,
capitalized Polish show title while preserving all v1 accepted and rejected proposal decisions.

The GUI now shows an artifact-derived completion tracker for every queued recording. Its green
states correspond to immutable correction, revision, and export artifacts on disk, so they remain
accurate after a browser or GUI restart. A single context-aware **Next step** action moves a queue
item through the workflow; optional LLM correction and translation can be explicitly marked
skipped. A saved workspace now also retains completed/failed queue history and its non-secret
skip/error annotations, then validates and restores that history after a GUI restart. Interrupted
GPU work is never revived: only the existing source-hash-validated staged-job recovery path can
resume it. Immutable artifact-derived green states remain independently durable.

Correction, review/export, translation, and semantic review/export are always-visible queues
derived from the same completed transcription records and immutable artifacts. Correction and
translation selected-item provider actions now run sequentially, with item-specific output roots,
consent, result/error summaries, and no automatic final publication. Native file import needs an
explicit durable shared output root: after validation, the selected canonical JSON is preserved
in a hidden content-addressed folder under that root. Browser-picked audio likewise becomes
durable when staged. Review, revision, candidate, and export artifacts use the selected root.
Workspace save now recognizes all
current form fields; an OS folder dialog chooses the shared output root without uploading folder
contents. A confirmed clear-current-state action forgets inactive queue/browser state without
deleting saved artifacts. Automated GUI checks pass; remaining operator qualification is tracked
in the active GUI list in `docs/99-roadmap-v2.md`.

The 2026-09-14 WSL retest confirmed default/custom workspace directories, retained import
selection after manual output-path entry, versioned canonical import, per-item semantic edits,
and durable review/export files. It exposed `Exec format error` for Python's direct Windows
launcher/dialog subprocesses and a major persistence gap: session-picked queue sources and dirty
review edits were absent after restoration. GUI-36–38 now have local fixes: explicit WSL `/init`
interop fallback without noisy `gio`, durable selected-source promotion, and draft checkpointing
before explicit workspace save. Later WSL retests passed browser opening, folder selection,
saved-workspace restoration after a full GUI restart, and the real-provider batch qualification.
Responsive redesign remains GUI-34, deferred.

The WSL `/init` retest now passes for automatic browser launch and its host folder dialog. That
dialog is intentionally a deployment adapter, not a Windows-only GUI dependency: GUI-40 adds
Zenity, KDialog, and Yad discovery for bare-metal Linux, while headless and future Docker runs use
direct server-visible paths inside explicit mounts. A browser directory upload cannot provide the
path required by current Python/FFmpeg services and would expose the directory contents; a
browser-owned writable-handle design would be a separate output architecture. GUI-37 durable
selected-source copies and GUI-38 explicit workspace-save review checkpointing passed the WSL
retest. GUI-39 tracks guarded reference-aware cleanup and the bundled help now specifies backup
scope and exact temporary/durable retention behavior.

The two-item real-provider GUI qualification now passes end to end: bulk correction skip and
generation update both selected items without duplicate revisions; verified transcript revisions
apply; OpenRouter translation produces two saved candidates with nonempty targets; distinct
semantic reviews reopen correctly; and original plus translated subtitle exports are written.
GUI-07, GUI-20, GUI-31, and GUI-35 are therefore operator-qualified. GUI-41 now implements the
default-off intentional-empty-target control with versioned artifact, audit, and export semantics;
its WSL browser retest passed, including placeholder-free exports and omission provenance.

The resulting GUI defect pass in GUI-42–48 is operator-qualified. Successful retries clear stale
per-stage errors; completed artifacts suppress legacy error annotations; missing review sources
produce a specific re-import instruction; selected inactive queue rows can be forgotten without
deleting files; transcript Preview saves a dirty draft and Apply asks only for Preview; and
translation initially selects OpenRouter consistently with correction. Selecting LM Studio resets
the known Gemini default to the qualified Bielik model, versioned canonical results discover their
own revision/export artifacts, and completion/error states have non-color check/X glyphs.

The 2026-09-25 WSL regression passed automatic Chrome launch, terminal cleanliness, OpenRouter
defaults, selected inactive queue removal, transcript Preview autosave/reopen, stale-error cleanup,
missing managed-source diagnosis/re-import, and a successful translation retry. GUI-42–45 are now
operator-qualified. The follow-up WSL checks also passed: selecting LM Studio replaces the known
Gemini default with the qualified Bielik model; versioned canonical results use their `_vNNN`
identity when discovering accepted revisions and original exports; and completion/error circles
include centered check/X glyphs for non-color identification. GUI-46–48 are operator-qualified.

GUI-39 managed durable-source cleanup passed its WSL browser qualification. Saved work state
exposes a source inventory for the selected output root, including exact retention reasons from
the current queue, the default and selected custom workspace catalogs, and
correction/review/translation lineage.
Only hash-valid, readable, structurally safe, unreferenced copies can be selected; cleanup repeats
the audit before a confirmed permanent deletion and leaves publication artifacts untouched.
GUI-50 additionally passed the hidden latest/per-result review-session lineage check: a managed
canonical copy required by a saved review remains protected after its queue item is removed.

The first GUI-39/41 browser pass exposed three follow-ups, now qualified as GUI-49–51. Workspace
save follows the selected shared output root and omits unavailable dormant fields/history with
visible counts rather than failing the whole checkpoint. Managed cleanup now protects hidden
latest/per-result transcript-review session pointers. Translation export provenance v2 records
the intentional-empty unit count and its placeholder-free export behavior.

The follow-up confirmed flexible/new workspace directories and correct intentional-omission
provenance. GUI-52 adds qualified inline status to managed-source inventory/cleanup. GUI-53 makes
workspace auto-save default-off after the test showed that its 60-second update could silently
replace an explicit recovery snapshot and remove that workspace's source-retention reason. Both
passed their WSL UI checks.

The GUI-52/53 retest passed inline inventory status, stable explicit workspace retention, and the
documented opt-in auto-save transition to an unreferenced source. It also exposed that cleanup
audited default plus custom workspace catalogs while Refresh list showed only one. GUI-54 now
combines and labels both catalogs and keeps every workspace operation bound to its catalog; it
passed WSL confirmation through the combined list and catalog-routed deletion workflow.

GUI-55 follows the unified catalog view: stale default-catalog workspaces with unavailable paths
remain selectable for deletion while restore and auto-save stay disabled. This maintenance path
is closed based on the owner’s confirmation.

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

At the v0.9 checkpoint, the tree passed formatting, lint, type checks, and all **640 tests**. A fresh
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
coverage, privacy/security controls, and the pre-Docker implementation sequence. At that
checkpoint the GUI requirements remained planned; the existing exported HTML transcript player
was not the GUI.

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
blocks without modifying the canonical result. A sentence selected with its immediately leading
terminal punctuation retains that punctuation in the preceding block; a dirty draft is saved as
a recovery checkpoint before a whole-block merge. Project/revision-scoped speaker display-name
editing and revision-local speaker addition are externally qualified: names and added
`speaker_NNN` IDs are persisted in the review and immutable revision, inherited by a child
review, and override only exports from that revision without altering the canonical result.
Unused revision-local speakers can be removed, while a speaker assigned to text is protected
until its blocks are reassigned or merged. The review-editor recovery/comfort slice is likewise
externally qualified: structural edits checkpoint a dirty draft first, the active editor
maintains a bounded local Undo/Redo history, and Prepare/Preview plus
Save/Restore/Clear/Undo/Redo are grouped by purpose. Undo/Redo never write artifacts and still
requires a later Save plus Preview before Apply.
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
The audited v1 dictionary remains immutable, while the explicitly selected project-wide
`ethics-in-the-loop-pl-en-v2` now maps both Polish owned-domain forms to the English project
address `ethicsintheloop.eu`; it does not add episode-specific correction rules.
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
