"""Real Windows filesystem/launcher regressions; no models, app deps or provider requests."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
