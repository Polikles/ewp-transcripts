# Package B agreements and execution plan

Execution update: owner now explicitly authorizes B5–B9 to completion. This planning record's
earlier no-start wording is historical; use [the execution checkpoint](2026-11-21-package-b-execution.md).

Date: 2026-11-21. Initial baseline: clean main 56f597e. Owner-decision update baseline:
clean main b97422b. Planning only; no B feature implementation or live ASR requests in this turn.
Authoritative scope/order stays in [the roadmap](../99-roadmap-v2.md); this checkpoint records
the execution detail and accepted decisions for the current owner request.

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
The owner requires one OpenRouter credential shared by ASR, correction and translation, with
independent model choices for each operation; do not create a second ASR-only key requirement.
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

Owner decisions accepted 2026-11-21:

- Provider: **OpenRouter**, reusing the same OpenRouter API key for ASR, LLM correction and
  translation. Local ASR remains the startup/default processing path.
- An ordinary ASR model dropdown, like correction/translation selection, offers these exact IDs:
  `openai/whisper-large-v3`, `openai/whisper-large-v3-turbo`, `elevenlabs/scribe-v2`,
  `microsoft/mai-transcribe-2`. The Whisper pair is the initial primary path; Scribe/MAI are
  additional functional comparison choices. This does not reopen a general model catalog,
  favorites or local model-management scope.
- Owner permits short representative excerpts/short episodes from the supplied podcast and
  English recordings: PL with two speakers and EN with one. The collection is approximately
  nine podcast hours plus several English hours; it is available material, not a processing
  mandate. Locate/verify accessible files at B8a; do not claim they are already present or send
  the whole corpus. If required examples are absent, request only the missing material.
- Total live cloud-ASR test budget: **USD 2**, across all models, calls and retries. Earlier LLM
  spending is separate. Tests establish feasibility, canonical structure, timing/speaker mapping
  and downstream correction/export compatibility; no model accuracy ranking/WER campaign.
- Authorization persists for these B8a tests within the stated source/provider/budget scope.
  Do not ask for the same permission again. First run model-free tests; reserve/check costs
  before live requests, count actual usage/cost and any uncertain charges conservatively, and
  stop before the remaining allowance is exhausted. Do not assume every error is unbilled or
  multiply the budget by the number of models. A larger scope/budget needs a new owner decision.

Public documentation check (2026-11-21): OpenRouter lists all four exact model IDs. Its
[speech-to-text guide](https://openrouter.ai/docs/guides/overview/multimodal/stt) describes a
separate `/api/v1/audio/transcriptions` endpoint authenticated by an OpenRouter bearer key,
structured `verbose_json`, requested word/segment timestamps and provider-specific speaker
options. Field availability differs across providers/models: listing is not integration
qualification. Verify the returned structure at B8a; never fabricate timing/speaker identity.
The four public model pages were checked without authentication or uploading audio:
[Whisper V3](https://openrouter.ai/openai/whisper-large-v3),
[Whisper V3 Turbo](https://openrouter.ai/openai/whisper-large-v3-turbo),
[Scribe v2](https://openrouter.ai/elevenlabs/scribe-v2),
[MAI-Transcribe 2](https://openrouter.ai/microsoft/mai-transcribe-2).
Recheck relevant capability/pricing information immediately before implementation/live tests;
no mutable price is promised from this planning snapshot.

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

## Remaining decisions / execution status

The three owner decisions (provider/model list, permitted material, budget) are resolved above.
No further product-scope question currently blocks B5–B8 or B8a preparation. Concrete capability,
source-file or credential availability issues are checked when their dependent slice begins;
credentials must not be printed or requested in chat. Do not reopen accepted Windows/A decisions.
The request answers planning questions; it does not itself start B product implementation.

## Verification and resume

Only TODO/status/roadmap/checkpoint and work-policy planning documents changed. Check git diff --check, local
Markdown link targets and changed-file scope; no product tests/builds/provider calls needed.
No disposable runtime artifacts or artist-package changes. Next: report the accepted decisions,
then proceed with B5 when the owner authorizes product implementation. The B8a test permission above
is retained for that later slice; no request was sent in this planning turn.

Owner-decision verification PASS: git diff --check, six-file documentation-only scope and 61 local
Markdown link targets. No product tests/builds, key reads,
model downloads, live ASR requests or audio uploads were performed. Source/lockfile/artist ZIP unchanged.
