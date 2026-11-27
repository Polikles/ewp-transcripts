# Current status — release plan revised, 2026-11-27

Active checkpoint: docs/checkpoints/2026-11-27-release-plan-revision.md.
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
- Prioritize build attestations early; formal per-version release checklist/notes/docs consistency.
- General cybersecurity/privacy review FIRST local EN outside Git, then owner review/approval;
  framework applicability/mapping follows. Only approved reports go under docs/security/.
- Existing technical privacy requirements/guides are not a complete user-facing privacy policy;
  policy preparation is tracked explicitly, with truthful data flows and owner/contact decisions.
- Quick-update entry, releases/ storage and required GH Pages site added. Latest site timing is
  AFTER first release; binary Git limit and proposed Release-assets/index design need agreement.
- MSIX/Store is a separate post-release channel research task, including individual account,
  Store updates/signing, optional model wizard, CLI preservation and proposed hardware tiers.
- Remove highlighting, separate reader tests and old5.12–5.14 research/benchmark programs.
  Bound audio repair; separate poor-audio mode plus one-file repaired/composite export. Optional
  sound detection is research with uncertain accuracy, not promised high-accuracy recognition.
- Profile transfer and200% browser zoom become upcoming-release scenarios. Physical AMD/other
  NVIDIA tests unavailable and not planned; corpus accuracy deferrals have no scheduled date.
- Artist integration/test is the dependency only for complete illustrated docs, not release.

NEXT: resolve owner release-gate/storage/Store-tier questions and prioritize SEC/PRIV/REL/INST IDs
from TODO and docs/99-roadmap-v2.md before implementation. Do not start unrelated optional work.
The portable v2 plan and question list live beside the repository, outside Git.
