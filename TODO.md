# Current TODO — owner plan revision, 2026-11-27

Delivered product remains **0.26.2**. This task changes plans and release policy, not runtime,
installer hardware gates or CI execution. The older mandatory-signing rule is superseded:
the first several public releases may be unsigned. Keep signing instructions/keys outside Git.

## Before and around the first public release

- [x] Record owner acceptance of theme/Snap, compressed installer size and NVIDIA preflight/docs.
- [x] Reconcile the revised scope, release policy and local portable plan/questions.
- [x] Check existing privacy documentation: technical requirements/guides exist, but no complete
      maintained user-facing privacy policy was found. Some security prose still needed updating.
- [x] Check GitHub feasibility: public artifact attestations are available; the ~142 MB EXE exceeds
      ordinary Git's 100 MiB file limit. Release assets plus versioned releases/ metadata/links/checksums ACCEPTED by owner.
- [x] Record all six owner decisions: storage accepted; attestations AND approved general report/
      privacy policy are first-release gates; quick update AFTER release; Store cloud-first without
      models; shared EXE/Store tiers with compatible6–8 GB/older NVIDIA experimental; contact approved.
- [ ] **SEC-01 — FIRST-RELEASE GATE:** General cybersecurity/privacy review, first in English, LOCAL OUTSIDE GIT.
      Map actual code/data flows, storage/retention/deletion, media/transcripts, temporary files,
      secrets in memory/OS stores/environment/IPC/network, consent, logs, reports, providers,
      native/browser/CLI, installer/downloads and CI. Findings, threats, tradeoffs and evidence.
      Owner reviews/approves before any report is published under docs/security/.
      Include the DEVELOPMENT VM: PAT versus Deploy Keys/SSH/App/OAuth/MCP per access channel,
      function/identity/scope/storage/revocation, sandbox/OS boundaries and compromise risks/tradeoffs.
      No secret values in evidence; distinguish VM-held and connector/service-held credentials.
- [ ] **PRIV-01 — FIRST-RELEASE GATE:** Draft the factual policy from the inventory/review and obtain
      owner approval before release/publication. Publisher/contact approved in SECURITY_REVIEW_PLAN;
      actual processing/provider roles still need evidence. EN first, PL/public links after review.
- [ ] **REL-01 — FIRST-RELEASE GATE:** Implement AND verify final-artifact attestations before first release.
      Attest actual final distributed bytes, verify repository/workflow/commit/digests, retain
      provenance bundles and verification instructions. No Authenticode/SmartScreen equivalence.
      Add narrowly scoped OIDC/attestation permissions; keep zero paid budgets/public runners.
- [ ] **REL-02:** Implement ACCEPTED storage: actual binaries in GitHub Release assets; versioned
      metadata/links/checksums in releases/. Retain at least2–3 downloadable versions and define
      older archival without breaking bootstrap URLs/checksums/provenance. No LFS needed.
- [ ] **REL-03:** Choose public version/scope, build and execute the per-version
      [release checklist](docs/RELEASE_CHECKLIST.md), including changelog/release notes and package-
      matched README/instructions/hardware/licenses/notices. Record owner publication approval.
- [ ] **REL-04:** Publish deliberately, then verify actual downloads, hashes, attestations and
      Windows/Ubuntu bootstrap targets. This plan revision does not publish/deploy anything.
- [ ] **WEB-01:** Required GitHub Pages project site linked from repo and linking latest installer,
      versioned Releases, verification, hardware and privacy information. Latest owner sequence:
      immediately AFTER first release; prepare content earlier. Public-site requirement retained.

Confirmed first-release gates: verified attestations AND owner approval of the general report and
privacy policy, alongside normal per-version release checks. Quick update is AFTER first release.
Framework mapping follows the general report and is not an additional first-release gate.
Next: SEC-01/PRIV-01 review and REL-01 implementation; no new owner policy decision is pending.

## Every subsequent release

- [ ] Version-specific changelog AND release description, complete documentation/package consistency
      checks and durable evidence under RELEASE_POLICY/RELEASE_CHECKLIST; do not overwrite releases.
