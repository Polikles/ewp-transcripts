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
