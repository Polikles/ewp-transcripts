# Native Windows 11 x64 setup and first checks

This is the repository-based package B path, with the same application, GUI and pinned models
as WSL. Agent checks run on Linux; native Windows/GPU acceptance is performed by the owner.
Use the [full package B acceptance checklist](GUI_PACKAGE_B_TEST_CHECKLIST.md). Keep an existing WSL environment intact.

1. Install the NVIDIA Windows driver and Microsoft's current Visual C++ x64 Redistributable.
   Install Git and uv (`winget install --id astral-sh.uv --exact`), then open a new terminal.
2. Clone/pull this repository into a Windows user directory. Use a separate Windows checkout
   and virtual environment; do not share WSL's `.venv` with Windows.
3. In PowerShell, run `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install`.
   The execution-policy override affects only this invocation. The script uses Python 3.12,
   the locked CUDA 12.8 packages and a SHA-256-pinned private FFmpeg **7.1.1 shared** archive.
   It does not replace system FFmpeg, install drivers or download models by default.
4. Explicitly prepare models: `uv run --locked --no-sync python scripts/setup-models.py`.
   Accept the gated pyannote model's terms first. Supply the read token privately when prompted,
   or through HF_TOKEN in the local terminal. `--public-only` skips the gated snapshot.
   Normal transcription remains offline and does not download missing models.
5. Run `uv run --locked transcriber doctor --test-speech-runtime`, then
   `uv run --locked transcriber gui`.

The private runtime is installed under `%LOCALAPPDATA%\ewp-transcripts\ffmpeg-7`. Launch prepares
its media path and Torch's DLL path for this process; system/user PATH is not rewritten. An
explicit `EWP_FFMPEG_PREFIX` points to another shared-build root containing `bin`.
Model defaults remain below `%USERPROFILE%\.cache\huggingface`; work files use the configured
runtime root. Copy media/output trees separately from portable profiles and check missing paths.

For dependency repair, save work, stop the GUI and run
`powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Repair`.
This restores locked TorchCodec/pyannote packages and the pinned private FFmpeg runtime. Do not
substitute FFmpeg 8+ or a static build: TorchCodec 0.7 needs compatible shared DLLs. If CUDA/cuDNN
or Visual C++ DLLs fail, preserve the doctor technical details for native diagnosis; an ordinary
`ffmpeg -version` success does not prove speech-runtime readiness.

Native paths such as `C:\Users\name\Podcast files\Żółć.wav` stay Windows paths. WSL still maps
Windows drive paths to `/mnt/<drive>/…`. System directories and symbolic-link/junction targets
are blocked in GUI path validation. Prefer ordinary local user directories for the first test.

Runtime evidence: [TorchCodec 0.7 Windows beta support](https://github.com/meta-pytorch/torchcodec/releases/tag/v0.7.0),
[shared FFmpeg archive](https://github.com/GyanD/codexffmpeg/releases/tag/7.1.1),
[Microsoft Visual C++ downloads](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).
Native Windows compatibility is qualified by actual execution, not by the presence of wheels.
