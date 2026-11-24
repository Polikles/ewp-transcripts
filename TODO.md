# Immediate work queue

## Delivered 0.23.1 owner follow-up — 2026-11-24

Owner confirms update succeeded and About shows0.23.0. Preserve that pass; registration had
already been removed, so selecting the remaining managed root manually was expected.
See `docs/checkpoints/2026-11-24-workspace-uninstall-followup.md`.

- [x] Read three new home-directory setup reports; retain private reports outside Git.
- [x] Save browser-selected media before any planning, both explicit save and automatic recovery.
- [x] Restore selections/settings only; never automatically run planning on load/restart.
- [x] Automatic saves must work from startup with empty display-name input; localized gray
      task/datecode default (zadanie/task), unique usable fallback name and reliable recovery.
- [x] Show moving gear beside batch Planning x/y; keep existing progress/consent safeguards.
- [x] Remove the two reported project-comment paragraphs from readable notices; preserve rights
      and legitimate attribution. Later: review all notices/user-facing technical commentary.
- [x] HF help links inline in numbered steps; only detailed-procedure and credits links below.
- [x] Keep technical-log expansion across update/repair progress rerenders; report save defaults
      to current user's Desktop and handles write errors without crashing.
- [x] Eliminate intermittent nested batch-job prompt from desktop launch; inspect launcher chain.
- [x] Add-model help/version diagnostics distinguish older/newer installer and block mismatch.
- [x] Installed model checkboxes disabled by default; explicit reinstall-selected switch enables
      selective repeat downloads and gated-token UI. Run diagnostics automatically after models/repair.
- [x] Rollback displays verified target version(s), excludes same-version repairs, allows choice
      when multiple older releases exist, and blocks when older files are unavailable.
- [x] Remove program/dependencies and desktop/registry entries BEFORE reporting uninstall complete;
      only the running uninstaller/helper may delete itself after window closure. Preserve work-state.
- [x] Focused synthetic browser restart, filesystem/integration and native Windows lifecycle/UI
      checks; distinct test version and immutable verified delivery; maintain affected EN/PL docs.
- [ ] Owner focused0.23.1 workspace/startup/model/rollback/uninstall retest; automated checks
      pass, no repeated full transcription or paid/model campaign needed.
- [ ] Deferred until copy review: shorten disk-space prose. Native Windows app interface remains
      after installer closure; no new paid/model campaign or artist-archive changes.

Updated: 2026-11-24. Read WORK_POLICY.md, WORK_STATUS.md and the active checkpoint after resume.
Authoritative sequencing: [roadmap](docs/99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20).

## Current handoff / owner review — 2026-11-24

### Active owner feedback — installer lifecycle and startup, 2026-11-24

Delivered0.23.0 from5edfc1d; native run45372295246 PASS. Local1135/17 integration cases,
5 real Windows cases,25 WPF groups and27 inspected previews. New next step: owner focused
GUI/update/removal/startup review. Full installer EN/PL review follows GUI completion.

Owner installed 0.22.2 and successfully transcribed an episode using the desktop shortcut.
The new feedback supersedes the handoff wait. Preserve that application pass and previous deliveries.
See `docs/checkpoints/2026-11-24-installer-lifecycle-startup.md`.

- [x] Locate/read supplied setup report without persisting private contents in Git.
- [x] Reduce Location textbox height; HF info short tooltip + visible hover/focus; larger left-aligned installation gear.
- [x] Show current installation phase and useful progress, download bytes/rate/ETA where measurable; timestamp report contents and collision-resistant filename.
- [x] EwP desktop and installed-program icons; dynamic initial program/model installed size.
- [x] Choose another installation opens folder dialog immediately; consistent full local-install disk budget in checks, distinct incremental model size.
- [x] Update preserves matching models without HF/OR prompts/downloads. Repair defaults to app-only; automatic host diagnostics, explicit model SHA/version/location verification and selective redownload; HF only for selected gated models.
- [x] Add-models automatically checks host, omits OR, asks HF only for missing/selected gated downloads.
- [x] Installed-program entry limits operations to repair/rollback/uninstall. Root uninstall.exe offers repair/uninstall.
- [x] Diagnose incomplete Windows removal (15.5 GB left); reliable owned-file deletion and direct user-facing Remove-EwP.ps1 without mandatory internal Plan; retain unrelated work/shared caches by default.
- [x] Clean idle Ctrl+C/launcher shutdown; preserve running-job safeguards.
- [x] After installer fixes: automatic startup recovery/autosave from launch, before output selection; associate saved state with output root, respect protected install directories.
- [x] Focused regression/integration/native Windows previews/lifecycle checks; new versioned delivery and affected EN/PL docs. See checkpoint/evidence; actual owner0.23.0 review remains pending.
- [ ] Later, after installer closure: native Windows application interface with controlled lifetime and unsaved/active-work handling. Do not implement the native app shell in this installer pass.

Historical handoff (superseded by active feedback above):
Read [complete session handoff](docs/checkpoints/2026-11-24-session-handoff.md). Owner was reviewing
installer0.22.2 and will send feedback in a NEW session. No product changes/builds requested now.

- [ ] Receive and address the next owner installer review; prepare a new version only for a new changed build.
- [ ] After installer GUI completion, consolidate full installer EN/PL copy for owner correction and integrate it.
- [ ] Actual owner Win11 managed-install/UAC/local-model and focused lifecycle acceptance after GUI approval; preserve prior application workflow acceptance.
- [ ] Maintain affected EN/PL installation/update/removal docs and packaged help after accepted installer changes.
- [ ] After native acceptance: deliberate release/tag/assets/online bootstrap activation; signing decision if a certificate becomes available. Nothing public has been activated.
- [ ] Parallel/non-blocking: integrate artist feedback/icons when supplied; documentation screenshots after final artwork. Preserve sent archives.

