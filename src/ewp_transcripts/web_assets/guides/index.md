# User manual

This manual describes the current 0.23.0 interface. Choose English or Polish in the application; recording language is a separate setting. Every guide is bundled with the program and opens without internet. The same numbered steps appear at the top of each workflow stage. Keep the application tab open while reading help.

## Start here

1. Follow [Installation and updates](installation.md) for Windows 11 x64 or WSL2 Ubuntu 24.04/26.04.
2. [Transcribe](transcribe.md): choose an output folder, add audio/video, plan all recordings, confirm the plan, add to queue and start.
3. [Optional correction](optional-correction.md): generate an assisted candidate or skip assistance.
4. [Source review & export](source-review.md): check speaker names/colors and wording, Apply the draft, confirm manual verification, save a verified revision and export subtitles.
5. [Optional translation](optional-translation.md): skip assistance for manual translation or generate a candidate.
6. [Translation review & export](translation-review.md): compare source and target, apply the draft, confirm meaning, save the translation and export.

The shortest local workflow is Transcribe → Source review & export. Correction dictionaries, LLM assistance and translation are optional. Importing an existing canonical result skips ASR. Completing ASR does not mean the recording is ready for publication.

## Keep work and transfer it

- [Saved work & cleanup](saved-work.md): checkpoints, restart, backups, recent locations and managed source copies.
- [Dictionaries](dictionaries.md): create, compare, edit a new edition, import and export independently.
- [Settings & About](settings.md): portable user profiles, shared OpenRouter key, diagnostics, optional ETA and temporary cleanup.
- [Files and exports](outputs.md): raw results, editable drafts, verified versions and download locations.
- [Troubleshooting](troubleshooting.md), [Windows setup](windows-native.md) and [Ubuntu upgrade recovery](ubuntu-upgrade.md).
- [Command-line reference](cli.md): configuration, command families and safe terminal examples.

## Recommended hardware

For local ASR, a practical starting recommendation is a recent **NVIDIA RTX with 12 GB VRAM or more**,
**32 GB RAM**, a multicore x64 CPU and an SSD. The tested reference is **RTX 3090 /24 GB VRAM**.
The recommendation is not a qualification of every matching card; **8 GB is not yet a tested minimum**.
Architecture matters too: current PyTorch 2.8/CUDA 12.8 binaries exclude Pascal, including GTX 1070.
Later GTX 1070/32 GB/i5-10400F tests must establish a compatible runtime before assessing VRAM headroom.
Allow 25 GB for initial installation plus extra models/media/outputs. Cloud ASR and result review
need no local NVIDIA GPU. AMD Windows remains experimental, with CPU alignment/diarization.
[Hardware detail and qualification](https://github.com/Polikles/ewp-transcripts/blob/main/docs/HARDWARE.md).

## Privacy and supported scope

Local GPU transcription uses explicitly downloaded models. Optional OpenRouter ASR uploads audio; optional API correction/translation sends text. Provider checks and price refresh do not upload recordings. A candidate always needs human review. API keys and upload/verification confirmations are excluded from workspaces and profiles.

This is a single-user local tool for podcasts and similar recordings, not a public multi-user web service. It binds to loopback. Reference testing used RTX 3090 with 24 GB VRAM. The 8 GB target remains unvalidated and requires a compatible GPU architecture/runtime. English is selectable; no representative English sample was supplied for the latest cloud qualification. There is no promised recognition accuracy for any language/model.

The text manual is complete for the current user workflow. Screenshots and final icon artwork will follow separately; they are not prerequisites for using these instructions.
