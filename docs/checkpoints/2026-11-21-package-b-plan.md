# Package B agreements and execution plan

Date: 2026-11-21. Baseline: clean main 56f597e. Planning only; no B feature implementation.
Authoritative scope/order stays in [the roadmap](../99-roadmap-v2.md); this checkpoint records
the execution detail and unanswered decisions for the current owner request.

## Confirmed agreements

- Package A is closed/owner accepted, including its final no-retest source-review adjustment.
- Target: Windows 11 x64. Agent implements and checks on this Linux VM, then pushes to GitHub.
  Owner pulls and executes native Windows tests. WSL remains supported and its accepted behavior
  must be preserved. Agent Linux checks do not qualify native Windows/GPU execution.
- Use the same application/canonical data/frontend on Windows and WSL. Preserve immutable
  source/revision/translation/export lineage and explicit manual publication verification.
- Deliver B5, B6, B7, B8, B8a, B9 in that order. Each slice gets updated TODO/checkpoint evidence,
  relevant automatic checks and a reviewable commit/push. Full owner Win/WSL workflow acceptance
  follows B9, then fixes/retest until accepted and feature freeze.
- Complete editable EN–PL terminology approval is task 10 after B acceptance, followed by the
  full English/Polish manuals. Keep only necessary changed-step/setup instructions current now.
  Artist icons remain independent/non-blocking; sent ZIP/demo is frozen. Final installer/release
  distribution remains later task 12; B5 still needs a reproducible native dependency/setup path.

## Sequential work and completion criteria

### B5 — Native Windows

Audit the full native dependency/lock/media/model chain before changing platform configuration.
The current pyproject.toml explicitly limits uv environments to Linux x86_64; lifting that alone
does not establish native support. Check the existing speech-stack pins and native runtime
requirements, paths, model/cache setup, process invocation and repair/doctor behavior. Preserve
the qualified WSL setup; isolate any necessary platform difference and verify it explicitly.

Provide reproducible repository-based Windows setup/launch instructions and the required setup
support. Verify CLI/help, GUI launch, local dependency diagnostics, user-space paths (including
spaces/PL characters), media/model access and file dialogs. Avoid speculative GUI redesign.
Record what is model-free/VM checked and what requires the owner's Windows machine. An early
small native launch probe may be needed to resolve Windows-only failures; the full workflow
checklist still belongs after B9.

### B6 — Optional OS credential storage

Add deliberate save/use/remove for provider API keys using an available OS credential store.
Keep session-only operation and an honest fallback when secure storage is unavailable in WSL.
Do not export keys into profiles/workspaces/artifacts/logs or persist them in browser storage.
Verify restart reuse, removal, unavailable-store behavior and existing session-key handling.

### B7 — Project/profile conveniences

Add recent projects/sessions, named input/output roots and scanning a selected directory for
strictly validated canonical results, with explicit selection of items to add to later queues.
Do not start ASR/providers on discovery. Add profile export with or without embedded dictionaries;
verify complete profile/dictionary exchange between Windows and WSL, making missing or different
platform paths explicit rather than guessing replacements. Retain draft/revision identity.

### B8 — Media selection and recording identities

Add explicit audio-stream selection for media with multiple audio streams, remaining appropriate
native file/directory picker handoffs (direct entry fallback where necessary), content-aware
recognition and visible distinct identities for same-name recordings. Preserve synchronized
multi-file episode grouping and exact staged-source checks. Verify wrong extensions, malformed
inputs, ambiguous streams and name collisions without overwriting another recording's artifacts.
Advanced channel editing, denoising and subtitle timing authoring stay outside this package.

### B8a — Optional cloud ASR

Before provider-specific implementation, settle the initial provider/model, permitted test media
and spending boundary. Research current official provider capabilities/limits/pricing then;
none is chosen or qualified by this planning record. No upload/paid call is authorized now.

Add a bounded adapter producing the existing canonical contract, explicitly recording source
identity, provider/model, usage/cost where available, disclosure consent and failures. Preserve
local ASR as the default and manual review/export gates. Verify response/timing/speaker mapping,
errors/cancellation/retry behavior and workflow integration using mocks first, then only explicitly
authorized representative live tests. Missing required canonical data must fail visibly rather
than being fabricated. Do not claim provider support from a synthetic response.

### B9 — Integrated qualification and handoff

Run relevant static/unit/integration/browser/package regression. Prepare one concrete owner
checklist for native Windows 11 x64 and WSL: setup/doctor/launch; audio/video/grouped ASR; queue
cancel/retry/restart; optional correction; manual review/source export; translation/review/export;
credential persistence/removal; profiles/dictionaries; project/media convenience features;
cleanup and version-bound downloads. Cloud live cases require the agreed material/budget.
Retain already accepted evidence, while checking the complete integrated package for regressions.
Owner executes full Win/WSL workflow; fix/retest until accepted, then freeze functionality and
proceed to task 10.

## Questions for the owner — before B8a, not blockers for B5–B8

1. Is there a preferred cloud ASR provider/model or existing account, or should the agent research
   and propose a short comparison before implementation?
2. Which recordings/excerpts may be sent to that provider for testing (language, duration and
   single-/multiple-speaker examples)? Permission for earlier LLM workflows is not ASR permission.
3. What currency and total spending cap apply to live ASR qualification? Limit implementation
   calls to mocks until the scope/cap and provider choice are explicitly agreed.

No additional owner product decision is currently needed for the already selected B5–B8 scope.
Routine implementation details belong to the agent, with new concrete incompatibilities reported
when found. Provider choices do not block the earlier slices. Do not infer authorization to start
B implementation merely from this request to describe the plan.

## Verification and resume

Only TODO/status/roadmap/checkpoint planning documents changed. Check git diff --check, local
Markdown link targets and changed-file scope; no product tests/builds/provider calls needed.
No disposable runtime artifacts or artist-package changes. Next: present this plan/questions,
record replies and proceed with B5 when the owner authorizes product implementation.

Planning verification PASS: git diff --check, four-file planning-only scope and 61 local Markdown
link targets. No product tests/builds were run; the source, lockfile and artist ZIP are unchanged.