Repeated historical boxes below are completion records, not separate open tasks. Full profile
exchange is provisional; browser zoom200% and broad research remain optional, not new gates.

## Active installer location/state/presentation fixes — 2026-11-23

Owner feedback on0.22.1. Deliver0.22.2; preserve earlier packages and artist archives. Full
installer EN/PL copy review is deferred until GUI completion, per owner; only required labels,
functional warnings/errors and changed-step docs are adjusted now.

- [x] Align radio dots/text on one center line using explicit control layout; modernize consistent cards, form fields, navigation and focus states. Keep current centered logo/icon/subtitle.
- [x] Fix shallow Windows install paths such as D:\Transcripts-test-01 without removing volume/home/system-directory/ownership protections. Support dedicated folders under Program Files and other writable/admin-authorized locations; host check stays unprivileged, protected mutations use Windows elevation without plaintext credential files or changing the user account.
- [x] Step2: Location and checks / Lokalizacja i test. Remove duplicate Check computer caption. Show VC download link only after a missing/inconclusive runtime test.
- [x] Detect existing managed installs for ALL maintenance actions; use the discovered location automatically, ask only if not found (allow an explicit alternate location). Do not treat source checkouts/unrelated folders as managed installs.
- [x] Reset action-specific folder defaults, host results/errors/logs, keys/terms and removal state on changing operation. Invalidate delayed work; prevent old Install state leaking into Update/Repair/Models/Rollback/Uninstall.
- [x] Read Windows DisplayVersion for names such as Windows11 26H2; show an actual warning icon and short older/unknown-version compatibility note, including Win11 24H2 and Win10.
- [x] Replace literal (i) button with a proper accessible information icon opening HF help.
- [x] Reflow installer license/artwork text into paragraphs and meaningful line breaks, preserving original attribution/licensing and asset files.
- [x] Add meaningful Python/native tests for drive-root sibling paths, protected permission flow/lock, detection/reset, version/VC outcomes, control alignment and info icon; inspect native screenshots. Run normal gates, clean matching artifacts, docs/checkpoints, commit/push.
- [ ] After GUI approval: consolidate full installer EN/PL descriptions/communications for owner review. This is intentionally deferred, not part of current wording polish.

Agent delivery complete:0.22.2 sourced51b106; native run45238109373 PASS,46 installer tests,
1127 Python tests,17 integrations and2 actual native filesystem tests PASS.19 native PNGs
visually reviewed; all six local installer artifacts match CI. Files: ../deliveries/ewp-0.22.2-installers.
Actual owner Win11/UAC/local-model installation remains pending after GUI review. No paid calls.

## Active installer usability correction — 2026-11-23

Owner rejected the0.22.0 graphical preview before installing. Preserve that immutable package;
no native installation PASS is claimed. New build0.22.1. Follow the dedicated checkpoint.

- [x] Center the existing framed EwP mark in EXE/Explorer/taskbar/window/header; embed a real multi-size ICO. Restore EN/PL subtitle below EwP Transcripts.
- [x] Replace the long form with operation-specific pages and Back/Next/Cancel. First screen: language and radio operations. Include adding pinned models to an existing install; no irrelevant bundle picker during installation.
- [x] Second install page: Program installation folder; automatically validate free space on that volume after selection, minimum25GB (20GB +5GB margin), and block Next when insufficient. Select existing location for maintenance, with relevant operation explanations.
- [x] Host checks on the relevant page: exact short EN/PL description and Check this computer; structured CPU model/OS/free+required GB/GPU+driver/VC++ rows, OK states; redraw cached results immediately on language change. Replace direct VC EXE download with a Microsoft documentation download link.
- [x] Local models/keys page: exact owner labels, fixed checked/disabled model list shown only when selected, explicit model disk need/cache location. No redundant cloud-engine comment or download checkbox.
- [x] HF masked modal: paste auto-check plus Check token and OK; status/code; validated token remains transient, main button disables and shows Token valid; enable separate pyannote terms acknowledgment only after access succeeds. (i) popup has concise account/terms/read-token steps and full repo instructions link.
- [x] OR masked modal with auto/manual key check, OK and valid status; optional OS-store save only during install. No credentials displayed/persisted in plaintext or upload consent implied.
- [x] Footer: licenses/artwork link bottom-left on every page; report link below technical log; navigation/Close bottom-right. Real operation progress/outcome screens.
- [x] New focused native UI/gating/localization/modal/icon tests and visual previews; normal gates, canonical clean artifacts, exact CI hash comparison, EN/PL copy/docs/checklist/checkpoints; commit/push0.22.1. No paid API/model campaign or artist archive changes.

Agent delivery complete:0.22.1 sourcea2b7a59; native run45202869710 PASS, all six local hashes match CI.14 native PNGs visually reviewed and supplied in ../deliveries/ewp-0.22.1-installers. Next is owner GUI review before actual installation; do not reopen old app workflow tests.

## Previous package: versioning, updates and distribution — 2026-11-23

Owner now authorizes implementing this full package (2026-11-23). Follow the execution checkpoint; planning-only holds are revoked.
Detailed scope and acceptance: [distribution plan](docs/DISTRIBUTION_PLAN.md). Current program
reports 0.22.0 for the managed-installer acceptance build. Baseline0.21.0 is committed; prior application/docs/artist acceptance remains retained.

