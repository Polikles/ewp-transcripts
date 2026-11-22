# Files and exports

## Raw ASR files

1. `episode_results.json` is the canonical, versioned source of truth: source hashes, models, timed words, speakers and provenance. Keep it unchanged.
2. `episode_segments.json` is a derived machine-readable segmentation export, enabled by default.
3. `episode_transcript.txt` is a readable raw transcript, enabled by default. Neither this nor segments means human approval.

These default files appear in the chosen transcription output folder. Optional configuration can disable derived outputs or add raw SRT/VTT. Re-exporting canonical JSON does not run ASR and does not create a manually verified revision. Matching completed source signatures are skipped unless an explicit force/new-version operation is used; force does not overwrite previous final files or bypass source safety checks.

A `*_results.partial.json`, `*_results.running.json` or `*_results.failed.json` describes run state/failure, not a completed canonical transcript. USER_CANCELLED is a cancellation diagnostic. Keep failure details for diagnosis; deleting them does not fix a provider or runtime problem. Interrupted processing restarts from the beginning on explicit retry.

## Review and publication directories

With normal GUI paths, source review creates `reviews`, `revisions` and `exports` below its project output root. Translation uses its own candidate/review/translation/audit paths and writes final downloads into `translation-exports`. Advanced path controls can change locations; read the displayed output path rather than assuming every file is beside the input recording.

An editable draft is a checkpoint. Apply in the GUI saves and validates it. Save and prepare for export creates an immutable revision/translation after manual verification. These are separate from the final Export/Save and export action. Existing publication files remain unchanged; subsequent versions get distinct identities/filenames.

## Formats

TXT is readable text. SRT and VTT are timed subtitles; choose those needed by the publishing platform. YTT is YouTube srv3 with speaker colors from the selected palette. HTML provides the available synchronized transcript export; platform rendering and optional media integration are separate from recognition. Select formats offered for the current source/revision/translation; the same options are not necessarily meaningful in every command.

Editing section/block splits serve human correction. Subtitle generation uses timed words and subtitle layout rules, not one cue per editor block. Export cannot invent timing for an untimed cloud response. Check the publishing platform's actual rendering, especially color profiles, before publication.

## Download, refresh and backup

Existing export downloads retrieves the exact saved file, with identity/hash validation. Exports also remain in the selected destination folder. Refresh checks whether that folder already contains exports; it neither regenerates them nor calls ASR/LLM. Translation files are in `translation-exports`. Exporting a changed palette creates a new YTT without changing a downloaded older YTT.

Keep raw canonical results, verified revisions/translations, audits, dictionaries and exports together in backups, including hidden durable source directories and a separately stored workspace manifest. A profile or workspace alone is not a full project backup.
