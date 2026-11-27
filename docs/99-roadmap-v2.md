# Current roadmap — owner revision, 2026-11-27

<a id="current-next-actions--2026-11-26"></a>
<a id="owner-scope-and-current-status--2026-11-20"></a>
<a id="accepted-package-sequence--package-a-authorized"></a>

This is the selected scope. [TODO](../TODO.md) holds actionable IDs; [status](../WORK_STATUS.md)
retains delivered evidence. The latest owner decisions supersede older signing, site, highlighting
and research proposals. [Historical snapshots](../archive/project-status/inventory.json) remain
unchanged; do not replay their NEXT instructions or cancelled obligations.

For the proposed order and per-task autonomy/owner-approval/manual-test split, see
[execution order and responsibilities](EXECUTION_ORDER.md). That proposal helps the owner select
post-release priorities; the accepted scope and first-release gates below do not change.

## Delivered foundation

<a id="13-gui"></a>

Product **0.26.2** is internally delivered and qualified. Canonical JSON/immutable lineage,
local/cloud ASR, mixed local-model queues, correction/translation/dictionaries, source review,
verified exports, autosave/recovery, EN/PL offline guides, managed installer lifecycle and native
Windows WPF/WebView2 are implemented. Owner accepts Personalization/closing, LEFT/RIGHT Snap,
startup/closing theme and ~142 MB compressed EXE. The player remains in the LEFT sidebar.

NVIDIA architecture/driver/VRAM preflight and the previous documentation audit passed. Current
runtime guidance stays [12+ GB compatible NVIDIA](HARDWARE.md), with cloud recommendation below
that capacity; this planning revision does not change library/model pins or existing hardware gates.
AMD Windows ASR remains experimental/physically untested; alignment/diarization use CPU.

## Release preparation and sequence

| Stage / ID | Work / dependency |
| --- | --- |
| SEC-01 | FIRST-RELEASE GATE: general code-grounded security/privacy report including DEV VM access/authentication/permissions and compromise tradeoffs, EN, LOCAL OUTSIDE GIT first; owner approval required before release/publication. |
| SEC-02 | After general report: applicability research and separate local EN framework mapping; not an additional first-release gate. |
| PRIV-01 | FIRST-RELEASE GATE: prepare factual privacy policy, obtain owner approval. Publisher/contact approved; actual processing roles need review. |
| REL-01 | FIRST-RELEASE GATE: implement and verify final-byte artifact attestations, with limited permissions and no Windows-signature claim. |
| INST-01 | Existing-install quick entry: older → Quick update; same → Repair/reinstall; newer → linked newer installer; Other actions always available. AFTER first release; safely select target if multiple roots exist. |
| REL-02 | Implement ACCEPTED GitHub Release assets plus versioned releases/ metadata/links/checksums; no large EXE Git blobs or LFS. Preserve 2–3 versions, decide older archival. |
| REL-03 | Final version/source/package, changelog and release description, matching docs/hardware/licenses/notices, per-version checklist and owner publication decision. |
| REL-04 | Deliberate first public release, then actual download/bootstrap/hash/provenance verification. |
| WEB-01 | Required GitHub Pages site AFTER first release per the owner's final sequencing statement; prepare earlier, link repository/latest installer/versioned Releases and privacy/verification information. |
| Parallel | Artist assets → integrate → test interface changes → complete illustrated EN/PL documentation. No deadline; does not block release. |
| Later | Independent MSIX/Store distribution and the bounded feature backlog below. |

**Signing is deferred. The first several public releases may be unsigned.** State this clearly in
release/download instructions; no Authenticode/SmartScreen guarantee. Future free OSS signing
(e.g. SignPath) needs eligibility/licensing review and owner-approved Actions signing. Actual signing
procedure/private instructions/keys stay outside Git. Do not buy a certificate or apply to a service
on the owner's behalf merely because it appears in this plan.

Follow [release policy](RELEASE_POLICY.md) and [per-version checklist](RELEASE_CHECKLIST.md).
Formal rules are now documented; new automated release/attestation enforcement is not yet implemented.
Current CI remains its two standard public jobs; zero paid budgets and 7-day artifact retention stay.

## Post-release scope — unassigned feature versions

