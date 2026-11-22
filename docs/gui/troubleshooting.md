# Troubleshooting

1. Save what you can and record the diagnostic code, application version, platform and operation.
2. Read the relevant entry below; expand technical JSON only when needed.
3. Retry explicitly after fixing the cause. Do not expose an API key or send private media/transcripts in an ordinary bug report.

## Launcher cannot find transcriber

`Failed to spawn: transcriber` occurs before the GUI opens. Confirm that you are in `ewp-transcripts`, not `ewp-waveform`, and that `pyproject.toml`/`uv.lock` belong to this application. Run `uv sync --locked`, then `uv run --locked transcriber --help`. Do not reuse a Windows `.venv` from WSL or vice versa. Installed environments are disposable; saved outputs/model caches are separate.

## GUI unavailable, About stuck at Loading, stale queue

Check that the terminal server is still running and use its printed URL/port. Pull current code, stop and restart the server, then reload the page so JS and server versions match. A browser initialization diagnostic can describe a client error even when the server is reachable; preserve that code. Do not infer a GPU hang solely from a stale page. Closing the browser does not stop work. If needed, reopen the saved workspace after the server is ready.

## Wrong output root or duplicate selection

All active queue jobs use one output root. Finish/remove staged jobs before choosing another. Terminal history alone does not lock output. Dry-run covers all unqueued selections; there is no need to inspect separately or select one episode for planning. Identical name/content is one selection. Different files sharing an episode ID need deliberately distinct identities, not deleting state JSON to bypass checks.

## Local ASR fails although ffmpeg works

Open Settings & About → Test local dependencies, then inspect the failed speech_runtime check and Doctor. A working ffmpeg executable does not prove FFmpeg shared ABI, TorchCodec, Torch and CUDA are compatible. If this began after Ubuntu 24 → 26, follow [Ubuntu upgrade recovery](ubuntu-upgrade.md). Windows uses [its repair script](windows-native.md). Save work and stop the server before changing dependencies. Do not make fake `libavutil` symlinks or randomly upgrade Torch/Codec.

## Model or language data missing

Run the explicit model setup command for your system after accepting required model terms. `HF_TOKEN` is needed for the gated download, not for using already complete local snapshots. If Windows setup reports `Blocked import of regex`, pull the current isolated-language-data script and rerun `uv run --locked --no-sync python scripts/setup-models.py`. Do not disable the NLTK security check. A model setup error differs from a successful setup followed by a decoding error.

## OpenRouter missing key, consent or word times

Before Start queue, enter a key or Use saved key; checking a typed key alone does not activate it. Give fresh consent for current cloud jobs. Neither consent nor a key is embedded in saved work. In a mixed queue, missing/invalid cloud authorization blocks all staged work before processing.

An ASR response without word timestamps cannot complete subtitles. It is a provider/model/endpoint response issue, not a missing workspace input path. Refresh model availability/prices, check credits and choose a supported timed-word path/model before explicit retry. The app restricts Whisper to known timing-capable routes and still validates every response. Changing models can cost money; no automatic paid fallback is performed. Keep failed JSON; deleting it does not repair provider timing.

For API correction/translation, also check endpoint/model readiness and the stage-specific disclosure checkbox. Output remains a non-final candidate until human review.

## Workspace not visible or cannot be saved

Open Saved work & cleanup; recent accessible catalogs are recalled automatically. If needed, select the actual catalog and Refresh or open the manifest directly. Saved work file shows where an older save lives. New saves default to the output folder when the optional catalog is blank; an old private/custom save keeps its own location. To create a separate copy, Save as new with a distinct name. Duplicate names are rejected deliberately. A ZIP of output alone does not include a manifest saved elsewhere.

If files moved, restore media/results and hidden source directories or use a valid transferred workspace. A profile alone contains no media. Load never starts ASR, and staged plans need fresh confirmation. Retry a failed/cancelled row explicitly; do not manually delete failure markers as a restoration technique.

## Apply, export or playback disabled

For source review, Apply validates the draft; then manual verification and Save and prepare for export enable export. For translation, Apply translation and semantic verification are separate from publishing and Save and export. Any new edit requires validation again. Empty target units need explicit omission approval. Hash/lineage mismatch requires the exact original source/revision, not editing IDs.

Playback needs all unchanged source tracks. Reload recording audio after restoring them. The mixed stream shares time zero. Editor sections do not control subtitle segmentation. Refresh existing exports discovers saved files without rerunning ASR or changing their contents.

## Terminal messages

The ONNX `/sys/class/drm` device-discovery warning can appear in WSL even when CUDA is working; use doctor and actual task results to distinguish a failure. Wav2Vec2 `masked_spec_embed` initialization text is a model-loader warning and is not by itself proof that the transcription failed; do not train a model just to silence it. If a task fails, inspect its actual failure code and speech-runtime details. Normal browser audio seeking/closing can abort an HTTP stream; routine disconnects are handled without treating them as an ASR failure. A new unhandled traceback should be reported with its operation and code, without private payloads.
