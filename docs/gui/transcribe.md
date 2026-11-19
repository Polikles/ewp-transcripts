# Transcribe

Use this guide with the matching stage in EwP Transcripts. Interface language does not change recording or translation language.

1. Choose output and audio: Choose the shared output directory first, then audio files. Select matching speaker tracks for one episode together.
2. Inspect file: Choose processing language separately for each selected recording and speaker count or auto-detection. Inspect checks all unqueued selections.
3. Plan and add to queue: Run Dry-run, review the exact plan, confirm it and Add to queue. Adding advances to the next unqueued recording.
4. Start queue: Start queue runs staged episodes in order. After completion, continue to optional correction or source review.

## Detailed instructions

Picking files does not start ASR. Inspect and Dry-run do not load models. Transcription uses pinned local models and the system media tools. A grouped episode must contain synchronized, compatible tracks.

Failed items retain a diagnostic code and technical details; other completed work remains available. Settings & About contains optional dependency diagnostics and the Ubuntu upgrade repair guide.

Use Add saved results in a stage queue to work from existing canonical JSON without repeating transcription. Save current work state before stopping the GUI.

## Next step

Return to the application and use the numbered sections and actions above. Saving a draft is separate from human approval and immutable publication.

Inspect checks all selected, unqueued episodes. Add to queue advances to the next available episode; staged inputs cannot be inspected or planned again. Each inactive queue row has Remove. Remove completed tasks from the queue appears only for recordings whose workflow is finished and preserves unfinished/failed jobs and every saved file. Recording cards on the left open that recording’s next unfinished stage.

The language selector belongs to the selected recording; switching recordings restores its language. Grouped tracks share their episode language. Inspect uses each recording’s selection. Start queue handles newly staged items alongside completed history and never reruns completed ASR. Adding later files and removing completed items do not leave Start disabled.

The path help belongs directly below the server input field, before the selected-file list. The (i) control beside language selection notes an observed behavior: EN for Polish audio has sometimes produced readable English text, but this is not a guaranteed translation mode and still requires review/correction. It does not change the actual transcription task or replace the optional translation workflow.
