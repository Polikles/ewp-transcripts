"""Installer filesystem transactions use tiny synthetic runtimes; never speech/model downloads."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("distribution_manager", ROOT / "installer/manager.py")
assert spec and spec.loader
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


def bundle(tmp_path: Path, version: str, *, fail: bool = False, actual: str | None = None) -> Path:
    """Real child processes, but a tiny fake uv/app instead of a multi-GB dependency install."""
    if os.name == "nt":
        pytest.skip("Synthetic uv here is a POSIX shell; native Windows has a separate checklist")
    uv = f'''#!/bin/sh
if [ "$1" = sync ]; then
 if [ -f fail ]; then echo simulated-dependency-failure; exit 7; fi
 mkdir -p .venv/bin
 ln -s "{sys.executable}" .venv/bin/python
fi
exit 0
'''
    app = f"""import sys
from pathlib import Path
if '--version' in sys.argv:print({actual or version!r})
elif 'gui' in sys.argv:Path('launched').write_text('synthetic, no audio')
else:print('synthetic help')
"""
    files = {
        "tools/uv": uv.encode(),
        "app/ewp_transcripts/__init__.py": b"",
        "app/ewp_transcripts/__main__.py": app.encode(),
        "app/scripts/repair-dependencies.sh": b"#!/bin/sh\nexit 0\n",
        "app/src/ewp_transcripts/resources/default-config.toml": b"[models]\n",
        "control/models.json": (ROOT / "installer/models.json").read_bytes(),
        "control/EwP.ico": (ROOT / "installer/windows/EwP.ico").read_bytes(),
        **{
            f"control/{name}": (ROOT / "installer" / name).read_bytes()
            for name in ("manager.py", "Install-EwP.ps1", "Install-EwP.sh", "Remove-EwP.ps1")
        },
    }
    if fail:
        files["app/fail"] = b"yes"
    return zipped(tmp_path / f"{version}-{fail}-{actual}.zip", files, version)


def zipped(path: Path, files: dict[str, bytes], version: str = "1.0.0") -> Path:
    meta = {
        "format": 1,
        "platform": "ubuntu-x64",
        "version": version,
        "sha256": {n: hashlib.sha256(v).hexdigest() for n, v in files.items()},
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("bundle.json", json.dumps(meta))
        for name, value in files.items():
            archive.writestr(name, value)
    return path


@pytest.fixture
def lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    registrations = []
    monkeypatch.setattr(manager, "host_report", lambda *args: {"ready": True, "checks": []})
    monkeypatch.setattr(
        manager, "register", lambda root, state: registrations.append(state["version"])
    )
    # Never touch the real user's desktop during uninstall.
    fakehome = tmp_path / "home"
    fakehome.mkdir()
    monkeypatch.setattr(manager.Path, "home", lambda: fakehome)
    return tmp_path / "Żółć managed installation", registrations


def install(root: Path, archive: Path):
    return manager.install(root, archive, local=False, terms=False, secrets={})


def test_real_process_lifecycle_update_failure_rollback_and_safe_removal(tmp_path, lifecycle):
    root, registrations = lifecycle
    first = install(root, bundle(tmp_path, "1.0.0"))
    publication = root / first["active"] / "app/my_verified_results.json"
    publication.write_text("private publication kept")
    (root / "my-workspace.json").write_text("private workspace kept")
    manager.launch(root)
    assert (root / first["active"] / "app/launched").exists()
    with pytest.raises(manager.InstallError, match="previous active"):
        install(root, bundle(tmp_path, "1.1.0", fail=True))
    assert manager.load_state(root)["active"] == first["active"]
    assert manager.app_python(root / first["active"]).exists()
    second = install(root, bundle(tmp_path, "1.1.0"))
    assert second["previous"] == first["active"]
    assert manager.rollback(root)["version"] == "1.0.0"
    with manager.exclusive(root), pytest.raises(manager.InstallError, match="active"):
        install(root, bundle(tmp_path, "1.2.0"))
    preview = manager.uninstall(root, confirmed=False)
    assert any("my_verified_results" in p for p in preview["preserved_unknown"])
    assert publication.read_text() == "private publication kept"
    manager.uninstall(root, confirmed=True)
    assert publication.read_text() == "private publication kept"
    assert (root / "my-workspace.json").exists()
    assert not (root / "installation.json").exists()
    assert registrations[:2] == ["1.0.0", "1.0.0"]  # Failed candidate restored registration.


def test_failed_first_install_can_retry_and_partial_install_can_be_removed(tmp_path, lifecycle):
    root, _ = lifecycle
    with pytest.raises(manager.InstallError):
        install(root, bundle(tmp_path, "1.0.0", fail=True))
    assert manager.load_owner(root)
    assert manager.load_state(root) is None
    install(root, bundle(tmp_path, "1.0.0"))
    assert manager.load_state(root)["version"] == "1.0.0"
    other = tmp_path / "incomplete installation"
    with pytest.raises(manager.InstallError):
        install(other, bundle(tmp_path, "1.1.0", fail=True))
    manager.uninstall(other, confirmed=True)
    assert not (other / "owner.json").exists()


def test_incorrect_version_or_downgrade_cannot_replace_working_app(tmp_path, lifecycle):
    root, _ = lifecycle
    state = install(root, bundle(tmp_path, "2.0.0"))
    with pytest.raises(manager.InstallError, match="Downgrade"):
        install(root, bundle(tmp_path, "1.0.0"))
    with pytest.raises(manager.InstallError, match="version"):
        install(root, bundle(tmp_path, "2.1.0", actual="1.0.0"))
    assert manager.load_state(root)["active"] == state["active"]


def test_existing_user_directory_and_changed_owned_links_are_preserved(tmp_path, lifecycle):
    root, _ = lifecycle
    root.mkdir()
    (root / "my_recording.wav").write_bytes(b"not audio")
    with pytest.raises(manager.InstallError, match="empty"):
        install(root, bundle(tmp_path, "1.0.0"))
    assert (root / "my_recording.wav").read_bytes() == b"not audio"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_text("keep")
    alias = tmp_path / "alias"
    alias.symlink_to(outside, target_is_directory=True)
    with pytest.raises(manager.InstallError, match="links"):
        manager.safe_root(alias / "install")
    managed = tmp_path / "managed"
    install(managed, bundle(tmp_path, "1.1.0"))
    import shutil

    shutil.rmtree(managed / "versions")
    (managed / "versions").symlink_to(outside, target_is_directory=True)
    with pytest.raises(manager.InstallError):
        manager.uninstall(managed, confirmed=True)
    assert (outside / "keep").read_text() == "keep"


@pytest.mark.parametrize(
    "name",
    ["../escaped", "/absolute", "app\\escape", "app/CON", "app/file.", "app/file ", "C:/test"],
)
def test_bundle_cannot_traverse_or_exploit_windows_path_normalization(tmp_path, name):
    archive = zipped(tmp_path / "bad.zip", {name: b"bad"})
    with pytest.raises(manager.InstallError):
        manager.inspect_bundle(archive)
    assert not (tmp_path / "escaped").exists()


def test_case_collisions_corruption_unknown_members_and_version_rejected(tmp_path):
    for i, files in enumerate([{"app/A": b"1", "app/a": b"2"}, {"app/file": b"1"}]):
        archive = zipped(tmp_path / f"bad{i}.zip", files)
        if i:
            with zipfile.ZipFile(archive, "a") as out:
                out.writestr("extra", b"bad")
        with pytest.raises(manager.InstallError):
            manager.inspect_bundle(archive)
    archive = zipped(tmp_path / "version.zip", {"file": b""}, "../../bad")
    with pytest.raises(manager.InstallError):
        manager.inspect_bundle(archive)


def test_models_and_terms_are_explicit_before_root_changes(tmp_path, lifecycle):
    root, _ = lifecycle
    with pytest.raises(manager.InstallError, match="terms"):
        manager.install(root, bundle(tmp_path, "1.0.0"), local=True, terms=False, secrets={})
    assert not root.exists()


def test_offline_model_verification_detects_same_size_corruption_and_missing_file(tmp_path):
    target = tmp_path / "snapshot" / ("a" * 40)
    target.mkdir(parents=True)
    (target / "model.bin").write_bytes(b"BAD!")
    catalog = tmp_path / "catalog.json"
    manager.atomic_json(
        catalog,
        {
            "models": [
                {
                    "code": "asr",
                    "repository": "test/model",
                    "revision": "a" * 40,
                    "path": str(target),
                    "files": {"model.bin": 4, "config.json": 2},
                    "hashes": {
                        "model.bin": {
                            "algorithm": "sha256",
                            "digest": hashlib.sha256(b"GOOD").hexdigest(),
                        },
                        "config.json": {
                            "algorithm": "git-sha1",
                            "digest": hashlib.sha1(b"blob 2\0{}").hexdigest(),
                        },
                    },
                }
            ]
        },
    )
    result = manager.verify_models(tmp_path / "uninstalled", catalog)[0]
    assert result["status"] == "fail" and set(result["issues"]) == {"model.bin", "config.json"}
    (target / "model.bin").write_bytes(b"GOOD")
    (target / "config.json").write_bytes(b"{}")
    assert manager.verify_models(tmp_path / "uninstalled", catalog)[0]["status"] == "pass"


def test_selected_public_model_download_needs_no_hf_and_preserved_gated_model_is_not_requested(
    tmp_path, monkeypatch
):
    root = tmp_path / "installation"
    release = root / "versions/test-1"
    catalog = release / "control/models.json"
    catalog.parent.mkdir(parents=True)
    entries = [
        {
            "code": code,
            "repository": "test/" + code,
            "revision": "a" * 40,
            "path": str(tmp_path / code),
            "files": {"model.bin": 4},
            "gated": gated,
        }
        for code, gated in [("asr", False), ("diarization", True)]
    ]
    manager.atomic_json(catalog, {"models": entries})
    manager.atomic_json(
        root / "owner.json", {"kind": manager.MAGIC, "root": str(root), "models": []}
    )
    monkeypatch.setattr(manager, "model_targets", lambda root, entries, *args: entries)
    commands = []
    monkeypatch.setattr(manager, "run", lambda command, **kw: commands.append(command))
    manager.prepare_models(
        root, release, selected=["asr"], redownload=False, terms=False, secrets={}
    )
    assert commands[0][-2:] == ["--model", "asr"]
    commands.clear()
    for entry in entries:
        path = Path(entry["path"])
        path.mkdir()
        (path / "model.bin").write_bytes(b"GOOD")
    manager.prepare_models(root, release, selected=None, redownload=False, terms=False, secrets={})
    assert commands == []
    with pytest.raises(manager.InstallError, match="gated"):
        manager.prepare_models(
            root, release, selected=["diarization"], redownload=True, terms=False, secrets={}
        )


def test_update_with_same_model_pins_prepares_no_models(tmp_path, lifecycle):
    root, _ = lifecycle
    state = install(root, bundle(tmp_path, "1.0.0"))
    state["local_models"] = True
    manager.atomic_json(root / "installation.json", state)
    assert manager.changed_model_codes(root, bundle(tmp_path, "1.1.0")) == []


def test_installed_size_counts_models_and_program_once(tmp_path):
    root = tmp_path / "installation"
    root.mkdir()
    model = tmp_path / "models"
    model.mkdir()
    (model / "weights.bin").write_bytes(b"12345")
    (root / "program.bin").write_bytes(b"123")
    manager.atomic_json(
        root / "owner.json",
        {"kind": manager.MAGIC, "root": str(root), "models": [str(model), str(model)]},
    )
    assert manager.installed_size(root) == 8 + (root / "owner.json").stat().st_size


def test_secret_input_and_child_logs_never_expose_keys(tmp_path, monkeypatch, capsys):
    secret = "not-a-real-token-123"
    env = {**os.environ, "HF_TOKEN": secret}
    manager.run(
        [sys.executable, "-c", 'import os;print(os.environ["HF_TOKEN"])'],
        cwd=tmp_path,
        environment=env,
    )
    assert secret not in capsys.readouterr().out
    monkeypatch.setattr(sys, "stdin", io.StringIO('["bad input"]\n'))
    assert manager.main(["check", "--root", str(tmp_path / "managed"), "--secrets-stdin"]) == 2
    assert "Invalid credential input" in capsys.readouterr().out


def test_selected_model_removal_keeps_shared_blobs_and_unrelated_snapshots(tmp_path, lifecycle):
    root, _ = lifecycle
    root.mkdir()
    cache = Path.home() / ".cache/huggingface/hub"
    repo = cache / "models--example"
    a = repo / "snapshots/abc"
    b = repo / "snapshots/def"
    blob = repo / "blobs/shared"
    unique = repo / "blobs/unique"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    blob.parent.mkdir()
    blob.write_text("shared")
    unique.write_text("only a")
    (a / "one").symlink_to(blob)
    (b / "one").symlink_to(blob)
    (a / "two").symlink_to(unique)
    manager.atomic_json(
        root / "owner.json", {"kind": manager.MAGIC, "root": str(root), "models": [str(a)]}
    )
    manager.remove_exact_models(root)
    assert not a.exists() and (b / "one").read_text() == "shared" and blob.exists()
    assert not unique.exists()
    manager.atomic_json(
        root / "owner.json",
        {"kind": manager.MAGIC, "root": str(root), "models": [str(b), str(tmp_path / "foreign")]},
    )
    with pytest.raises(manager.InstallError):
        manager.remove_exact_models(root)
    assert b.exists()


def test_current_working_directory_is_a_valid_existing_install(tmp_path, lifecycle, monkeypatch):
    root, _ = lifecycle
    install(root, bundle(tmp_path, "1.0.0"))
    monkeypatch.chdir(root)
    assert manager.safe_root(root) == root
    assert manager.main(["launch", "--root", str(root)]) == 0


def test_partial_owner_and_corrupt_state_cannot_authorize_foreign_removal(tmp_path):
    root = tmp_path / "foreign"
    root.mkdir()
    manager.atomic_json(root / "owner.json", {"kind": "other", "root": str(root)})
    with pytest.raises(manager.InstallError):
        manager.removal_preview(root)
    (root / "owner.json").unlink()
    manager.atomic_json(
        root / "installation.json",
        {"kind": manager.MAGIC, "root": str(root), "active": "../../elsewhere"},
    )
    with pytest.raises(manager.InstallError):
        manager.load_state(root)


def test_uninstall_keeps_added_symlink_targets_and_unknown_release_directories(tmp_path, lifecycle):
    root, _ = lifecycle
    state = install(root, bundle(tmp_path, "1.0.0"))
    outside = tmp_path / "external_data"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    (root / state["active"] / "app/linked_data").symlink_to(outside, target_is_directory=True)
    other = root / "versions/manual-project"
    other.mkdir()
    (other / "results.json").write_text("publication")
    manager.uninstall(root, confirmed=True)
    assert (outside / "keep.txt").read_text() == "keep"
    assert (other / "results.json").read_text() == "publication"


def test_dead_lock_is_recovered_and_unknown_or_live_owner_is_protected(tmp_path, monkeypatch):
    root = tmp_path / "installation"
    root.mkdir()
    lock = root / ".lifecycle.lock"
    lock.write_text("12345")
    monkeypatch.setattr(manager, "process_alive", lambda pid: False)
    with manager.exclusive(root):
        assert lock.read_text() == str(os.getpid())
    assert not lock.exists()
    lock.write_text("unknown")
    with pytest.raises(manager.InstallError), manager.exclusive(root):
        pass
    assert lock.read_text() == "unknown"
    lock.write_text(str(os.getpid()))
    monkeypatch.setattr(manager, "process_alive", lambda pid: True)
    with pytest.raises(manager.InstallError), manager.exclusive(root):
        pass
    assert lock.exists()


def test_obsolete_releases_are_pruned_but_added_project_files_remain(tmp_path, lifecycle):
    root, _ = lifecycle
    first = install(root, bundle(tmp_path, "1.0.0"))
    work = root / first["active"] / "app/my_publication.txt"
    work.write_text("keep")
    install(root, bundle(tmp_path, "1.1.0"))
    install(root, bundle(tmp_path, "1.2.0"))
    assert work.read_text() == "keep"
    assert not manager.app_python(root / first["active"]).exists()
    preview = manager.removal_preview(root)
    assert any(work.is_relative_to(root / p) for p in preview["preserved_unknown"])
    manager.uninstall(root, confirmed=True)
    assert work.read_text() == "keep"


def test_hf_access_failure_is_early_and_never_prints_token(
    tmp_path, lifecycle, monkeypatch, capsys
):
    import urllib.error
    import urllib.request

    root, _ = lifecycle
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(request.full_url)
            assert "not-real-hf" in request.get_header("Authorization")
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)

    monkeypatch.setattr(urllib.request, "build_opener", lambda *args: Opener())
    with pytest.raises(manager.InstallError, match="HF access"):
        manager.install(
            root,
            bundle(tmp_path, "1.0.0"),
            local=True,
            terms=True,
            secrets={"hf_token": "not-real-hf"},
        )
    assert calls and not root.exists()
    assert "not-real-hf" not in capsys.readouterr().out


def test_openrouter_is_passed_only_on_stdin_and_never_persisted_in_inventory(
    tmp_path, lifecycle, monkeypatch, capsys
):
    root, _ = lifecycle
    secret = "not-real-openrouter"
    original = manager.subprocess.run
    seen = []

    def child(command, **kwargs):
        if "-c" in command and "OSCredentialStore" in command[-1]:
            assert secret not in " ".join(command)
            assert kwargs["input"] == secret
            seen.append(True)
            return manager.subprocess.CompletedProcess(command, 0, "", "")
        return original(command, **kwargs)

    monkeypatch.setattr(manager.subprocess, "run", child)
    manager.install(
        root,
        bundle(tmp_path, "1.0.0"),
        local=False,
        terms=False,
        secrets={"openrouter_key": secret},
    )
    assert seen
    assert secret not in (root / "installation.json").read_text()
    assert secret not in (root / "owner.json").read_text()
    assert secret not in capsys.readouterr().out


def test_distribution_is_deterministic_and_excludes_untracked_private_files(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "distribution_builder", ROOT / "tools/build_distribution.py"
    )
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    source = tmp_path / "source"
    downloads = tmp_path / "tools"
    downloads.mkdir()
    files = {
        "src/ewp_transcripts/_version.py": '__version__ = "0.22.0"\n',
        "src/ewp_transcripts/__init__.py": "# app\n",
        "scripts/host.ps1": "# committed LF script\n",
        "installer/models.json": '{"models":[]}',
        "installer/windows/EwP.ico": "synthetic public icon",
        "src/private-key.txt": "UNTRACKED-SECRET-MUST-NOT-SHIP",
        "private benchmark/sample.txt": "PRIVATE-CORPUS-MUST-NOT-SHIP",
        **{
            n: "public project metadata"
            for n in ("pyproject.toml", "uv.lock", "README.md", "LICENSE", "LICENSING.md")
        },
        **{
            f"installer/{n}": "# helper"
            for n in ("manager.py", "Install-EwP.ps1", "Install-EwP.sh", "Remove-EwP.ps1")
        },
    }
    for name, value in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    link = source / "src/linked-secret.txt"
    link.symlink_to(source / "src/private-key.txt")
    (source / "scripts/host.ps1").write_bytes(b"# committed LF script\r\n")
    tracked = [n for n in files if "private" not in n] + ["src/linked-secret.txt"]

    def git(command, **kwargs):
        if command[1] == "show":
            return files[command[2].split(":", 1)[1]].encode()
        if command[1] == "rev-parse":
            return "a" * 40 + "\n"
        if command[1] == "status":
            return b""
        assert command[1] == "ls-files"
        return "\0".join(tracked).encode()

    monkeypatch.setattr(builder, "ROOT", source)
    monkeypatch.setattr(builder.subprocess, "check_output", git)
    # Tiny synthetic archive exercises the real packaging/hash logic without downloaded tools.
    tool = downloads / "uv.zip"
    with zipfile.ZipFile(tool, "w") as archive:
        archive.writestr("uv.exe", b"synthetic runtime")
    monkeypatch.setattr(
        builder,
        "UV_HASHES",
        {"windows-x64": (tool.name, hashlib.sha256(tool.read_bytes()).hexdigest())},
    )
    for name in (
        "LICENSE-MIT",
        "LICENSE-APACHE",
        "dotnet-LICENSE.txt",
        "dotnet-THIRD-PARTY-NOTICES.txt",
        "windowsdesktop-LICENSE.txt",
    ):
        (downloads / name).write_text("public license")
    first = builder.build(tmp_path / "first", downloads)[0]
    second = builder.build(tmp_path / "second", downloads)[0]
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert archive.read("app/scripts/host.ps1") == b"# committed LF script\n"
        assert not any("private" in name or "linked-secret" in name for name in archive.namelist())
        assert not any(b"MUST-NOT-SHIP" in archive.read(n) for n in archive.namelist())
        meta = json.loads(archive.read("bundle.json"))
        assert meta["source_dirty"] is False
        assert meta["source_commit"] == "a" * 40
        assert set(meta["sha256"]) == set(archive.namelist()) - {"bundle.json"}
        assert all(
            hashlib.sha256(archive.read(n)).hexdigest() == v for n, v in meta["sha256"].items()
        )
    with pytest.raises(ValueError, match="immutable"):
        builder.build(tmp_path / "first", downloads)


def test_deferred_windows_removal_releases_worker_pipes_and_keeps_unicode_plan(
    tmp_path, monkeypatch
):
    temporary = tmp_path / "deferred"
    temporary.mkdir()
    monkeypatch.setattr(manager, "removal_worker_directory", lambda: temporary)
    captured = {}

    def popen(command, **kwargs):
        captured.update(kwargs)
        assert command[0] == "powershell.exe"

    monkeypatch.setattr(manager.subprocess, "Popen", popen)
    root = tmp_path / "Żółty katalog"
    manager.defer_windows_removal(root, [str(root / "runtime")], 4321)
    plan = json.loads((temporary / "plan.json").read_text(encoding="utf-8"))
    assert plan["root"] == str(root)
    assert 4321 in plan["pids"]
    for stream in ("stdin", "stdout", "stderr"):
        assert captured[stream] == manager.subprocess.DEVNULL
    assert "-Encoding UTF8" in (temporary / "remove.ps1").read_text(encoding="utf-8")


def test_installed_ubuntu_uninstall_uses_existing_python_offline(tmp_path):
    if os.name == "nt":
        pytest.skip("POSIX shell wrapper")
    root = tmp_path / "managed Żółć"
    (root / "tools").mkdir(parents=True)
    (root / "owner.json").write_text("{}")
    script = root / "Install-EwP.sh"
    script.write_bytes((ROOT / "installer/Install-EwP.sh").read_bytes())
    uv = root / "tools/uv"
    uv.write_text('#!/bin/sh\nprintf "%s\\n" "$UV_PYTHON_INSTALL_DIR" "$@"\n')
    import subprocess

    result = subprocess.run(
        ["bash", str(script), "uninstall"], capture_output=True, text=True, check=True
    )
    lines = result.stdout.splitlines()
    assert lines[0] == str(root / "tools/python")
    assert "--offline" in lines
    assert lines[-2:] == ["--root", str(root)]


def test_host_checks_are_structured_and_use_selected_volume_and_25gb_margin(tmp_path, monkeypatch):
    from types import SimpleNamespace

    class Key:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    registry = SimpleNamespace(
        HKEY_LOCAL_MACHINE=1,
        OpenKey=lambda hive, path: Key(path),
        QueryValueEx=lambda key, name: (
            {
                "ProcessorNameString": "Owner CPU model",
                "Installed": 1,
                "Version": "v14.44",
                "DisplayVersion": "26H2",
            }[name],
            1,
        ),
    )
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(manager.platform, "system", lambda: "Windows")
    monkeypatch.setattr(manager.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(manager.platform, "release", lambda: "11")
    monkeypatch.setattr(manager.platform, "version", lambda: "10.0.26100")
    monkeypatch.setattr(manager.shutil, "which", lambda tool: "nvidia-smi.exe")
    monkeypatch.setattr(manager, "windows_vc_files", lambda: True)
    monkeypatch.setattr(
        manager.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stdout="NVIDIA Test GPU, 580.00\n"),
    )
    free = 25_000_000_000
    probed = []

    def usage(path):
        probed.append(path)
        return SimpleNamespace(free=free)

    monkeypatch.setattr(manager.shutil, "disk_usage", usage)
    root = tmp_path / "selected-volume" / "installation"
    report = manager.host_report(root, False)
    rows = {r["code"]: r for r in report["checks"]}
    assert report["ready"] is True
    assert probed == [tmp_path]
    assert rows["architecture"]["context"]["cpu_model"] == "Owner CPU model"
    assert rows["platform"]["context"]["name"] == "Windows 11 26H2"
    assert rows["gpu"]["context"]["devices"] == [{"name": "NVIDIA Test GPU", "driver": "580.00"}]
    assert rows["disk"]["context"] == {
        "additional_bytes": free,
        "free_bytes": free,
        "required_bytes": free,
        "installation_bytes": 20_000_000_000,
        "reserve_bytes": 5_000_000_000,
    }
    free -= 1
    assert manager.host_report(root, False)["ready"] is False


def test_cancel_interrupts_a_quiet_dependency_child_without_waiting_for_output(tmp_path):
    import threading
    import time

    marker = tmp_path / "cancel"
    started = tmp_path / "started"

    def request():
        deadline = time.monotonic() + 5
        while not started.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        marker.write_text("cancel")

    thread = threading.Thread(target=request)
    thread.start()
    token = manager.CANCEL_FILE.set(marker)
    begin = time.monotonic()
    try:
        with pytest.raises(manager.InstallError, match="INSTALL_CANCELLED"):
            manager.run(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path;import time;"
                    "Path('started').write_text('yes');time.sleep(60)",
                ],
                cwd=tmp_path,
                environment=dict(os.environ),
            )
    finally:
        manager.CANCEL_FILE.reset(token)
        thread.join(timeout=6)
    assert time.monotonic() - begin < 5


def test_cancelled_update_discards_candidate_and_keeps_active_version(
    tmp_path, lifecycle, monkeypatch
):
    root, _ = lifecycle
    first = install(root, bundle(tmp_path, "1.0.0"))
    original = manager.run
    marker = tmp_path / "cancel"

    def run(command, **kwargs):
        if "sync" in command:
            marker.write_text("cancel")
        return original(command, **kwargs)

    monkeypatch.setattr(manager, "run", run)
    token = manager.CANCEL_FILE.set(marker)
    try:
        with pytest.raises(manager.InstallError, match="INSTALL_CANCELLED"):
            install(root, bundle(tmp_path, "1.1.0"))
    finally:
        manager.CANCEL_FILE.reset(token)
    assert manager.load_state(root)["active"] == first["active"]
    assert manager.app_python(root / first["active"]).exists()
    assert len(list((root / "versions").iterdir())) == 1


def test_real_icon_contains_all_windows_sizes_and_model_catalog_matches_pins():
    import struct
    import tomllib

    data = (ROOT / "installer/windows/EwP.ico").read_bytes()
    assert struct.unpack_from("<HHH", data) == (0, 1, 7)
    sizes = []
    for i in range(7):
        width, height, _, _, planes, bits, size, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + i * 16
        )
        sizes.append(width or 256)
        assert width == height and planes == 1 and bits == 32
        assert data[offset : offset + 8] == b"\x89PNG\r\n\x1a\n"
        assert offset + size <= len(data)
    assert sizes == [16, 24, 32, 48, 64, 128, 256]
    config = tomllib.loads((ROOT / "src/ewp_transcripts/resources/default-config.toml").read_text())
    models = json.loads((ROOT / "installer/models.json").read_text())["models"]
    assert len(models) == 4
    assert models[0]["revision"] == config["models"]["asr_revision"]
    assert models[1]["revision"] == config["models"]["alignment_revision"]
    assert models[2]["revision"] == config["models"]["english_alignment_revision"]
    assert models[3]["revision"] == config["diarization"]["model_revision"]
    assert all(m["bytes"] == sum(m["files"].values()) for m in models)


def test_repair_cannot_silently_upgrade_an_existing_install(tmp_path, lifecycle, capsys):
    root, _ = lifecycle
    original = install(root, bundle(tmp_path, "1.0.0"))
    code = manager.main(
        ["repair", "--root", str(root), "--bundle", str(bundle(tmp_path, "1.1.0")), "--yes"]
    )
    assert code == 2
    assert "choose update explicitly" in capsys.readouterr().out
    assert manager.load_state(root)["active"] == original["active"]


@pytest.mark.parametrize(
    "value",
    [r"D:\Transcripts-test-01", r"C:\Apps", r"C:\Program Files\EwP Transcripts", r"Z:\New program"],
)
def test_windows_install_folder_depth_is_not_a_user_profile_restriction(value):
    from pathlib import PureWindowsPath

    manager.validate_root_shape(
        PureWindowsPath(value), PureWindowsPath(r"C:\Users\DS"), windows=True
    )


@pytest.mark.parametrize("value", ["C:\\", "D:\\", r"C:\Users\DS"])
def test_windows_volume_and_home_roots_still_cannot_be_owned_by_installer(value):
    from pathlib import PureWindowsPath

    with pytest.raises(manager.InstallError, match="root"):
        manager.validate_root_shape(
            PureWindowsPath(value), PureWindowsPath(r"C:\Users\DS"), windows=True
        )


def test_external_windows_runtime_lock_keeps_protected_root_read_only(tmp_path, monkeypatch):
    root = tmp_path / "Protected program"
    root.mkdir()
    state = tmp_path / "User profile"
    lock = manager.lifecycle_lock_path(root, windows=True, local_app_data=state)
    assert not lock.is_relative_to(root)
    monkeypatch.setattr(manager, "lifecycle_lock_path", lambda _: lock)
    before = list(root.iterdir())
    with manager.exclusive(root):
        assert lock.exists()
        assert list(root.iterdir()) == before
        with pytest.raises(manager.InstallError), manager.exclusive(root):
            pass
    assert not lock.exists()


def test_new_windows_runtime_lock_observes_old_running_app_lock(tmp_path, monkeypatch):
    root = tmp_path / "program"
    root.mkdir()
    (root / ".lifecycle.lock").write_text(str(os.getpid()))
    lock = tmp_path / "profile" / "lock"
    monkeypatch.setattr(manager, "lifecycle_lock_path", lambda _: lock)
    with pytest.raises(manager.InstallError, match="active lock"), manager.exclusive(root):
        pass
    assert not lock.exists()


@pytest.mark.parametrize(
    ("release", "display", "status"),
    [
        ("11", "26H2", "pass"),
        ("11", "24H2", "warning"),
        ("11", "25H2", "warning"),
        ("10", "22H2", "warning"),
        ("11", "", "warning"),
    ],
)
def test_windows_marketing_release_and_older_warning_are_not_guessed_from_build(
    tmp_path, monkeypatch, release, display, status
):
    from types import SimpleNamespace

    class Key:
        def __init__(self, value):
            self.value = value

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def query(key, name):
        values = {
            "ProcessorNameString": "CPU",
            "Installed": 1,
            "Version": "v14.44",
            "DisplayVersion": display,
        }
        return values[name], 1

    monkeypatch.setitem(
        sys.modules,
        "winreg",
        SimpleNamespace(HKEY_LOCAL_MACHINE=1, OpenKey=lambda _, key: Key(key), QueryValueEx=query),
    )
    monkeypatch.setattr(manager.platform, "system", lambda: "Windows")
    monkeypatch.setattr(manager.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(manager.platform, "release", lambda: release)
    monkeypatch.setattr(manager.platform, "version", lambda: "10.0.26300")
    monkeypatch.setattr(manager, "windows_vc_files", lambda: True)
    monkeypatch.setattr(manager.shutil, "which", lambda _: None)
    rows = {r["code"]: r for r in manager.host_report(tmp_path, False)["checks"]}
    result = rows["platform"]
    assert result["status"] == status
    assert result["context"]["display_version"] == display
    assert result["context"]["build"] == "10.0.26300"
    assert (
        result["message"] == f"Windows {release} {display}"
        if display
        else result["message"] == f"Windows {release} (10.0.26300)"
    )


def test_privileged_model_download_does_not_leave_profile_or_follow_system_link(tmp_path):
    home = tmp_path / "user"
    target = home / ".cache/models/pinned"
    target.mkdir(parents=True)
    manager.validate_elevated_model_targets([str(target)], home)
    with pytest.raises(manager.InstallError, match="custom model"):
        manager.validate_elevated_model_targets([str(tmp_path / "system")], home)
    system = tmp_path / "system"
    system.mkdir()
    file = system / "model.bin"
    file.write_bytes(b"protected, must remain")
    (target / "model.bin").symlink_to(file)
    with pytest.raises(manager.InstallError, match="leave the user profile"):
        manager.validate_elevated_model_targets([str(target)], home)
    assert file.read_bytes() == b"protected, must remain"


def test_windows_lock_state_cannot_redirect_elevated_writes_via_directory_link(tmp_path):
    profile = tmp_path / "profile"
    profile.mkdir()
    other = tmp_path / "system"
    other.mkdir()
    (profile / "EwPTranscriptsState").symlink_to(other, target_is_directory=True)
    with pytest.raises(manager.InstallError, match="links or junctions"):
        manager.lifecycle_lock_path(tmp_path / "program", windows=True, local_app_data=profile)
    assert not list(other.iterdir())
