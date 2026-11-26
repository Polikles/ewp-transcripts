# Native Windows setup and repair

## Managed launch and shutdown

### AMD (experimental)

On AMD-only Windows installations, ASR can use the experimental ROCm profile; alignment and
speaker diarization use CPU. AMD support has not been tested on a physical AMD card. Install/Update
shows an acknowledgement after detecting an AMD display adapter, including mixed GPU computers.
Keep the AMD driver current and read automatic diagnostics before local transcription. The installer
downloads verified AMD runtime libraries; existing model snapshots are reused. See the
[AMD compatibility/qualification notes](https://github.com/Polikles/ewp-transcripts/blob/main/docs/AMD_EXPERIMENTAL.md).

The window remembers its last position, normal size and maximized state. Without valid saved
geometry it uses the centered default. Windows brings an off-screen saved position back onto
an available display. Personalization in Settings & About → User profile controls the title bar.
Saving and shutdown progress appears centered in the opposite theme for contrast.

Since0.25.0 the managed shortcut opens a dedicated EwP Transcripts window without PowerShell
or a separate browser. Opening the shortcut again brings that window forward. Closing saves pending
files, workspace state and transcript edits before stopping the application. During active work choose
Keep working, Wait and close, or Stop and close. Save failure keeps the window open. Restart restores
work without automatically planning or starting the queue. Update/uninstall request the same save and
close; a failed save blocks removal.

The window requires Microsoft WebView2 Evergreen Runtime. A missing-runtime message links to
Microsoft's runtime page. .NET libraries are included. Window preferences and the renderer profile
live under `%LOCALAPPDATA%\EwPTranscriptsState\desktop`; work-state keeps its existing location.
Explicit browser mode remains available through `launch.ps1 -Browser`; closing that browser leaves
the server running, so stop it with Ctrl+C in its terminal. Restoring a retained version older
than0.25.0 uses its browser launch mode.


This page covers source-checkout setup/repair. For the new managed wizard and terminal bundles, use [Installation and updates](installation.md). Managed private FFmpeg is below its installation root, not the separate source-checkout default. The application workflow was owner-tested on Windows 11; new managed installation acceptance is recorded separately.

1. Follow [Installation and updates](installation.md) for Git, uv, the NVIDIA Windows driver and Microsoft Visual C++ x64 runtime.
2. In a separate Windows checkout, run `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install`.
3. For local ASR, run `uv run --locked --no-sync python scripts/setup-models.py` after accepting the gated model terms.
4. Run `uv run --locked transcriber doctor --test-speech-runtime`, then `uv run --locked transcriber gui`.

The PowerShell execution-policy override applies only to that invocation. The script uses Python 3.12, locked CUDA 12.8 packages and SHA-256-pinned FFmpeg 7.1.1 shared files. It does not change global PATH, install a GPU driver or fetch models by default. `-SetupModels` requests the separate model stage; `-PublicOnly` skips its gated snapshot. Do not share WSL's virtual environment.

Private FFmpeg is normally under `%LOCALAPPDATA%\ewp-transcripts\ffmpeg-7`. Launch prepares process-specific media/Torch DLL lookup. An explicit `EWP_FFMPEG_PREFIX` can point to another supported shared-build root containing `bin`. A system FFmpeg executable or static build alone does not provide the compatible DLLs required by TorchCodec 0.7.

For an AMD source checkout, set `$env:EWP_LOCAL_ACCELERATOR='amd'` before setup/repair and
use `uv run --locked --no-sync` for doctor, model preparation and launch. Ordinary uv sync can
replace the HIP overlay with the base NVIDIA wheel; rerun AMD setup/repair if that happens.
The source commands above otherwise describe the NVIDIA baseline. See the
[AMD source procedure](https://github.com/Polikles/ewp-transcripts/blob/main/docs/AMD_EXPERIMENTAL.md).

At first launch the blank startup window follows Windows light/dark appearance. Later launches
use the saved application theme; system selection continues following Windows. Loading and empty
closing surfaces use that same background, while the centered save/shutdown popup keeps its
contrasting theme. Left and right half-screen Snap restoration is owner-confirmed.

## Repair

Save work and stop the GUI, then run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Repair
uv run --locked transcriber doctor --test-speech-runtime
```

This restores locked TorchCodec/pyannote packages and the private FFmpeg runtime. Retain diagnostic details for CUDA/cuDNN/Visual C++ errors rather than replacing packages at random. Do not substitute FFmpeg 8+ for the pinned shared build. Normal updates use `git pull` and `uv sync --locked`; working setups do not need routine reinstalls.

Models normally live below `%USERPROFILE%\.cache\huggingface`. Native paths such as `C:\Users\name\Podcast files\Żółć.wav` remain native; use ordinary user directories. System directories and symlink/junction targets are blocked. Portable profiles do not copy recordings: move output/media trees separately and check missing paths.

If older model setup reports `Blocked import of regex`, update and rerun the same model command. Current language-data setup uses an isolated child outside the checkout; no disabling of NLTK import security is needed. Native install, local/cloud workflow and restart checks have passed owner tests on Windows 11 x64/RTX 3090; this does not qualify every machine.
