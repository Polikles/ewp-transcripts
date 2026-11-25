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

Local gate1176 PASS/12 native skips,17 integrations included; Ruff/format/mypy119 files PASS.
First product source7178bc7. Native WPF tests now cover automatic entry for all required actions,
no duplicate full worker on disk changes, disk row/Next low-space recovery and retained CPU failure.
No manual retest requested; next planned text/notices stage recorded in TODO/roadmap only.

Next-stage plan (not executed in this correction): audit all user-facing notices/licensing text
for project-only comments and misleading wording while preserving real attribution/rights;
consolidate complete installer EN/PL text pairs with stable IDs for owner wording review, including
shorter disk descriptions; integrate accepted wording and synchronize offline help. Then design/
implement the native Windows app shell with controlled lifetime, closing/saving and active-job
handling. No public release/signing action inferred, and no new manual-test gate after0.24.2.

## Final verified delivery

0.24.2 delivered from7178bc7478897016e9663905739adb48afe73c00. Native run45683385827 SUCCESS:
38 WPF groups/12 real Windows cases,1176 local tests/17 integrations, Ruff/format/mypy119 PASS.
Three new native previews inspected; two archive digests/six product hashes and packaged help/source
match CI. Delivery: /home/linuch/project-ewp/deliveries/ewp-0.24.2-installers.
Checkpoint: docs/checkpoints/2026-11-25-automatic-host-checks.md and automatic-host-evidence.json.
Required checks auto-start on step2 for Install/Update/Repair/Add-models with a valid target;
folder changes refresh disk/Next while preserving CPU/OS/GPU/runtime checks. Hardware failures
remain blocking; local-profile changes rerun the needed full diagnostic. No duplicate workers.

Owner explicitly waives further manual retesting after this correction. Do not reopen a manual
checklist, paid/model/transcription campaign or rebuild merely on resume. Preserve previous
mixed-three-model inference, uninstall-while-running and application/manual acceptance.
NEXT planned stage: full installer EN/PL text consolidation and user-facing licensing/credits/
notices audit, then accepted wording/offline help updates. Native Windows app interface/lifetime
follows installer closure. Broad next-stage work was not executed merely to answer the plan.
Public release/signing/bootstrap activation remain later; EXE is unsigned/internal.

EXE SHA25627b34df73cb347fc87750a6d08a1f5bd5ceb39cd19008e694dc88932f0774f35.
Native case duration36.06s.38 WPF groups include new automatic-check/cache/failure assertions.
Three focused previews (disk low/ready and update-auto-ready) inspected. All50 prior installer
hashes verified unchanged. Updated EN/PL installation help is packaged and matches the source.
Evidence:2026-11-25-automatic-host-evidence.json / delivery DELIVERY.json. No new manual checklist.
No new model weights/provider calls, model repository/pin changes or artist work. Disposable cleanup follows.

Cleanup complete: exact /tmp/ewp-auto-host.NQbyvg task directory removed after preserving delivery evidence. No servers/browser processes were needed for this native-only correction. Prior deliveries untouched.
