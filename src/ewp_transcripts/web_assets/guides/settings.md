# Settings & About

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Preferences and profile: Keep ETA off or enable it after calibration. Save, load or transfer one user-profile JSON with preferences, workspaces and dictionaries.
2. Test local dependencies: Run the optional environment test to enable Doctor and repair controls.
3. Read doctor report: Run doctor and inspect failed checks and technical details. Missing HF_TOKEN is harmless with complete offline models.
4. Repair only when needed: Reinstall dependencies opens terminal steps. Save work and stop the GUI before changing its environment.
5. Check application information: Check version, local processing, optional providers, licenses and notices.

## Detailed instructions

Diagnostics are maintenance tools, not required clicks in every transcription workflow. Tests run bounded child processes without downloading models or transcribing. Passing dependency checks does not qualify the complete GPU/model workflow.

Ubuntu 24.04 and 26.04 are accepted. The installation script automatically checks/repairs native audio libraries after installing locked dependencies. An OS upgrade can replace FFmpeg 6 with FFmpeg 8 while leaving the Python environment pinned to TorchCodec 0.7. See the Ubuntu upgrade guide when this occurs.

Repair uses bash scripts/repair-dependencies.sh in the transcription checkout. It preserves system FFmpeg, locked ML versions, model caches and previous artifacts. Keys are process-memory-only. Audio transcription is local; optional correction and translation send text only after explicit consent to the separately operated provider. No third-party retention guarantee is implied.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

In-progress feedback uses the owner-provided animated gear.svg motion mark, including global requests, adjacent button feedback, running statuses and active queue/card indicators. Its original reduced-motion behavior is preserved; completed/error markers are static.

## ETA and portable profiles

ETA becomes available only after three successful comparable complete transcriptions on the same
computer (language, models, speaker/track topology and execution phases must match). It remains
approximate. Elapsed and percentage are visible without ETA. Timing calibration is not transferred.

Save profile writes the current snapshot to the private local state directory. Load saved profile
restores it. Export profile saves and downloads ewp-user-profile.json; Import profile chooses that
single JSON in a browser picker. No media, transcripts, credentials, disclosure/verification consent,
active jobs or timing cache is embedded. Workspace records reference original external files.
Save transcript drafts separately before closing the program.

Profiles include the default workspace catalog and the explicitly selected custom catalog. Select
another catalog before making a separate export if needed. The selected dictionary library and
available dictionary files referenced by those workspaces are embedded, with original bytes/hash,
version and hidden status. Custom palette definitions are included. Missing files remain unavailable
references; no content is guessed or silently regenerated. The profile is limited to 16 MiB.

Import restores catalogs/preferences without running the queue or replacing the current editor.
Open Saved work & cleanup to choose a restored workspace. Missing paths are visibly unavailable;
restore their files (and original paths, or update a saved workspace copy) before loading. Dictionaries
are placed in content-addressed private directories, so an existing edition is not overwritten.
Independent dictionary import/export is also available in Dictionaries. Profile import merges saved
records; it does not delete existing workspaces, palettes or dictionary files.
