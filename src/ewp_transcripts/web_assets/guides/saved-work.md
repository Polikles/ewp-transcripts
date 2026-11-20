# Saved work & cleanup

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose output root and catalog: Use the same shared output root and workspace catalog as the recording’s durable artifacts.
2. Save current work state: Name the workspace and Save current work state before stopping. Dirty review drafts are checkpointed first.
3. Load saved work: Refresh, select the workspace and Load selected work state after a restart. Re-enter provider credentials.
4. Inspect cleanup before deleting: Refresh the managed-source inventory and read retention reasons before any explicit cleanup.

## Detailed instructions

A workspace references durable files; it does not embed audio, transcript text, credentials or human approval. Back up the output root including dot-directories and any separate workspace catalog. Interrupted transcription restarts from the beginning.

Auto-save defaults off. Enabling it replaces the active saved checkpoint periodically; leave it off for a stable explicit recovery point. Loading work preserves exact recording/review/translation identity and checks current file hashes.

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
