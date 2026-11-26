# Actions cost transparency and next stages — 2026-11-26

Owner has NOT yet tested desktop0.25.0. Current task documents existing GitHub Actions usage/costs
and adds public-only jobs,7-day new-artifact retention and same-ref concurrency cancellation.
See docs/GITHUB_ACTIONS.md and docs/checkpoints/2026-11-26-actions-costs-plan.md.
No new cloud build, product rebuild, billing-setting change or remote artifact deletion in this task.
NEXT: owner desktop/interface test → fixes → AMD support visibly marked (experimental), with no
physical AMD hardware available → remaining release tasks → first public release. AMD is authorized
as the stage AFTER interface feedback, not as an immediate implementation/research campaign.
Before introducing external CI/billing changes, explain usage/costs; paid execution/allowance changes
require owner approval. Existing0.25.0 package/source/native evidence and prior passes remain intact.

Earlier boundaries follow.

# Delivered native Windows application — 2026-11-26 / 0.25.0

0.25.0 delivered from9b8da316fc0a87fceebaf824f0342dc43788f004. Native run45811242398 PASS:
46 installer WPF groups,18 Windows filesystem cases and4 real desktop cycles (one end-to-end case).
1201 local tests/19 Windows skips,17 integrations, Ruff/format306/mypy120 PASS.65 previews reviewed
in overview and4 desktop/close views full-size. Both CI archive digests/six product hashes/446 packaged
source files verified; desktop EXE matches independent local build byte for byte.68 prior hashes kept.
Native WPF/WebView2 window preserves approved UI, owns backend/worker job, has no console and focuses
on repeat launch. Close flushes work, offers wait/stop, preserves save refusal; crash/maintenance
leave no owned workers. Windows TEMP alias recovery and shutdown connection-reset races corrected.
Files: /home/linuch/project-ewp/deliveries/ewp-0.25.0-installers.
Checkpoint: docs/checkpoints/2026-11-26-native-windows-app.md and matching evidence JSON.
NEXT: focused owner desktop-window/update/close feedback, not a repeated full inference campaign.
Evergreen WebView2 Runtime required; missing-runtime UI links Microsoft before backend startup.
GPU/provider inference not requalified; prior mixed-model/installer acceptance remains. No paid calls;
cumulative spend USD0.0291461230985028369. AMD research/experimental adapter and first public release
remain after desktop review. EXE unsigned/internal; no public publication/signing performed.

Earlier boundaries follow.

# Delivered existing-installation preflight — 2026-11-26 / 0.24.4

0.24.4 delivered from d280943b0fcdda3ecb184d74c8be10fd207898bd. Native run45795432181 PASS:
46 WPF groups/18 actual Windows cases,1186 local tests/17 integrations, Ruff/format302/mypy119 PASS.
Installer detects existing registered/managed installations at step2, including another target root;
older/same/newer versions get Update/Repair/rollback-or-newer-installer guidance and actual path.
GUI rechecks before Next/host/install, shared backend checks before model/key/host/runtime preparation
and at registration. Negative tests prove no workers/new target creation and intact original files.
Fresh-install folder and host labels both show25GB. Existing HF model-cache reuse is unchanged.
All49 native previews inspected in overview,8 affected full-size views; both CI archives/six product
hashes/source payload verified. All62 prior installer hashes, models/notices/review files preserved.
Files: /home/linuch/project-ewp/deliveries/ewp-0.24.4-installers.
Checkpoint: docs/checkpoints/2026-11-26-install-preflight.md and install-preflight-evidence.json.
Owner explicitly waives further manual retests. NEXT planned work is native Windows application
interface/lifetime; no new checklist, build/model/paid campaign on resume. AMD research and first
public release/EXE in releases/ remain AFTER native app interface. EXE unsigned/internal.

Earlier boundaries follow.

# Delivered owner copy integration — 2026-11-26 / 0.24.3

0.24.3 delivered from d57480694fbc197037ebd3114756a5d794a5e88c, native run45785526544 PASS:
42 WPF groups/12 real Windows cases,1176 local tests/17 integrations, Ruff/format/mypy119 PASS.
All43 native previews inspected in overview and7 focused full-size views; six product hashes,
CI archive digests and source payload verified. Files: /home/linuch/project-ewp/deliveries/ewp-0.24.3-installers.
Follow opening TODO and docs/checkpoints/2026-11-26-installer-reviewed-copy.md / integration evidence.
Owner EN/PL values applied without Decyzja;2 explicit notice deletions, Polish companion notices,
release-folder hyperlinks, separate smaller OR spend footnote and light body motif delivered.
Original AGPL/vendor licenses, report/terminal English, model pins, app workbook and56 prior
installer hashes unchanged. Raw private returned XLSX remains private; approved values archived.
NEXT: owner manual text/layout review. No repeated full transcription/model/paid campaign or build
merely on resume. Native Windows app interface follows installer copy/layout closure. AMD research
is TODO AFTER native interface; experimental without hardware qualification. First public release
and .exe in releases/ also follow native interface; no public release/signing done here.

