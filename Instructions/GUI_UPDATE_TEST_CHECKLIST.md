# Focused update check — saved locations and pre-start key validation

Owner acceptance update 2026-11-22: focused checks passed. The final unique-save-name and key-feedback
polish requires automatic verification only; no further owner retest. Next is the local EN/PL
workbook review. The checklist below is retained as historical test detail.

2026-11-22. Use the existing installation: stop GUI, `git pull`,
`uv run --locked transcriber gui`, refresh the page (Ctrl+F5). No reinstall or model downloads.
The owner already confirms output-folder save/load, successful cloud ASR after key activation,
subtitle export and correct workflow status. Keep those passes; another paid transcription is
not required for these changes. Old failed/cancelled recovery was not repeated by the owner
because the old files are gone; retain the existing automated evidence.

1. Choose output and (optionally) a separate saved-work directory, then save a named workspace.
   Its displayed file path should start with that name, e.g. `Podcast--<UUID>.workspace.json`.
   Save as new creates another file/identity; saving the selected entry updates that entry.
   Earlier UUID-only saves should still load and get a readable filename when saved again.
2. Restart server and browser. Output/catalog fields and the saved-work list should return
   without reselecting directories or clicking Refresh. Loading remains an explicit action;
   no transcription starts and upload consent is unchecked. Unavailable directories are ignored.
3. In Manage OpenRouter key, check short session/save/use labels. Save key and Use saved key share
   one row; Remove saved key and Clear session key are smaller and share the next row.
   Close window is at the bottom right. Use saved key activates it immediately; Set session only
   is disabled until text is entered. API-check feedback remains directly below its button.
4. For an existing staged cloud task, clear the session key (keep any OS-saved key), deliberately
   select upload consent and Start. With no environment key either, the missing-key error should
   appear immediately: the task stays staged, no media preparation/transcription starts and no
   new partial/failed result appears. An environment-supplied key is still valid until removed
   from the launching terminal. Load/enter a key and use Check API key to verify activation;
   successful ASR/export was already tested and need not be repeated. A rejected key or failed
   authentication also leaves the entire mixed/local-cloud queue staged. Local-only queues
   remain independent of OpenRouter.

One terminal line `Transcription ... failed` followed by exception type and file/frame lines is
one failure report. The supplied `openrouter.py:274` stack was the late missing-key failure;
the new preflight rejects that condition before a worker starts. Send the full new error/code
and action if anything else appears; do not send keys or transcripts.

Full B acceptance and terminology review remain separate. After functions settle, the agent
prepares one local editable field/message-ID + EN/PL table; the owner may correct both languages.
The approved/applied version becomes the repository reference, then EN/PL manuals follow.
Artist ZIP stays frozen. [Deferred installation/removal checks](INSTALLER_QUALIFICATION_PLAN.md).
