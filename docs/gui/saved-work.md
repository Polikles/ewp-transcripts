# Saved work & cleanup

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose output root and catalog: Leave the optional catalog blank to store new saved-work JSON files in the output directory, or choose a separate catalog for saves and backups.
2. Save current work state: Name the workspace and Save current work state before stopping. Dirty review drafts are checkpointed first.
3. Load saved work: The list refreshes when this stage opens. Select the workspace and Load selected work state after a restart. Re-enter or explicitly load provider credentials; upload consent stays unchecked.
4. Inspect cleanup before deleting: Refresh the managed-source inventory and read retention reasons before any explicit cleanup.

## Detailed instructions

A workspace references durable files; it does not embed audio, transcript text, credentials or human approval. Back up the output root including dot-directories and any separate workspace catalog. Interrupted transcription restarts from the beginning.

Auto-save defaults off. Enabling it replaces the active saved checkpoint periodically; leave it off for a stable explicit recovery point. Loading work preserves exact recording/review/translation identity and checks current file hashes.

An empty name highlights/focuses the name field before saving. Existing entries in the private
default catalog remain listed alongside the chosen output/custom catalog; saving an already selected
entry keeps its original catalog. Refresh is available below Save. Remove/Clear actions affect
saved/current state and are visually secondary. A workspace JSON alone is not a media backup.

Loading work also invalidates any earlier cloud-upload confirmation. Select the checkbox again
only when you intend to start the currently staged cloud jobs. A saved API key and upload consent
are separate; loading a key never supplies consent.

Remove from list only removes a selection entry. Forgetting an inactive queue item and deleting a saved workspace do not delete publication files. Managed-source cleanup is a separate explicit operation and retains copies still referenced by current work, workspace catalogs or review lineage.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

## Restart and completed/cancelled history

Save the current work state after saving/applying a review or changing the queue. Cancel unwanted
waiting/running tasks and wait for terminal status before stopping if you do not want them to finish.
On restart, load the same named workspace/catalog. Saved staged work is hash-checked and re-staged;
completed, failed and cancelled history is restored as history, never as a running GPU operation.
Completed review/export can recover without original audio when the canonical result still exists;
playback still requires the original media. Credentials and human consent/verification remain unset.
Refresh Existing export downloads in either review stage to download an existing applied version.
Temporary-workdir cleanup is a separate Settings & About action with an explicit preview.

Loading shows a modal with loaded/total queue jobs until the queue and saved editors are ready.
Failed/cancelled history may reference moved media without being omitted; actual retry still
requires unchanged original sources. Retry replaces its selected old row with a new staged attempt.

## Projects and named locations

Expand Projects and locations to reopen recent recording reviews or remember a named project.
Opening/preparing a review also records its own result/output reference. These are references,
not complete backups. Remove from list deletes only the catalog entry. Named input/output
directories fill the transcription fields without starting jobs; changing input replaces the
pending file selection, while staged queue tasks remain intact.

Find saved results scans the selected directory only (up to 500 entries), validates canonical
JSON content and shows checkboxes. Add selected results to queues copies only those validated
canonical results into the shared output's durable source area; it never reruns transcription.
A result changed after scanning must be scanned again. Up to 50 selected results can be added
at once. Paths unavailable marks missing or foreign-computer references; restoring original
files/path access is separate from loading a profile.

## Pending selections and retained failures

Save also preserves browser-selected media that has only been planned, before Add to queue.
Load restores those files, their per-file language/count/stream options and input path, then
replans metadata against the current files. It does not run ASR or restore plan approval; review
and confirm the refreshed plan before adding. Selecting the same named file with the same content
again keeps one entry. Different content remains a distinct selection and may need an explicit ID.
Older saves without pending-selection metadata cannot recover expired temporary browser copies;
choose them again. New workspaces use version 3; earlier versions 1/2 remain readable.

Loading a snapshot taken before a later failed/cancelled attempt recognizes its retained matching
failure state and restores that inactive row. Completed rows also remain. The source hashes and
current episode signature must agree; failure files stay on disk. Retry is explicit and restarts
processing from the beginning, with fresh cloud consent when needed. Do not delete failed JSON
files to try to repair provider timing or workspace restoration.

The loaded name fills its field and clears an old missing-name highlight. Existing names are
readonly to avoid accidental rename. Select **Save as a new workspace** to enter a different name
and create a separate record. The original remains. The **Saved work file** line shows the actual
manifest location: updating a selected legacy entry keeps it in its private/custom catalog even
when the optional catalog input is blank. For a new output-folder copy, select Save as new.
A complete output-folder ZIP may therefore lack a manifest stored in an older separate catalog.

## Recognizable files and remembered directories

New saves use `<workspace name>--<UUID>.workspace.json`. Characters forbidden in Windows filenames
are replaced with underscores; Polish letters and spaces remain recognizable. The UUID preserves
identity for older saves even if their names coincide. New names must be unique across the known
catalogs: Save as new rejects an existing name and highlights the name field. Comparison ignores
case, surrounding whitespace and equivalent Unicode spellings. Choose another name; updating the
selected existing save still works. Earlier UUID-only JSON saves still
load, and saving them again migrates their filename while keeping that identity. Save as new makes
a separate ID/file; removing a save deletes only its manifest.

Last-used output and optional catalog directories, plus up to 20 recent catalogs, are remembered
locally by the server. On reopening, accessible saved work is listed without reselecting paths or
clicking Refresh. An input already changed by the user is not overwritten by a delayed recall.
Unavailable directories are ignored; no audio, key, approvals or automatic queue start are restored
by directory recall. The registry is `workspace-locations.json` beside the private `gui-workspaces`
catalog (`XDG_STATE_HOME/ewp-transcripts`, or `~/.local/state/ewp-transcripts`). It is a local directory
reference list, separate from portable workspace files and browser storage.
