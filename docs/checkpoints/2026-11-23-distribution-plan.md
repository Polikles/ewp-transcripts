# Versioning and distribution planning checkpoint

2026-11-23. Baseline clean main `438f91e`. Owner accepts prior delivery and asks what comes next,
explicitly adding update procedure/SemVer enforcement, short Windows/Ubuntu terminal installers
and a later graphical installer styled like the application. Current task is the concrete plan,
not implementation, release/tag publication or another artist-package build.

## Audit findings

- Application metadata remains `0.20.0`, with substantial changes accumulated in Unreleased since
  its 2026-11-16 checkpoint. Proposed next baseline `0.21.0` reflects added functionality; no
  retroactive fictional releases. Version-fallback code still mentions `0.2.0` and belongs in the
  upcoming single-source/consistency audit. No product version changed during this planning task.
- Existing PowerShell/Ubuntu install scripts assume a checkout; Windows also assumes uv/driver/
  Visual C++ prerequisites. They can be reused but do not satisfy a no-checkout copy/paste bootstrap.
- Current README/manual has the simple source update path, not a managed update/rollback operation.
- Uninstall and graphical Windows installer were already requested; broaden terminal lifecycle
  scope to both OS families and consolidate those older backlog entries.
- Lower TODO task10/application/docs/artist checkboxes were stale although work was delivered and
  accepted; corrected them instead of reopening completed stages.

## Recorded plan

[Distribution plan](../DISTRIBUTION_PLAN.md) and opening TODO now order: version audit/proposed
0.21.0/release discipline → common install/update ownership and recovery → Windows/Ubuntu removal
with explicit model choices → short no-checkout terminal bootstrap on both OS families → focused
installation lifecycle testing → Windows graphical wizard and matching uninstall/shortcuts/
registration, sharing tested operations. Final runnable README commands and complete EN/PL docs
ship with the actual artifacts, not speculative URLs today.

Wizard covers host tests, language/location, selected models/dependencies, masked transient HF
access token with separate upstream terms, optional shared OpenRouter key explicitly stored in
OS keyring, progress/readiness/launch. Key setup never supplies audio-upload/paid-usage consent.
Keep existing user work/models/credentials by default; do not delete whole shared model caches.
Windows GUI format/framework/signing is evaluated during implementation. Ubuntu GUI not presumed.
NVIDIA driver installation/elevation requirements must be explained; WSL results are not proof of
bare-metal Ubuntu qualification. Preserve existing RTX 3090 qualification and unqualified >=8 GB
expectation. Artist icons remain independent and non-blocking.

## Verification and handoff

Plan/README/TODO/roadmap/status/policy and AGENTS latest instructions updated. Current install
commands unchanged; actual app version remains `0.20.0`. No installer, model download, new token,
provider call or paid run performed. Formal reference: https://semver.org/spec/v2.0.0.html; initial
0.y.z project policy is explicit rather than claiming stable-API promises before 1.0.

Next is owner selection/authorization to implement the planned package. Do not start it or create
public releases merely on context recovery. Do not rebuild either artist archive. Verification
results and temporary-root cleanup are recorded below before commit/push.

Final verification: `make check` PASS (Ruff/format, mypy 115 source files, 1081 tests). 106 local
plan/entry links resolve; `git diff --check` passes. No product/runtime tests or new dependencies
introduced; ordinary existing regression gate reused. Task-owned temporary root
`/tmp/ewp-distribution-plan.YH71yB` removed after checks. No paid/model/installer calls or artist
archive changes. Deliver these planning files on main; implementation begins on the next owner
instruction. Current actual version remains 0.20.0 and proposed 0.21.0 is only the first planned task.
