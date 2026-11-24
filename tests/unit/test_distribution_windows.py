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
    ("preserve_work", "broken_python", "live_wizard"),
    [(False, False, False), (True, False, False), (False, True, False), (True, False, True)],
)
def test_direct_remove_script_cleans_readonly_runtime_and_preserves_user_work(
    tmp_path, preserve_work, broken_python, live_wizard
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
    blocker = None
    wizard = root / "wizards/test/EwP-Setup.exe"
    if live_wizard:
        wizard.parent.mkdir(parents=True)
        wizard.write_bytes(b"synthetic maintenance image")
        state = manager.load_state(root)
        state["wizard"] = str(wizard)
        manager.atomic_json(root / "installation.json", state)
        shutil.copyfile(ROOT / "installer/windows/EwP.ico", root / "EwP.ico")
        manager.register(root, state)
        (root / "work-state").mkdir()
        (root / "work-state/session.json").write_text("private recovery preserved")
        ready = tmp_path / "lock-ready"
        blocker = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import sys,time;from pathlib import Path;f=open(sys.argv[1],'rb');"
                "Path(sys.argv[2]).touch();time.sleep(90)",
                str(wizard),
                str(ready),
            ]
        )
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert ready.exists()
    arguments = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(root / ("Install-EwP.ps1" if live_wizard else "Remove-EwP.ps1")),
        "-Yes",
    ]
    if live_wizard:
        arguments += ["-Action", "uninstall", "-SecretsStdin"]
    try:
        result = subprocess.run(
            arguments,
            input=json.dumps({"wizard_pid": blocker.pid, "wizard_source": str(wizard)}) + "\n"
            if blocker
            else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        # The adapter reports success while the simulated wizard still owns its EXE.
        assert not (root / "tools").exists()
        assert not (root / "versions").exists()
        assert not (root / "installation.json").exists()
        if blocker:
            assert blocker.poll() is None and wizard.exists()
            import winreg

            with pytest.raises(FileNotFoundError):
                winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts",
                )
            desktop = subprocess.check_output(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    "[Environment]::GetFolderPath('Desktop')",
                ],
                text=True,
            ).strip()
            shortcut = Path(desktop) / "EwP Transcripts.lnk"
            if shortcut.exists():
                details = subprocess.check_output(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-Command",
                        "$w=New-Object -ComObject WScript.Shell;"
                        "$s=$w.CreateShortcut($env:EWP_TEST_LINK);"
                        "@{target=$s.TargetPath;arguments=$s.Arguments;working=$s.WorkingDirectory}"
                        "|ConvertTo-Json -Compress",
                    ],
                    env={**os.environ, "EWP_TEST_LINK": str(shortcut)},
                    text=True,
                )
                pytest.fail("Owned desktop shortcut remains: " + details + result.stdout)
            assert set(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()) == {
                "wizards/test/EwP-Setup.exe",
                "recording.wav",
                "work-state/session.json",
            }
    finally:
        if blocker:
            blocker.terminate()
            blocker.wait(timeout=10)
            deadline = time.monotonic() + 10
            while wizard.exists() and time.monotonic() < deadline:
                time.sleep(0.1)
            assert not wizard.exists(), "Deferred maintenance EXE did not delete after closure"
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


@pytest.mark.parametrize("exit_code", [0, 259])
def test_terminated_process_handle_does_not_keep_a_stale_lock_alive(exit_code):
    child = subprocess.Popen([sys.executable, "-c", f"import sys;sys.exit({exit_code})"])
    child.wait(timeout=10)
    # Popen still retains a Windows process HANDLE here; OpenProcess alone is insufficient.
    assert child._handle is not None
    assert manager.process_identity(child.pid) is None
    assert not manager.process_alive(child.pid)


