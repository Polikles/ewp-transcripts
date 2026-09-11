# Development Handoff

## Snapshot

- Date: 2026-09-11
- Branch: `main`
- Baseline commit: `806adcf` (`fix(gui): validate canonical result handoffs`)
- Application version: `0.19.0`
- Verification: `UV_CACHE_DIR=/tmp/ewp-uv-cache ./scripts/check.sh` — **705 passed**
- Release state: internal requirements work only; do not tag or publish a release yet.

## What is working

The local browser GUI supports the complete single-job path: inspect/dry-run/stage/transcribe,
optional LLM correction or skip, manual review with revision-local speakers and safe
split/merge, verified transcript export, optional LLM translation or skip, semantic review, and
translated export. Canonical results remain immutable; review and translation candidates are
non-final until explicitly previewed, confirmed, and applied.

Review drafts are persisted per canonical-result path beneath the selected output root. Switching
between results preserves an unsaved active draft and restores the matching saved draft. The
latest handoff behavior is intentional: skipping correction opens the selected result in manual
review rather than leaving the previous result active.

All GUI canonical-result handoffs now validate the *content* as a strict completed canonical
result JSON. Audio or subtitle files are rejected before correction, review, translation, or a
workflow skip can continue. A dry-run whose decision is `skip` because a completed result already
exists reports that result path instead of an opaque output-plan error.

## Immediate next work

Implement the already-recorded GUI stage queues in
[99 - Post-0.1 roadmap](99-roadmap-v2.md#13-gui):

1. Give correction, review/export, and translation an expandable visible per-stage queue, even
   for one item.
2. Let the operator reopen or restart the relevant stage for any queued item without stale form
   state.
3. Preserve the existing grey/green/red/blue status legend across all stage queues.
4. Build the foundations for checkbox bulk selection and **Select all** for optional LLM
   correction and translation; retain per-item consent, dictionary, provenance, retries, error
   isolation, and manual-review gates.

This is the priority before the planned visual/branding overhaul. Do not treat the current
single-active-form UI as sufficient multi-job workflow support.

## Important constraints

- Follow the contracts in [26 - Local browser GUI contract](26-local-web-gui-contract.md), the
  warning/error catalogue, and the roadmap; application/domain services remain authoritative.
- The GUI invokes application services directly. It must not shell out to the CLI or duplicate
  pipeline logic.
- API keys are memory-only for the active GUI server process: never persist them in browser,
  workspace, project, logs, provenance, or settings. The GUI is intentionally single-user/local;
  multi-user hosting is out of scope.
- Dictionaries are project-scoped, immutable/versioned, and auditable by hash. Do not turn
  individual translation mistakes into broad dictionary substitutions.
- LLM correction and translation create candidates only. Manual review remains the final
  authority. Local Bielik translation is usable but not recommended for quality; Gemini 2.5 Flash
  through OpenRouter is the qualified cloud correction path.
- Preserve result/revision/translation lineage and never silently overwrite artifacts.

## Deferred work already on the roadmap

The roadmap also records cloud STT qualification, safer but practical local path selection,
system pickers, content-aware source checks/TOCTOU mitigation, saved non-secret preferences and
workspaces, full cross-directory end-to-end qualification, accessibility/help polish, the
floating workflow navigator, light/dark and Polish/English UI, branded frontend work, and
post-functional public-data ASR/dictionary evaluation.

## Resume checklist

```bash
git pull --ff-only
git status --short
UV_CACHE_DIR=/tmp/ewp-uv-cache ./scripts/check.sh
```

Then read this handoff, [26 - Local browser GUI contract](26-local-web-gui-contract.md), and the
GUI section of [99 - Post-0.1 roadmap](99-roadmap-v2.md) before changing the stage-queue design.
