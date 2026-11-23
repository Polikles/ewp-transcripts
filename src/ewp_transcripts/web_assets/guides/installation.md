# Installation and updates

## Choose installation mode

1. For the Windows graphical installer, run `EwP-Setup-0.22.1.exe` and follow the wizard below.
2. For terminal installation, download the Windows ZIP or Ubuntu tar.gz/ZIP and run the short commands below. No manual repository checkout or preinstalled Python/uv is required.
3. Keep an existing source checkout if that is how you develop/run the app; use the source-update section instead of treating it as a managed installation.

Managed installation was introduced in0.22.0;0.22.1 corrects the graphical wizard. Current test artifacts are provided with the owner handoff and by the repository's Installer build and Windows startup Actions workflow. Public online bootstrap URLs are activated only when the matching versioned release is published. Do not try a guessed download URL. The GUI EXE is currently unsigned; no code-signing certificate has been supplied.

Current targets are Windows 11 x64 and Ubuntu 24.04/26.04, including WSL2. Existing application workflow tests on Windows/WSL remain accepted. The new managed lifecycle has real Ubuntu VM evidence; native Windows 11 installation/removal acceptance is separate from compiling or launching the wizard on a Windows CI runner. Reference GPU: RTX 3090 24 GB. At least 8 GB on another NVIDIA GPU remains an unqualified expectation.

## Windows wizard

Run `EwP-Setup-0.22.1.exe` from a normal user account. It embeds the application bundle,
its own graphical runtime and the centered framed EwP icon, not multi-GB model data.

1. **Action and language.** Select English/Polski and one radio action: Install, Update, Repair,
   Add local models, Restore previous version or Uninstall. The next screen follows that choice.
2. **Folder and computer.** For Install, choose **Program installation folder**, separate from
   recordings and the old Git checkout. Free space on that volume is checked automatically;
   Next is blocked below **25 GB** (20 GB installation plus5 GB free margin). Run **Check this
   computer** for CPU model, OS, disk, NVIDIA GPU/driver and Visual C++ readiness. Results use
   OK and change language immediately with the language selector. The Visual C++ link opens
   Microsoft's instructions; it does not trigger a direct executable download. Install a missing
   NVIDIA driver separately. Host tests prepare a small private Python runtime if needed.
3. **Local models and keys.** Select **Use local models on my GPU…** to show the fixed checked
   model list and required space (about8.4 GB before cache reuse, plus sentence data). Existing
   exact files are reused; the model-cache volume is checked separately. Use **Enter Hugging Face
   token** to open a masked dialog. Pasting checks automatically; **Check token** repeats it and
   **OK** accepts a valid result. The main page then shows Token valid and enables the separate
   pyannote terms acknowledgment. The (i) popup gives account/access/read-token steps and a link
   to [full HF instructions](https://github.com/Polikles/ewp-transcripts/blob/main/Instructions/HUGGINGFACE_ACCESS.md). The token is transient.
   The optional OpenRouter key has the same masked/checked flow. Its main-page description explains
   that it can be configured later. A confirmed key is saved deliberately in the OS store only
   during installation; no audio or cloud-use consent is granted.
4. **Installation and result.** Next starts the selected operation. The custom gear and stage
   feedback show activity. Back/Next/Cancel form the navigation; cancellation during preparation
   stops child work safely and preserves the prior active program and downloaded cache.
   The short final activation/removal steps must finish before closing. After success, launch
   from the wizard or desktop shortcut. Licenses/artwork stays bottom-left on every screen;
   Save report is a link directly below Technical details/log, with Close bottom-right.

Maintenance asks for the existing managed location. Update uses the embedded target version;
Repair and Add local models require a matching installed version so they do not silently upgrade
an older installation. Add local models uses the same pinned model/access checks. Rollback omits
model/key forms. Uninstall shows a removal preview and default-preserve model/key choices before
its explicit confirmation. Windows Add/Remove Programs opens this matching wizard.

Without local models, use OpenRouter ASR or review/export existing results; the program's normal
recording default remains local GPU. OR is optional and never required for local work. No token
or key is written to a profile, report or plaintext fallback. See [Settings](settings.md).

## Terminal installation from the downloaded package

Windows PowerShell, from the directory containing the downloaded ZIP:

```powershell
Expand-Archive .\EwP-0.22.1-windows-x64.zip -DestinationPath .\EwPSetup
powershell -ExecutionPolicy Bypass -File .\EwPSetup\control\Install-EwP.ps1 -Bundle .\EwP-0.22.1-windows-x64.zip
```

Add `-Local -AcceptModelTerms` after accepting the upstream gated-model terms to prepare local models. The token prompt is hidden; blank can reuse complete models. Add `-SaveOpenRouterKey` only if you want a separate hidden prompt and explicit OS-store save. `-Root 'D:\Apps\EwP'` chooses a custom empty location. The execution-policy override applies to this invocation only. Keep filenames/paths quoted when they contain spaces.

Ubuntu 24.04/26.04, from the downloaded tar.gz directory:

```bash
mkdir -p EwPSetup
tar -xzf EwP-0.22.1-ubuntu-x64.tar.gz -C EwPSetup
bash EwPSetup/control/Install-EwP.sh install --bundle "$PWD/EwPSetup/bundle.zip"
```

Add `--local --accept-model-terms` for local models, `--save-openrouter-key` for an optional hidden OR prompt, or `--root "$HOME/Apps/EwP"` for a custom directory. Missing Ubuntu prerequisites can be installed with an explicit sudo prompt. Do not install a Linux display driver inside WSL; the Windows NVIDIA driver provides WSL CUDA. A bare-metal Ubuntu compatibility claim requires actual execution evidence, not inference from WSL alone.

Use the accompanying SHA256SUMS file to check downloaded artifacts. Online entry scripts `Install-EwP-0.22.1.ps1` and `.sh` are generated with exact payload hashes for the corresponding release; they cannot download an unpublished release. These scripts and the GUI share the same lifecycle manager, dependency lock and model rules.

## Managed update and rollback

Save work/backups, cancel safely or finish jobs, and stop the running GUI server. A browser tab closing is not enough. The managed launcher holds an activity lock; update/removal refuses while that application is running. A verified dead lock after interruption can be recovered; an unknown/live owner stays protected.

Download the new version's bundle. Use the existing wizard with a selected bundle, or run the new installer at the same root. Terminal examples for the default location:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action update -Bundle 'C:\Downloads\NEW_WINDOWS_BUNDLE.zip'
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action rollback
```

```bash
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" update --bundle '/path/NEW_UBUNTU_BUNDLE.zip'
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" rollback
```

Replace the uppercase bundle placeholder with the actual downloaded file. CLI update/repair retains the existing local-model choice unless `--cloud-only`/`-CloudOnly` or an explicit local choice is supplied. Unchanged complete models do not need downloading again. New/missing gated models still need terms/token confirmation. Private FFmpeg and locked dependencies are verified, then the installed version is checked before atomically switching the active pointer.

A failed preparation keeps the previous active version. Rollback selects the retained verified previous app; it does not rewrite user data. This release does not migrate workspaces/profiles. Do not assume an arbitrary future schema downgrade is safe. Only the active and immediate previous runtime need to be kept; older app-owned files are pruned after successful activation, preserving added project files. Ordinary outputs/model caches/profiles/dictionaries/keys are not reset by update.

## Managed uninstall

Use Add/Remove Programs/the wizard, or preview in a terminal:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action uninstall
```

```bash
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" uninstall
```

Read the plan. Re-run with `-Yes`/`--yes` to confirm. Optional `-RemoveModels`/`--remove-models` removes the exact recorded snapshots, and `-RemoveKey`/`--remove-key` removes the common saved OR entry. Those choices are independent; default removal preserves them. Custom/unverifiable model locations remain protected. Shared HF blobs still referenced by other snapshots are retained; the whole HF cache is never removed. Models can also be used by other apps, so review that choice carefully.

Original recordings, publications and user state remain outside managed runtime removal. Added unknown files inside an app release are preserved too; the directory can remain nonempty for that reason. Windows finishes locked-file removal after the wizard/interpreter exits. Desktop/registry entries belonging to another install are not removed. Temporary bootstrap runtimes are cleaned when their wrapper closes. Installed Ubuntu launch/rollback/uninstall reuses the existing private Python offline; no new bootstrap download is needed.

A legacy Git checkout is not a managed install and is never removed by guessing its paths. Back it up before any manual cleanup. The new manager can coexist with it and reuse exact model snapshots; transfer profile/workspaces deliberately and check original media paths.

## Source-checkout installation and update

Use a separate checkout/environment on native Windows and WSL. For a new Windows source install, install Git, uv, NVIDIA driver for local ASR and Microsoft Visual C++ x64, then:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
uv run --locked --no-sync python scripts/setup-models.py
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

For a fresh Ubuntu source checkout:

```bash
./scripts/install-fresh-ubuntu.sh --install
./scripts/setup-models.sh
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Model preparation remains explicit. `--public-only` omits the gated diarizer and does not prepare the complete local mixed-speaker workflow. A missing HF_TOKEN is harmless with complete offline models. Normal transcription does not silently download a missing model. Cloud APIs still require network and their own consent.

For an ordinary checkout update, stop/save/back up first, then:

```text
git pull --ff-only
uv sync --locked
uv run --locked transcriber gui
```

Do not reinstall everything or redownload models on every update. Use [Windows repair](windows-native.md) or [Ubuntu upgrade recovery](ubuntu-upgrade.md) after relevant diagnostics. Launch prints the local URL, normally `http://127.0.0.1:8765/`; `gui --no-open-browser` and `gui --port 8766` are available. Closing the browser does not stop processing. See [Saved work](saved-work.md), [Files/exports](outputs.md) and [Troubleshooting](troubleshooting.md) before moving or deleting project files.
