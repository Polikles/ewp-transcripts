# Focused update check — pending work and cloud timing

2026-11-22. Use the existing installation. Favicon, API checking, mixed local/cloud queue and restored
upload-consent blocking are owner-confirmed passes. No reinstall, model download, full four-model
benchmark or repeat installation checks are required.

1. Stop GUI, `git pull`, `uv run --locked transcriber gui`, refresh the page (Ctrl+F5).
   At full width the background artwork continues into both side gutters, in light/dark themes.
   In the key dialog, Use saved key activates it immediately. Set session key is disabled with
   empty input, enabled after typing and disabled again after clearing it.
2. Choose a test output directory and two tracks from one episode. Plan, then Save work **before
   Add to queue**. Confirm the displayed Saved work file path. Restart/load: the name fills its
   field, old validation clears, two files and their input path return, and metadata is replanned.
   Plan approval remains unchecked. Select those same files again: still two files/one episode.
   Review/confirm the plan, then Add to queue should work without a native required-input error.
3. Existing workspace names are readonly. Select Save as a new workspace, give a different name
   and Save: two separate entries/manifests remain. Background list refresh must not undo the choice.
   A selected older save may live in the private catalog; its displayed path explains why it is
   absent from an output-folder ZIP. Save as new with blank optional catalog creates an output-root copy.
4. Load a saved queue with completed and failed/cancelled work. Also check a snapshot saved before
   an attempt later failed/cancelled: its retained matching failure state restores the inactive row.
   All rows should return, no ASR starts automatically, and retry remains explicit. Do not delete
   failure JSON files. Media/final artifacts and prior exports remain intact.
5. One cloud follow-up is enough: use the previously failing s0e01 tracks with Whisper Large,
   deliberately grant upload consent and start. The complete result should include real word times
   and open in source review/export. Do not repeat already passed local ASR or all four cloud models.
   If Scribe still fails, send the new technical details (`cloud_response` model/chunk/counts) and
   the affected content-free usage-ledger entry. Do not send keys or full transcripts.
6. Clearing browser/current workflow state may leave the server-session key available; that is
   intentional. Report commit, Windows/WSL, action and expected/actual behavior for any new defect.

Full B acceptance and terminology review remain separate. After functions settle, the agent prepares
one local editable field/message-ID + EN/PL table; owner can correct both languages. Applied/approved
version becomes the repository reference, followed by consistent EN/PL manuals. The artist ZIP stays
frozen. [Deferred installation/removal checks](INSTALLER_QUALIFICATION_PLAN.md).
