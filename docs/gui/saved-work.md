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
