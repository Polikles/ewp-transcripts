# Command-line reference

1. Run from the transcriber checkout; quote paths containing spaces.
2. Use `uv run --locked transcriber --help`, then the selected command's `--help` before using options.
3. Keep canonical source JSON unchanged. A CLI preview and a GUI button with an approved user-facing name can have different publication semantics; follow the command's help.

## Common commands

```text
uv run --locked transcriber --version
uv run --locked transcriber gui --help
uv run --locked transcriber doctor --help
uv run --locked transcriber inspect --help
uv run --locked transcriber dry-run --help
uv run --locked transcriber transcribe --help
uv run --locked transcriber export --help
uv run --locked transcriber clean --help
```

`inspect` remains a separate CLI diagnostic even though the GUI merges inspection into Dry-run. `dry-run` plans without creating result/work directories or loading models. `transcribe` runs the local transcription path; use the GUI for cloud ASR and its exact queue upload authorization. `export` regenerates raw exports from canonical JSON without audio/ASR. `clean` previews marker-verified temporary directories; it is not GUI source cleanup or an uninstaller.

## Configuration

Precedence is packaged defaults → preset → user config → optional `transcriber.toml` in the current directory → explicit `--config` file → command options. Not every command exposes every option; use its help. User config defaults to `~/.config/ewp-transcripts/config.toml`. Packaged defaults are in `src/ewp_transcripts/resources/default-config.toml`; there is no required tracked root `transcriber.toml`. Create one only for deliberate overrides and keep secrets out of it. GUI per-recording selections are recorded separately in plans/workspaces.

Use native user paths in Windows, or server-visible Linux/Windows-drive paths in WSL. Quote the complete path. Multi-file grouping, duration/sample-rate checks, immutable output versions and offline model rules still apply from the CLI.

## Review, translation and dictionaries

```text
uv run --locked transcriber revise --help
uv run --locked transcriber translate --help
uv run --locked transcriber dictionary --help
uv run --locked transcriber benchmark --help
```

`revise` prepares editable source review, validates it and publishes immutable revisions. Its `correct` provider path generates assistance and may incur charges even in preview. `translate` prepares manual translation, validates, publishes, audits and exports; `automate` creates a non-final candidate. `dictionary` proposes mappings from exact result/revision pairs and publishes reviewed decisions. `benchmark` is an advanced private research/evaluation tool, not required for the normal podcast workflow.

For complete advanced flag examples, see the repository's [CLI runbook](../../Instructions/README.md). All CLI diagnostics/help preserve technical English codes. The Polish manual explains the ordinary terminal workflow; it does not translate executable command names, flags or JSON fields. GUI workspaces/profiles are managed in the GUI, not by inventing command names.

## Local CLI example

Replace these paths and the exact generated filenames with your own. After prepare, edit the generated source review before preview/apply. For translation, fill each target line between prepare and preview. Never change machine-owned headers/source lines. These commands run real transcription/publication when invoked; read their help first.

```text
uv run --locked transcriber dry-run "recordings" --output-dir "output"
uv run --locked transcriber transcribe "recordings" --language pl --output-dir "output" --non-interactive
uv run --locked transcriber export "output/episode_results.json" --format srt --format vtt --output-dir "raw-exports"
uv run --locked transcriber revise prepare "output/episode_results.json" --output-dir "reviews"
uv run --locked transcriber revise preview "reviews" --results-dir "output"
uv run --locked transcriber revise apply "reviews" --results-dir "output" --output-dir "revisions" --audit
uv run --locked transcriber export "output/episode_results.json" --revision "revisions/episode_revision_001.json" --format srt --output-dir "exports"
uv run --locked transcriber translate prepare "output/episode_results.json" --revision "revisions/episode_revision_001.json" --target-language en --output-dir "translation-reviews"
uv run --locked transcriber translate preview "translation-reviews" --results "output" --revisions-dir "revisions"
uv run --locked transcriber translate apply "translation-reviews" --results "output" --revisions-dir "revisions" --output-dir "translations"
uv run --locked transcriber translate export "translations" --format srt --format vtt --output-dir "translation-exports"
```

Provider assistance uses `revise correct` or `translate automate`. Read their `--help`, readiness/disclosure and cloud opt-in options before making a paid call; the GUI is the guided path for shared-key and per-job consent management. No API key is needed for the local example.
