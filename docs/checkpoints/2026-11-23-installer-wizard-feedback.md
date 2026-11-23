# Installer wizard usability feedback

2026-11-23. Baseline134286f clean. Owner did NOT start0.22.0 installation because the
long form/branding/operation/credential UX is confusing. Follow the opening TODO, every owner
label and requested order. Implement0.22.1 without changing delivered0.22.0/artist archives.
No subagents/paid ASR/model qualification. Use dedicated task temp root, native CI and visual
previews, not only compilation. Core shared lifecycle remains; adapt host structured data/disk
preflight and add existing-install local model mode through repair. New operations must not
silently update an installed older version. HF/OR validation is explicit and read-only, never audio.

Plan: inventory→stateful wizard/navigation/branding/icon→disk+host data→credential modals/help→
focused native rendering/gates/mocks→docs/version/normal checks→clean build/native CI→handoff.
Token validation dependencies: first verify HF model access, then acknowledge terms in installer;
main UI contains only valid state, values stay in masked modal/transient memory. OR key saved
only in OS store through shared manager at installation, no plaintext files. Native owner test
remains pending after a corrected preview. Record choices/evidence/cleanup before final handoff.

Task temp: /tmp/ewp-wizard-feedback.TEkrTX. SDK10.0.404/runtime10.0.15/uv0.13.9 tool pins
reused, fresh downloads verified. New patch0.22.1;0.22.0 and artist packages preserved.
Implemented split native WPF wizard (action→folder/host→models/keys or maintenance confirmation→
progress/result), fixed framed SVG header/subtitle and seven-size ICO in EXE. Metadata-only public
HF pinned revisions show8,427,081,436 bytes for four snapshots, recorded with file sizes for cache
reuse. No models or credentials downloaded/used. CPU/GPU-driver/disk host context now structured;
25GB fresh-root gate includes20GB+5GB reserve. Cooperative cancellation interrupts quiet child
processes and discards failed candidate, keeping the active installation/cache. Same-version repair
prevents the model-add action from silently upgrading.

Current verification: prototype cross-build PASS;1111 Python tests/mypy116 and17 integrations
PASS, including30 installer lifecycle/host/cancel/icon/model-pin cases. Native self-test expanded
for operation/page/25GB/localization/token/terms/stale responses, matching-version model add,
removal gates, PE icon extraction and PNG previews. Real native execution/visual inspection is
next; compilation alone does not qualify appearance. HF/OR dialog validation tests use synthetic
injected responses; no new provider/media/paid call. Docs/new HF help updated EN/PL; checklists
prioritize visual review before owner installation. Use temp tool paths for final build, keep
all intermediates in task root, then remove after content-free evidence/final handoff.
