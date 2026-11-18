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
