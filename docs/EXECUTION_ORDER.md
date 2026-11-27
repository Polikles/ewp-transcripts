# Proposed execution order and responsibility matrix

Owner request2026-11-27: group work before/after first release, distinguish bounded changes from
larger changes, and identify agent work, owner decisions and owner tests. This is a **sequencing
proposal for discussion**, not owner acceptance of a new feature priority or authority to publish.
Scope/gates already agreed in [roadmap](99-roadmap-v2.md), [TODO](../TODO.md) and
[release policy](RELEASE_POLICY.md) stay authoritative. Product0.26.2/runtime/CI are unchanged.

Complexity is a preliminary judgment about change surface, not a promised duration. A small code
change can require serious privacy/audio verification. Analytical work may require substantial
research while making no architectural changes. Do not conflate code completion with physical-GPU,
Store certification, legal compliance or owner approval.

## Responsibility rules

- **Agent:** investigate, prepare concrete drafts/prototypes, implement reversible agreed changes,
  unit/integration/native CI checks within existing authorization, update docs and preserve evidence.
  No repeated approval for already-authorized routine work or already-settled six decisions.
- **Owner decision:** report/privacy approval, residual-risk decisions, feature/design selection
  where options remain, account/identity/secret changes and final external publication. Present a
  reviewable result first. No report publication before its explicit approval.
- **Owner test:** targeted real Windows/audio/workflow acceptance where synthetic tests cannot
  establish the intended outcome. Recommendations below are not new blanket release blockers.
  Do not repeat accepted transcription/UI tests solely because a document was edited.
- Access/account settings that tools cannot inspect are reported unknown or delegated to the owner;
  do not ask for credential values in chat. Hardware not available remains untested/unscheduled.

## A. Before first release — dependencies, not optional feature expansion

| Order / task | Result / dependency | Agent can do | Owner decision / test |
| --- | --- | --- | --- |
| A1 — SEC-01 | General EN security/privacy report LOCAL OUTSIDE GIT; actual source/data flows, secrets, logs, media, native/browser/CLI, installer/CI and DEVELOPMENT VM authentication/permissions. | Code and non-secret configuration/metadata review, bounded checks, evidence/threats/tradeoffs, remediation proposals. Record inaccessible service-side facts honestly. | REQUIRED report review/approval before release or report publication; confirm inaccessible account facts if material. No recording benchmark required. |
| A2 — findings, conditional | Triage A1; repair concrete issues before freezing the final review. Scope depends on findings, not a speculative feature list. | Routine reversible fixes and regressions; split high-impact changes into reviewable proposals. | Accept documented residual risks; approve material behavior changes or credential rotation/revocation/settings changes. Targeted tests only if affected behavior needs real Windows/audio. |
| A3 — PRIV-01 | Local EN policy grounded in A1/A2: what is stored/transferred, where/how long, controls/limitations, owner-approved publisher/contact. | Draft/reconcile with implementation, prepare PL/help links after EN approval. No invented processing roles or retention promises. | REQUIRED policy approval before first release; confirm factual roles/communications as needed. Reading/approval, not an extra user-test campaign. |
| A4 — REL-01 + release enforcement | Production attestations and verifiable final bytes; machine-checkable gates and a deliberate publication path. Can be prepared while A1/A3 are reviewed. | Workflow changes within agreed standard public CI, least permissions, pinned Actions, digest/identity verification, retained provenance, failure-path tests; prepare unpublished release candidate. | Final release approval later; owner acts only for actual inaccessible repo/account settings or additional access not already authorized. No routine transcription retest for a CI-only change. |
| A5 — REL-02 | Accepted storage implemented: actual Release assets plus versioned releases/ notes/hashes/links, retention2–3 versions and non-breaking archival policy. | Prepare index/schema/metadata, candidate asset set and bootstrap hashes/URLs; checks without uploading a public release. | Storage design already approved; only a concrete archive/deletion exception needs a new decision. No manual app test. |
| A6 — REL-03 / candidate freeze | Unique version/source; changelog AND release description; matching README/EN/PL instructions/hardware/licenses/notices; clean build/manifests/hashes, regression results. Include final delta review of A1/A3 after actual CI/fixes. | All preparation/checks; profile-transfer and actual browser200% zoom scenarios to the extent available; record results/limits. Do not claim the old0.26.2 report covers later changed code/permissions automatically. | Focused profile transfer or actual Windows smoke test only for scope unavailable to agent/affected user workflow; accept documented test limitations. No new AMD/other-card campaign. |
| A7 — final review | General report/policy approvals refer to final reviewed source/configuration; candidate includes successful attestations and actual known limits. | Provide a concise approval packet and fix review comments. | REQUIRED approval of general report AND privacy policy; explicit public-release decision on the concrete candidate. Prior planning approval does not itself publish/approve reports. |

