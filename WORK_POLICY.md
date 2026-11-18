# Work policy and context recovery

Updated: 2026-11-18. Read `AGENTS.md` first; this file supplements its rules.

1. On resume, read `WORK_STATUS.md`, `TODO.md`, the active task checkpoint linked there,
   and `docs/99-roadmap-v2.md`. Inspect Git status before edits. Historical handoff sections
   do not override current checkpoints or reopen owner-qualified gates.
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
