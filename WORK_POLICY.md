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
   for exact scope and retain permission without asking again. B implementation still waits for
   the owner start instruction; no calls in this planning update. Declined historical roadmap
   ideas must not return as gates.