| Topic | Retained scope / boundary |
| --- | --- |
| STORE-01: MSIX / Microsoft Store | Independent distribution in addition to EXE; solo individual account, Store signing/update delivery, optional local-model wizard and separate cloud/local hardware listing. [Research plan](MSIX_STORE_PLAN.md); no Store publication yet. |
| HWPOL-01: shared hardware policy | Implement owner-approved EXE AND Store tiers in HARDWARE.md; compatible6–<8 GB/older NVIDIA experimental, no physical qualification claim. |
| INST-01: quick update | AFTER first release, implement the version-aware entry described above. |
| Ollama/local API adapters | Retain optional Ollama expansion. LM Studio/OpenRouter already exist. |
| Alignment/timing | Focused improvements only; no manual timing override editor. |
| Core CLI directory discovery | FR-A05/ADR-0017: content-based ffprobe discovery, safe non-media skips/probe reuse. Follow with documentation/CLI pipeline review. The installed app must continue to expose CLI usage. |
| Advanced channels | Crosstalk/deduplication, explicit channel/speaker topology and surround; preserve legitimate repetitions and sources. |
| Bounded audio preparation | Diagnose likely problems, normalize loudness, investigate practical useful dereverberation. Simple preparation, not a general restoration project. |
| Poor-audio attempt mode | Separate mode/button for automated original/prepared comparison, optional controlled readable-fragment composite, both canonical results/provenance retained, repaired/composite audio export as ONE file. Design timeline/edit map and review before merging fragments. |
| Extra subtitle formats | Additional formats/styling/authoring/platform presets and preview; existing TXT/SRT/VTT/YTT/HTML remain delivered. No bilingual HTML requirement. |
| Non-speech authoring / optional sound detection | Existing timed-event foundation plus authoring/styling. Research a separate opt-in experimental switch for throat clearing, animal sounds etc.; document uncertain accuracy/false positives. Evaluate detector/models/schema changes rather than promise a high-accuracy Whisper switch. |
| Reference material | Retain later expansion when useful annotated material exists; no scheduled benchmark/human comparison program. |
| Free OSS code signing | Later research into SignPath or other free eligibility, project credibility, solo-owner approval and Actions integration; no signing gate for early releases. |

## Release regression scenarios and explicitly unavailable validation

- Starting with upcoming releases, include full profile transfer (Windows/WSL where available)
  and real browser 200% zoom in release scenarios. They are implemented/unqualified checks, not
  new feature projects. Record exact results and owner-accepted exceptions, not invented passes.
- Physical AMD and other/lower-VRAM NVIDIA: no owner hardware available, no tests currently planned;
  retain at the end of TODO with experimental/untested labels.
- English, three-plus speakers, timestamp and DER/JER accuracy: ADR-0014 deferral until suitable
  annotated material exists, with no scheduled date or mandatory benchmark campaign.

## Removed / outside scope

- Old portable plan5.2: ALL optional word/phrase highlighting removed; whole-block following remains removed.
- Old5.4: separate less-technical-user testing stage removed; ordinary current feedback continues.
- Old5.12–5.14: comparative/human-vs-machine/review-time studies, dedicated translation-quality suites,
  public-corpus/general-dictionary studies and model/quantization/hardware benchmark automation removed.
- GTX1070 tests/collectors/legacy runtime; further EXE slimming/minimal downloader; local Scribe/MAI.
- Docker, bilingual HTML, additional editorial/LLM punctuation modes, speaker-count research,
  full model catalog/favorites/loading management, manual timing overrides, alternate translation
  chunking, owned input snapshots and unselected scheduling/auto-maintenance.
- Voice biometrics/cloning datasets, clock-drift correction and distributed/multi-GPU processing.

## Owner answers — all six decisions settled

1. Storage ACCEPTED: actual binaries as GitHub Release assets; releases/ metadata/links/checksums.
2. Verified attestations AND approved general cybersecurity report/privacy policy before first
   release; quick update AFTER first release. Framework mapping is subsequent, not a new gate.
3. Store begins model-free/cloud-first (ASR and optional cloud correction), then Settings wizard
   adds local models on qualifying hardware, with explicit keys/consent/model terms.
4. Shared hardware categories apply to BOTH EXE and Store/model wizard.
5. Compatible6–<8 GB and older compatible NVIDIA (e.g. RTX20xx) are experimental: may or may not work.
   Unsupported kernels/driver/architecture remain unsupported; capacity alone does not fix them.
6. Publisher/privacy/security contact: Damian Szczęch, szczech.dam+transcripts@gmail.com. Do not
   silently replace separate licensing contacts or infer legal data-processing roles from this label.

Required Pages remains AFTER first release. No new policy answer is needed before starting
SEC-01/PRIV-01 and REL-01. Those tasks are still pending; this revision does not implement or approve
them, change current0.26.2 binaries/hardware gates, or publish a release/report/site.

## Historical identifiers

R01/R03 B7 delivered; R02/R08 B8 delivered with FR-A05 deferral; R04 cloud delivered; R05/R06 removed;
R07/R09/R10 retained within bounded channels/audio/subtitle work; R11 authoring optional, HTML base
delivered, bilingual removed; R12 native delivered; R13 distribution delivered, public release pending,
Store research added, Docker removed; R14 selected cleanup/aliases delivered, extra scheduling removed;
R15 artist independent, GH Pages now required. E01/E02/E06/E09 delivered; E03/E04/E07 outside scope;
E05 Ollama later; E08/E10 removed; E11 timing retained; E12 separate reader stage removed; E13 highlighting removed.