- [ ] Full profile export/import/transfer scenario (including Windows/WSL as available); preserve
      absent-media/path, dictionary/palette, credential/consent exclusions and paused queue semantics.
- [ ] Actual browser 200% zoom scenario; verify navigation, dialogs, queue, review and LEFT player.
- [ ] Maintain attestations, hashes, actual download checks and Pages latest links once implemented.
- [ ] Automate machine-checkable release gates and record manual approvals/exceptions; the checklist
      is formalized, but new CI enforcement is still an implementation task, not an existing pass.

## Independent work / post-release backlog

- [ ] **INST-01 — AFTER FIRST RELEASE:** Implement startup discovery and quick-update/other-actions entry screen.
      Older installed version → Quick update; same → Repair/reinstall; newer → linked Download
      newer installer. Preserve full maintenance actions, safe roots, work and model identities.
      Select the target safely when multiple roots exist; no automatic mutation.
- [ ] **SEC-02:** After the general report, research applicable frameworks and create a separate
      local EN mapping (ISO27001/42001, GDPR and selected candidates). Owner review before publishing;
      no claim of certification/legal compliance and no added first-release gate.
- [ ] Artist assets/feedback → integration → interface regression/owner review → complete illustrated
      EN/PL manuals/screenshots. This is the only current artwork dependency; no release blocker.
- [ ] **STORE-01:** Research and plan an independent MSIX/Microsoft Store channel for a solo
      individual developer: identity, Microsoft signing, Store-managed updates, model wizard,
      package/state/model paths, executable dependencies, CLI access and EXE↔Store coexistence.
      Initial Store package has NO speech models: cloud ASR/optional cloud correction first, with
      a Settings local-model wizard on qualifying hardware. Shared EXE/Store tiers are agreed in HARDWARE.
- [ ] **HWPOL-01:** Implement the agreed shared EXE/Store/model-wizard classification: unsupported
      runtime or <6 GB cannot use local; compatible6–<8 GB, older NVIDIA and AMD are experimental;
      compatible RTX30xx+8–<12 GB experimental,12+ GB expected. Test metadata/boundaries/cloud fallback
      without claiming physical qualification. This planning task does not modify0.26.2 hardware gates.
- [ ] Ollama/further local API adapters; existing LM Studio/OpenRouter remain delivered.
- [ ] Alignment/timing refinements; no manual timing editor.
- [ ] Core CLI content-aware directory discovery (FR-A05/ADR-0017), followed by a mandatory CLI/
      pipeline documentation review. Installed distribution MUST retain usable CLI entry points.
- [ ] Advanced channels/crosstalk/surround with source/repetition integrity.
- [ ] Bounded audio diagnostics/normalization and feasible useful dereverberation; no audio-rescue
      subproject. Separate poor-audio attempt mode/button, original/repaired comparison and optional
      controlled composite; export resulting repaired/composite audio as ONE file with provenance.
- [ ] Additional subtitle formats/styling and explicit non-speech authoring. Optional experimental
      sound-detection research/switch (throat clearing, cat meow etc.), documented uncertain accuracy;
      do not promise a high-accuracy Whisper mode or silently infer authoritative semantic events.
- [ ] Reference-material expansion only when suitable material exists; no scheduled quality campaign.
- [ ] Later free OSS signing eligibility (e.g. SignPath), Actions integration with owner approval.
      Check solo-maintainer/package-license eligibility, no paid certificate commitment.

## Unavailable hardware and deferred validation — at the end of the list

- AMD physical GPU and other/lower-VRAM NVIDIA configurations: owner has no test hardware and
  currently plans no tests. Experimental/untested labels remain; no mandatory campaign.
- English/three-plus-speaker/timestamp/diarization quality: deferred until suitable annotated
  material exists; no scheduled date (ADR-0014).

## Removed

Word/phrase and whole-block playback highlighting; separate less-technical-user test stage;
comparative correction/review-time or human-vs-machine studies, PL↔EN quality benchmark suites,
public-corpus/universal-dictionary research and model/quantization/hardware benchmark automation
(old portable-plan 5.12–5.14); GTX1070/telemetry/legacy runtime; further EXE slimming; local Scribe/MAI.
Other exclusions remain in the roadmap. Artist work and unavailable hardware do not block release.
