"""Real WPF/WebView2 lifecycle with the actual GUI, tiny public media and no ML packages."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows desktop host")
ROOT = Path(__file__).resolve().parents[2]


def wait_until(check, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.1)
    raise AssertionError("Desktop lifecycle condition timed out")


def alive(pid):
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
    finally:
        kernel.CloseHandle(handle)


def test_real_desktop_save_restart_focus_and_crash_owns_process_tree(tmp_path):
    import ctypes
    from ctypes import wintypes

    root = tmp_path / "ewp-desktop-test-Żółć"
    release = root / "versions/native-test"
    release.mkdir(parents=True)
    bundles = list((ROOT / "installers").glob("EwP-*-windows-x64.zip"))
    assert len(bundles) == 1
    with zipfile.ZipFile(bundles[0]) as archive:
        version = json.loads(archive.read("bundle.json"))["version"]
        archive.extractall(release)
    for name in ["manager.py", "models.json", "EwP.Transcripts.exe"]:
        shutil.copyfile(release / "control" / name, root / name)
    for name, data in {
        "owner.json": {
            "kind": "ewp-transcripts-managed-v1",
            "root": str(root),
            "id": "native-desktop-test",
            "releases": ["versions/native-test"],
            "models": [],
        },
        "installation.json": {
            "kind": "ewp-transcripts-managed-v1",
            "root": str(root),
            "active": "versions/native-test",
            "version": version,
            "local_models": False,
        },
    }.items():
        (root / name).write_text(json.dumps(data), encoding="utf-8")
    uv = ROOT / "installers/extracted/tools/uv.exe"
    venv = release / "app/.venv"
    subprocess.run([str(uv), "venv", "--python", sys.executable, str(venv)], check=True)
    python = venv / "Scripts/python.exe"
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    needed = {"pydantic", "typer", "keyring", "rapidfuzz"}
    packages = [
        f"{item['name']}=={item['version']}" for item in lock["package"] if item["name"] in needed
    ]
    subprocess.run([str(uv), "pip", "install", "--python", str(python), *packages], check=True)
    sites = venv / "Lib/site-packages"
    (sites / "ewp-test-source.pth").write_text(str(release / "app/src"), encoding="utf-8")
    # A test-only site hook creates fake media-worker descendants inside the owned backend's job.
    # It is never included in the product; neither process imports ML or contacts a provider.
    (sites / "sitecustomize.py").write_text(
        """import json,os,subprocess,sys
if os.environ.get("EWP_DESKTOP_MODE")=="1" and "gui" in sys.argv:
 code=("import json,os,subprocess,sys,time; from pathlib import Path; "
       "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(600)'],"
       "creationflags=0x08000000);Path(os.environ['EWP_TEST_WORKER_RECORD'])"
       ".write_text(json.dumps([os.getpid(),p.pid]));time.sleep(600)")
 subprocess.Popen([sys.executable,"-c",code],creationflags=0x08000000)
""",
        encoding="utf-8",
    )
    evidence = ROOT / "installers/desktop-evidence"
    evidence.mkdir(exist_ok=True)
    executable = root / "EwP.Transcripts.exe"
    state_directory = None
    try:
        for phase in ["save", "restore", "crash", "maintenance"]:
            worker_record = tmp_path / f"{phase}-workers.json"
            report = evidence / f"{phase}.json"
            environment = {**os.environ, "EWP_TEST_WORKER_RECORD": str(worker_record)}
            if phase != "save":
                environment["EWP_DESKTOP_EXPECT_RECOVERY"] = "1"
            if phase in {"crash", "maintenance"}:
                environment["EWP_DESKTOP_CRASH_TEST"] = "1"
            args = [
                str(executable),
                "--root",
                str(root),
                "--self-test-report",
                str(report),
                "--preview-dir",
                str(evidence / phase),
            ]
            process = subprocess.Popen(args, env=environment)
            try:
                wait_until(report.exists, 120)
                data = json.loads(report.read_text(encoding="utf-8"))
                assert data["result"] == "PASS", data
                state_directory = Path(data["state_directory"])
                wait_until(worker_record.exists)
                descendants = [
                    data["manager_pid"],
                    data["server_pid"],
                    *json.loads(worker_record.read_text()),
                ]
                if phase == "crash":
                    # Second launch must focus the existing window without spawning another server.
                    user = ctypes.windll.user32
                    user.ShowWindow(wintypes.HWND(data["window_handle"]), 6)
                    second = subprocess.run(
                        [str(executable), "--root", str(root)], capture_output=True, timeout=20
                    )
                    assert second.returncode == 0
                    assert process.poll() is None and alive(data["server_pid"])
                    wait_until(
                        lambda user=user, data=data: (
                            not user.IsIconic(wintypes.HWND(data["window_handle"]))
                        )
                    )
                    process.kill()
                elif phase == "maintenance":
                    # Exercise the real uninstall/update stop handshake against the live window.
                    subprocess.run(
                        [
                            str(python),
                            "-c",
                            "import runpy,sys;from pathlib import Path;"
                            "m=runpy.run_path(sys.argv[1]);"
                            "m['stop_running_application'](Path(sys.argv[2]))",
                            str(root / "manager.py"),
                            str(root),
                        ],
                        check=True,
                        timeout=100,
                    )
                assert process.wait(timeout=60) == 0 or phase == "crash"
                wait_until(
                    lambda descendants=descendants: not any(alive(pid) for pid in descendants)
                )
                assert (root / "work-state").is_dir()
                workspaces = list((root / "outputs").glob("*.workspace.json"))
                assert workspaces
                for workspace in workspaces:
                    for media in json.loads(workspace.read_text(encoding="utf-8"))["pending_media"]:
                        source = Path(media["path"])
                        assert source.is_relative_to(root / "outputs") and source.is_file()
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                if report.exists() and json.loads(report.read_text())["result"] != "PASS":
                    snapshot = {
                        str(path.relative_to(root)): json.loads(path.read_text(encoding="utf-8"))
                        for folder in [root / "work-state", root / "outputs"]
                        for path in folder.rglob("*.json")
                        if path.stat().st_size < 1_000_000
                    }
                    (evidence / f"{phase}-synthetic-state.json").write_text(
                        json.dumps(snapshot, indent=2), encoding="utf-8"
                    )
    finally:
        if state_directory is not None:
            shutil.rmtree(state_directory, ignore_errors=True)