1. [x] Audit Unreleased changes since 0.20.0; prepare proposed 0.21.0 baseline and a consistent SemVer/build handoff procedure. Every delivered test/install build must have a distinct version; synchronize CLI/GUI/package/lock/installer and current docs, preserving historical evidence.
2. [x] Define shared managed install/update operations and installation ownership inventory. Prepare dedicated EN/PL update instructions: safe stop/save/backup, fixed target version, compatible migrations, verified replacement/recovery, readiness/version checks; keep models, user data and OS keys by default.
3. [x] Implement Windows AND Ubuntu scripted uninstall with preview, app-owned runtime cleanup and explicit optional model/credential removal. Preserve recordings/publications and avoid wholesale shared-cache/global-tool deletion.
4. [x] Deliver Windows PowerShell and Ubuntu 24.04/26.04 terminal bootstraps: one/few copyable README lines, no manual repo clone; install pinned app/deps and deliberately selected models, shared install/update/repair/uninstall paths and integrity-checked versioned payloads.
5. [x] Agent verification: real Ubuntu VM install/update/rollback/reinstall/uninstall; synthetic failure/repair/model-removal guards; supply focused owner Windows 11 x64 acceptance checklist. Record actual WSL/native-Ubuntu qualification separately; no repeated old full-workflow or paid-ASR campaign by default.
6. [x] Build the Windows graphical wizard (EXE/MSI/form chosen after feasibility): clickable host tests, installation location, app/native deps/model selection/downloads, masked transient HF token plus gated-terms instructions, optional OR key deliberately stored in system keyring, progress/results and launch.
7. [x] Match installer styling to the app where feasible, EN/PL copy/accessibility, desktop shortcut, Add/Remove Programs integration and matching GUI uninstall using the same operations. Installer key setup never grants cloud upload consent.
8. [x] Final short README install/update/uninstall/download instructions and matching complete EN/PL docs; versioned artifacts/release notes/digests. Publication is a deliberate delivery step, not performed by this plan update.

Remaining acceptance: owner Windows11x64 focused installer test; no new paid-ASR or old full-workflow repetition. Native Windows CI startup PASS(run45157522471); exact local artifact hashes match CI. Public release/bootstrap activation and optional code signing follow native acceptance.

Artist feedback/icons and later documentation screenshots remain parallel and non-blocking.
Existing checkout-based setup scripts remain available alongside the new managed no-checkout packages.

## Delivered EN/PL documentation and updated artist reference — 2026-11-22

Baseline clean `main` at `fea5e7f`. Owner explicitly passed Windows retest1–5, closes GUI/interface gate
and requests documentation. Preserve all native startup/queue/cancel/Escape/wording passes; no
further mandatory GUI retest, paid ASR or installation qualification for this documentation task.

- [x] Record owner acceptance in policy/roadmap/checkpoints and approved language reference.
- [x] Audit existing EN user-facing docs against current code, CLI help, install scripts and approved UI names; consolidate stale/contradictory workflow advice.
- [x] Update EN quickstart/install/step guides plus complete user-manual navigation, outputs, privacy, profiles, dictionaries, recovery, maintenance and troubleshooting.
- [x] Prepare full matching PL user docs: Windows 11 x64 and WSL setup/updates, local/cloud transcription, optional correction/translation, review/export, settings, dictionaries, saved work/profiles/cleanup and common errors.
- [x] Package EN/PL offline help with language-aware navigation/full-article links; preserve current approved UI labels and route restrictions.
- [x] Validate guide numbering/packaged mirrors/local links/commands/HTML/language switching and ordinary appropriate checks. Screenshots wait for custom icons.
- [x] Record evidence/checkpoints, remove disposable test outputs, commit/push and deliver EN/PL entry points.
- [x] Then refresh a NEW artist review package with approved GUI/language/docs, preserving original sent ZIP (already authorized sequence).

Delivered: [EN manual](docs/gui/README.md), [PL manual](docs/gui/pl/README.md), bilingual offline
help and `deliveries/ewp-gui-artist-review-2026-11-22.zip` outside Git. Source commitcca698b; final
archive/manifest/source stamp and offline browser checks pass. Original sent ZIP preserved. Follow
[checkpoint/evidence](docs/checkpoints/2026-11-22-user-documentation.md). Await documentation or
artist feedback. The later managed uninstall/graphical installer is implemented; owner installer acceptance remains open above.

## Delivered Windows startup / queue refresh correction — 2026-11-22

Baseline clean mainb0c2ddf. Owner reports startup null href error, About Loading placeholders,
no live phases/progress/completion despite GPU activity, stale cancellation and initial output-root
mismatch, key dialog Escape, language-info position and new EN/PL subtitle. No docs/artist stage yet.

- [x] Reproduce Windows-specific bootstrap after localized help links; fix null href and About metadata, ensure queue refresh survives optional startup failures.
- [x] Verify live queue status/phases/progress/result completion and cancellation against changing backend state; diagnose mismatch without weakening shared-output guard.
- [x] Fix Escape handling/focus from every key-dialog entry point, without saving/unloading credentials accidentally.
- [x] Place per-recording language (i) beside the label, before the select; preserve dismissal and per-file settings.
- [x] Subtitle EN "Local-first transcript workflow", PL "Lokalne narzędzie do transkrypcji"; update maintained language reference.
- [x] Add focused Windows-session browser regression plus ordinary appropriate checks; update plans/checkpoint/evidence, clean temp outputs, commit/push main.
- [x] Owner passes targeted Windows retest1–5 and explicitly closes this stage on2026-11-22. Interface accepted; EN docs → complete PL docs → NEW artist package now authorized.

