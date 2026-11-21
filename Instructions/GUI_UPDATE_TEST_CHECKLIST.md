# Focused update check — restored consent and layout

2026-11-21. This is the active follow-up for the already installed Windows/WSL application.
Installation, local/cloud ASR, source SRT/VTT export and translation progress have already passed
owner checks. Do not reinstall Python dependencies, FFmpeg or models for this retest.

1. Stop the GUI, `git pull`, then `uv run --locked transcriber gui`. Refresh the browser page.
   Check that the framed favicon is centered. At half width the controls remain usable; on a
   very wide/full screen the interface stays centered with side gutters and readable review text.
2. Collapse **Transcription engine**. Step **2. Plan and add to queue** and its actions remain
   visible. Expand OpenRouter options: the two hints are short. In Manage OpenRouter key, use
   **Check API key**: its result appears directly below that button. This check uploads no audio.
3. Open **Saved work & cleanup**. The list refreshes automatically. Save with an empty name:
   the name field receives focus/highlight and an explanation. Enter a name and save.
   The optional catalog hint is above its input; leaving it blank saves the workspace JSON
   in the output directory. Existing saves in a separate/legacy catalog remain accessible.
   Refresh is below Save; Remove/Clear are subdued and aligned right below the main row.
4. Plan/stage a short **OpenRouter Whisper** job. Click Start without checking upload consent:
   the checkbox is highlighted/focused, an explanation appears, and no transcription starts.
   Check consent, then save work **without starting**. Stop/restart the server, load that save
   and try Start again: it must still be blocked. Provider/model persist, consent stays unchecked.
   Re-entering/loading the API key must not grant upload consent. No paid successful retry is
   required for this check; stop here and report if anything starts unexpectedly.
5. If these checks pass, report the commit, Windows/WSL, browser and any remaining issue.
   Existing acceptance evidence remains valid. The remaining full package-B workflow gate and
   final EN–PL terminology approval are separate; do not repeat installation checks after updates.

[Full B workflow reference](GUI_PACKAGE_B_TEST_CHECKLIST.md).
[Deferred install/uninstall qualification](INSTALLER_QUALIFICATION_PLAN.md).
