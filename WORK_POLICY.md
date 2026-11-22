# Work policy and context recovery

Updated: 2026-11-22. Read `AGENTS.md` first; this file supplements its rules.

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