Reproduced before fix: Windows null-href/About Loading, backend completed while UI remained
running. Fixed/verified with real queue and synthetic phases:1056 tests,17 integrations,216 full
layouts,8 modal locale/entry cases and3 caption widths. See Instructions/GUI_WINDOWS_REFRESH_RETEST.md.
No paid/model/reinstall changes. Original output mismatch not reproduced; guard eligibility7 cases pass.

## Delivered task10 corrections / interface approved — 2026-11-22

Baseline clean maince9ddfc. Owner returned the same-named workbook in private benchmark.
Integrate the edits and deliver an interface update for owner approval. Later docs/package stages
remain ordered after that approval; do not start them as part of this integration.

- [x] Validate returned workbook against delivered originals, IDs/placeholders/formulas and source snapshot; inspect all EN/PL edits and notes.
- [x] Apply owner text changes in both languages, including dynamic templates, tooltips/errors and quick guides; preserve technical values/workflow behavior.
- [x] Commit corrected reference table/workbook with stable IDs and change provenance; keep original/returned private files untouched.
- [x] Run copy coverage, focused EN/PL browser/workflow tests and ordinary checks; no paid API/GPU/reinstall.
- [x] Update changelog/policy/roadmap/checkpoint/evidence; clean disposable root, commit/push and provide approval instructions.
- [x] Owner approves interface after Windows retest1–5 on2026-11-22; documentation stages now active.

Implemented and verified:106 owner rows (18 EN /105 PL), plus one synchronized quick-guide
title.1050 tests,17 integrations,216 full browser layouts and36 focused copy cases pass. Use
Instructions/GUI_TERMINOLOGY_APPROVAL.md next; no full manual rewrite or artist refresh before approval.

## Delivered final B polish / active owner terminology review and task 10 EN–PL review — 2026-11-22

Baseline clean main8475723. Owner reports all focused checks pass; duplicate new workspace names
are the remaining issue. No further manual retest requested after this small fix. Location recall
and mixed-queue missing-key blocking explicitly accepted. Transition to terminology review is authorized.

- [x] Reject Save as new with an existing name, highlight name and show "Taki zapis już istnieje, spróbuj innej nazwy"; preserve updates/legacy saves.
- [x] Short two-line key success feedback to the right of Check API key; preserve responsive dialog.
- [x] Automated targeted/browser/ordinary/integration checks; no paid ASR, reinstall or owner retest.
- [x] Generate complete local editable stable-ID / EN / PL review workbook, including messages, states, errors, hints/tooltips, quick guides and dynamic templates; document safe editing/round-trip mapping.
- [x] Update plans/checkpoint/evidence and deliver product changes/tooling to main; initial review file stays local for owner editing.
- [x] After owner corrections: apply EN and PL edits, commit approved reference table, obtain interface approval.
- [x] Then review/update English documentation, then prepare full Polish user documentation.
- [x] Finally update a NEW artist review package with approved GUI/language changes. Latest owner instruction supersedes the earlier freeze at that later stage; keep already sent ZIP unchanged now.

Local review: [instructions](Instructions/UI_LANGUAGE_REVIEW.md). Workbook2218 rows; no owner
manual retest required. Historical wait is resolved: corrections, interface approval, manuals and the new artist package were delivered2026-11-22. Preserve the original workbooks.

## Delivered B recent locations, save filenames and cloud preflight — 2026-11-22

Baseline clean main 5d60f7f. [Checkpoint](docs/checkpoints/2026-11-22-b-locations-key-preflight.md).
Owner confirms output-folder save/load, cloud ASR after key activation, full subtitle workflow and
queue progress pass. Old retained-failure checklist item not repeated (files no longer present);
retain automatic recovery evidence, do not claim another native pass or repeat paid ASR/model setup.

- [x] Remember last used output/workspace catalog locations across server/browser restart; auto list saved work without manual refresh/path rediscovery.
- [x] Human-readable workspace filenames beginning with saved name; retain stable UUID identity, old UUID-only saves, copies/import/delete and safe Windows filenames.
- [x] Key modal: Close bottom-right; short session-only/save/use labels; Save/Use share one row; Remove/Clear session secondary on one row. Preserve session activation and empty-input disabling.
- [x] Reject cloud queue Start immediately if shared key absent, before staging worker/media/outputs; preserve fresh consent, local-only queue and explicit OS-key loading. No audio/readiness call on consent alone.
- [x] Explain supplied terminal stack: one missing-key exception with frame list, not separate exceptions per frame; preserve meaningful diagnostics.
- [x] Changed-step docs/mirrors, checklist/changelog/roadmap/policy/checkpoint/evidence; focused regressions/browser/restart + ordinary/integration gates, clean disposable outputs, commit/push main.

Implemented/verified:1046 tests,17 integrations, mypy115, full Chromium216 layouts,
key-dialog12 cases and actual directory/preflight/editor/export restart checks pass. No paid calls.
Dedicated test root removed; delivery main, next focused owner update check. A remains closed.

## Delivered B saved-work, pending-media and cloud timing feedback — 2026-11-22

Baseline main 7a1c2da. [Checkpoint](docs/checkpoints/2026-11-22-b-recovery-cloud-timing.md).
Owner confirms favicon, API check and restored cloud consent blocking now work; mixed local/cloud
queue starts correctly. Preserve those passes. No model reinstallation, artist ZIP changes or
full terminology/manual generation during these remaining functional fixes.

