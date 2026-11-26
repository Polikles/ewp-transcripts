# EWP Transcriber

Local-first transcript workflow for podcasts and similar recordings: local GPU or optional cloud ASR, human correction, optional translation and verified subtitle exports. The executable is `transcriber`; the GUI is served locally, with a dedicated Windows window for managed installations.

[English user manual](docs/gui/README.md) · [Polska instrukcja użytkownika](docs/gui/pl/README.md) · [Quick start](Instructions/GUI_QUICKSTART.md) · [Advanced CLI runbook](Instructions/README.md)

## Current status

Version 0.26.0 is an internal preview on `main`, with managed installation/update/removal, a standalone Windows wizard and a dedicated Windows application window. Installer and desktop qualification are recorded separately from GPU inference. The owner has accepted the current GUI, EN/PL interface copy and focused Windows workflow fixes. Native Windows 11 x64 and WSL2 Ubuntu 24.04/26.04 are the current paths; the reference GPU is RTX 3090 with 24 GB VRAM. Other NVIDIA GPUs with at least 8 GB VRAM are expected to work without a compatibility or performance guarantee. Full portable-profile exchange has provisional owner acceptance rather than complete manual qualification. Windows AMD ASR is available as **experimental**, with CPU word alignment/diarization and no physical AMD inference qualification; see [AMD implementation and limits](docs/AMD_EXPERIMENTAL.md).

The workflow supports PL/EN/automatic source language, audio and video, synchronized speaker tracks, explicit cancellation/retry, work checkpoints, dictionaries and portable preferences. Recognition and translation quality still require human checking. Latest cloud qualification used short Polish samples; no representative English sample was supplied. Broad research benchmarks and hardware studies are optional, not everyday prerequisites. See the [scope and roadmap](docs/99-roadmap-v2.md).

## Install and launch

