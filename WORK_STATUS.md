# Current status — release plan revised, 2026-11-27

Active checkpoint: docs/checkpoints/2026-11-27-execution-order.md.
The current product remains **0.26.2**, source040e0084fec778f4ee82dbff590b3a38d217fc5b,
native run45970090999 PASS. Delivery: /home/linuch/project-ewp/deliveries/ewp-0.26.2-installers.
Local1261 passed/20 Windows skips, native48 wizard groups/18 filesystem cases/6 desktop cycles,
AMD DLL import,189 visual previews; all6 product hashes and92 previous products verified.
See docs/checkpoints/2026-11-27-nvidia-docs-audit-evidence.json. Owner accepts theme, Snap and size.

This task revises plans/docs only. No app/installer code, pins, binaries, remote settings, CI
permissions, signing services, certificate purchases, attestations or public releases were changed.
No new physical GPU/model/provider tests; spend USD0.0291461230985028369 unchanged.

## Owner decisions now authoritative

- Early public releases MAY BE UNSIGNED; signing no longer blocks them. Later free OSS signing
  research, potentially SignPath + owner-approved Actions; private procedure/keys outside Git.
- Verified attestations AND owner-approved general report/privacy policy are first-release gates;
  framework mapping follows separately. Formal per-version release checklist remains required.
- General cybersecurity/privacy review FIRST local EN outside Git, then owner review/approval;
  framework applicability/mapping follows. Only approved reports go under docs/security/.
  Include development VM authentication/authorization per channel (PAT/Deploy Keys/SSH/App/MCP),
  capability mapping, secret lifecycle, OS/agent boundaries and compromise risks, without secret values.
- Existing technical privacy requirements/guides are not a complete user-facing privacy policy;
  policy preparation is tracked explicitly, with truthful data flows and owner/contact decisions.
- Quick update AFTER first release. Storage ACCEPTED: Release assets plus releases/ metadata,
  links/checksums, no LFS. Required Pages follows first release.
- MSIX/Store is a separate post-release channel research task, including individual account,
  Store updates/signing, model-free/cloud-first initial app, optional local-model wizard, installed
  CLI and shared EXE/Store tiers; compatible6–8 GB/older NVIDIA experimental, implementation pending.
- Publisher/privacy/security contact approved: Damian Szczęch, szczech.dam+transcripts@gmail.com.
- Remove highlighting, separate reader tests and old5.12–5.14 research/benchmark programs.
  Bound audio repair; separate poor-audio mode plus one-file repaired/composite export. Optional
  sound detection is research with uncertain accuracy, not promised high-accuracy recognition.
- Profile transfer and200% browser zoom become upcoming-release scenarios. Physical AMD/other
  NVIDIA tests unavailable and not planned; corpus accuracy deferrals have no scheduled date.
- Artist integration/test is the dependency only for complete illustrated docs, not release.

Current task: propose grouping/order and per-task responsibility/test matrix, now written in
docs/EXECUTION_ORDER.md and the local Polish Kolejnosc-dzialan-EwP-2026-11-27.txt. Owner will use
it to select sequencing; no optional feature priority is silently accepted. Proposed next path:
SEC-01/PRIV-01 drafts, REL-01/REL-02 preparation, actual findings remediation, final delta review/
release checks, owner report/policy/publication approvals, release verification. Pages afterward,
then suggested Quick update+hardware batch. Larger Store/audio tracks start with a design decision.
All six prior policy questions remain settled. No report, policy approval, attestation, runtime/CI
implementation or publication occurred in this planning task. Portable v3 and answered decisions
remain current accepted scope records; the new local sequencing matrix is a proposal beside them.
