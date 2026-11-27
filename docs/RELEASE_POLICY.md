# Release policy

Owner revision: 2026-11-27. Applies to EVERY identifiable public version, not only first release.
See [versioning](VERSIONING.md), [checklist](RELEASE_CHECKLIST.md) and [roadmap](99-roadmap-v2.md).

## Signing and provenance

The first several public releases may be **unsigned**. The former mandatory pre-release signing
rule is withdrawn. State unsigned status plainly in download/release instructions. Do not promise
that Windows trust/reputation prompts disappear or ask users to disable system security.

Prioritize GitHub artifact attestations for production releases early, preferably first release.
An attestation links a digest to build identity; it is not Windows Authenticode, a malware verdict,
or certification. Verification must check the expected repository/workflow/source, not just the
existence of any attestation. Keep the artifact immutable after checksum/provenance generation.
If signing is introduced later, attest final distributed bytes after signing or explicitly link
the transformations and final digests. An attestation for a pre-signing EXE does not cover its
changed signed bytes. Do not publish transcripts, tokens or private report material as provenance.

Later investigate free OSS signing (e.g. SignPath), eligibility of a solo-maintained noncommercial
project, package/license/asset conditions and owner-approved Actions integration. Eligibility is
not guaranteed. Actual signing procedure, owner instructions, keys and credentials stay OUTSIDE Git.
No paid certificate, account application or service authorization follows from this policy alone.

## Per-version obligations

1. Choose a unique version and source commit; preserve schema/model identities separately.
2. Maintain BOTH changelog and release description, including behavior changes, known limits,
   privacy/security changes, unsigned/signed status and migration notes where needed.
3. Verify README, EN/PL instructions/offline help, hardware requirements, licenses AND notices
   against the actual prepared package, its dependencies and bundled assets. Screenshots awaiting
   artist work may be explicitly deferred; text instructions and accurate notices may not be guessed.
4. Run relevant quality, integration, security/dependency and native packaging checks. Record exact
   evidence/limitations and accepted exceptions. Include profile transfer and real browser200% zoom
   in upcoming-release scenarios; unavailable GPU/annotated-corpus campaigns remain unscheduled.
5. Build once from clean reviewed source with pinned tools/dependencies. Verify manifests, packaged
   source, all digests and native startup. Preserve previous published/qualified artifacts.
6. Generate/verify release attestations once implemented; preserve verification instructions and
   retrievable provenance beyond CI artifact expiry. SBOM/dependency inventory evaluation belongs
   in supply-chain work; never claim an SBOM exists until generated and checked.
7. Require an explicit owner release decision with a completed per-version checklist. Prepare a
   concrete reviewable draft before asking to publish. Do not treat a main push as publication.
8. Publish a matching immutable version/tag/assets, then independently download and verify exact
   published bytes, checksums, provenance and Windows/Ubuntu bootstrap URLs.
9. Maintain a versioned releases/ index and, once deployed, Pages latest-download links. Keep at
   least2–3 versions available; agree older archival before removing any public link/asset. Do not
   silently break version-specific bootstrap URLs or overwrite an old release with another build.

## Storage decision

The owner wants releases/ in the repository. Current EXE142200142bytes exceeds ordinary Git's
100 MiB file limit. Proposed design: releases/<version>/ metadata, hashes and links, with actual
EXE and future approved MSIX/DEB assets in GitHub Releases. GitHub documents a per-release-asset
limit below2 GiB and no total release size/bandwidth limit. LFS is an alternative needing explicit
quota/billing review; no LFS setting or budget is enabled by this plan. DEB remains a possible
asset format, not an approved new packaging implementation.

## Enforcement status

This policy and checklist are formalized. Automated production attestation/release gates are
**planned, not implemented** in the existing two-job build/startup workflow. Implement verification
and a manual owner publication gate with least permissions, pinned Actions, existing public-only
standard runners,7-day CI artifact retention and zero paid budgets. Evaluate solo-owner approval
mechanics; do not assume GitHub's prevent-self-review setting permits the owner to approve their
own run. Release assets/provenance must outlive the temporary CI artifact retention.

Open decisions: first-release gating of security-report approval/privacy policy, attestations and
quick update; storage; exact site timing. Latest owner statement places required Pages deployment
after first release. No public deployment is performed by this document change.

Primary sources checked2026-11-27:

- [GitHub large-file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- [GitHub Release assets](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [Attestation generation/permissions](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [Attestation meaning and verification](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- [SignPath Foundation eligibility](https://signpath.org/terms)
