# Automatic required host checks — 2026-11-25

Baseline2b45b7f, delivered0.24.1 source8e55212. Target0.24.2.
Owner wants automatic required checks at entry to Location step2 for Install and Update; a new
folder also gets an automatic free-space recheck. Owner explicitly waives manual tests after
this correction. Preserve prior passes; no extra model/inference/paid campaign. Full installer
EN/PL and notices audit is next planned work; native app shell follows installer closure.
Implementation/automated verification/artifacts pending. See opening TODO for exact acceptance.

Implementation: shared AutoCheckHost is called on entering/back to Location, after path debounce
and native folder selection for every operation that requires host checks. Invalid paths wait;
busy/in-flight and cached checks do not spawn duplicate workers. A changed target refreshes only
the disk JSON row, aggregate ready flag, labels and Next, retaining CPU/OS/GPU/runtime results.
Failed hardware checks remain blocking. If required local/cloud profile changes, rerun the full
check rather than reuse the wrong GPU requirement. Check this computer remains an explicit full
retry. Stale in-flight path results are epoch-filtered; automatic checking continues at new path.
Native synthetic worker injection tests all four actions, invalid target/uninstall exclusions,
low→adequate disk transitions, unchanged cached hardware rows and failed-CPU preservation.
Manual retest explicitly waived by owner; no new owner gate/checklist.
