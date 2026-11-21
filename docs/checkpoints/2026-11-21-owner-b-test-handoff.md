# Owner package B installation/testing handoff

Date 2026-11-21. Product baseline main 134eba8. Owner asks how to install/run native Windows
and what to test. No product changes; B native Windows/full WSL acceptance remains pending.

Read scripts/setup-windows.ps1, scripts/setup-models.py, Instructions/WINDOWS_NATIVE.md and
Instructions/GUI_PACKAGE_B_TEST_CHECKLIST.md before explaining commands. Native Windows uses
PowerShell and its own user-directory checkout/.venv. Prerequisites: NVIDIA Windows driver,
Visual C++ x64 Redistributable, Git and uv. Install script prepares Python 3.12, locked packages,
private SHA-256-pinned FFmpeg shared runtime and doctor; explicit setup-models.py prepares local
snapshots after user download confirmation and gated HF read token/terms. GUI launch is
uv run --locked transcriber gui; server prints loopback URL, Ctrl+C stops it. Preserve diagnostic
failures instead of proceeding blindly with local ASR. Test Windows and WSL sequentially.

Owner sequence: native install/doctor/GUI first; short PL two-track + MP4 local transcription,
manual correction and exports; shared OpenRouter key/OS storage; cloud short samples then >2 min
mixed Scribe/MAI to exercise default chunking/boundaries; saved-work/restart; cross-OS portable
profile/dictionary/project refs; same full workflow in WSL. Whisper uses one speaker/separate
tracks, Scribe/MAI mixed audio. No accuracy/model benchmark. Record per-OS passed/failed/code/
terminal details without credentials. Canonical/raw outputs are not a verified publication.

Existing full checklist is authoritative; this checkpoint preserves the explained start order.
English manuals/complete PL documentation wait for B acceptance and task-10 terminology approval;
artist ZIP stays frozen. No additional paid calls/model downloads or product tests in this handoff.