- [x] Extend artwork background across full viewport while keeping content width bounded.
- [x] Disable Set session key with empty input, including after Use saved key; input enables it.
- [x] Inspect supplied ZIPs privately; reproduce/fix restoration of failed/cancelled tasks and progress/failure reporting. Retained source/result state remains intact and no ASR auto-starts.
- [x] Restore loaded workspace name and clear stale validation highlight; avoid silently renaming selected saves, retain explicit Save as new behavior.
- [x] Persist/recover pending media/planning selections and valid source paths before staging; invalidate stale plans safely, deduplicate repeated selections by identity without grouping collisions.
- [x] Diagnose OpenRouter missing word timing for Whisper/Scribe from archives/protocol; meaningful provider/parser regression, no invented timing and no deleting failure files as a workaround.
- [x] Preserve server-session key independently from browser/workspace clearing; document process/session distinction.
- [x] Record task-10 format: stable field/message ID + editable EN/PL, owner can correct both; initial review file local VM, approved/applied version committed as translation reference. Generate after function freeze.
- [x] Update changed-step docs/checklist, changelog, roadmap, checkpoints/evidence; meaningful ordinary/integration/browser/restart checks; clean disposable root and commit/push main.

Owner follow-up: use the current update-only checklist. Whisper missing timings reproduced/fixed;
Scribe supplied sample/tail pass, original native Scribe incident remains to observe with new diagnostics.
Full B acceptance stays pending; no paid agent requalification or artist-package changes.

## Delivered B restore-consent, workspace and wide-screen feedback

Baseline clean main dee74cd. Owner confirms SRT/VTT-only progress, generated-translation status
and duplicate-generation lock, and correction/translation consent blocking work. Installation is
already qualified for updates; fresh install/uninstall tests move to the later uninstall/installer
milestones. [Checkpoint](docs/checkpoints/2026-11-21-b-restore-consent-layout.md).

- [x] Reproduce/fix restored cloud-ASR queue starting without fresh checkbox consent; enforce frontend and backend after load/retry, preserve provider/model and clear confirmations. No paid requests for tests.
- [x] Center logo inside framed favicon; inspect existing SVG geometry, preserve artist ZIP.
- [x] Bound wide-screen GUI/editor width with centered side margins above comfortable 3/4-screen layout; verify half/full 4K logical widths and EN/PL.
- [x] Put key-check result immediately below Check API key button, separate from other credential messages.
- [x] Fix Transcription engine disclosure accidentally enclosing step 2 heading; planning controls remain visible when collapsed.
- [x] Replace cloud hints with owner's two short EN/PL paragraphs (current prices/duration, no charge for estimates; Whisper one speaker per track, mixed audio better with Scribe/MAI).
- [x] Missing saved-work name highlights/focuses name field. Fix field labels/order and exact optional catalog hint above input; blank catalog resolves to output-root saved work (existing global saves still reachable).
- [x] Refresh saved workspace list when entering Saved work & cleanup; arrange Refresh below Save, secondary Remove/Clear below/right aligned with Open saved file action.
- [x] Separate update-only focused checklist from deferred fresh-install/uninstall/GUI-installer qualification; retain passed owner evidence.
- [x] Meaningful regression/browser/recovery/ordinary gate and integration as appropriate; changed-step docs/ENPL copy/changelog/checkpoints/evidence; clean disposable root, commit/push main.

Next: owner follows `Instructions/GUI_UPDATE_TEST_CHECKLIST.md`; keep prior passes. Full B owner
acceptance is still separate. Original native bypass cause unproven; fresh grant boundary verified.

## Active B Windows workflow polish and state feedback

Baseline main 3c413ce. Owner confirms native Windows local ASR, source subtitle export and cloud
ASR work; shared-key OS save/load actions also work. Full B acceptance is still pending.
[Checkpoint](docs/checkpoints/2026-11-21-b-workflow-state-polish.md).

- [x] Rename rail action Add files / Dodaj pliki (media and completed JSON).
- [x] Prevent plan header/word squeezing; Polish process -> Przetwórz, speaker auto -> Automatycznie in the plan.
- [x] Source-review controls: Apply first on the common main action row, remaining draft/history controls there; Clear current draft alone below aligned right. Mirror this in translation review.
- [x] Rewrite source download guidance as two clear lines; translation guidance matches and names translation-exports.
- [x] Credential dialog: explicit Close window and top-right close, plus shared-key API check; maintain session/OS-store semantics and no automatic restore/unlock.
- [x] Shorten Refresh models and estimate cost to Refresh and estimate cost / Odśwież i oszacuj koszt.
- [x] Missing ASR cloud consent highlights/focuses checkbox, explains failure; smaller text and Consent is not permanently saved.
- [x] Missing key clearly requests entering or loading an already saved key after restart; remove obsolete cost-limit guidance.
- [x] Missing optional-correction consent explains which checkbox is required, highlights/focuses it instead of generic Error.
- [x] Diagnose/fix source-export progress for cloud results; generate translation updates queue stage/status and disables duplicate generation for that source until explicitly reopened.
- [x] Keep translation dictionary file picker inside its optional disclosure; audit sibling native pickers after DOM reparenting.
- [x] Review Windows audio disconnect exceptions (WinError10053) and handle expected browser disconnects without stack spam; retain genuine media/file failures.
- [x] Meaningful regressions/browser/normal gate and integration; changed-step docs/ENPL copy/checkpoint/evidence/changelog; cleanup, commit/push and focused owner checklist. 1031 tests, 17 integrations, full/focused Chromium and actual restart/recovery pass.
- [x] Historical app retest gate superseded by owner focused acceptance/task10 authorization and final Windows startup checks on2026-11-22. Managed-installer acceptance is separate and remains open above.

## Delivered B owner Windows/GUI fixes — native retest next

Owner confirms Windows installation and GUI launch work; doctor/dependency checks all pass.
Reported queue failure was before ASR with masked GUI_TRANSCRIPTION_FAILED on audio group and MP4.
The reproduced Windows publication defect and requested UI changes are fixed; see the
[checkpoint](docs/checkpoints/2026-11-21-windows-queue-gui-feedback.md).

