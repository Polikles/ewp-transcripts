# EwP Transcripts GUI — quick start in WSL

Current A owner-feedback changes: GUI inspection and planning are one Dry-run action; use the
[focused retest](GUI_PACKAGE_A_RETEST.md). The complete terminology/manual revision remains
after feature completion and owner EN–PL approval.


Use the existing working WSL installation. This preview does not require another model download,
a new distribution, Docker, or a desktop environment. [Consolidated manual test plan](GUI_PREVIEW_TEST_PLAN.md).

Every stage now has numbered Quick steps below the active-recording frame and stage strip.
Click a step to reach its matching controls, or open Full instructions (English) in a separate
tab. The [per-stage guides](../docs/gui/README.md) are bundled for offline use, including optional
correction/translation and the supporting tools. The left recording queue changes the active
editor independently of batch checkboxes. At wide widths the task context is on the right;
at half-screen widths open Recording details in the frame.

Fresh installation automatically prepares compatible native audio libraries. If a later
Ubuntu 24.04 → 26.04 upgrade causes a dependency mismatch, use the
[Ubuntu upgrade recovery guide](../WSL%20config/UBUNTU_UPGRADE.md) instead of reinstalling models.

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

Confirm that this is the transcription project before running `uv`:

```bash
pwd
sed -n '1,8p' pyproject.toml
```

The project name must be `ewp-transcripts`. In particular, `~/waveform/ewp-waveform`
is a separate project and does not supply the `transcriber` command.

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

## If `uv` cannot find `transcriber`

`error: Failed to spawn: transcriber` followed by `No such file or directory (os error 2)`
means the command could not be started. Check the project directory first. The reported
case ran from `~/waveform/ewp-waveform` and printed `Built ewp-waveform`; `uv` prepared
that project's `.venv`, which does not contain `transcriber`. The GUI had not started.

Switch to the existing transcription checkout, using its actual location if different:

```bash
cd "$HOME/transkrypcje/ewp-transcripts" && uv run --locked transcriber gui
```

Use the guarded update/start block above when pulling the recent changes before testing.
No environment deletion or model setup is needed to correct the working directory. If the
same error persists in the confirmed `ewp-transcripts` project, run `uv sync --locked`, then
`uv run --locked --no-sync transcriber --version`, and retain any synchronization error.

## Use the preview

- Choose interface **English / Polski** and **System / Light / Dark** independently of audio language.
- **Settings & About:** optional **Test local dependencies** checks model paths, CUDA and native
  speech-library loading without downloading models or transcribing. A completed test enables
  **Run doctor** and **Reinstall dependencies…**. The repair button provides terminal steps to run
  after saving work and stopping the GUI; see [native repair](../WSL%20config/TROUBLESHOOTING.md).
- Choose a shared output root and select audio/video or saved canonical result JSON. Main picker and
  **Add audio** in the left rail use the same selection. Matching tracks such as `s0e00-Szymon.wav`
  and `s0e00-Damian.wav` form one episode. Set language/count directly per recording; multiple
  audio streams reveal a choice automatically. Dry-run checks/plans all pending episodes in one
  combined table. Review/confirm it, Add to queue once, then Start queue. Selection alone runs no ASR.
  Direct WSL/server paths remain supported; staging preserves durable local source copies.
  Synchronized tracks need matching sample rates; duration differences over 100 ms warn and over
  500 ms block. Changing settings/selection requires replanning.
- Open **Transcription engine** for optional OpenRouter ASR. Manage the shared key, check the key
  and connection, then explicitly refresh model availability/hourly prices and the cost estimate.
  Checks upload no audio. Starting cloud jobs requires fresh upload/payment consent. Cost protection
  is calculated internally; displayed estimates are not provider billing caps.
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

## Diagnose a failed transcription

A failed queue item displays its diagnostic code, message and **Failure technical details (JSON)**.
In **Settings & About**, run **Test local dependencies** and expand **Dependency technical details (JSON)** for failed native
imports. Preserve the displayed code and technical details when reporting a failure; avoid posting
private transcript content. The dependency test does not certify full model loading or GPU execution.

A working `ffmpeg -version` does not prove that TorchCodec can load its required shared libraries.
The locked TorchCodec 0.7 build supports FFmpeg 4–7; an Ubuntu 26.04 installation may instead have
FFmpeg 8. Missing `libavutil.so.56` through `.59` is a native-library compatibility problem, and
re-running `uv sync --locked` alone does not supply those OS libraries. Check `ffmpeg -version` and
the failed import details before changing the environment. Keep the pinned Python package versions;
stop the GUI and run `bash scripts/repair-dependencies.sh` from the transcription checkout.
It restores locked audio packages and builds private compatible FFmpeg 7 audio libraries only
when needed. Restart the GUI and rerun the test in Settings & About. See
[native repair details](../WSL%20config/TROUBLESHOOTING.md).
Never rename or symlink incompatible versioned FFmpeg libraries to make an import pass.
See [the pinned TorchCodec installation notes](https://github.com/meta-pytorch/torchcodec/tree/v0.7.0#installing-torchcodec).
The reported pyannote `torchcodec is not available. Cannot read audio file` queue failure
matches this dependency issue. The repair passes actual TorchCodec and pyannote WAV decoding
on the development VM; full model/GPU execution still needs the bounded WSL retry.

The output-folder chooser is a host desktop dialog, launched through PowerShell under WSL. Browser
CSS cannot style it. DPI awareness/visual styles are enabled, and automatic shell upgrading is
requested when supported by the host .NET runtime; Windows PowerShell's older runtime may retain
its legacy folder dialog. The direct output-path field remains available. Check appearance and
text sharpness on the actual Windows display; the Linux VM cannot qualify that behavior.

## Package A maintenance and downloads

Queue rows offer Cancel task and Retry from beginning. Running cancellation waits for a safe
stage boundary; final publication cannot be cancelled. Settings & About has a separate temporary
workdir inventory with filters and preview/confirmation. Both review/export stages offer hash-bound
Existing export downloads, including after saved-work recovery, without ASR or re-exporting.
Use the focused [package A checklist](GUI_PACKAGE_A_TEST_CHECKLIST.md) for owner acceptance.
