# Source review & export

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose recording: Choose a completed recording from the queue to prepare or reopen its own review.
2. Speaker names and colors: Check display names, speaker assignments and the YTT color profile. Add speaker creates another editable speaker.
3. Review transcript: Correct wording and speaker assignments. Place a caret between whole words for Split at cursor; use Separate selected text for a selection.
4. Check and save revision: Use Apply to save and validate the draft. Confirm manual verification, then Save and prepare for export. Prepare text for review creates a draft when needed.
5. Export subtitles: Choose formats and Export verified revision. Translation is optional and can follow later.

## Detailed instructions

Choose one recording for the editor; batch checkboxes are independent. The queue action restores that recording’s saved review or prepares a new draft. Direct source/output paths remain available as an advanced fallback.

Speaker names and colors keeps stable speaker IDs. Switching the YTT profile updates visible colors for the next export and retains custom overrides. Preview tries a configured profile, Apply commits colors for this recording, and Save keeps a reusable custom profile; previous exports stay unchanged. Add speaker adds a revision-local identity, not a new ASR run or voice-recognition identity. An in-use speaker cannot be removed until its blocks are reassigned.

Text boxes grow to fit their text. Use All sections or Previous section / Next section to navigate. Split at cursor requires one caret, complete words and nonempty text on both sides. Selecting text uses Separate selected text instead. Neither operation invents timestamps. Undo and Redo change only the current editor.

Prepare and validate and Draft and history are below the transcript. Save draft creates a durable checkpoint. Apply saves dirty changes and validates the exact draft; it does not publish or scroll away. An edit invalidates validation and verification. Prepare text for review creates the draft when required.

Only confirm I manually verified wording, speakers… after reviewing all sections. Save and prepare for export creates an immutable child while retaining the original ASR result. Choose TXT, SRT, VTT, YouTube YTT, HTML or Segments JSON and export. Repeated export allocates a new version rather than overwriting earlier files. The configured production YTT profile remains available; brand-palette YouTube qualification is separate.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

Color profiles are defined in subtitles.ytt_color_profiles; Configured production uses subtitles.ytt_speaker_palette. EwP brand is a separate preset. Selecting a profile previews its speaker colors immediately. Preview does not change export preferences: Apply commits the visible colors for this recording’s next export. Save stores a named custom profile for other recordings and future sessions; use a custom name to preserve configured presets. Existing exports stay unchanged.
