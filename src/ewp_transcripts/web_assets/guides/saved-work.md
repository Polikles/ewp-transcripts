# Saved work & cleanup

Use the numbered steps below with the matching GUI stage.

1. Choose output root and catalog: Leave the optional catalog blank to store new saved-work JSON files in the output directory, or choose a separate catalog for saves and backups.
2. Save current work state: Name the workspace and Save current work state before stopping. Dirty review drafts are checkpointed first.
3. Load saved work: The list refreshes when this stage opens. Select the workspace and Load selected work state after a restart. Re-enter or explicitly load provider credentials; upload consent stays unchecked.
4. Inspect cleanup before deleting: Refresh the managed-source inventory and read retention reasons before any explicit cleanup.

## 1. Choose output root and catalog

Choose the output root before working. An empty optional work-storage directory saves NEW workspace JSON files in that output folder; choose another catalog for a separate save/backup location. Updating a selected older save keeps its actual owning catalog. Read Saved work file to see the manifest's real path. The server remembers accessible recent output/catalog locations locally; the list refreshes when this section opens. This recall does not start work or supply consent.

## 2. Save current work state

Enter a recognizable unique workspace name and Save current work state. Dirty source/translation drafts are checkpointed first. New filenames begin with the name and end with `--<UUID>.workspace.json`. Windows-forbidden filename characters are replaced; Polish letters can remain. Do not identify a workspace only by its UUID.

The loaded name is filled automatically and locked against accidental renaming. Updating it saves the same workspace. Save as a new workspace requires another name and keeps the original. A duplicate name in known catalogs is rejected; case, surrounding whitespace and equivalent Unicode spellings do not create distinct names. An empty/duplicate name highlights the field.

Auto-save is off by default. If enabled, it periodically updates the active checkpoint when tracked work changes; it is not a substitute for deliberately saving important editor work. Explicit save is the recommended recovery point before stopping the server.

## 3. Load saved work

Select a listed workspace and Load selected work state, or open its manifest file. The progress overlay reports loaded/total jobs while checking paths, sources and editors. Wait for completion. Completed, failed and cancelled jobs are restored, along with staged jobs and their per-file options. Interrupted work is never silently resumed. Retry is explicit and starts from the beginning.

Pending files that were planned but not queued are retained in new saves and replanned on load. Review and confirm the refreshed plan before Add to queue. Selecting the same named file with the same content again does not duplicate it. Distinct content may need a distinct recording ID. Older saves without durable pending-selection metadata may require selecting the original files again.

Credentials and upload/manual-verification checkboxes are excluded. Re-enter or explicitly load the OpenRouter key if the server no longer has one, then give fresh cloud consent. A key still present in the same server process is independent of loading work. Missing paths remain a recovery issue; a saved manifest is not an embedded copy of every file.

## Back up or move a project

Back up the entire output folder INCLUDING hidden directories such as `.ewp-gui-sources`, and all separately configured review, revision, translation, dictionary and workspace catalogs. Preserve source recordings too if they remain external. New GUI pending-media copies are durable references below the output root; temporary browser-selection copies alone are not backups.

The workspace JSON contains references, hashes, options and workflow identity, not media bytes, secrets or consent. Reopening a completed result can permit editing/export without audio; playback needs unchanged media. Moving to another computer requires transferring these files and checking paths. A [user profile](settings.md) transfers preferences/catalog records and optional dictionaries, not recordings or transcripts. Do not edit hashes to bypass a changed source.

## 4. Inspect cleanup before deleting

Remove selected work state deletes only that workspace manifest. Clear current work state forgets inactive in-memory/browser workflow state after confirmation; it refuses while active work is running. Neither deletes published revisions/exports or all source media.

Managed source copies inventory lists app-owned durable copies and why each is retained. Preview deletion only for unreferenced copies, inspect the plan, then confirm explicitly. Current work, known saved catalogs and lineage references protect files. Other catalogs outside those known to this operation must be audited separately. This is separate from temporary-workdir cleanup in Settings; it does not delete original external recordings or model caches.

## Projects and locations

Recent projects reopen result/output references. Named locations fill input/output fields without starting ASR; changing the input location replaces the pending selection, not staged jobs. Find saved results scans the selected directory, validates canonical JSON and allows adding selected results without ASR. It scans up to 500 entries and imports at most 50 selected results in one action. Unavailable paths are references needing restoration, not permission to regenerate data.