- [x] Diagnose/fix Windows queue persistence; expose sanitized exception/stack/OS codes instead of masking unexpected failures; stop duplicate generic error/action rendering and localize messages.
- [x] Simplify step 1: remove input-directory picker and directory-media button; share one audio/video/previous-result picker with left rail; rail label Add audio / Dodaj audio.
- [x] Remove Select episode / Selected for planning buttons; keep per-recording settings directly editable and Remove from list; batch plans all inputs.
- [x] Replace permanently visible stream/ID section with automatic multi-stream warning and explicit per-file selection when needed (ID controls only for actual collisions). All-stream processing is an alternative, not required if explicit selection is available.
- [x] Replace cloud cost-limit input with live hourly prices and duration-based estimates; add shared-key/connection check and explicit model availability/pricing/estimate refresh; retain backend cost protection as an internal safeguard.
- [x] Use Local GPU (default) / Lokalne GPU (domyślne); merge duplicate dry-run tables into one source/decision/warnings/language/count table.
- [x] Update necessary EN/PL copy, tests/checklist, changelog/checkpoints/roadmap; verify and push; native owner re-test remains required.

- [x] Owner confirms native local ASR and subtitle exports, and cloud ASR now succeed. Continue the new status/consent/layout feedback above; full Windows/WSL B acceptance remains pending.

## Earlier installation/distribution request — consolidated into the next package

- [x] Tracked in the new Windows/Ubuntu lifecycle package above: Windows uninstall script with documented removal of application environment/private FFmpeg and optional downloaded models. Inventory exact owned paths and shared caches; preserve recordings/publications and unrelated/shared model editions unless explicitly selected.
- [x] Standalone graphical Windows EXE installer without a repository checkout; desktop launch icon and Add/Remove Programs registration.
- [x] Matching graphical uninstaller, including explicit optional model removal. See the consolidated distribution plan above; this is no longer an unspecified later backlog item.

## Completed Windows model-setup fix

- [x] Fix NLTK 3.10.1 blocking regex inside the checkout's .venv during setup-models.py; -P alone also reproduces the failure.
- [x] Prepare NLTK data from an isolated child/neutral working directory, preserving safety hook, model pins, caller paths and explicit downloads.
- [x] Test the locked NLTK import without network and the model setup flow/failures with stubs; update Windows instructions/checkpoints, verify, commit/push.

- [x] Owner confirms native Windows model preparation/install/GUI launch and doctor/dependency checks pass. Continue queue/workflow fixes and the B checklist. [Fix checkpoint](docs/checkpoints/2026-11-21-windows-model-setup-nltk.md).

## Completed B8a follow-up: large cloud recordings

- [x] Replace the mixed-audio 24 MiB rejection with automatic byte/time-bounded requests.
- [x] Merge word times/text on the original timeline, with overlap ownership/deduplication that preserves real repetitions.
- [x] Reconcile request-local speaker IDs using shared timed words; flag unresolved identity instead of guessing or blocking the recording.
- [x] Account for context/rounding in budget preflight, keep cancellation/no-auto-retry/secret boundaries.
- [x] Add boundary/large-input/cost/cancellation/downstream regressions; update EN/PL UI, guides/checklist, checkpoints and roadmap; commit/push.

Evidence: [chunking checkpoint](docs/checkpoints/2026-11-21-cloud-chunking.md). 982 tests / 15
integrations pass; live Scribe/MAI boundary/review/export cases pass. Owner B acceptance remains next.

- [x] Explain native Windows installation/launch and the owner test order; see [test handoff](docs/checkpoints/2026-11-21-owner-b-test-handoff.md). Full owner Windows/WSL acceptance remains pending.

## Current state: B5–B9 agent delivery complete; owner acceptance next

Owner explicitly instructed execution of B5–B9 to completion, returning only for missing
information or concrete blockers. A stays closed. Active execution checkpoint:
[package B execution](docs/checkpoints/2026-11-21-package-b-execution.md).

- [x] B5 agent implementation: native lock resolution, Windows setup/repair/model preparation, guarded OS primitives/paths/launch/doctor; 935 model-free tests and 12 FFmpeg integration tests pass. Owner Windows execution remains B9 acceptance.
- [x] B6 agent implementation: shared OpenRouter credential save/use/remove, explicit OS access and session fallback; 937 tests pass. Real native store acceptance remains in B9.
- [x] B7 agent implementation: recent projects/locations, strict canonical scanning/queue selection, optional dictionary-free profile/catalog transfer; 942 tests/12 integrations pass. Native profile exchange remains owner B9 acceptance.
- [x] B8 agent implementation: exact stream/ID plan/stage/recovery, content-based folder scan, native picker handoffs; 957 tests/13 integrations pass. Native desktop checks remain owner B9 acceptance.
- [x] B8a agent implementation/functional PL qualification: four-model OpenRouter ASR, shared key, fresh consent/cost guard, same canonical/downstream workflow. Ten paid calls cost USD 0.0095832333762821113 total; owner waives live EN (no sample).
- [x] B9 agent checks/checklist: 973 unit tests, 14 integrations, full 144-case Chromium/restart/focused B HTTP checks and wheel/sdist resource/privacy/CLI audit pass. [Owner checklist](Instructions/GUI_PACKAGE_B_TEST_CHECKLIST.md). Native Win11x64/full WSL acceptance remains owner-run.

