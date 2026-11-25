"""Explicit model/language setup stays isolated from checkout imports and downloads in tests."""

import importlib.metadata
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from ewp_transcripts.config import ApplicationConfig

ROOT = Path(__file__).resolve().parents[2]


def script():
    spec = importlib.util.spec_from_file_location(
        "ewp_test_model_setup", ROOT / "scripts/setup-models.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_language_setup_isolates_process_preserves_paths_and_cleans_directory(
    tmp_path, monkeypatch
):
    module = script()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NLTK_DATA", os.pathsep.join(["language-data", str(tmp_path / "absolute")]))
    original = os.environ["NLTK_DATA"]
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        assert Path(kwargs["cwd"]).is_dir()
        assert not list(Path(kwargs["cwd"]).iterdir())
        assert arguments[:3] == [sys.executable, "-I", "-c"]
        assert "NLTK_DISABLE_IMPORT_SECURITY" not in arguments[-1]
        assert "punkt_tab" in arguments[-1]
        assert kwargs["env"]["NLTK_DATA"] == os.pathsep.join(
            [str(tmp_path / "language-data"), str(tmp_path / "absolute")]
        )
        assert kwargs["check"] is False
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", run)
    module.prepare_language_data()
    assert Path.cwd() == tmp_path and os.environ["NLTK_DATA"] == original
    assert not Path(calls[0][1]["cwd"]).exists()


def test_locked_nltk_import_succeeds_from_neutral_child_without_network(tmp_path, monkeypatch):
    if importlib.util.find_spec("nltk") is None:
        pytest.skip("Locked NLTK installation is required for this import regression")
    module = script()
    actual_run = subprocess.run
    monkeypatch.chdir(ROOT)
    # A parent PYTHONPATH must not shadow regex in the isolated preparation child.
    (tmp_path / "regex.py").write_text('raise RuntimeError("shadow regex imported")')
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    version = importlib.metadata.version("nltk")
    code = "import nltk, regex, sys; assert sys.flags.isolated; print(nltk.__version__)"
    if version == "3.10.1":
        code += '; assert any(type(f).__name__=="NLTKSafeImportFinder" for f in sys.meta_path)'

    def import_only(arguments, **kwargs):
        # Exercise the real child/cwd/flags/env while omitting ONLY the network download.
        result = actual_run(
            [*arguments[:-1], code], **kwargs, capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == version
        return result

    monkeypatch.setattr(module.subprocess, "run", import_only)
    module.prepare_language_data()
    assert Path.cwd() == ROOT
    assert "nltk" not in sys.modules


def test_language_setup_failure_stops_before_model_downloads(monkeypatch):
    module = script()
    monkeypatch.setattr(sys, "argv", ["setup-models.py", "--yes", "--public-only"])
    hf = ModuleType("huggingface_hub")

    def download(**kwargs):
        raise AssertionError("Models must not download after language setup failure")

    hf.snapshot_download = download
    monkeypatch.setitem(sys.modules, "huggingface_hub", hf)
    monkeypatch.setattr(
        module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=7)
    )
    with pytest.raises(SystemExit, match="Language data setup failed"):
        module.main()


def test_public_model_setup_keeps_pins_and_skips_gated_token_prompt(monkeypatch):
    module = script()
    calls = []
    config = ApplicationConfig()
    monkeypatch.setattr(module, "load_config", lambda: config)
    monkeypatch.setattr(module, "prepare_language_data", lambda: calls.append("language"))
    monkeypatch.setattr(
        module.getpass, "getpass", lambda *args: pytest.fail("Public setup prompted for token")
    )
    monkeypatch.setattr(sys, "argv", ["setup-models.py", "--yes", "--public-only"])
    hf = ModuleType("huggingface_hub")
    hf.snapshot_download = lambda **kwargs: calls.append(kwargs)
    monkeypatch.setitem(sys.modules, "huggingface_hub", hf)
    module.main()
    assert calls[0] == "language" and len(calls) == 4
    assert [(x["repo_id"], x["revision"], x["local_dir"]) for x in calls[1:]] == [
        (config.models.asr_repository, config.models.asr_revision, config.models.asr_snapshot_path),
        (
            config.models.alignment_model,
            config.models.alignment_revision,
            config.models.alignment_snapshot_path,
        ),
        (
            config.models.english_alignment_model,
            config.models.english_alignment_revision,
            config.models.english_alignment_snapshot_path,
        ),
    ]


def test_help_and_cancel_do_not_prepare_or_download(monkeypatch):
    module = script()
    monkeypatch.setattr(
        module, "prepare_language_data", lambda: pytest.fail("Unexpected language setup")
    )
    monkeypatch.setattr(sys, "argv", ["setup-models.py", "--help"])
    with pytest.raises(SystemExit) as result:
        module.main()
    assert result.value.code == 0
    monkeypatch.setattr(sys, "argv", ["setup-models.py"])
    monkeypatch.setattr("builtins.input", lambda *args: "n")
    with pytest.raises(SystemExit, match="Cancelled"):
        module.main()


def test_installer_progress_reports_real_http_bytes_instead_of_snapshot_file_counts(
    monkeypatch, capsys
):
    import io
    import json

    import huggingface_hub
    from huggingface_hub import file_download

    progress = __import__("importlib").import_module("huggingface_hub.utils.tqdm")
    monkeypatch.setattr(progress, "tqdm", progress.tqdm)  # Restore the child-only hook after test.
    module = script()
    monkeypatch.setattr(module, "prepare_language_data", lambda: None)
    monkeypatch.setattr(
        sys, "argv", ["setup-models.py", "--yes", "--model", "asr", "--progress-json"]
    )
    monkeypatch.setattr(
        file_download,
        "_request_wrapper",
        lambda **kwargs: SimpleNamespace(
            headers={"Content-Length": "8"},
            iter_content=lambda **kw: [b"1234", b"5678"],
            raise_for_status=lambda: None,
        ),
    )

    def transfer(**kwargs):
        target = io.BytesIO()
        file_download.http_get(
            "https://synthetic.invalid/model",
            target,
            displayed_filename="model.bin",
            expected_size=8,
        )
        assert target.getvalue() == b"12345678"

    monkeypatch.setattr(huggingface_hub, "snapshot_download", transfer)
    module.main()
    events = [
        json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")
    ]
    assert events[0]["stage"] == "model-item" and events[-1]["stage"] == "model-complete"
    events = [event for event in events if event["stage"] == "download"]
    assert events and events[-1]["bytes"] == events[-1]["total"] == 8
    assert events[-1]["unit"] == "B" and events[-1]["message"] == "model.bin"
    assert events[-1]["download_id"].endswith(":model.bin")
