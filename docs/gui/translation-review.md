# Translation review & export

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose recording: Open the recording’s manual translation or saved candidate from its queue. Check source and direction.
2. Review source and target: Compare every source unit with the target and correct meaning, names, omissions and additions.
3. Apply translation: Apply translation saves and validates the draft. Resolve errors and review warnings; it does not publish a final translation.
4. Save translation: Confirm manual semantic verification, then Save and prepare for export to publish an immutable translation.
5. Save and export: Choose formats and Save and export. The source lineage is audited before export; Proceed with next output returns to the queue.

## Detailed instructions

The source text and ownership are immutable. Review the editable target in context; provider output is not evidence of correctness. Check direction and the exact source revision, especially when a newer verified source is available.

Empty targets are rejected by default. Only enable Allow empty translation units when intentionally omitting a unit, then Apply translation again. Omission provenance is retained and omitted units are excluded from exported text/captions. Verification and omission confirmation are not restored from a saved workspace.

Save and prepare for export publishes an immutable manual child. Apply translation saves and validates the draft without publication. Exports use the approved translation and support TXT, SRT, VTT and HTML. Existing artifacts remain intact. Source-language YTT is handled in Source review & export; this stage does not add a translated YTT renderer.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

Queue legends sit below the queue. Clear current draft is a secondary action below Apply translation and affects the current browser view; saved files remain available. Hover over Apply and Audit/export for their verification and lineage requirements.

After saving a verified translation, you can visit other stages and return to export without regenerating an API candidate. Export uses the active saved review identity and its own output root.

## Download an existing translation export

Existing export downloads lists the selected applied manual translation's published files, including
its provenance JSON. Refresh checks their exact bytes and source/revision/translation identity; it
does not regenerate a candidate, run ASR or write an export. Click the exact filename to download.
After restarting, load saved work and refresh to obtain new session download links. A missing or
changed artifact cannot be downloaded. The original publication/version stays unchanged.


## Review actions and saved exports (Windows feedback follow-up)

The common main action row starts with Apply (Apply translation in translation review), followed
by Undo, Redo, Save draft and Restore saved draft. Clear current draft is alone below, aligned
with the rightmost main action. On desktop/half-screen widths, long labels wrap within buttons
instead of moving an action to a new row; phone widths can reflow. Clear affects the current
browser view; saved drafts and published files remain on disk.

Download a file. Exports are also saved in the selected destination folder.
Refreshing checks whether exports already exist in the selected directory.

Translations are saved in the translation-exports folder. Download links populate after exporting.
A generated API candidate completes assisted translation; semantic review remains pending until
you explicitly verify and save a manual translation. Its existing candidate does not undo that
manual completion.