**Release boundary — REL-04:** only after A7, publish the approved immutable tag/version/assets,
then independently download and verify bytes/attestations/bootstrap URLs and preserve evidence.
Agent can perform these mechanics after explicit publication authorization; owner need not manually
calculate every hash. If a published-download check fails, repair the delivery through the version/
immutability policy rather than silently replace assets. This is release completion, not an optional
later feature. Early releases remain unsigned. Framework mapping, quick update, Store and artwork
are NOT additional first-release gates.

## B. After release — relatively bounded product/documentation changes

This is the proposed order within this group, subject to owner prioritization. Each chosen product
change still receives relevant tests and per-version release checks. Bounded does not mean trivial.

| Order / task | Expected change surface | Agent can do | Owner decision / test |
| --- | --- | --- | --- |
| B1 — WEB-01 | Small static GitHub Pages site; immediately after first release. Repo/latest/versioned downloads, privacy/hardware/verification links; minimal app impact. | Prepare page, bilingual content as selected, link/version checks and deployment draft. | Review concrete page and approve actual publication/settings if not already authorized; optional visual review, no ASR retest. |
| B2 — INST-01 | Small/medium: version-aware startup entry using existing update/repair machinery, safe target selection and Other actions. Explicitly after first release. | Code/UI/fixture tests for older/same/newer/multiple/missing install, native packaging tests and docs. | Recommended short Windows check of real existing-install Quick update/Repair behavior; no full transcription suite if runtime/models unchanged. |
| B3 — HWPOL-01 | Small/medium: shared classification/reasons for EXE and future model wizard; agreed thresholds, no library adaptation. | Centralize rules, boundary/unknown/multi-GPU/cloud-safe tests and EN/PL docs. | Policy already approved. Optional check on existing RTX3090 only; no request for unavailable AMD/6–8 GB/RTX20xx hardware. Synthetic tests do not qualify physical inference. |
| B4 — CLI discovery + documentation | Medium but contained core change: FR-A05/ADR-0017 ffprobe classification/probe reuse, safe skips, recursion/order/path integrity. | Implementation and representative synthetic-media/non-media regressions, installed CLI checks, REQUIRED follow-on CLI/pipeline documentation review. | Optional focused check on a real input folder/planned tool invocation when available; no design approval for already-defined behavior or mandatory whole-GUI retest. |
| B5 — simple audio diagnostics/normalization | Medium bounded FFmpeg/preparation work; preserve source/hash/timeline, opt-in transformed copy, useful warnings. No general restoration project. | Diagnostics/numeric normalization, fixtures, clipping/duration/source-integrity checks and documentation. | Review behavior/controls before exposing the option; targeted listening on an agreed real sample helps confirm usefulness. No human-vs-machine benchmark. |
| B6 — Ollama adapter | Small/medium IF existing provider abstraction is reusable; API/stream/error differences must first be checked. Further unknown adapters are not all assumed equally small. | Compatibility spike, bounded implementation, local/mock protocol/privacy/failure tests, docs. | Choose any needed local model/server settings; focused real local correction check if endpoint/model unavailable to agent. No paid provider campaign. |
| B7 — simple extra subtitle exports | Small/medium for additive ASS/SSA/styled VTT profiles using existing result/cue data; excludes burned-in rendering and a new preview UI. | Format/escaping/determinism/lineage tests, fixtures and docs. | Select desired first format/style and visually check a sample in its target player/platform. No ASR rerun to test export. |

## C. After release — analysis with little product-code impact

These tasks can be scoped independently of B, not necessarily after every B item. Research effort
is variable; separating research from implementation avoids committing to a large design prematurely.

