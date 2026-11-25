# Early local ASR checks and active recording selection — 2026-11-25

Baselineb95533c, delivered0.24.0 source50cb47b. Target0.24.1.
Owner passes three-model mixed local queue. Current feedback supersedes wait: missing optional
models can be planned/staged and fail only inside the ASR adapter after preparation. Model label
runs into next text. Active transcript must be outlined in sidebar and Source review table.
Acceptance: opening TODO; preserve pins/results/accepted mixed inference. Synthetic model-free
regression only, no weights, paid calls or repeated GPU test. Implementation/verification pending.

Implementation: shared lightweight offline snapshot presence/size check drives model badges and
real GUI planning/staging/start/worker guards. Controller/queue accept injected validators because
model-free/custom services remain supported; real LocalGuiServer always supplies require_local_asr.
No ASR imports/hashes/network during planning. Default configured model checked as well as optional
models. Startup validation is atomic: any missing model leaves ALL staged jobs untouched, before
cloud key checks or media preparation. Missing model has dedicated EN/PL GUI_LOCAL_ASR_MODEL_REQUIRED
install/restart/retry guidance; no unrelated dependency-test hint.

Queue model labels display as block with a5.59px observed gap. Sidebar pressed state uses a single
result/identity match rather than OR of possibly stale identities. Open review path drives both
sidebar aria-pressed and stage-item aria-current, refreshed after polling/re-render. Persistent3px
accent outline plus inset stripe and stronger title work in both themes, without layout shifts.

Local gate1175 PASS/12 native skips,17 integrations included, Ruff/format/mypy119 PASS.
Browser13 cases PASS: missing v3/Turbo plan rejected before staging, label separation, four review
switches and sidebar/poll refresh in each light/dark theme. No page errors/external/provider/model
calls. Screenshots inspected. Owner mixed three-model queue acceptance retained; no new inference
campaign. Final HTTP guard tests, native build/artifact qualification and delivery follow.

Final local gate1176 PASS/12 native skips (17 integrations), Ruff/format/mypy119 PASS. Added real
HTTP queue-start test: a removed model leaves restored jobs staged and does not call provider
checks or transcription service. Dedicated GUI staging check runs before preserving picked media.
Focused browser screenshots inspected and selection/spacing verified geometrically. No model pins,
paid calls or actual inference changed. Final source/native package qualification follows.

Final browser14 cases PASS, including actual successful plan followed by synthetic model removal:
direct staging returns GUI_LOCAL_ASR_MODEL_REQUIRED before source preservation and creates no job.
Four-recording review/sidebar selection and polling remain correct in both themes. Local1176 PASS,
12 native skips,17 integrations, Ruff/format/mypy119 PASS. Source8e552126ced7a8a786a1af55319b785d5e8bfc0b.
Native run45678022822 SUCCESS:35 WPF groups/12 Windows cases (31.65s). Artifact source/hash check
and delivery metadata follow. Three focused application screenshots visually inspected. Installer
WPF was unchanged; its native compilation/render/lifecycle regressions still pass for this bundle.

## Final verified delivery

0.24.1 delivered from8e552126ced7a8a786a1af55319b785d5e8bfc0b. Native45678022822 SUCCESS:
35 WPF groups/12 actual Windows cases;1176 local tests/17 integrations, Ruff/format/mypy119 PASS.
Browser14 cases/3 inspected app screenshots PASS: early missing-model errors, post-plan deletion
staging guard, queue label spacing, four-recording selection/sidebar switches/polling in both themes.
Six local hashes and packaged source match CI. Owner mixed three-model local queue PASS retained.
Files: /home/linuch/project-ewp/deliveries/ewp-0.24.1-installers.
Checkpoint: docs/checkpoints/2026-11-25-model-preflight-selection.md and matching evidence JSON.
Next is focused owner early-model/spacing/active-marker feedback; no repeated model/GPU/paid
campaign, no rebuild merely on resume. Models/pins unchanged. Full installer/notices audit,
native app shell and signing/public release/bootstrap remain later. EXE unsigned/internal.

EXE SHA256bc72227f516a2a32fd54db1baefd7ea34be51f55b19022a1736deaa3722749b3.
Two CI archive digests, six product hashes and actual packaged source verified.44 older installer
hashes preserved unchanged. Native installer UI unchanged;3 app screenshots visually inspected.
Evidence is2026-11-25-model-preflight-evidence.json and delivery DELIVERY.json. User checklist:
Instructions/MODEL_PREFLIGHT_SELECTION_RETEST_PL.md / delivery RETEST-PL.md. Browser14 cases and
HTTP/queue tests use synthetic inputs only. No new model downloads/inference/provider calls,
private media, credentials or transcript payloads committed. Disposable cleanup follows.

Cleanup complete: own synthetic server/browser processes stopped and exact /tmp/ewp-model-preflight.EtKp9X removed after retaining delivery evidence. Previous delivery directories untouched.
