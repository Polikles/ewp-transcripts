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
      ordinary Git's 100 MiB file limit. Record Release-assets/index proposal; storage decision open.
- [ ] **SEC-01:** General cybersecurity/privacy review, first in English, LOCAL OUTSIDE GIT.
      Map actual code/data flows, storage/retention/deletion, media/transcripts, temporary files,
      secrets in memory/OS stores/environment/IPC/network, consent, logs, reports, providers,
      native/browser/CLI, installer/downloads and CI. Findings, threats, tradeoffs and evidence.
      Owner reviews/approves before any report is published under docs/security/.
- [ ] **SEC-02:** After the general report, research applicable frameworks, then create a separate
      local EN mapping. Include ISO 27001/42001 and GDPR; assess other candidates, applicability,
      scope/roles and exclusions first. Do not claim certification or legal compliance.
- [ ] **PRIV-01:** Draft a complete factual privacy policy from the inventory/review; resolve owner
      identity/contact and provider roles. Review before publishing/linking it in docs/app/site.
- [ ] **REL-01:** Implement and verify artifact attestations early, preferably for the first release.
      Attest actual final distributed bytes, verify repository/workflow/commit/digests, retain
      provenance bundles and verification instructions. No Authenticode/SmartScreen equivalence.
      Add narrowly scoped OIDC/attestation permissions; keep zero paid budgets/public runners.
- [ ] **INST-01:** Implement startup discovery and quick-update/other-actions entry screen.
      Older installed version → Quick update; same → Repair/reinstall; newer → linked Download
      newer installer. Preserve full maintenance actions, safe roots, work and model identities.
      Resolve first-release timing and multiple-installation selection; no automatic mutation.
- [ ] **REL-02:** Resolve releases/ storage; retain at least 2–3 downloadable versions, define older
      archival without silently breaking bootstrap URLs/checksums/provenance. Proposal: GitHub
      Release assets plus versioned metadata/links/checksums in releases/, rather than large Git blobs.
- [ ] **REL-03:** Choose public version/scope, build and execute the per-version
      [release checklist](docs/RELEASE_CHECKLIST.md), including changelog/release notes and package-
      matched README/instructions/hardware/licenses/notices. Record owner publication approval.
- [ ] **REL-04:** Publish deliberately, then verify actual downloads, hashes, attestations and
      Windows/Ubuntu bootstrap targets. This plan revision does not publish/deploy anything.
- [ ] **WEB-01:** Required GitHub Pages project site linked from repo and linking latest installer,
      versioned Releases, verification, hardware and privacy information. Latest owner sequence:
      immediately AFTER first release; prepare content earlier. Public-site requirement retained.

Whether SEC-01/PRIV-01, attestations and INST-01 are mandatory first-release gates is an explicit
owner decision, not an invented approval requirement. See roadmap open decisions and local questions.

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

- [ ] Artist assets/feedback → integration → interface regression/owner review → complete illustrated
      EN/PL manuals/screenshots. This is the only current artwork dependency; no release blocker.
- [ ] **STORE-01:** Research and plan an independent MSIX/Microsoft Store channel for a solo
      individual developer: identity, Microsoft signing, Store-managed updates, model wizard,
      package/state/model paths, executable dependencies, CLI access and EXE↔Store coexistence.
      Proposed hardware tiers and unresolved 6–8 GB/older-generation cases are in MSIX_STORE_PLAN.
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
