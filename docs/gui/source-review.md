# Source review & export

Use the numbered steps below with the matching GUI stage.

1. Choose recording: Choose a completed recording from the queue to prepare or reopen its own review.
2. Speaker names and colors: Check display names, speaker assignments and the YTT color profile. Add speaker creates another editable speaker.
3. Review transcript: Correct wording and speaker assignments. Place a caret between whole words for Split at cursor; use Separate selected text for a selection.
4. Check and save revision: Use Apply to save and validate the draft. Confirm manual verification, then Save and prepare for export.
5. Export subtitles: Choose formats and Export verified revision. Translation is optional and can follow later.

## 1. Choose recording

Open the recording's review/export action in its queue. This prepares a new draft or restores that recording's saved draft. Existing canonical result JSON can be imported instead of transcribing again. The selected result and output root determine review identity; do not combine unrelated result/revision paths. Direct paths remain an advanced fallback.

The recording whose transcript is open has a strong outline in both the left recording queue and the Choose recording list. The marker follows recording switches and queue refreshes in light and dark themes.

## 2. Speaker names and colors

Set display names and check each block's speaker assignment. Add speaker creates an editable identity for this revision; it is not automatic voice recognition or a new ASR run. Reassign an in-use speaker's blocks before removing it.

Choose a YTT color profile. Example default is the initial choice; EwP Brand® is the owner's podcast identity preset. Preview displays the selected colors, Apply uses them for this recording and Save creates a reusable custom profile. Existing per-speaker overrides are retained. Colors affect future YTT exports; files already exported remain unchanged. SRT does not carry the YTT palette.

## 3. Review transcript and listen

Correct every section's wording, punctuation, names, quotations and speaker labels. The source-file hint below Speaker identifies word provenance; renaming a speaker does not change it. Large blocks/sections are divided around sentence endings for convenient review. These presentation splits do not determine subtitle cue boundaries. If punctuation cannot supply useful boundaries, the first section shows a caution; inspect those divisions and speaker assignments particularly carefully.

Recording audio in the left rail plays the episode. Synchronized tracks/channels are mixed on one timeline from time zero, not concatenated. Go to this fragment seeks to a real word timestamp and starts playback. New or changed words may use the nearest known timestamp, which the player reports. Playback speed can be adjusted. If audio is unavailable, restore unchanged source files and Reload recording audio; editing a saved result can continue without playback. Leaving the stage pauses audio.

Place the caret between whole words and use Split at cursor, or select whole text and Separate selected text to isolate a passage. Merge with previous block joins it back. Assign the resulting blocks to the right speaker. Text areas resize automatically. Undo/Redo affect current draft history, not already published revisions. Structural actions checkpoint dirty text; Save draft remains available whenever you want a checkpoint.

## 4. Check and save revision

Apply saves and validates the current draft; review errors and warnings. It does not publish a final revision. After reading the complete text, tick manual verification and select Save and prepare for export. This writes an immutable verified revision and enables its export. Missing verification highlights the checkbox; do not tick it until wording, speakers and sentence boundaries have actually been checked.

Save draft can checkpoint unfinished work. Restore saved draft loads the previous saved draft; Clear current draft clears the current view after confirmation and does not delete published files. Changing a draft after validation requires Apply again. To revise an already verified result, make another revision; do not edit the canonical result or immutable revision JSON in place.

## 5. Export subtitles

Select formats and Export verified revision. The default directory is `exports` below the review project root; custom paths are available in advanced controls. Existing export downloads links download the actual saved files. Refresh checks the directory for prior exports without regenerating them. New palette exports create a new artifact; older versions remain available. See [Files and exports](outputs.md) for formats and the difference from raw ASR exports.

Proceed to the next queue item or [Optional translation](optional-translation.md). Translation is not required to complete source review/export. Save work before ending the session; export files and immutable revisions remain on disk after the browser/server closes.
