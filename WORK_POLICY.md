# Work policy and context recovery

Updated: 2026-11-21. Read `AGENTS.md` first; this file supplements its rules.

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
