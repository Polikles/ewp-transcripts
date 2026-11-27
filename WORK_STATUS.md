# Current status — release plan revised, 2026-11-27

Active checkpoint: docs/checkpoints/2026-11-27-owner-release-decisions.md.
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

NEXT: SEC-01/PRIV-01 general local-English-first review/policy and REL-01 attestation implementation.
All six owner questions are answered; no policy clarification blocks those tasks. No review report,
policy approval, attestations, hardware-gate implementation or publication was completed by this edit.
Portable plan v3 and the answered decision list live beside the repository, outside Git.
