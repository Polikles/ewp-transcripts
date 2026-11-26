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

First clean candidate source d280943b0fcdda3ecb184d74c8be10fd207898bd;
Windows run45795432181. All62 previous installer payload hashes verified; model pins, notices,
AGPL and both original review workbooks unchanged. Owner reports0.24.3 uninstall succeeded and
original earlier installation remained intact; preserve that qualification. Manual retest waiver
supersedes prior copy-review waiting boundary. Next after final artifact delivery: native Windows
application interface/lifetime, not a further owner checklist. No native app work in this fix.

## Final verified delivery

- [x] Detect before data/workers, version-specific EN/PL guidance, original root displayed;
  changing new target cannot bypass detection. Newer-installer phrase links releases.
- [x] Same-root explicit maintenance preserved; failed/new Install cannot alter existing files.
- [x] Recheck before Next/host/install and early shared backend/CLI, final registration race guard.
- [x]25GB fresh-install labels, cache/disk rerender and actual gate agree.
- [x]1186 local tests,17 integrations, Ruff/format302/mypy119 PASS;72 focused distribution tests.
- [x] Native run45795432181 SUCCESS:46 WPF groups,18 Windows cases (29.15s), including6 actual
  registry-view/version refusal cases without workers. No skipped native cases.
- [x]49 native previews inspected as overview,8 full-size focused screens: three version relations
  in EN/PL and EN/PL fresh-install matching25GB labels. Paths/actions/link visible and readable.
- [x] Two CI artifact digests/six product hashes, full bundle manifest, every packaged app file and
  manager.py match clean source d280943b0fcdda3ecb184d74c8be10fd207898bd.
- [x] All62 earlier artifact hashes, model pins, project/vendor notices, AGPL and original review
  workbooks unchanged. No new downloads of models, paid-provider calls or transcript campaign.
- [x] Owner explicitly waives manual retest; no manual gate left open for this correction.

Delivery: /home/linuch/project-ewp/deliveries/ewp-0.24.4-installers.
EXE EwP-Setup-0.24.4.exe:157323320 bytes, SHA256
fcac161fb30fec3ae83eb97843d6f4903653eeb14ecc13be1619cab8610f5254.
Machine evidence:2026-11-26-install-preflight-evidence.json / delivery DELIVERY.json,
windows-self-test.json, previews/, SHA256SUMS.txt. No public release/signing/bootstrap activation.
Temporary signed URLs initially expired during approval; refreshed only after approved downloader
started, both archive hashes then matched. Temporary downloads/configs/candidates cleaned after
preserving final evidence and delivery. Private originals and prior deliveries stay untouched.

Next planned stage: native Windows application interface/lifetime; AMD research (experimental
without hardware qualification) and first public release follow that interface. Do not reopen
manual testing, model/paid tests or another rebuild merely on resume. Prior user uninstall/update/
mixed-model qualification and cumulative cloud spend USD0.0291461230985028369 remain preserved.