def test_windows_kernel_lock_recovers_after_crash_and_pid_reuse(tmp_path):
    root = tmp_path / "managed"
    root.mkdir()
    helper = tmp_path / "lock-owner.py"
    marker = tmp_path / "lock-ready"
    helper.write_text(
        "import runpy,sys,time\nfrom pathlib import Path\n"
        "m=runpy.run_path(sys.argv[1])\n"
        "with m['exclusive'](Path(sys.argv[2])):\n"
        " Path(sys.argv[3]).touch()\n time.sleep(60)\n"
    )
    child = subprocess.Popen(
        [sys.executable, str(helper), str(ROOT / "installer/manager.py"), str(root), str(marker)]
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists()
        with pytest.raises(manager.InstallError, match="active"), manager.exclusive(root):
            pytest.fail("Healthy owner was bypassed")
    finally:
        child.terminate()
        child.wait(timeout=10)
    with manager.exclusive(root):
        assert manager.lifecycle_lock_path(root).read_text() == str(os.getpid())
    lock = manager.lifecycle_lock_path(root)
    lock.write_text(str(os.getpid()))
    _, started, _ = manager.process_identity(os.getpid())
    os.utime(lock, (started - 10, started - 10))  # The recorded PID belongs to a newer process.
    with manager.exclusive(root):
        pass
    assert not lock.exists()
    lock.write_text("4")  # A prior-boot PID may now be an inaccessible system process.
    os.utime(lock, (1, 1))
    with manager.exclusive(root):
        pass
    assert not lock.exists()


@pytest.mark.parametrize(
    "crash_launcher,legacy_runtime", [(False, False), (True, False), (False, True)]
)
def test_repeat_launch_reopens_verified_instance_and_uninstall_stops_it(
    tmp_path, monkeypatch, crash_launcher, legacy_runtime
):
    root = tmp_path / "EwP runtime"
    app = root / "versions/test/app"
    package = app / "ewp_transcripts"
    package.mkdir(parents=True)
    native_python = sys.executable
    if legacy_runtime:
        base = root / "tools/legacy-python"

        def link_or_copy(source, target):
            try:
                os.link(source, target)
            except OSError:
                shutil.copyfile(source, target)
            return target

        shutil.copytree(sys.base_prefix, base, copy_function=link_or_copy)
        native_python = str(base / "python.exe")
    subprocess.run(
        [native_python, "-m", "venv", "--without-pip", str(app / ".venv")],
        check=True,
        capture_output=True,
    )
    (package / "__init__.py").write_text("")
    shutil.copyfile(ROOT / "src/ewp_transcripts/web_runtime.py", package / "web_runtime.py")
    server = package / "__main__.py"
    server.write_text("""import json,os,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from ewp_transcripts.web_runtime import publish_runtime
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def answer(self,stop):
  if self.headers.get('X-EWP-Runtime-Token')!=os.environ['EWP_RUNTIME_TOKEN']:
   self.send_error(403);return
  data=json.dumps({'pid':os.getpid(),'status':'ready'}).encode()
  self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  if stop:threading.Thread(target=self.server.shutdown,daemon=True).start()
 def do_GET(self):self.answer(False)
 def do_POST(self):self.answer(True)
http=HTTPServer(('127.0.0.1',8765),Handler)
publish_runtime(port=8765)
try:http.serve_forever()
finally:http.server_close()
""")
    import hashlib

    files = {
        "app/ewp_transcripts/__init__.py": hashlib.sha256(b"").hexdigest(),
        "app/ewp_transcripts/__main__.py": hashlib.sha256(server.read_bytes()).hexdigest(),
    }
    files["app/ewp_transcripts/web_runtime.py"] = hashlib.sha256(
        (package / "web_runtime.py").read_bytes()
    ).hexdigest()
    manager.atomic_json(app.parent / "bundle.json", {"version": "1.0.0", "sha256": files})
    manager.atomic_json(
        root / "owner.json",
        {
            "kind": manager.MAGIC,
            "id": "runtime-test",
            "root": str(root),
            "releases": ["versions/test"],
            "models": [],
        },
    )
    manager.atomic_json(
        root / "installation.json",
        {"kind": manager.MAGIC, "root": str(root), "active": "versions/test", "version": "1.0.0"},
    )
    helper = tmp_path / "launch-owner.py"
    helper.write_text(
        "import runpy,sys\nfrom pathlib import Path\n"
        "m=runpy.run_path(sys.argv[1]);m['launch'](Path(sys.argv[2]))\n"
    )
    launch_arguments = [sys.executable, str(helper), str(ROOT / "installer/manager.py"), str(root)]
    environment = os.environ.copy()
    if legacy_runtime:
        # Earlier protocol: an integer PID file and manager.py launch, with no runtime record.
        legacy = root / "manager.py"
        legacy.write_text("""import os,sys,hashlib,subprocess
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--root')+1])
lock=Path(os.environ['LOCALAPPDATA'])/'EwPTranscriptsState/locks'/(hashlib.sha256(str(root).casefold().encode()).hexdigest()+'.lock')
lock.parent.mkdir(parents=True,exist_ok=True)
f=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(f,str(os.getpid()).encode());os.close(f)
try:subprocess.run([str(root/'versions/test/app/.venv/Scripts/python.exe'),'-m','ewp_transcripts','gui'],cwd=root/'versions/test/app')
finally:lock.unlink(missing_ok=True)
""")
        launch_arguments = [native_python, str(legacy), "launch", "--root", str(root)]
        environment["EWP_RUNTIME_TOKEN"] = "synthetic-legacy-token-0123456789abcdef"
        (root / "outputs").mkdir()
    child = subprocess.Popen(
        launch_arguments,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 15
        record = None
        while time.monotonic() < deadline:
            if legacy_runtime:
                import urllib.error
                import urllib.request

                try:
                    request = urllib.request.Request(
                        "http://127.0.0.1:8765/api/v1/runtime-control",
                        headers={"X-EWP-Runtime-Token": environment["EWP_RUNTIME_TOKEN"]},
                    )
                    with urllib.request.urlopen(request, timeout=1) as response:
                        status = json.load(response)
                    identity = manager.process_identity(status["pid"])
                    record = {"pid": status["pid"], "identity": identity[0]}
                    break
                except (urllib.error.URLError, TimeoutError):
                    pass
            elif manager.runtime_session_path(root).exists():
                record = manager.runtime_record(root)
                if record and manager.runtime_request(record, "ping"):
                    break
            time.sleep(0.1)
        assert record and (legacy_runtime or manager.runtime_request(record, "ping"))
        opened = []
        import webbrowser

        monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url))
        if not legacy_runtime:
            manager.launch(root)
            assert opened == ["http://127.0.0.1:8765/"]
        assert child.poll() is None
        if crash_launcher:
            child.terminate()
            child.wait(timeout=10)
            assert manager.process_identity(record["pid"]) is not None
            manager.launch(root)
            assert opened == ["http://127.0.0.1:8765/", "http://127.0.0.1:8765/"]
        # The real adapter must stop the server, acquire its released mutex, and await cleanup.
        for name in ("manager.py", "Install-EwP.ps1", "Remove-EwP.ps1"):
            shutil.copyfile(ROOT / "installer" / name, root / name)
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(root / "Install-EwP.ps1"),
                "-Action",
                "uninstall",
                "-Root",
                str(root),
                "-Yes",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert not (root / "installation.json").exists()
        assert not (root / "versions").exists()
        assert (root / "outputs").is_dir()
        child.wait(timeout=10)
        if crash_launcher:
            assert child.returncode != 0
        elif not legacy_runtime:
            assert child.returncode == 0
        assert manager.process_identity(record["pid"]) is None
        assert not manager.lifecycle_lock_path(root).exists()
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
        identity = manager.process_identity(record["pid"]) if record else None
        if identity and identity[0] == record["identity"]:
            subprocess.run(["taskkill.exe", "/PID", str(record["pid"]), "/F"], capture_output=True)
