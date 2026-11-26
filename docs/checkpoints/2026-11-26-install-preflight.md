# Existing-installation preflight — 2026-11-26

Baseline2442694; product0.24.3 source d574806. Target0.24.4. Owner reports Install into a new
folder despite an existing registered installation; many files downloaded before late registration
refused a different root. Existing install remained intact and uninstall/update passed. Manual
retesting explicitly waived after this correction. Next stage is native Windows application UI.
Root cause confirmed: SelectOperation skips discovery for Install; LocationProblem inspects only
chosen directory. Backend checks conflicting registration only in register(), after setup/diagnostics.
Fresh install disk gate25GB but host text uses20GB installation_bytes. Follow opening TODO.
No paid/model campaign, native app implementation/public release. Implementation/tests/delivery pending.

Implemented: Install now calls registry/default-location discovery including partial registration
and registry DisplayVersion fallback. Step2 shows original root/version and blocks older/same/newer
with Update/Repair/rollback-newer-installer guidance. Refresh on folder edit, Next, explicit host
check and immediately before RunOperation; no worker when blocked. Backend reads HKCU/HKLM in
32/64-bit views, checks conflicting location before models/HF/host/runtime work and before CLI
credential prompts, retaining a registration-time guard for races. Same-root explicit Update/Repair
remains supported; direct new Install at existing root requires maintenance. Ubuntu desktop conflict
is checked early too. Complete cached models still reuse without HF.
Fresh-install HostText now shows25GB matching gate/folder even for cached legacy host JSON; existing
20GB program/model budget and separate maintenance allowance retain their internal semantics.
Catalog/new composed messages, changelog, version0.24.4 and mirrored EN/PL help updated.

Automated local gate:1186 passed,18 Windows-only skips,17 integrations included; Ruff/format302
and mypy119 PASS.72 focused distribution tests pass, including3 versions/other root stopping
before every worker, same-root explicit maintenance and all4 registry hive/view combinations.
Native WPF covers6 locale/version cases, root change bypass, manual/auto checks, no target creation,
late registration before operation, newer-installer link and matching25GB labels on cached refresh.
Six real Windows registry-view/version tests are added, preserving any preexisting real key.
Native clean-source build/results/previews and final hashes pending; no manual retest gate.
