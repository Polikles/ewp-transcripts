# Source review & export

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose recording: Choose a completed recording from the queue to prepare or reopen its own review.
2. Speaker names and colors: Check display names, speaker assignments and the YTT color profile. Add speaker creates another editable speaker.
3. Review transcript: Correct wording and speaker assignments. Place a caret between whole words for Split at cursor; use Separate selected text for a selection.
4. Preview and apply revision: Use Preview in Prepare and validate, inspect the result, confirm manual verification, then Apply verified revision.
5. Export subtitles: Choose formats and Export verified revision. Translation is optional and can follow later.

## Detailed instructions

Choose one recording for the editor; batch checkboxes are independent. The queue action restores that recording’s saved review or prepares a new draft. Direct source/output paths remain available as an advanced fallback.

Speaker names and colors keeps stable speaker IDs. Switching the YTT profile updates visible colors for the next export and retains custom overrides. Adopt brand palette explicitly resets this recording’s custom colors; previous exports stay unchanged. Add speaker adds a revision-local identity, not a new ASR run or voice-recognition identity. An in-use speaker cannot be removed until its blocks are reassigned.

Text boxes grow to fit their text. Use All sections or Previous section / Next section to navigate. Split at cursor requires one caret, complete words and nonempty text on both sides. Selecting text uses Separate selected text instead. Neither operation invents timestamps. Undo and Redo change only the current editor.

Prepare and validate and Draft and history are below the transcript. Save draft creates a durable checkpoint; Preview saves dirty changes and validates the exact draft. Preview does not scroll to Apply or publish anything. An edit invalidates the previous Preview and verification.

Only confirm I manually verified wording, speakers… after reviewing all sections. Apply verified revision creates an immutable child while retaining the original ASR result. Choose TXT, SRT, VTT, YouTube YTT, HTML or Segments JSON and export. Repeated export allocates a new version rather than overwriting earlier files. The configured production YTT profile remains available; brand-palette YouTube qualification is separate.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.