| Task | Result / prerequisites | Agent can do | Owner decision / test |
| --- | --- | --- | --- |
| C1 — SEC-02 | Applicable-framework register AFTER A1; separate local EN mapping (ISO27001/42001, GDPR, selected other frameworks). No first-release gate. | Primary-source research, roles/scope/evidence/gaps mapping; no automatic certification or legal-compliance claim. | Supply genuinely missing organizational/context facts; review/approve report before publication. No app manual test just to approve the mapping. |
| C2 — STORE-01 feasibility | Independent MSIX/Store route, cloud-first/model-free initial app, writable locations/runtime/dynamic code/CLI/channels/update/privacy/account feasibility. | Code/package inventory, primary-policy research, limited packaging spike/test plan and explicit go/no-go options. | Choose whether to proceed with the concrete design; account eligibility/identity verification stays with owner. No Store submission during research. |
| C3 — free OSS signing research | Eligibility/conditions (e.g. SignPath), solo-maintainer fit, actual package/license constraints and approval mechanism. Deferred from first releases. | Research and prepare private owner instructions/proposal outside Git; no account application or key purchase. | Decide whether/when to apply and provide identity/service actions. No app test for research. Signing mechanics are D9. |
| C4 — dereverberation feasibility | Is a simple practical method worthwhile without broad audio restoration scope? | Evaluate bounded options/dependency/cost/offline/timeline implications and a limited authorized sample. | Listen/decide whether useful enough to implement. If not useful or too invasive, drop/defer it; no mandatory quality study. |

## D. After release — larger or more uncertain product/workflow changes

Proposed internal order follows dependencies, not a promise to implement everything. First select
which track is valuable. Every larger track starts with a concrete design/prototype checkpoint.

| Order / task | Why larger / dependency | Agent can do | Owner decision / test |
| --- | --- | --- | --- |
| D1 — MSIX channel implementation | C2 decision first: package identity, executable/runtime deployment, writable state/models, EXE coexistence/migration and preserved CLI. | Prototype/package/manifest, synthetic/native lifecycle and headless CLI/update/migration tests, docs. | Approve architecture/migration tradeoffs, own developer-account setup/identity; real Windows install/uninstall/CLI acceptance on chosen channel. |
| D2 — Settings local-model wizard | D1 storage/runtime contract + B3 rules; turn installer model functionality into supported in-app download/diagnostics/repair controls. | Reuse backend where safe, progress/cancel/retry/terms/token tests, cache/state/doctor integration, docs. | Approve concrete UI; focused real model install/use test on available supported hardware. No AMD qualification from a download/import pass. |
| D3 — Store publication/autoupdate | D1/D2 and account/certification ready: Store-managed version/update, state/model retention, EXE separation, CLI and package signature path. | Prepare submission/listing/checklist, update scenarios and test evidence; execute specifically authorized submission mechanics. | Owner account access/identity and final Store publication approval; actual Store install and version-to-version update test. Cannot replace Store acceptance with CI fixtures. |
| D4 — alignment/timing refinements | Can change real recognition alignment/seek behavior despite a small diff; canonical timing/lineage boundaries. | Narrow investigation, regression fixtures and tests on available authorized material; preserve original results. | Select actual troublesome cases and review timing/audio where objective references are unavailable. No broad annotated-corpus gate added. |
| D5 — advanced channels/crosstalk/surround | New topology/merge/deduplication decisions, interaction with diarization and legitimate repetitions. | Design, synthetic-channel/media tests, source/timeline/repetition integrity, explicit fallback behavior. | Approve ambiguity/fallback choices and review representative real multichannel audio if available; no arbitrary new dataset campaign. |
| D6 — poor-audio attempt + one-file export | B5 and useful C4 outcome; separate mode/button, original/prepared recognition comparison, controlled composite with edit map and consistent timing/provenance. Confidence alone cannot certify audible quality. | Prototype bounded preparation/comparison, result retention, timeline/edit-map tests, single repaired/composite audio export and docs. | Approve workflow/splice/selection policy; listening and transcript review on actual poor audio are needed to judge utility. Keep both sources/results; no silent destructive merge. |
| D7 — non-speech authoring/styling | Existing timed-event data helps, but creation/edit UI and projection/export/lineage must agree. | Design/prototype, semantic/schema compatibility tests, exports and docs. | Choose necessary controls and review a concrete transcript/export; no need to transcribe again for manual event authoring. |
| D8 — automatic sound detection | Research-heavy: detector/model choice, false positives, animal/throat sounds and possible schema extension, experimental opt-in controls. Separate from manual D7. | Feasibility spike, license/runtime/privacy/resource checks, examples, opt-in/error/projection tests. | Decide go/no-go after samples; provide/listen to representative sounds where available and accept uncertain accuracy. No promised high-accuracy Whisper switch. |
| D9 — optional signing integration | C3 eligibility/service acceptance; provenance before/after signing, CI trust boundary, owner authorization and private key/service management. | Prepare/review workflow integration and exact-artifact verification; keep actual private procedure/keys outside Git. | Owner service/account/identity approval and approval of the concrete build to sign; optional Windows trust check. Not a new first-release gate. |
| D10 — burned-in subtitles / richer preview | More than an additive text exporter: media encoding/render pipeline, UI/playback, dependencies/resources and timeline integrity. | Prototype/render fixtures, failure/progress/source-preservation tests and docs after format selection. | Choose presentation/output expectations and review an actual rendered clip. No need for new ASR merely to judge subtitle rendering. |

