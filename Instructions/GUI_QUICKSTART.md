# EwP Transcripts GUI — quick start in WSL

Use the existing working WSL installation. This preview does not require another model download,
a new distribution, Docker, or a desktop environment. [Consolidated manual test plan](GUI_PREVIEW_TEST_PLAN.md).

## Open WSL and the existing checkout

In **Windows PowerShell**, list distributions and open the existing Ubuntu 26.04 distribution:

```powershell
wsl.exe --list --verbose
wsl.exe -d "NAME-FROM-THE-LIST"
```

The distribution's registered name is installation-specific; do not create a second installation.
Inside WSL, the documented checkout location is:

```bash
cd "$HOME/transkrypcje/ewp-transcripts"
```

If it is elsewhere, enter that existing directory instead. If necessary, locate it with
`find "$HOME" -maxdepth 4 -type d -name ewp-transcripts 2>/dev/null`.
Do not clone over an existing checkout. The VM path in development reports is not your WSL path.

## Copy-paste update and start

Run in the checkout. The guard stops the update/start if there are local changes; it never resets,
stashes or discards them. A failed fast-forward also prevents startup from continuing.

```bash
git status --short
if test -z "$(git status --porcelain)"; then
  git pull --ff-only &&
  git log -1 --format='%H %s' &&
  uv run --locked transcriber gui
else
  printf '%s\n' 'STOP: local changes exist. Preserve/review them before updating.'
fi
```

Compare the printed **full SHA** with the delivered SHA in the implementation report before testing.
`main` may later contain newer commits: record the SHA you actually run. No tag/public release is needed.

`uv run --locked` uses the supported Python 3.12 project environment and synchronizes it only when
needed by the checked-in lock/project metadata. This preview preserves the ML dependency versions.
A one-time editable package rebuild may be needed for the new application version. If you want to
separate environment preparation from launching, use:

```bash
uv sync --locked
uv run --locked --no-sync transcriber gui
```

Do not run `uv lock`, upgrade packages, or rerun model setup merely to test this GUI. Downloads needed
for packaging/dependency preparation require connectivity; manual review/export needs no models.
If `uv` is missing from PATH in a new terminal, use `source "$HOME/.local/bin/env"` when that file exists.
An optional `source .venv/bin/activate` is supported; activation is unnecessary with `uv run`.

## Browser and terminal

The server prints:

```text
GUI http://127.0.0.1:8765/
Press Ctrl+C to stop.
```

Keep this terminal running. A Windows browser should open automatically. If it does not, paste
**http://127.0.0.1:8765/** into the Windows browser. You can disable automatic opening explicitly:

```bash
uv run --locked transcriber gui --no-open-browser
```

If port 8765 is occupied, use `--port 8766` and the matching printed URL. Do not change the server to
listen publicly. Check that the banner says **EwP Transcripts** and Settings & About shows **0.20.0**.
A stale tab should be reloaded after updating; required resources are served locally without a CDN.

## Use the preview

- Choose interface **English / Polski** and **System / Light / Dark** independently of audio language.
- **Transcribe:** choose a shared output root, select several audio files, then inspect, dry-run and
  explicitly stage each. **Start queue** begins processing; picking files alone does not run models.
  Direct WSL/server paths remain supported. The browser copies selected audio locally; staging makes
  the selected source durable under the chosen root.
- Existing canonical `*_results.json` / versioned results can be imported from stage queues to skip ASR.
- Use **Source review & export** for text/speaker edits, Preview, explicit human Apply and source export.
  Cursor splitting and selected-text isolation are separate commands. Neither invents timestamps.
- **Optional translation** offers assistance or **Open manual translation**. Review meaning separately
  in **Translation review & export** before translated publication.
- Dictionaries are optional. Provider checks, exact-model choices and scoped consent remain in the
  optional stages. Never paste API keys into paths, workspace names, feedback or screenshots.
- **Saved work & cleanup:** explicitly save before stopping. Auto-save defaults off. The workspace
  references files; back up the output root including dot-directories and any separate workspace catalog.

The color panel retains stable speaker IDs and custom overrides. **Adopt brand palette** is explicit;
brand exports create new versions. **Configured production palette** preserves the qualified YTT setup.
Previously generated files are not recolored. New palette YouTube qualification remains pending.

## Stop, restart and recover

Use **Save current work state**, note the workspace catalog/name and output root, then press **Ctrl+C**
in the server terminal. Restart with the same command. Under **Saved work & cleanup**, select the same
catalog, refresh, select the saved workspace and load it. Check exact recording/draft identity rather
than merely counting queue rows. Interrupted transcription starts again; it is not a GPU checkpoint.
Server-memory provider keys must be entered again after restart. Confirmation boxes are not restored.

If startup fails, retain the diagnostic code and a short relevant terminal excerpt without secrets or
transcript text. Follow [the test plan](GUI_PREVIEW_TEST_PLAN.md) for one consolidated acceptance session.
