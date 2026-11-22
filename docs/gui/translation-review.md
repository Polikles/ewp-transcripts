# Translation review & export

Use the numbered steps below with the matching GUI stage.

1. Choose recording: Open the recording’s manual translation or saved candidate from its queue. Check source and direction.
2. Review source and target: Compare every source unit with the target and correct meaning, names, omissions and additions.
3. Apply translation: Apply translation saves and validates the draft. Resolve errors and review warnings; it does not publish a final translation.
4. Save translation: Confirm manual semantic verification, then Save and prepare for export to publish an immutable translation.
5. Save and export: Choose formats and Save and export. The source lineage is audited before export; Proceed with next output returns to the queue.

## 1. Choose recording

Open the selected recording's manual translation or generated candidate. Verify canonical source, optional source revision and direction. Each recording restores its own review; switching stages must not require generating another paid candidate. If a path/hash no longer matches, restore the correct original rather than editing provenance fields in JSON.

## 2. Review source and target

Read the immutable source beside each editable target unit. Check meaning, negatives, names, numbers, quotations, speaker identity, omissions, additions and style. Keep uncertainty faithful to the source. Save translation draft checkpoints unfinished work; Undo/Redo concern the current draft. Restore saved draft reopens its last saved contents; Clear current translation review only clears the view after confirmation.

Empty targets fail by default. If an omission is intentional, enable Allow empty translation units before validation and publication. The immutable translation/audit records the omission; exported text/subtitles omit it rather than inserting a blank cue. The confirmation is not carried between unrelated reviews.

## 3. Apply translation

Apply translation saves and validates the draft. Read warnings and resolve errors. This does not publish a verified translation. Editing after validation invalidates that validation; apply again. Draft controls follow the source-review layout with Apply first and clear separated below.

## 4. Save translation

After checking every unit, tick manual semantic verification and use Save and prepare for export. This writes an immutable translation tied to the exact source lineage. It does not alter the source revision. Technical IDs/hashes identify provenance; they are not editable wording.

## 5. Save and export

Choose formats and Save and export. The app audits source lineage before generating files. Exports go to `translation-exports` beneath the translation output root. Existing export downloads retrieves those actual files; Refresh checks for existing versions and does not run translation or regenerate files. Back up immutable translations and their audits/source revisions with the exports.

Proceed with next output returns to the queue. Translation workflow status changes after candidate generation, verified save and export; exporting only SRT or only VTT is sufficient to record export. To continue later, [save work](saved-work.md), then reopen this recording's own review after restart.