Earlier boundaries follow.

Current boundary 2026-11-25: full installer EN/PL review table delivered (1148 entries),
see installer-copy-table checkpoint and docs/installer-copy-review/README.md. Await returned
owner corrections before integration/help; preserve app workbook/product 0.24.2 and prior passes.
No new manual/model/paid campaign or native app shell merely on resume.

Current boundary2026-11-25:0.24.2 automatic required host checks delivered/automatically verified. Owner waives further manual retests; no new manual gate/model/paid campaign. Next planned work is full installer EN/PL and notices audit, then native app interface after installer closure. Follow opening TODO/status and automatic-host-checks checkpoint.

Current boundary2026-11-25:0.24.1 delivered; follow opening TODO/status and model-preflight-selection checkpoint. Owner confirms mixed local three-model ASR queue; preserve that acceptance without repeated inference/paid tests. Await focused early-model/spacing/selection feedback.

Current boundary2026-11-25:0.24.0 delivered from50cb47b after owner0.23.2 feedback. Optional
Whisper v3/Turbo addition is authorized and implemented (earlier deferred-only prohibition is
superseded); no public desktop weights established for Scribe/MAI. Follow opening TODO/status and
local-asr-installer checkpoint/evidence. Owner next tests actual optional model install/inference;
no paid/model campaign merely after resume. Preserve uninstall-while-running pass and old artifacts.

# Work policy and context recovery

Current boundary2026-11-24: owner0.22.2 install/desktop/transcription PASS is retained. New installer
lifecycle/startup feedback is delivered as0.23.0 (source5edfc1d/native run45372295246). Follow its
checkpoint and await focused owner review. Native Windows interface follows installer closure;
full installer copy review is still after GUI completion. No new model/paid campaign is implied.

Updated: 2026-11-23. Read `AGENTS.md` first; this file supplements its rules.

1. On resume, read `WORK_STATUS.md`, `TODO.md`, the active task checkpoint linked there,
   and `docs/99-roadmap-v2.md`. Inspect Git status before edits. Historical handoff sections
   do not override current checkpoints or reopen owner-qualified gates.
   Start each new work request by updating the concrete task list in `TODO.md`, including
   every user-reported issue; consult it before each slice and after context compression.
2. Every task gets a dated file under `docs/checkpoints/` recording its objective, baseline,
   evidence, changes, verification, limitations and exact next steps. Update it after a
   meaningful discovery, before handing off, and before a context reset when possible.
3. Keep the immediate queue in `TODO.md`; keep product sequencing and acceptance in the
   existing `docs/99-roadmap-v2.md`. Link these from `WORK_STATUS.md`; avoid competing roadmaps.
4. Distinguish reproduced failures, hypotheses, automated checks and owner qualification.
   A model-free VM pass never establishes WSL, GPU or provider success.
5. Use the supplied private GUI handoff as a reference; do not commit its prototype,
   private material, audio, transcripts, runtime output or credentials. Disposable execution
   artifacts belong in a dedicated `mktemp -d` directory under `/tmp`.
6. Finish authorized diagnosis and fixes without repeated confirmation. Preserve ML pins,
   immutable artifacts and qualified workflows. Record user-visible changes in `CHANGELOG.md`.
7. End each task with a checkpoint containing checked/unchecked work and commands needed
   to resume. Do not mark environmental or owner-only verification as completed.

8. Owner scope (2026-11-20): follow the current classification at the top of the roadmap.
   Research benchmarks, universal dictionaries, hardware presets and accurate ETA calibration
   are not completion gates. Prepare the complete editable EN–PL terminology file only after
   feature completion, then owner approval and Polish documentation. Documentation screenshots
   wait for custom GUI/icons; waiting for the artist has no deadline and blocks no other work.

9. Latest sequencing decision (2026-11-20): the roadmap package table and TODO govern order.
   A1–A4 → concrete owner checklist → fix/retest acceptance → B5–B8 → B8a cloud ASR → B9 full
   native-Windows/WSL workflow acceptance → task 10 EN–PL approval. The owner has now explicitly
   accepted package A on 2026-11-21 after the complete focused retest. The final source-review
   action layout adjustment passed ordinary verification, with no new owner retest. A is closed;
   next is B5 preparation for Windows 11 x64 (agent changes/checks/push on Linux VM, owner pulls/tests
   natively). Do not reopen the passed A acceptance gate.
   B feature implementation/cloud calls are not part of the A closure task.
   B arrangements/decisions are now confirmed: Windows 11 x64 owner tests; OpenRouter B8a shares
   one key with correction/translation, uses the four selected ASR model IDs and short supplied
   PL/EN functional samples within USD 2 total including retries. Follow the B planning checkpoint
   for exact scope and retain permission without asking again. Owner now explicitly authorizes
   B5–B9 execution to completion; earlier planning-only holds are revoked. Interrupt only for
   concrete missing information or blockers. Declined historical roadmap
   ideas must not return as gates.

