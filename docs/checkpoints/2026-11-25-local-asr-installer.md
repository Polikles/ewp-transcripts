# Installer and optional local ASR — 2026-11-25

Baseline96cb2af, delivered0.23.2. Current owner request supersedes previous wait.
Scope and acceptance: opening TODO. Target0.24.0. Private report remains outside Git.
Owner confirms uninstall with running app PASS. Report0.23.2 installation/OS-key save completes;
Xet fallback notices incorrectly occupy activityProgress via generic stage=log.

Implementation/verification in progress. Preserve existing pins; new optional snapshots pinned
separately, explicit downloads only. No new paid-provider calls or media upload authorization.
Local Whisper v3/v3-turbo feasible using existing WhisperX/CTranslate2 backend. Scribe/MAI public
local weights not established; primary-source feasibility findings to be recorded before delivery.

## Feasibility and sources (2026-11-25)

Public Hugging Face metadata read only (no model weights downloaded):
https://huggingface.co/api/models/Systran/faster-whisper-large-v3?blobs=true
revision edaa852ec7e145841d8ffdb056a99866b5f0a478, MIT, 3090839273 bytes.
https://huggingface.co/api/models/dropbox-dash/faster-whisper-large-v3-turbo?blobs=true
revision 0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf, MIT, 1621668947 bytes.
The previous mobiuslabsgmbh repository redirects to dropbox-dash; use canonical pinned identity.
CTranslate2-compatible conversion; existing WhisperX load_model accepts a local snapshot directory.
https://elevenlabs.io/docs/overview/models describes Scribe as a hosted API model.
https://microsoft.ai/models/mai-transcribe-2/ and
https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe describe hosted
access. Public desktop-downloadable weights/license for these exact models not established;
no fabricated local checkboxes, unrelated substitutes or third-party credentials added.
Full local/cloud exact-model parity is therefore limited to publicly available Whisper weights.
No additional provider cost or media upload; previous spend remains USD0.0291461230985028369.

Local gate PASS1163 tests/12 native skips (17 integrations), Ruff/format/mypy119 files.
Credential tests cover saved/session/environment/typed precedence, unavailable storage, check failure,
CSRF and no secret in replies. Optional selection tested through setup argument dispatch, installer
ownership/defaults, configured custom target mapping and actual queue-to-service configuration.
Browser/native tests and immutable artifacts pending. No model inference/GPU success claimed.
