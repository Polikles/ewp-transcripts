# Settings & About

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Test local dependencies: Run the optional environment test to enable Doctor and repair controls.
2. Read doctor report: Run doctor and inspect failed checks and technical details. Missing HF_TOKEN is harmless with complete offline models.
3. Repair only when needed: Reinstall dependencies opens terminal steps. Save work and stop the GUI before changing its environment.
4. Check application information: Check version, local processing, optional providers, licenses and notices.

## Detailed instructions

Diagnostics are maintenance tools, not required clicks in every transcription workflow. Tests run bounded child processes without downloading models or transcribing. Passing dependency checks does not qualify the complete GPU/model workflow.

Ubuntu 24.04 and 26.04 are accepted. The installation script automatically checks/repairs native audio libraries after installing locked dependencies. An OS upgrade can replace FFmpeg 6 with FFmpeg 8 while leaving the Python environment pinned to TorchCodec 0.7. See the Ubuntu upgrade guide when this occurs.

Repair uses bash scripts/repair-dependencies.sh in the transcription checkout. It preserves system FFmpeg, locked ML versions, model caches and previous artifacts. Keys are process-memory-only. Audio transcription is local; optional correction and translation send text only after explicit consent to the separately operated provider. No third-party retention guarantee is implied.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.
