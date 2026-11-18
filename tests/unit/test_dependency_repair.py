"""Repair checks native audio before downloads and rejects a corrupt source archive."""

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/repair-dependencies.sh"


def _command(directory: Path, name: str, body: str) -> None:
    path = directory / name
    path.write_text("#!/bin/bash\nset -eu\n" + body)
    path.chmod(0o755)


def _environment(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    commands = tmp_path / "commands"
    commands.mkdir()
    env = dict(os.environ)
    env.update(
        PATH=f"{commands}:/usr/bin:/bin",
        EWP_REPAIR_TEST_ROOT=str(tmp_path),
        EWP_FFMPEG_PREFIX=str(tmp_path / "native-install"),
    )
    return commands, env


def test_working_native_decode_avoids_download_and_compilation(tmp_path: Path) -> None:
    commands, env = _environment(tmp_path)
    _command(commands, "uv", "exit 0\n")
    for tool in ("curl", "gcc", "make"):
        _command(commands, tool, 'touch "$EWP_REPAIR_TEST_ROOT/unexpected"; exit 9\n')
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT), "--native-only"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "already work" in result.stdout
    assert not (tmp_path / "unexpected").exists()


def test_source_checksum_failure_never_extracts_or_installs(tmp_path: Path) -> None:
    commands, env = _environment(tmp_path)
    _command(
        commands,
        "uv",
        """
case "$*" in
  *compatibility_prefix*) printf '%s\\n' "$EWP_FFMPEG_PREFIX"; exit 0 ;;
  *) exit 1 ;;
esac
""",
    )
    _command(commands, "mktemp", 'exec /usr/bin/mktemp -d "$EWP_REPAIR_TEST_ROOT/build.XXXXXX"\n')
    _command(commands, "curl", 'for destination; do :; done\nprintf tampered > "$destination"\n')
    for tool in ("gcc", "make", "tar"):
        _command(commands, tool, 'touch "$EWP_REPAIR_TEST_ROOT/unexpected"; exit 9\n')
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT), "--native-only"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "checksum" in result.stderr
    assert "Repair failed" in result.stderr
    assert not (tmp_path / "unexpected").exists()
    assert not Path(env["EWP_FFMPEG_PREFIX"]).exists()