10. B delivery update (2026-11-21): B5–B9 agent implementation/VM verification is complete. Use
    docs/checkpoints/2026-11-21-b9-verification.md and Instructions/GUI_PACKAGE_B_TEST_CHECKLIST.md
    for owner native Windows 11 x64/full WSL acceptance. Short live PL cloud checks passed at
    USD 0.0095832333762821113 total; owner waives live EN because no sample is present. Preserve
    that evidence after disposable cleanup; do not restart paid tests merely after context reset.
    A remains closed. Full EN–PL approval follows B acceptance, then manuals; artist ZIP frozen.

11. Owner B8a follow-up (2026-11-21): automatically split long cloud recordings into bounded
    requests and merge one timeline; the former single-request mixed-audio restriction is
    superseded. See docs/checkpoints/2026-11-21-cloud-chunking.md for tests and safe speaker
    continuity handling. Cumulative live-ASR spend including this follow-up is
    USD 0.0153610111540591670 within the original USD 2 budget. Retain that total after cleanup.

12. Current Windows feedback (2026-11-21): owner confirms installation/model setup/GUI/doctor pass.
    A reproduced Windows CRT directory-descriptor publication defect and requested picker, per-file
    settings, conditional stream/identity controls, single-plan table and OpenRouter check/estimate
    changes are delivered in the Windows queue/GUI checkpoint. Continue from that checkpoint and
    owner B retest; do not repeat model setup or paid pilots. Uninstall/model-removal script and
    standalone EXE installer/desktop shortcut/Add-Remove Programs/GUI uninstall are later TODO only.

13. Latest B native feedback: owner confirms local/cloud ASR and source subtitle export work.
    Continue from docs/checkpoints/2026-11-21-b-workflow-state-polish.md and its focused B checklist
    for remaining native acceptance. Status, consent/key-dialog, layout/copy and expected browser
    audio-disconnect fixes are verified with synthetic media/deterministic translation; no new paid
    qualification is needed. A stays closed, artist ZIP stays frozen, final terminology/manual gate
    is unchanged. Do not interpret missing session key after restart as a model-install failure.

14. Latest restored-consent feedback: use the active update-only checklist, not installation/model
    preparation after routine updates. Fresh-install/reinstall qualification waits for uninstall
    scripts and the later graphical installer. Keep owner-confirmed SRT/VTT progress, translation
    status/generation lock and correction/translation blocking passes. OpenRouter Whisper Large
    actually ran in the reported unchecked-consent incident; test exact restored cloud identity
    and server-side fresh consent, without another paid run. Do not infer a proven root cause
    merely from hardening the boundary. Follow the current restore-consent checkpoint.

15. 2026-11-22 feedback: use the current recovery/cloud-timing checkpoint and update-only
    checklist. Owner confirms favicon/API check/fresh consent/mixed queue pass. Targeted supplied
    s0e01 diagnosis reproduced Together dropping word times after DeepInfra returned them; Whisper
    routing/price subset is now DeepInfra/Groq. The corrected tail and Scribe tail return real words.
    No further paid tests after this diagnosis: cumulative authorized spend is now
    USD 0.0291461230985028369, including this task's USD 0.0137851119444436699. Preserve exact totals
    after disposable cleanup. Do not claim the original native Scribe failure was reproduced.
    New workspace v3 preserves pending media; versions 1/2 remain readable. Retain file-backed
    failed/cancelled history, no auto retry, protected source copies, explicit Save as new identity.
    Task 10 must include stable field/message ID and editable EN/PL (owner may edit EN too): initial
    local VM review file, then apply owner corrections and commit the approved catalog as the
    reference for later revisions/translations. Generate only after functional freeze, then manuals.

16. Latest saved-location/key feedback (2026-11-22): owner confirms output-root save/load, cloud ASR
    once a key is active, export and progress. Continue from the recent-locations/named-save/key
    preflight checkpoint; retain old automatic failed/cancelled recovery evidence without claiming
    a new native retest. Remember local directories independently of workspace identity/credentials;
    readable filenames preserve UUID/legacy compatibility. Validate active cloud credentials before
    worker/media startup while keeping fresh consent and explicit OS-key loading. No further paid
    pilot/reinstall, no artist changes; task10/manual gate remains after functional acceptance.

