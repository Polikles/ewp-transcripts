# Ubuntu upgrade: repair speech dependencies

1. Save work, stop the GUI and keep the failed speech_runtime technical details.
2. In the transcriber checkout, run `bash scripts/repair-dependencies.sh`.
3. Run `uv run --locked transcriber doctor --test-speech-runtime`, restart the GUI and repeat Test local dependencies.
4. Retry the failed/cancelled job explicitly after checks pass. Model downloads are not part of this repair.

## If this started after Ubuntu 24 → 26

Ubuntu 24.04 and 26.04 under WSL2 are accepted. A system upgrade can replace FFmpeg libraries while the locked Python environment still uses TorchCodec 0.7. Having `ffmpeg` and `ffprobe` commands available does not establish compatible shared libraries. Errors mentioning missing `libavutil.so.56` through `.59` are evidence to check the shared-library ABI.

The repair script restores locked TorchCodec/pyannote packages. If native decoding still fails, it downloads verified FFmpeg 7.1.5 source and builds private audio-only shared libraries. System FFmpeg is preserved; the private build is for internal PCM audio, not a replacement for the system's general video decoder. Network access and compiler tools are needed; the script prints a concrete missing-tool instruction when applicable. A failed build retains its own build log.

Use `--native-only` only when deliberately preserving an already correct locked Python environment. Do not create symlinks pretending that FFmpeg 8 libraries have an older ABI. Do not fix this by randomly upgrading Torch, CUDA or TorchCodec. Existing models, canonical results, revisions and exports remain intact.

For a new WSL installation use [Installation and updates](installation.md). Windows has a different [native repair procedure](windows-native.md). Run repair after a relevant failed check, not after every routine source update.