B8a live qualification and limitations: [cloud checkpoint](docs/checkpoints/2026-11-21-b8a-cloud-asr.md).
B9 evidence and next gate: [verification checkpoint](docs/checkpoints/2026-11-21-b9-verification.md).
No key/audio/transcript/runtime output committed. Owner test is pending; task 10 stays after B
acceptance/function freeze, followed by terminology approval and full EN/PL manuals.

The historical planning-only statements below are superseded by this execution instruction.

Current decisions update: OpenRouter ASR with one shared provider key, a four-model dropdown,
short functional PL/EN podcast tests and a total live-ASR budget of USD 2. Record/verify the
provider capability details; no product implementation or paid/media calls in this update.

- [x] Verify public OpenRouter model IDs/transcription response capabilities in official documentation.
- [x] Record accepted provider/model/media/budget scope in the B plan, roadmap and status; retain serial B5–B9 order and closed A.

Current planning request (2026-11-21): describe B agreements, execution order and remaining
owner decisions. [B planning checkpoint](docs/checkpoints/2026-11-21-package-b-plan.md).

- [x] Reconcile B5–B9 with the accepted roadmap and confirmed Windows 11 x64 execution split.
- [x] Describe deliverables, verification and the final Win/WSL acceptance checklist.
- [x] Identify remaining decisions without reopening A or starting B features/provider calls.

The owner passed the entire focused checklist on 2026-11-21 and accepts A. No new owner retest
is requested for the final UI adjustment below, now implemented and verified. Package A is closed.

- [x] Remove the redundant Prepare text for review button from source-review step 4, retaining automatic preparation when opening review/export from the queue.
- [x] Merge the two action panels: first row Undo, Redo, Save draft, Restore saved draft; second row Apply, Clear current draft. Rename the restore/clear labels coherently in EN/PL.
- [x] Run the normal quality gate and focused UI verification; record owner acceptance and close A in TODO, roadmap, policy and checkpoints. Commit/push the change.
- [x] Record B preparation as the next resume point, including native Windows test environment/execution arrangements; no B feature implementation or cloud calls in this closure task.

## Package A acceptance record

Active checkpoint: [A closure and B preparation](docs/checkpoints/2026-11-21-package-a-closure.md).
The owner passed the entire [focused retest](Instructions/GUI_PACKAGE_A_RETEST.md) on 2026-11-21.
The final layout adjustment above requires no additional owner retest. B preparation follows A
closure; implementation of B is not part of this closure task.

## Completed A acceptance fixes — owner feedback

Checkpoint: [A acceptance fixes](docs/checkpoints/2026-11-20-package-a-feedback.md).

- [x] Correct rail next-step labels for staged/queued/running/failed/cancelled ASR; distinguish ASR complete from workflow finished.
- [x] Show modal/translucent restore progress with loaded/total saved queue jobs until queue and editor recovery finish; no automatic ASR/consent.
- [x] Retry replaces the failed/cancelled queue row with a fresh attempt; label Retry / Ponów.
- [x] Fix valid cancelled attempts being omitted from saved work; accurately report actual omissions and localize the message.
- [x] Merge GUI Inspect and Dry-run into one planning step, keeping safety/hash/explicit confirmation; first-use planning must remain valid when confirmation is checked.
- [x] Show the custom gear during batch planning and restoration, and correct untranslated new cancellation/cleanup messages.
- [x] Infer skipped optional LLM correction when manual review/downstream work begins, so next-step/finished state follows actual work.
- [x] Explain raw ASR results/segments/transcript files and distinguish retained durable media from temporary cleanup; preserve owner-qualified cleanup/export behavior.
- [x] Fix cramped/unstable native audio controls; remove the redundant permanent speed selector once browser controls have sufficient room, preserving seeking/mixed playback.
- [x] Run focused regression/browser/restart/package checks, update retest checklist and commit/push A fixes; owner subsequently accepted A.
- [x] Record the final two-column EN–PL approval requirement after functional additions and before the full EN/PL manual rewrite. The actual task-10 export is still pending; no artist ZIP changes.
- [x] Owner passed [the entire focused feedback retest](Instructions/GUI_PACKAGE_A_RETEST.md) on 2026-11-21; A accepted with the final layout adjustment above, no new owner retest.

Owner evidence: restart preserves edits and leaves ASR/checkboxes stopped/unset; waiting/running
cancellation and no rerun of completed ASR work on WSL; temporary cancelled workdir deletion and
versioned export downloads/restart recovery pass. Legacy workdirs remain protected, durable media
remains present. The feedback fixes and the complete focused retest are now accepted.

## Package A — original tasks 1–4, in order

- [x] A1: Check latest restart recovery (queue, saved source/translation reviews, publication/export pointers). Preserve owner acceptance of already tested workflows. Full profile transfer may be checked during Windows work.
- [x] A2: Cancel waiting/running tasks safely with honest requested/cancelled status, no incomplete final publication, and restart-from-beginning retry semantics.
- [x] A3: Workdir immutable creation time and retained reason (failed/cancelled/successful-retained); preview/filter explicit cleanup without deleting referenced or final artifacts.
- [x] A4: Download verified existing exports through the GUI, preserving exact artifact/version identity and avoiding ASR reruns.
- [x] Run relevant regression/packaging checks, then deliver one concrete manual checklist for the implemented A package.
- [x] Owner tested A; reported defects were fixed and the complete focused retest passed on 2026-11-21.
- [x] A acceptance gate passed and final no-retest layout adjustment verified. A is closed; later B implementation/acceptance is recorded below.

## Package B — original tasks 5–9, with cloud ASR inserted as 8a

