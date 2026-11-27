# Per-version release checklist template

Copy this template into a dated per-version release record; do not tick this reusable template
as proof of a release. Follow [release policy](RELEASE_POLICY.md) and [version policy](VERSIONING.md).
Upcoming implementation must enforce machine-checkable gates; this file is not an automated gate.

## Identity and decision

- Version / source commit / workflow run / platform assets:
- Owner scope and publish decision:
- Signing status (early unsigned releases are permitted):
- Required first-release gates: verified attestations; owner-approved general report AND privacy policy.
- Gate evidence/approval references (these requirements cannot be silently waived):

## Before publication

- [ ] Unique version, clean reviewed source, matching changelog AND release description.
- [ ] README, EN/PL instructions/offline mirrors and hardware requirements match actual package.
- [ ] Licenses/notices/dependency and asset attribution match actual package; no project comments
      masquerade as license terms. No unapproved translation/rewrite of original licenses.
- [ ] FIRST RELEASE: owner has approved the general cybersecurity report AND privacy policy;
      approval/version/source references recorded. Later releases review changes against that baseline.
      Private reports are not copied to Git before owner approval. Framework mapping is separate.
- [ ] Privacy/security description matches changes; open findings and accepted limitations recorded.
- [ ] Relevant static/unit/integration/dependency/security and native lifecycle checks have evidence.
- [ ] Full profile export/import/transfer scenario: available Windows/WSL pair, dictionaries/palettes,
      missing media/paths, idempotent import, credential/consent exclusion, paused queue. Record
      exact tested scope or owner-approved exception; do not label unavailable scope PASS.
- [ ] Actual browser200% zoom: navigation, dialogs, queue, review, LEFT player and focus/scroll.
- [ ] Native/package manifests, committed payload, versions, final sizes and all hashes verified.
- [ ] Actual final distributed bytes have verified attestations; expected repository/workflow/
      commit/digest checked. REL-01 MUST be implemented before first release; no missing pass inferred.
- [ ] Unsigned/signed status, relevant warnings and verification steps are accurate and visible.
- [ ] Bootstrap URLs and embedded hashes prepared for this exact immutable public version.
- [ ] Versioned releases/ metadata links to the actual Release assets; retention/archival follows the accepted design.
- [ ] Owner explicitly approves publication after reviewing the complete candidate/evidence.

## After publication

- [ ] Public version/tag/assets match the approved candidate; no asset was replaced in place.
- [ ] Independent actual downloads match hashes, provenance and manifests.
- [ ] Windows/Ubuntu bootstrap URLs retrieve the intended version and exact payload.
- [ ] Release notes, latest/versioned download links and repo index are correct.
- [ ] Required GitHub Pages site links the latest installer/Releases/privacy/verification once deployed;
      first-site deployment follows first release under the current owner sequence.
- [ ] Required content-free evidence retained independently of7-day CI expiry; previous versions intact.

## Recorded limits

- Physical AMD/other NVIDIA: unavailable; no tests currently planned. Do not silently add a gate.
- Corpus accuracy: deferred pending suitable annotated material, no scheduled campaign.
- Artist package → integration/test → illustrated documentation; no release-blocking dependency.
- Actual failures, owner-accepted exceptions, remediation owner and follow-up IDs:
