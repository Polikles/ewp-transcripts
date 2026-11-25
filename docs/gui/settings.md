# Settings & About

Use the numbered steps below with the matching GUI stage.

1. Preferences and profile: Keep ETA off or enable it after calibration. Save, load or transfer one user-profile JSON with preferences, workspaces and dictionaries.
2. Test local dependencies: Run the optional environment test to enable Doctor and repair controls.
3. Read doctor report: Run doctor and inspect failed checks and technical details. Missing HF_TOKEN is harmless with complete offline models.
4. Repair only when needed: Reinstall dependencies opens terminal steps. Save work and stop the GUI before changing its environment.
5. Check application information: Check version, local processing, optional providers, licenses and notices.

## 1. Preferences and profile

Choose theme and interface language independently of recording/translation language. On first launch the interface follows the Windows user interface language (Polish or English; browser preference elsewhere). An explicitly saved interface language takes precedence. Percent and elapsed time are ordinary queue feedback. ETA is off by default and becomes available after three successful comparable local transcriptions on this computer: matching language, models, stream/speaker arrangement and phases. It estimates processing, not human review, and need not be accurate. Timing calibration is not transferred in a profile.

Save profile stores a local snapshot; Load saved profile restores it. Export profile downloads one `ewp-user-profile.json`; Import profile accepts that single JSON. It contains preferences, custom palettes, named locations/recent project references, workspace catalog records and, by default, available dictionary editions. Clear Include dictionaries in profile for a smaller reference-only export; transfer exact dictionaries separately in that case.

A profile does not contain media, transcripts, active jobs, API keys, confirmations or timing cache. It does not replace saving drafts/workspaces or backing up their files. Import merges catalogs without deleting existing workspaces/dictionaries or running the queue. Embedded dictionaries retain exact content/hash in private content-addressed storage. Foreign/missing paths remain visibly unavailable. The profile size limit is 16 MiB.

## Shared OpenRouter key

Manage OpenRouter key opens one dialog for cloud ASR, correction and translation. A typed key can be set with Set session only. Save key deliberately stores it in the OS credential store; Use saved key immediately activates the stored entry for the current server. Set session only is disabled when input is empty; it is unnecessary after Use saved key. Check API key verifies typed input without activating it, or checks the active key if input is empty. If neither session nor environment supplies a key, this explicit check loads the saved OS key and activates it only after a successful connection check. Its result is shown beside the button. It sends no audio/transcript.

Clear session key removes the server-memory entry; Remove saved key deletes the OS entry and clears the session entry. An environment-supplied `OPENROUTER_API_KEY` can still apply until removed from the launching terminal. Close window, × or Escape closes the dialog and clears unsubmitted input, retaining deliberately activated keys. Clearing browser/workflow data does not clear a running server's active key. Restarting loses memory-only keys. Checking the connection loads the saved OS key when no typed, session or environment key is available. The success message confirms the saved key was loaded and that no audio was uploaded. This never grants upload consent or starts transcription.

Windows uses Credential Manager. Linux/WSL requires an available Secret Service; there is no plaintext fallback. Store access can prompt to unlock it. Browsers connected to one local server share its active key; this is a single-user deployment. Keys never enter portable profiles, workspace JSON, transcript files or browser storage. Provider consent is always separate from key availability.

## 2. Test local dependencies

Use this when installing or diagnosing a local runtime problem, not as a mandatory workflow step. It checks Python/platform, FFmpeg/ffprobe, GPU/CUDA, speech-library loading and pinned snapshots in bounded processes without downloading models or transcribing. Completed testing enables Doctor and repair controls. A working FFmpeg executable alone does not prove TorchCodec's shared libraries load.

## 3. Read doctor report

Read failed checks and expand technical details when needed. Native Windows 11 and WSL Ubuntu 24.04/26.04 are accepted baselines. A missing HF_TOKEN is harmless with complete offline snapshots. For a terminal report use `uv run --locked transcriber doctor --test-speech-runtime`; ordinary doctor stays model-lazy. Passing diagnostics establishes readiness checks, not complete recognition quality or all possible model/GPU execution paths.

## 4. Repair only when needed

Save work, stop the GUI and follow the platform-specific terminal repair instructions. [Windows](windows-native.md) uses `scripts/setup-windows.ps1 -Repair`. [Ubuntu upgrade recovery](ubuntu-upgrade.md) uses `bash scripts/repair-dependencies.sh`. Repair restores locked Python/native audio dependencies; it is not a new model download or deletion of previous results. Do not run installers merely to test an ordinary update that is already working.

## Temporary work directories

Refresh the inventory, filter retention reason/minimum age, select unprotected rows and Preview cleanup. Read count and size, then Confirm deletion within five minutes. A changed selection/reference requires another preview. Active tasks, known queue/workspace references, unknown files and legacy directories without known ownership are protected. Only the configured temporary root is inspected. Inspect other workspace catalogs separately. This operation is distinct from managed-source cleanup, and never targets published results or models.

## 5. Check application information

About shows application/API version, processing scope, licenses and artwork notices. Local GPU work stays local after setup; optional providers have their own policies and fees. Error codes and technical JSON are diagnostic references, not normal workflow steps. Read [Troubleshooting](troubleshooting.md) before sending a report; omit secrets and private transcript/audio content.