17. Latest owner acceptance (2026-11-22): focused save/load/directory/key/mixed-queue checks pass.
    Finish unique-new-save names and short right-side key feedback with automated verification;
    no more manual retest. Task10 is now explicitly authorized. Produce the complete local editable
    ID/EN/PL workbook, await owner edits, apply both languages and commit the approved reference.
    After interface approval: review/update EN docs, prepare full PL docs, then create a NEW artist
    review package reflecting approved GUI/language. This supersedes the earlier permanent package
    freeze at that future stage only; keep the already sent original archive unchanged now.
    Do not infer additional native/WSL/GPU qualification or repeat paid pilots during language work.

18. Returned terminology workbook (2026-11-22): owner now authorizes integrating the corrected
    EN/PL file and delivering the interface for approval. Use the terminology-application checkpoint.
    Commit the corrected reference; keep initial/returned private workbooks unchanged. Record small
    integration adjustments explicitly. Full EN review, complete PL manuals and NEW artist package
    remain sequential after interface approval, not part of the integration gate. No paid tests.

19. Windows startup feedback (2026-11-22): exact-href lookup broke after localized help URLs,
    before About/polling initialization. A synthetic Windows-session browser reproduction confirms
    backend completion while UI stays running. Follow the startup-refresh checkpoint/retest; do
    not treat this as proven ASR/GPU failure or rerun paid tests. Stable IDs and early idempotent
    polling fix it; preserve the shared-output guard. Owner accepts UI generally, with new subtitle,
    info placement and modal Escape changes. Docs/artist work still waits for this approval gate.

20. Owner closes the Windows/GUI/interface stage on2026-11-22 after passing retest1–5. EN docs
    review/update and complete PL user documentation are now authorized and active; do not wait
    for another wording approval or repeat native tests. Keep exact approved UI terms and source
    contracts, user-oriented procedures, honest platform limits and deferred uninstall/installer
    scope. Package usable EN/PL offline help. New artist review package follows documentation under
    existing authorization; original ZIP remains untouched. Screenshots still wait for custom icons.

21. Documentation stage delivered 2026-11-22: EN review/update, complete PL user manuals and bilingual
    offline help, followed by the authorized NEW artist reference. Original archive preserved.
    Follow the documentation checkpoint/evidence and await the next owner-selected work. Do not
    reopen accepted UI/GPU/paid gates or redo the artist package merely after a context reset.

22. Owner distribution planning request 2026-11-23: record SemVer/version-handoff correction,
    explicit update procedure, Windows/Ubuntu short terminal installers and removal lifecycle,
    then a styled Windows GUI wizard with host checks, selected model downloads, masked transient
    HF token and optional deliberate OR OS-keyring storage. Desktop shortcut/Add-Remove Programs
    and graphical uninstall remain included. Share operations/pins between adapters; preserve user
    data/models/keys by default and require explicit targeted removal. Current turn is planning,
    not implementation/release or permission for paid tests. Proposed next baseline 0.21.0; do not
    claim it is already shipped. Details in docs/DISTRIBUTION_PLAN.md and its checkpoint.

23. Owner authorizes full distribution implementation2026-11-23: work through the agreed plan
    until done or concrete missing information/action is required. Earlier planning-only holds
    are revoked. Prepare reviewable artifacts and checks before any final publication/signing
    decision. No new paid/model qualification campaign or artist-archive rebuild is implied.

24. Distribution0.22.0 implementation/VM checks2026-11-23: preserve previous application/manual
    acceptance, artist archives and cloud-spend total. Shared installer/terminal/wizard behavior
    and content-free evidence are in the execution checkpoint. Owner Windows11 native installer
    acceptance is still required; CI startup/compilation do not qualify local GPU/model install.
    Online bootstrap URLs require actual matching release publication; never claim them live early.

25. Owner installer feedback2026-11-23 rejects0.22.0 preview before installation. Complete the
    detailed0.22.1 usability checklist and inspect native rendered previews before a new handoff.
    Preserve old artifacts and app acceptance; no full workflow/paid requalification. HF/OR masked
    modal checks never imply audio consent, credentials stay transient until deliberate OS save.

26. Owner0.22.1 feedback2026-11-23: implement location/permission/state/presentation fixes as0.22.2.
    Full installer EN/PL copy review is explicitly deferred until GUI is finished; keep that TODO.
    Do not reopen accepted app workflow, paid provider tests or artist packages. See active checkpoint.

27. Owner requests a LOCAL new-session handoff2026-11-24 while reviewing installer0.22.2.
    Follow docs/checkpoints/2026-11-24-session-handoff.md; wait for new-session feedback rather
    than starting product changes, new builds, release, copy review or artist work now. Reconcile
    stale completed TODO boxes without claiming installer acceptance. No commit/push requested
    for this handoff; preserve its local docs edits at resume.
