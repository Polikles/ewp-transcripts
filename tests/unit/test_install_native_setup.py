"""Exercise installer/native ordering without downloads or system changes."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/install-fresh-ubuntu.sh"


def _tool(directory: Path, name: str, body: str) -> None:
    path = directory / name
    path.write_text("#!/bin/bash\nset -eu\n" + body)
    path.chmod(0o755)


@pytest.mark.parametrize(
    ("mode", "fail_native"),
    [("--install", False), ("--verify-only", False), ("--install", True)],
)
def test_install_probes_native_audio_after_sync_and_verify_does_not(
    tmp_path: Path, mode: str, fail_native: bool
) -> None:
    commands = tmp_path / "commands"
    commands.mkdir()
    env = dict(
        os.environ,
        PATH=f"{commands}:/usr/bin:/bin",
        EWP_INSTALL_TEST_ROOT=str(tmp_path),
        EWP_TEST_FAIL_NATIVE="1" if fail_native else "0",
    )
    _tool(commands, "sudo", 'printf "sudo %s\\n" "$*" >> "$EWP_INSTALL_TEST_ROOT/commands.log"\n')
    _tool(
        commands,
        "uv",
        """
printf "uv %s\\n" "$*" >> "$EWP_INSTALL_TEST_ROOT/commands.log"
case "$*" in
  *compatibility_prefix*) printf '%s\\n' "$EWP_INSTALL_TEST_ROOT/native-prefix" ;;
  *"python -") [[ "$EWP_TEST_FAIL_NATIVE" != 1 ]] ;;
esac
""",
    )
    for name in ("git", "ffmpeg", "ffprobe", "curl", "rg", "nvidia-smi"):
        _tool(commands, name, 'printf "available\\n"\n')
    if fail_native:
        _tool(commands, "curl", "exit 7\n")
        for name in ("gcc", "make", "tar", "xz", "sha256sum"):
            _tool(commands, name, "exit 9\n")
    _tool(
        commands,
        "df",
        'printf "Filesystem Blocks Used Available Capacity Mounted\\n'
        'fixture 99999999 1 99999998 1%% /\\n"\n',
    )
    _tool(
        commands,
        "mktemp",
        """
if [[ "${1:-}" == -d ]]; then
  exec /usr/bin/mktemp -d "$EWP_INSTALL_TEST_ROOT/repair.XXXXXX"
fi
exec /usr/bin/mktemp "$EWP_INSTALL_TEST_ROOT/doctor.XXXXXX.json"
""",
    )
    result = subprocess.run(
        ["bash", str(SCRIPT), mode, "--yes"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    calls = (tmp_path / "commands.log").read_text().splitlines()
    if fail_native:
        assert result.returncode != 0
        assert "Repair failed" in result.stderr
        assert "Application installation completed" not in result.stdout
        assert "uv run --locked --no-sync transcriber --version" not in calls
        return
    assert result.returncode == 0, result.stderr
    if mode == "--install":
        sync = calls.index("uv sync --locked")
        probe = calls.index("uv run --locked --no-sync python -")
        version = calls.index("uv run --locked --no-sync transcriber --version")
        assert sync < probe < version
        assert any("apt install" in call and "xz-utils" in call for call in calls)
    else:
        assert not any(
            "sync --locked" in call or "python -" in call or call.startswith("sudo")
            for call in calls
        )