- [x] B5 agent implementation/checks: Native Windows dependency/media/model/path/CLI/GUI launch support, sharing the same application and frontend as WSL.
- [x] B6 agent implementation/checks: Opt-in OS credential storage: save/read/remove API keys; preserve session-only fallback and exclude secrets from profiles/exports/logs.
- [x] B7 agent implementation/checks: Recent projects/sessions, named input/output locations, canonical-result directory scanning and optional profile export without embedded dictionaries.
- [x] B8 agent implementation/checks: Audio-stream choice, remaining native picker conveniences, content-aware media discovery and explicit IDs for same-name recordings.
- [x] B8a agent implementation/checks: OpenRouter four-model ASR delivered and short PL live cases pass within the shared USD 2 budget. Owner explicitly waives EN live material. Long mixed audio now chunks automatically with timed context, remapped speakers and explicit uncertain-assignment review.
- [x] B9 agent implementation/checks: Complete package regression and prepare the one full native-Windows + WSL workflow test/checklist.
- [x] Owner accepts focused workflow checks and explicitly authorizes task10 after final automated polish, with no further manual retest. Retain documented platform qualification limits.

B5 execution arrangement confirmed 2026-11-21: Windows 11 x64. Agent implements/checks on this
Linux VM and pushes to GitHub; owner pulls the repository and performs native-Windows launch and
full-workflow testing. This does not imply agent access to native Windows or claim its qualification.

[Execution detail and resolved decisions](docs/checkpoints/2026-11-21-package-b-plan.md):
OpenRouter with one key shared by ASR/correction/translation. ASR dropdown:
`openai/whisper-large-v3`, `openai/whisper-large-v3-turbo`, `elevenlabs/scribe-v2`,
`microsoft/mai-transcribe-2`. Owner permits short supplied podcast/English excerpts (PL two
speakers, EN one), functional canonical/downstream compatibility checks, USD 2 total live-ASR
spending including retries across all models. No full-corpus/accuracy benchmark. Locate actual
material and recheck current capabilities/costs at B8a; preserve this authorization. Original planning questions are resolved; B agent delivery is complete and owner native Windows/full WSL acceptance is next.

## Terminology, documentation and distribution — current owner sequence

- [x] Task 10 export: local editable ID/EN/PL workbook for owner corrections, including dynamic copy, guides and diagnostics; preserve placeholders/codes.
- [x] Task 10 application: owner EN/PL corrections integrated, reference committed and interface approved 2026-11-22.
- [x] Task 11a: English documentation reviewed/updated and delivered 2026-11-22.
- [x] Task 11b: Complete Polish user documentation and bilingual offline help delivered 2026-11-22.
- [x] NEW artist reference with approved GUI/language/docs delivered 2026-11-22; original archive preserved.
- [x] Task12 implementation/VM verification: managed lifecycle, versioned terminal packages and native Windows graphical wizard0.22.0. Owner native installation acceptance/publication remain separate, as above.
- [ ] Parallel, no deadline/non-blocking: integrate artist icons/feedback when supplied. Do not modify the sent ZIP/demo. Documentation screenshots wait for final custom GUI/icons.

## Nice-to-have only

- Ollama/further local-model expansion; word/phrase-level playback highlighting (not whole-block highlighting).
- Alignment/timing refinements and optional instruction review with less-technical users.
- Non-speech authoring, advanced channels/crosstalk/surround, audio repair/comparison and additional subtitle formats.
- Earlier optional research: private/public corpus benchmarks, universal dictionaries, model benchmark automation and hardware presets. No ETA/percentage accuracy study is scheduled.

## Removed / outside selected scope

- Full model catalog/favorites/local model-loading management; manual timing overrides.
- Alternative translation chunking and owned input snapshots; whole-block audio-follow highlighting.
- Additional LLM punctuation/editorial modes, speaker-count research, bilingual HTML and Docker from the old roadmap.
- Other unselected broad deployment/research/scheduling ideas are not package obligations and must not reappear as completion gates.

## Acceptance already retained

Owner accepts recent GUI/workflow and browsers/palette. Restart recovery including progress feedback
is accepted; full profile exchange remains
provisionally accepted without a complete owner test. The full focused A checklist passed on
2026-11-21, including recovery/player feedback. Actual browser page zoom
200% remains optional/unchecked. Existing regression/security/lineage checks remain required.
Tested hardware is RTX 3090 24 GB; >=8 GB VRAM elsewhere is an unqualified expectation, without
a compatibility/performance guarantee. No completed acceptance is reopened because an old plan
calls it future.

## Delivered history

- [Batch planning, sentence-aware review and portable profiles](docs/checkpoints/2026-11-20-batch-sentences-profiles.md)
- [Mixed playback, progress and artist reference](docs/checkpoints/2026-11-19-review-mix-progress-artist.md)
- [Artist package sent for review](docs/checkpoints/2026-11-19-artist-review-package.md)
- [Playback and video](docs/checkpoints/2026-11-19-playback-video-progress.md)
- [Brand/palette and feedback](docs/checkpoints/2026-11-19-gui-review-and-brand-feedback.md)
- [Polish UI and recovery fixes](docs/checkpoints/2026-11-18-gui-localization-and-recovery.md)
- [Workflow polish](docs/checkpoints/2026-11-18-gui-workflow-polish.md)
- [Guided workflow](docs/checkpoints/2026-11-18-guided-workflow.md)
- [Native dependency repair](docs/checkpoints/2026-11-18-gui-dependency-repair.md)
- [Resolved launch diagnosis](docs/checkpoints/2026-11-18-gui-launch.md)

The repaired local-only ASR/source-export path on WSL/RTX 3090 and the later MP4/mixed playback
owner successes remain accepted. GUI-55 stays closed. Do not tag/publish a release as part of this
planning update. Do not reopen delivered work merely because a historical plan calls it future.
