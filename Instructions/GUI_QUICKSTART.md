# GUI quick start

The current complete instructions are available in [English](../docs/gui/README.md) and [Polish](../docs/gui/pl/README.md), including offline help in the application. Installation is separate from an ordinary update.

## Existing installation

Save work and stop the GUI server. In the same platform's transcriber checkout:

```text
git pull
uv sync --locked
uv run --locked transcriber gui
```

Open the printed local URL. For a new computer follow [Installation and updates](../docs/gui/installation.md); do not treat a manual acceptance checklist as a recurring reinstall requirement.

## First recording

1. Choose a shared output directory, then add audio/video or a completed canonical result JSON. Select synchronized speaker tracks together.
2. Choose language/speaker count per recording. Dry-run checks every unqueued selection; read and confirm its plan, Add to queue, then Start queue. Existing result imports skip ASR.
3. Skip optional LLM correction or generate a candidate after checking provider settings and consenting.
4. Open source review, correct speakers/text and use Apply. Confirm manual verification, Save and prepare for export, then export the required formats.
5. Translate only if needed; review source/target meaning, apply the draft, confirm verification, save and export.
6. Save current work state before ending the session. Back up output files and hidden sources, not only the workspace JSON.

Local-only operation needs no OpenRouter key. Cloud ASR sends audio; correction/translation sends text. A workspace never carries an upload consent or API key. Full help covers [outputs](../docs/gui/outputs.md), [restart/backup](../docs/gui/saved-work.md) and [troubleshooting](../docs/gui/troubleshooting.md).
