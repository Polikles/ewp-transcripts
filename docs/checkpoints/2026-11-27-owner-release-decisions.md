# Owner release decisions settled — 2026-11-27

Baseline1289414. Planning/documentation-only follow-up; product0.26.2/source040e008 and immutable
qualified packages remain unchanged. All six previously open owner questions are answered.

1. Accept actual binaries in GitHub Release assets, versioned metadata/links/checksums in releases/.
   No LFS; preserve the agreed2–3 available versions and safe older archival work.
2. FIRST-RELEASE GATES: implemented/verified final-artifact attestations AND owner approval of
   the general cybersecurity report and privacy policy. General report starts LOCAL EN OUTSIDE Git;
   approval required before publication. Framework mapping follows separately and is not a new gate.
   Quick update is explicitly AFTER first release. Required Pages remains after release.
3. Store initially has no speech models: cloud ASR and optional cloud correction, then a Settings
   wizard installs local models on qualifying hardware. Preserve review/exports and installed CLI.
4. Shared planned hardware classification applies to BOTH classic EXE and Store/model wizard.
5. Compatible6–<8 GB cards and older compatible NVIDIA such as RTX20xx are experimental. Compatible
   AMD stays experimental; RTX30xx+8–<12 experimental,12+ expected. Unsupported actual runtime/
   driver/architecture (including Pascal with current pins) remains unsupported. Unknown metadata
   is unverified, not fabricated success. No current installer hardware code/pin changes here.
6. Approved publisher/privacy/security contact: Damian Szczęch, szczech.dam+transcripts@gmail.com.
   Record in SECURITY_REVIEW_PLAN; do not silently modify separate licensing contacts/legal terms
   or infer GDPR/controller roles solely from the contact label.

Additional owner steering: SEC-01 MUST include the DEVELOPMENT VM and its actual authentication/
authorization mechanisms. Identify PAT versus Deploy Keys/SSH/Apps/OAuth/MCP separately by channel,
function/identity/scope/storage and lifecycle; assess OS/agent/connector boundaries and compromise
tradeoffs. Never expose actual secret values or assume connector credentials live on the VM.
This scope update does not claim an authentication inventory has already been performed.

Updated authority/status/TODO/roadmap/release policy/checklist/security/Store/hardware/distribution
docs and releases/ index. Portable Polish plan v3 and answered-decision file are local outside Git;
older v1/v2/question files remain historical. Workspace HANDOFF matches the settled decisions.

NEXT: SEC-01/PRIV-01 code-grounded general local EN report/policy and REL-01 attestation work.
Those are not completed by this plan edit. No policy clarification is pending; obtain no repeated
confirmation for these already-authorized tasks. Actual report approval/publication remains its
explicit owner boundary. No release/site/report, certificate application, signing, CI permission
change, paid/model/provider or physical-GPU campaign occurred. Provider spend unchanged.

Validation is recorded in the adjacent owner-release-decisions-evidence.json. Previous checkpoint
and audit evidence retain their original dated scope rather than being rewritten as new passes.

Validation PASS:299 Markdown documents/562 local links, zero maintained link errors; nine unchanged
frozen runbook paths retained. All153 requirements traced, seven historical snapshots unchanged.
Runtime/model/toolchain/CI files unchanged; portable v3/decision files UTF-8. No application-suite
rerun for this documentation-only owner-decision/scope update.
