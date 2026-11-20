# Package A feedback retest

Date: 2026-11-20. Follow-up to the owner's A1–A4 test. Keep the already confirmed WSL
cancellation, source/translation export versions and restart download results. Package B remains
blocked on acceptance of these fixes; there is no need to repeat all previous qualification.

1. **Plan directly after file selection.** Choose synchronized audio tracks plus a separate video.
   Inspect is merged into Dry-run: the GUI now has choose → plan/add → start. Run Dry-run once;
   every selected unqueued episode should be planned. The custom gear appears during Planning.
   Try Add without confirmation, then check confirmation and Add again without repeating the plan.
   Both episodes must enter the queue. A real language/count/output/source change still requires
   a fresh plan. CLI/API Inspect remains available for diagnostics.
2. **Read the rail before ASR.** Waiting/running/failed/cancelled tasks say the next stage is
   transcription. An imported canonical says ASR completed, rather than implying its whole
   workflow finished. Recording cards still open the correct stage.
3. **Recover a mixed queue.** Save a workspace containing completed ASR plus staged audio/video
   and any saved editor changes. Restart/load. A translucent modal shows loaded/total queued jobs
   and remains until queue/editor restoration finishes. ASR must stay stopped and confirmation
   boxes unset. The last save/load message must not falsely look finished during a new operation.
4. **Retry a cancelled task.** Retry / Ponów creates a fresh staged attempt and replaces that
   selected cancelled row. It does not remove source, published or retained temporary files.
   Previously saved duplicate history from the earlier implementation can still be removed from
   the list explicitly. Other completed ASR must not run again.
5. **Save terminal history.** Save after a cancellation and successful retry. A valid cancelled
   history record must not be omitted just because its old planned result now exists. Failed/
   cancelled history may remain even if the original media has moved; actually retrying still
   checks the original source hashes. Genuinely missing completed canonical results/staged inputs
   can be omitted and are reported separately from cleared stale form fields.
6. **Enter manual review directly.** Open a canonical result in manual source review without
   clicking Skip LLM-assisted correction. Starting manual review implies skipping that unused
   optional stage. Saved downstream revisions/exports also recover this inference. Existing real
   correction candidates still show completion. After the remaining workflow finishes, it should
   no longer be stuck on optional correction.
7. **Check native playback.** In source review, check the native three-dot menu and its speed
   submenu at full/half screen and after a few reloads. There is no permanent duplicate speed
   selector. Try 1.5x and 2x for a mixed episode and an individual recording; seeking still uses
   the shared episode timeline. Native-menu labels/layout belong to the browser.
8. **Check PL maintenance feedback.** Confirm Ponów, cancellation state, cleanup reasons and
   preview count are localized. Changing an inventory filter disables the stale rows until its
   refresh completes. Preview does not delete anything; Confirm deletion removes selected eligible
   temporary WAV workdirs. Durable copies under `.ewp-gui-sources/media` are intentionally separate
   and remain protected/managed through Managed source copies.

Raw ASR normally writes `<episode>_results.json`, `<episode>_segments.json` and
`<episode>_transcript.txt` with the shipped output configuration. They are unreviewed results;
publication uses the manually accepted revision. The minimal stage guide explains these files.

Report PASS/FAIL/NOT RUN with the numbered case and relevant diagnostic code. Complete two-column
EN–PL terminology approval is task 10 after functional additions; comprehensive EN revision and PL
manuals follow owner corrections/approval. Artist assets/ZIP are unchanged.
