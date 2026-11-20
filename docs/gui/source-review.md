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

The left recording rail contains Recording audio while this stage is open. All synchronized
files/channels in the episode are mixed from their shared time zero into one private mono preview,
so a guest on a separate track remains audible when seeking to their words. Original paths,
stream/channel choices and hashes are verified. The mix uses the longest source duration without
concatenation, timing offsets or source modification. Go to this fragment below a speaker selector
saves any dirty draft, then seeks to a real source-word start and starts the complete episode mix.
Changed/inserted text may use the nearest known timestamp, explicitly marked in player status.

Small source-file hints below Speaker come from immutable source-word provenance, not the current
speaker label. Renaming or reassigning a speaker does not rewrite where the words originated.
An ambiguous mapping lists relevant section sources conservatively. Changing stages pauses audio;
returning restores the per-recording position in this browser session. Original recordings must
remain available and match their canonical hashes. If any source is missing, restore it and use
Reload recording audio; transcript editing still works. Server restart prepares a new private mix.

Review sections aim for anchor_target_words (default 200) and anchor_target_speaker_blocks
(default 5), then choose a nearby sentence end, including closing quotes and common EN/PL
abbreviation handling. These are presentation targets, not hard sentence cuts. A search extends
up to twice the word target. Without a usable sentence end, a bounded fallback keeps the editor
usable and a red note above the first section requests extra attention to punctuation and speakers.
This is a structural heuristic, not an ASR confidence score. Correcting speaker assignments matters
more than presentation splits; splitting a block here does not determine subtitle line breaks.

Unchanged legacy text can be repartitioned at source-word sentence boundaries while retaining
speaker assignments. Edited legacy and parent-revision anchors keep their identities and use sentence-aware within-block
presentation; unresolved old section boundaries receive the same caution. Reading does not replace
saved bytes. Explicit Save persists the displayed draft structure. Canonical JSON/timing and published
revisions remain unchanged. These changes do not require repeating ASR.

The recording player has room for the browser's native controls, including its overflow menu
and playback-speed option where supported. Rate changes persist as a display preference for
both mixed episodes and individual recordings. The redundant permanent speed selector is removed.

Text boxes grow to fit their text. Use All sections or Previous section / Next section to navigate. Split at cursor requires one caret, complete words and nonempty text on both sides. Selecting text uses Separate selected text instead. Neither operation invents timestamps. Undo and Redo change only the current editor.

Prepare and validate and Draft and history are below the transcript. Save draft creates a durable checkpoint. Apply saves dirty changes and validates the exact draft; it does not publish or scroll away. An edit invalidates validation and verification. Prepare text for review creates the draft when required.

Only confirm I manually verified wording, speakers… after reviewing all sections. Save and prepare for export creates an immutable child while retaining the original ASR result. Choose TXT, SRT, VTT, YouTube YTT, HTML or Segments JSON and export. Repeated export allocates a new version rather than overwriting earlier files. Example default is the startup choice; explicit production settings remain available as Configured palette when different. EwP Brand® retains the owner’s identity colors. New-palette YouTube qualification is separate.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

Example default is a visibly different six-color example palette and the first choice in a fresh session. EwP Brand® is the owner’s identity preset; its registered-mark symbol and original colors are retained. Named profiles are defined in subtitles.ytt_color_profiles; explicitly configured subtitles.ytt_speaker_palette colors remain available as Configured palette if they differ from Example default. Legacy configured/brand workspace IDs and legacy EwP brand configuration names still load. Selecting a profile previews its speaker colors immediately. Preview does not change export preferences: Apply commits the visible colors for this recording’s next export. Save stores a named custom profile for other recordings and future sessions; use a custom name to preserve configured presets. Existing exports stay unchanged.

Save and prepare for export requires the human-verification checkbox. Missing verification outlines that row and shows a message immediately below it; no revision is submitted. Checking it clears the local error, and saving still requires the explicit Save action. Saved per-recording colors and existing exports are retained when profiles change.

## Download a published export

After export, open Existing export downloads. Refresh existing exports also works after loading
saved work; it validates existing files without running ASR or writing new exports. Click the
exact filename/version to download the original bytes. The displayed SHA-256 identifies that file;
older registered palette/export versions stay available. Download links expire after 30 minutes
and are renewed by refresh after a restart. Missing/changed files are withheld, never repaired silently.

Compatible older exports can be checked read-only against the deterministic renderer. A historical
custom palette without a download record may need its original export settings; the application
does not guess its identity. New GUI exports keep a private download registry with artifact and
source/revision hashes. Back up the local application state as well as the output root when needed.