D4/D5/D7 need not wait for Store publication if the owner prioritizes them. D6 need not depend on
Store; D8 need not wait for all other optional work. The table is a tractable dependency proposal,
not a rigid queue running every item in numeric order.

## E. Independent dependency, repeating checks and unscheduled work

| Task | Agent can do | Owner / external dependency |
| --- | --- | --- |
| Artist assets → integration/test | Inspect supplied asset/license boundaries, integrate, automated layout/regression checks. | Artist availability (no deadline); owner reviews changed appearance. No release blocker. Complexity depends on actual assets/redesign, not assumed small. |
| Illustrated EN/PL manuals | After accepted artwork/UI, capture stable views, write/synchronize instructions and check links. | Owner final content/appearance review if desired; no separate less-technical-reader test stage. |
| Every-release checks | Changelog/description/docs/hardware/licenses/notices, source/hashes/attestations/downloads, regression record and retention. | Owner approves publication; only targeted user acceptance for changed or inaccessible behavior. |
| Profile transfer and actual200% browser zoom | Add repeatable scenarios and run available automated/native/browser checks at releases. | Focused real profile/Windows–WSL test where unavailable; accept explicit limits rather than invent PASS or impose unavailable hardware. |
| Reference-material expansion | Validate structure/lineage/privacy and process authorized new references when supplied. | Owner decides/provides suitable material and rights/annotations. No date, no removed benchmark program restored. |
| Physical AMD / other NVIDIA | Maintain synthetic rule tests and honest experimental/untested documentation. | No owner hardware; currently NO physical tests planned. Do not schedule or request them as release work. |
| English/3+ speakers/timestamp/diarization quality | Retain existing tools/evidence/ADR-0014 and explicit limitations. | Suitable annotated material unavailable; no scheduled campaign or completion gate. |

## Suggested selection for the next discussion

1. A1/A3 security/privacy drafts; in preparation/parallel A4/A5, then A2 as actual findings warrant.
2. A6 final-source/delta/regression evidence → A7 owner approvals → deliberate release and actual
   download verification. No optional feature work added to the first-release critical path.
3. B1 required Pages immediately after release, then suggested first bounded product batch B2+B3
   (quick update + agreed hardware classification) with one focused Windows review session.
4. Next choose B4 (CLI pipeline readiness) versus C1/C2 (frameworks/Store feasibility); these can
   proceed as independent tracks when useful. They do not require implementing all B features.
5. Select a larger track only after its concrete design/research result. Store D1→D2→D3 is one
   coherent track; audio B5→C4→D6 another. Artist/docs stay independent; unscheduled work stays out.

Group approvals to reduce owner effort: general report/policy review, final release approval,
one targeted installer batch review, then separate Store/audio design decisions only if selected.
No account changes, publication, inference benchmark, paid service or implementation occurs in
this planning task. Next sequencing selection is still the owner's decision.
