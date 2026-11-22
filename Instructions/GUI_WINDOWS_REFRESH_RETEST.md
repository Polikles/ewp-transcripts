# Windows startup and live-queue retest

Use the existing installation. Stop the old server with Ctrl+C, `git pull`, then
`uv run --locked transcriber gui`. Refresh the browser with Ctrl+F5. No model preparation,
reinstallation, paid ASR or browser-data deletion is needed for this correction.

1. The left status should say the local service is ready. Settings & About must show application
   and API versions instead of Loading. On Windows, the dependency-help link opens Windows setup.
2. Use one short local recording. After Start, its row should show the phase, approximate progress
   bar and elapsed clock, then ASR completed and the next step without refreshing the page.
   The finished row must no longer offer Cancel. A newly waiting/active task can still be cancelled.
3. Open Manage OpenRouter key from Settings or the workflow. Escape closes the window; Tab stays
   inside it. Closing discards unsubmitted text and leaves any already activated key alone.
4. In selected recordings, the language information icon is next to Recording language, above
   the select. It still closes after clicking elsewhere. The subtitle is Local-first transcript
   workflow / Lokalne narzędzie do transkrypcji.
5. Keep one shared output directory for active queue tasks. Staged/queued/running work intentionally
   blocks staging into another directory; completed/failed/cancelled history does not. Remove or
   finish pending work before changing the queue's output. The isolated original mismatch is not
   reproduced; that guard has not been weakened.

The old stale display could outlive a completed backend task. If the output directory already
contains its completed `*_results.json`, add that file as a completed result rather than rerunning
ASR just to recover the interface. Save/restore and immutable publication rules remain unchanged.

After this targeted Windows check and interface approval: English documentation review/update →
complete Polish user documentation → NEW updated artist review package. Preserve previous passes.
