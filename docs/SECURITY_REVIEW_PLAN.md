# Security and privacy review plan

This is a TASK SPECIFICATION, not an audit report, security assurance or privacy policy.
Owner instruction2026-11-27: general report first, EN, local outside Git; owner approval before
publishing a reviewed version under docs/security/. No report has been produced by this plan revision.

## Documentation check

[Technical security/privacy requirements](11-security-and-privacy.md), README, CLI privacy notes,
[key settings](gui/settings.md) and [saved-work guidance](gui/saved-work.md) describe parts of the
mechanism. No complete maintained user-facing privacy policy was found in the tracked docs.
Technical requirements are not evidence that every control is correctly implemented. PRIV-01 must
produce a factual policy from verified data flows and owner decisions, without invented contact
details, retention periods, provider guarantees or certification claims.

## SEC-01 — general report first

Write the English draft in a local directory OUTSIDE the repository, e.g. the workspace sibling
private-reviews/. Use a dated source commit and explicit scope/version. No real keys, recording
content, personal paths or exploitable private material in shared evidence. Keep detailed findings
local until owner review; publication is a separate action after approval.

Review layers and trust boundaries:

1. User/deployment: single-user loopback, native/browser/CLI, filesystem/OS accounts, same-user
   access, shared machine, malicious local software and limits when OS/account is compromised.
2. Data inventory: source audio/video, temporary normalized/extracted/chunked audio, IPC streams,
   canonical/revised/translated text, exports, dictionaries, workspaces/autosave/backups/profiles,
   source paths/names/hashes, preferences, model caches and usage/cost metadata.
3. Storage lifecycle: exact paths and owning process, format/content, access permissions,
   encryption at rest or its absence, retention after success/failure/crash/update/uninstall,
   cleanup protection and deletion limits, backup/cloud-sync exposure and removable volumes.
4. Secrets end to end: HF/OR/API passwords/tokens from installer/dialog/clipboard/environment,
   session memory, Windows Credential Manager/Linux Secret Service, process creation/arguments,
   IPC/stdio/temp files and network headers. Follow save/read/test/use/delete/restart/error paths;
   distinguish OS protection from protection against the same user or administrator. Check plaintext
   fallback, accidental persistence, inherited environment and output/exception redaction.
5. Network/consent: offline transcription, installation/model downloads, provider metadata/key tests,
   cloud audio and text transfers, local/LAN LLM boundaries, TLS/HTTP tradeoffs, redirects and endpoint
   selection, scoped consent/reload behavior, third-party logging/retention/training uncertainty.
6. Browser/native/CLI surfaces: origin/host/CSRF/CSP, XSS/output handling, file/download identities,
   source/path/symlink validation, authenticated native lifecycle/permission broker and process jobs,
   local ports, loopback access and invocation in automation/pipelines.
7. AI/content: untrusted transcripts/media/provider output, prompt injection, faithful correction,
   hallucinations and non-final results, parser/model deserialization and malicious model risk,
   cost/large-input denial of service, semantic/timing and source integrity.
8. Installer/supply chain: verified URLs/digests, dependency/model/toolchain licenses and pins,
   privilege boundaries, scripts/rollback/uninstall, CI token/OIDC scopes, untrusted PR/workflow
   inputs, logs/artifacts/provenance, unsigned download threats and future channel isolation.
9. Operational communication: reports/support attachments, crash traces, security contact,
   vulnerability response, dependency advisories, privacy claims and noncommercial solo maintenance.
10. Development VM and development tooling: inventory authentication PER CHANNEL, including Git
    SSH/Deploy Keys, SSH agent/forwarding, PAT/fine-grained PAT, gh/HTTPS credential helpers,
    GitHub App/OAuth/MCP/connected-service access and CI GITHUB_TOKEN/OIDC where applicable. Determine
    which identity supplies each function (read repo, push, API, Actions/artifacts, releases/Pages,
    packages and administration), credential location/ownership, repository versus account scope,
    read/write/privilege limits, expiry/rotation/revocation and host verification. Do not assume
    PAT or Deploy Keys merely from a successful push, or equate connector-held credentials with
    secrets stored on the VM. Mark service/account-side facts that cannot be inspected as unknown.
    Review VM user/root privileges, filesystem permissions, agent sandbox/approval boundaries,
    remote access, caches/logs/process environment, backups/snapshots and private corpus/report
    locations. Assess compromise blast radius, credential theft/abuse, shared-machine and supply-
    chain risks, developer/assistant/tool data disclosure and least-privilege versus convenience.
    Read only non-secret configuration, identities and metadata needed for evidence: never print
    PAT values, private keys, auth headers, credential-store payloads or a wholesale environment
    dump. Record actual capabilities separately from permissions merely requested by tooling.

Deliver: executive summary; component/data-flow and persistence tables; threat actors/boundaries;
code/config references; tests actually performed; findings by likelihood/impact/confidence;
mitigations and residual risks/tradeoffs; prioritized remediation; uncertainties/questions; privacy
policy gap analysis. Separate observed implementation, documented intention and untested hypotheses.
No blanket claim of encryption, safety or absence of uploads based only on tests or requirements.

## PRIV-01 — user-facing policy

Explain local processing and all optional external calls, what is written where, retention/deletion,
credentials and consent, installation/update traffic, OS/third-party boundaries, metadata/path privacy,
user controls, limitations and contact/version/effective date. Determine whose data flows to whom;
do not equate the app user's controller responsibilities with the project's own role. Owner-approved
publisher/contact: **Damian Szczęch**, **szczech.dam+transcripts@gmail.com**. Use this supplied address
for privacy/security correspondence; do not silently rewrite separate licensing-inquiry contacts
or approved legal text. Determine actual legal roles from evidence, not the contact label alone.
Prepare EN first; PL/public links follow review. Owner approval of BOTH the general report and
privacy policy is a confirmed first-public-release gate. Framework mapping is a subsequent stage.

## SEC-02 — frameworks AFTER the general report

First produce an applicability register: instrument/version, reason, actual actor/role/use case,
jurisdiction/audience, mandatory or voluntary character, exclusions/uncertainty, required evidence
and realistic solo-project scope. Then map accepted findings/controls to selected instruments.
ISO management-system alignment is not product certification; framework mapping is not a legal
opinion or proof of compliance. Do not buy standards/certification or invent inaccessible clause text.

Candidates to assess, not automatically applicable obligations:

- ISO/IEC27001 with27002 and privacy-management guidance, plus ISO/IEC42001 for AI governance.
- GDPR: project/user/provider roles, lawful handling, minimization/retention/security, data-subject
  information/rights and external-provider/international-transfer issues where applicable.
- NIST CSF/SSDF and AI RMF; OWASP ASVS/SAMM and relevant GenAI risks; SLSA/OpenSSF supply-chain work.
- EU AI Act, Cyber Resilience Act and any genuinely relevant additional law (including NIS2 only
  if actual entity/activity scope warrants it). Assess OSS/noncommercial context; no blanket exemption.
- Microsoft Store privacy/security/distribution requirements for the later Store channel.

The framework report is also local EN first and separately owner-approved before publication.
No immediate benchmark/human-comparison campaign is introduced by this security review.

Starting primary references (versions/applicability must be checked during SEC-02):

- [ISO standards](https://www.iso.org/popular-standards.html)
- [NIST SSDF](https://csrc.nist.gov/Projects/ssdf)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP GenAI](https://genai.owasp.org/)
- [GDPR text](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [EU Cyber Resilience Act](https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act)
