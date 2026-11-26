"""Real Windows AMD DLL/package import, without a physical GPU or speech models."""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows ROCm package import")
ROOT = Path(__file__).resolve().parents[2]


def test_verified_amd_overlay_imports_on_windows_without_models(tmp_path):
    uv = ROOT / "installers/extracted/tools/uv.exe"
    venv = tmp_path / "amd-python"
    subprocess.run([str(uv), "venv", "--python", sys.executable, str(venv)], check=True)
    python = venv / "Scripts/python.exe"
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = [
        f"{p['name']}=={p['version']}"
        for p in lock["package"]
        if p["name"] in {"numpy", "pyyaml", "pydantic"}
    ]
    subprocess.run([str(uv), "pip", "install", "--python", str(python), *packages], check=True)
    (venv / "Lib/site-packages/ewp-source.pth").write_text(str(ROOT / "src"), encoding="utf-8")
    subprocess.run(
        [str(python), str(ROOT / "scripts/setup-amd.py"), "--uv", str(uv)], check=True, timeout=360
    )
    result = subprocess.run(
        [
            str(python),
            "-c",
            "import ctranslate2,json; print(json.dumps("
            "{'version':ctranslate2.__version__,'library_import':True}))",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    value = json.loads(result.stdout)
    assert value == {"version": "4.9.1", "library_import": True}
    evidence = ROOT / "installers/amd-evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "windows-import.json").write_text(
        json.dumps(
            {
                "result": "PASS",
                "ctranslate2": value,
                "pinned_runtime": "7.2.0.dev0",
                "models_downloaded": False,
                "gpu_inference_tested": False,
                "physical_amd_card_available": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
