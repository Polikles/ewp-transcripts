"""Real Windows filesystem/launcher regressions; no models, app deps or provider requests."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows filesystem checks")
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("native_distribution", ROOT / "installer/manager.py")
assert spec and spec.loader
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


@pytest.fixture
def native_target():
    if not Path("D:\\").is_dir():
        pytest.skip("No D: volume on this Windows host")
    root = Path(tempfile.mkdtemp(prefix="ewp-native-drive-", dir="D:\\"))
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    ("preserve_work", "broken_python"), [(False, False), (True, False), (False, True)]
)
def test_direct_remove_script_cleans_readonly_runtime_and_preserves_user_work(
    tmp_path, preserve_work, broken_python
):
    """Real PS adapter, managed Python, deferred worker and read-only uv-style dependencies."""
    root = tmp_path / "Żółć installation"
    app = root / "versions/test-1/app"
    app.mkdir(parents=True)
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(app / ".venv")],
        check=True,
        capture_output=True,
    )
    for name in ("manager.py", "Install-EwP.ps1", "Remove-EwP.ps1"):
        shutil.copyfile(ROOT / "installer" / name, root / name)
    (app.parent / "bundle.json").write_text(json.dumps({"sha256": {}}))
    for directory in ("cache", "runtime", "tools"):
        folder = root / directory
        folder.mkdir()
        dll = folder / "readonly.dll"
        dll.write_bytes(b"synthetic installed dependency")
        dll.chmod(0o444)
    if broken_python:
        shutil.rmtree(app / ".venv")
        shutil.copyfile(ROOT / "installers/extracted/tools/uv.exe", root / "tools/uv.exe")
    owner = {
        "kind": manager.MAGIC,
        "root": str(root),
        "id": "native-owned-test",
        "releases": ["versions/test-1"],
        "models": [],
    }
    manager.atomic_json(root / "owner.json", owner)
    manager.atomic_json(
        root / "installation.json",
        {"kind": manager.MAGIC, "root": str(root), "active": "versions/test-1", "version": "1.0.0"},
    )
    if preserve_work:
        (root / "recording.wav").write_bytes(b"private work must remain")
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(root / "Remove-EwP.ps1"),
            "-Yes",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    report = next(e["report_directory"] for e in events if e.get("stage") == "removal")
    deadline = time.monotonic() + 45
    while (root / "owner.json").exists() and time.monotonic() < deadline:
        if (Path(report) / "removal-error.txt").exists():
            pytest.fail((Path(report) / "removal-error.txt").read_text())
        time.sleep(0.2)
    assert not (root / "owner.json").exists(), report
    assert not (root / "tools").exists()
    assert not (root / "versions").exists()
    if preserve_work:
        assert (root / "recording.wav").read_bytes() == b"private work must remain"
    else:
        deadline = time.monotonic() + 5
        while root.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not root.exists()


def test_real_empty_d_drive_child_passes_check_instead_of_depth_error(native_target):
    assert len(native_target.parts) == 2
    assert manager.safe_root(native_target) == native_target.resolve()
    result = manager.host_report(native_target, False)
    assert {row["code"] for row in result["checks"]} >= {
        "architecture",
        "platform",
        "disk",
        "vc_runtime",
    }
    assert not list(native_target.iterdir())  # Host check creates nothing in the chosen folder.


def test_program_files_model_free_launcher_uses_only_external_activity_lock(tmp_path, monkeypatch):
    parent = Path(os.environ["PROGRAMFILES"])
    try:
        root = Path(tempfile.mkdtemp(prefix="EwP-native-test-", dir=parent))
    except PermissionError:
        pytest.skip("This runner cannot create an owned test folder below Program Files")
    try:
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Profile"))
        monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
        marker = tmp_path / "launch-result.json"
        monkeypatch.setenv("EWP_INSTALLER_TEST_RESULT", str(marker))
        app = root / "versions" / "test-1" / "app"
        app.mkdir(parents=True)
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", str(app / ".venv")],
            check=True,
            capture_output=True,
        )
        package = app / "ewp_transcripts"
        package.mkdir()
        (package / "__init__.py").write_text("")
        (package / "__main__.py").write_text(
            "import json,os\nfrom pathlib import Path\n"
            "root=Path.cwd().parents[2]\n"
            "Path(os.environ['EWP_INSTALLER_TEST_RESULT']).write_text(json.dumps({'launched':True,'root_lock':(root/'.lifecycle.lock').exists()}))\n"
        )
        manager.atomic_json(
            root / "installation.json",
            {
                "kind": manager.MAGIC,
                "root": str(root),
                "version": "1.0.0",
                "active": "versions/test-1",
            },
        )
        assert manager.safe_root(root) == root.resolve()
        manager.launch(root)
        assert json.loads(marker.read_text()) == {"launched": True, "root_lock": False}
        assert not (root / ".lifecycle.lock").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)
