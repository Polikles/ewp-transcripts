# EWP Transcriber

Local-first transcript workflow for podcasts and similar recordings: local GPU or optional cloud ASR, human correction, optional translation and verified subtitle exports. The executable is `transcriber`; the browser GUI is served locally.

[English user manual](docs/gui/README.md) · [Polska instrukcja użytkownika](docs/gui/pl/README.md) · [Quick start](Instructions/GUI_QUICKSTART.md) · [Advanced CLI runbook](Instructions/README.md)

## Current status

Version 0.20.0 is an internal preview on `main`. The owner has accepted the current GUI, EN/PL interface copy and focused Windows workflow fixes. Native Windows 11 x64 and WSL2 Ubuntu 24.04/26.04 are the current paths; the reference GPU is RTX 3090 with 24 GB VRAM. Other NVIDIA GPUs with at least 8 GB VRAM are expected to work without a compatibility or performance guarantee. Full portable-profile exchange has provisional owner acceptance rather than complete manual qualification.

The workflow supports PL/EN/automatic source language, audio and video, synchronized speaker tracks, explicit cancellation/retry, work checkpoints, dictionaries and portable preferences. Recognition and translation quality still require human checking. Latest cloud qualification used short Polish samples; no representative English sample was supplied. Broad research benchmarks and hardware studies are optional, not everyday prerequisites. See the [scope and roadmap](docs/99-roadmap-v2.md).

## Install and launch

Follow [Installation and updates](docs/gui/installation.md) for prerequisites and explicit model preparation. Do not share a virtual environment between native Windows and WSL.

Windows PowerShell, inside this checkout:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
uv run --locked --no-sync python scripts/setup-models.py
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

WSL Ubuntu, inside this checkout:

```bash
./scripts/install-fresh-ubuntu.sh --install
./scripts/setup-models.sh
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Model preparation is an explicit download with upstream model terms; normal local transcription does not silently download missing models. Open the printed loopback URL, normally `http://127.0.0.1:8765/`. GUI help includes complete English and Polish user guides offline. An ordinary update is `git pull` then `uv sync --locked` after saving work and stopping the server; it does not require a fresh installation or another model download.

## Normal workflow

1. Choose the output folder and add audio/video or existing canonical result JSON.
2. Dry-run checks all unqueued selections. Review/confirm the plan, Add to queue, then Start queue.
3. Optionally generate assisted correction, or go directly to source review.
4. Correct speakers/text, Apply the draft, confirm manual verification, Save and prepare for export, then export subtitles.
5. Optionally translate, review meaning, save a verified translation and export it.

The default raw ASR files are `*_results.json`, `*_segments.json` and `*_transcript.txt`. They are not manually verified publication files. Canonical JSON stays unchanged; verified source revisions and translations are immutable. GUI source exports default to `exports`; translation exports use `translation-exports`. See [files and downloads](docs/gui/outputs.md) and [saving/backups](docs/gui/saved-work.md).

## Local processing and optional providers

Local ASR uses pinned WhisperX/pyannote/alignment snapshots. Optional OpenRouter ASR uploads audio; assisted correction/translation sends text to OpenRouter or a separately operated LM Studio endpoint after scoped consent. Provider prices, availability and data policies can change. No API response is human approval. Cloud ASR requires real word timestamps and splits long audio into bounded requests; paid retries are explicit.

One OpenRouter key serves ASR, correction and translation. It can live only in the GUI server's memory or be deliberately saved in the OS credential store. Connected browsers share the server's active key. Workspaces/profiles/browser storage never contain it or upload/verification confirmations. The app is a single-user loopback tool, not a multi-user hosted service.

## Documentation and development

- [Complete EN manual](docs/gui/README.md) and [complete PL manual](docs/gui/pl/README.md).
- [Advanced CLI](Instructions/README.md), [Windows](Instructions/WINDOWS_NATIVE.md), [Ubuntu upgrade repair](WSL%20config/UBUNTU_UPGRADE.md).
- [Configuration defaults](src/ewp_transcripts/resources/default-config.toml), [schemas](schemas), [examples](examples).
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