Use the standalone Windows wizard `EwP-Setup-0.26.0.exe`, or the terminal packages below.
Current acceptance builds are attached to [Installer build and Windows startup](https://github.com/Polikles/ewp-transcripts/actions/workflows/distribution.yml) (GitHub sign-in may be required), and supplied in the owner handoff. Public release downloads/online launchers remain pending the deliberate first public release. The test EXE is unsigned. No manual repository clone or preinstalled Python/uv is needed for these packages.

Windows PowerShell, after downloading `EwP-0.26.0-windows-x64.zip`:

```powershell
Expand-Archive .\EwP-0.26.0-windows-x64.zip -DestinationPath .\EwPSetup
powershell -ExecutionPolicy Bypass -File .\EwPSetup\control\Install-EwP.ps1 -Bundle .\EwP-0.26.0-windows-x64.zip -Local -AcceptModelTerms
```

Ubuntu 24.04/26.04, including WSL2, after downloading the corresponding tar.gz:

```bash
mkdir -p EwPSetup
tar -xzf EwP-0.26.0-ubuntu-x64.tar.gz -C EwPSetup
bash EwPSetup/control/Install-EwP.sh install --bundle "$PWD/EwPSetup/bundle.zip" --local --accept-model-terms
```

Accept the linked [pyannote model terms](https://huggingface.co/pyannote/speaker-diarization-community-1) first. The HF read-token prompt is hidden; complete cached snapshots are reused. Omit the local/model flags for cloud-only or existing-result review. An OR key is optional and never required for local work. Check `SHA256SUMS.txt`; let the installer finish before closing it. The wizard offers host tests, model/token fields, optional deliberate OR OS-store save and a desktop launch shortcut. Read [complete EN installation/update/uninstall instructions](docs/gui/installation.md) or [pełne instrukcje PL](docs/gui/pl/installation.md).

For a development/source checkout, existing scripts remain supported:

```text
# Windows: powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
# Ubuntu: ./scripts/install-fresh-ubuntu.sh --install
uv run --locked transcriber gui
```

Source model preparation is a separate explicit step: `scripts/setup-models.py` on Windows or `./scripts/setup-models.sh` on Ubuntu. Save work/stop the server before a source update, then `git pull --ff-only` and `uv sync --locked`. Managed installs use their Update/Repair/Rollback actions instead. Neither path silently starts ASR or redownloads every model. See [versioning and delivery policy](docs/VERSIONING.md).

## Normal workflow

1. Choose the output folder and add audio/video or existing canonical result JSON.
2. Dry-run checks all unqueued selections. Review/confirm the plan, Add to queue, then Start queue.
3. Optionally generate assisted correction, or go directly to source review.
4. Correct speakers/text, Apply the draft, confirm manual verification, Save and prepare for export, then export subtitles.
5. Optionally translate, review meaning, save a verified translation and export it.

The default raw ASR files are `*_results.json`, `*_segments.json` and `*_transcript.txt`. They are not manually verified publication files. Canonical JSON stays unchanged; verified source revisions and translations are immutable. GUI source exports default to `exports`; translation exports use `translation-exports`. See [files and downloads](docs/gui/outputs.md) and [saving/backups](docs/gui/saved-work.md).

## Local processing and optional providers

Local ASR uses pinned Whisper snapshots with pyannote/alignment models. The NVIDIA path uses WhisperX; the experimental Windows AMD path uses an isolated CTranslate2 ROCm/HIP worker for ASR and CPU alignment/diarization. Install/Update detects AMD display adapters and requires the experimental-support acknowledgement. AMD CPUs alone do not select this profile. [AMD setup, runtime pins and qualification](docs/AMD_EXPERIMENTAL.md) describe the additional download and hardware limits. Optional OpenRouter ASR uploads audio; assisted correction/translation sends text to OpenRouter or a separately operated LM Studio endpoint after scoped consent. Provider prices, availability and data policies can change. No API response is human approval. Cloud ASR requires real word timestamps and splits long audio into bounded requests; paid retries are explicit.

One OpenRouter key serves ASR, correction and translation. It can live only in the GUI server's memory or be deliberately saved in the OS credential store. Connected browsers share the server's active key. Workspaces/profiles/browser storage never contain it or upload/verification confirmations. The app is a single-user loopback tool, not a multi-user hosted service.

## Documentation and development

- [Complete EN manual](docs/gui/README.md) and [complete PL manual](docs/gui/pl/README.md).
- [Advanced CLI](Instructions/README.md), [Windows](Instructions/WINDOWS_NATIVE.md), [Ubuntu upgrade repair](WSL%20config/UBUNTU_UPGRADE.md).
- [Configuration defaults](src/ewp_transcripts/resources/default-config.toml), [schemas](schemas), [examples](examples).
- [AMD acceleration (experimental): implementation, installation and limits](docs/AMD_EXPERIMENTAL.md).
- [Native Windows application: window, lifecycle and qualification](docs/NATIVE_WINDOWS_APP.md).
- [GitHub Actions: builds, Windows checks and costs](docs/GITHUB_ACTIONS.md).
- [Changelog](CHANGELOG.md), [testing strategy](docs/TESTING_STRATEGY.md), [current checkpoint](WORK_STATUS.md), [tasks](TODO.md), [roadmap](docs/99-roadmap-v2.md).
- [Reviewed EN/PL interface reference](docs/ui-language/README.md), [artwork and third-party notices](src/ewp_transcripts/web_assets/brand/NOTICE.txt).

Run `make check` for lint, formatting, typing and model-free tests. Relevant media/filesystem changes also require `make test-integration`. GPU or paid-provider tests need actual hardware/material and explicit scope; model-free tests do not establish GPU quality. Keep private recordings, transcripts, secrets and generated work out of Git.

## License

Copyright © 2025–2026 Damian Szczech.

EWP Transcriber is free software licensed under the
[GNU Affero General Public License v3.0 only](LICENSE)
(`AGPL-3.0-only`).

You may use, modify, and redistribute the software, including commercially, subject to
the GNU AGPL. Modified versions remain subject to its copyleft requirements, including
the source-code requirements applicable to modified versions used for remote network
interaction.

The software is provided without warranty, as described in Sections 15 and 16 of the GNU
AGPL. Alternative licensing terms may be available directly from the copyright holder.
