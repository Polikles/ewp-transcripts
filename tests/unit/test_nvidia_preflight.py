"""Pinned-library hardware preflight: no ML imports, CUDA context, models or physical GPU."""

from __future__ import annotations

import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_distribution import manager


def test_preflight_policy_tracks_the_actual_locked_library_stack():
    root = Path(__file__).resolve().parents[2]
    packages = {
        p["name"]: p["version"]
        for p in tomllib.loads((root / "uv.lock").read_text())["package"]
        if "version" in p
    }
    assert packages["torch"] == "2.8.0+cu128"
    assert packages["ctranslate2"] == "4.8.1"
    assert packages["nvidia-cuda-runtime-cu12"] == "12.8.90"
    assert packages["nvidia-cudnn-cu12"] == "9.10.2.21"
    assert "whl/cu128" in (root / "pyproject.toml").read_text()


def device(cc="8.6", memory=24 * 1024**3, driver="580.00", index="0"):
    return {
        "name": "Synthetic NVIDIA",
        "driver": driver,
        "index": index,
        "uuid": "GPU-test-" + index,
        "compute_capability": cc,
        "vram_bytes": memory,
    }


@pytest.fixture(autouse=True)
def clean_cuda_selection(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    monkeypatch.delenv("CUDA_DEVICE_ORDER", raising=False)


@pytest.mark.parametrize("cc", ["3.5", "5.2", "6.0", "6.1", "6.2"])
def test_pre_volta_is_unsupported_even_with_enough_memory(cc):
    result = manager.nvidia_compatibility([device(cc)], "Windows")
    assert result["compatibility"] == "unsupported_architecture"
    assert result["local_supported"] is False


@pytest.mark.parametrize("cc", sorted(manager.NVIDIA_COMPUTE))
def test_known_locked_architectures_meet_preflight_without_claiming_inference(cc):
    result = manager.nvidia_compatibility([device(cc)], "Windows")
    assert result["compatibility"] == "supported"
    assert result["cuda_runtime"] == "12.8.90"


@pytest.mark.parametrize("cc", ["N/A", "99.0", "7", "8.foo"])
def test_unknown_metadata_does_not_certify_local_asr(cc):
    result = manager.nvidia_compatibility([device(cc)], "Windows")
    assert result["compatibility"] == "unknown"
    assert result["local_supported"] is False


@pytest.mark.parametrize("memory", [4, 6, 8, 10, 11])
def test_low_memory_warns_but_does_not_forbid_compatible_local_choice(memory):
    result = manager.nvidia_compatibility([device(memory=memory * 1024**3)], "Windows")
    assert result["compatibility"] == "low_vram"
    assert result["local_supported"] is True


def test_nominal_twelve_gib_card_with_driver_reserved_memory_is_not_rejected():
    result = manager.nvidia_compatibility([device(memory=12282 * 1024**2)], "Windows")
    assert result["compatibility"] == "supported"


@pytest.mark.parametrize("system,driver", [("Windows", "572.60"), ("Linux", "570.124.05")])
def test_old_driver_does_not_meet_the_full_update_one_project_baseline(system, driver):
    result = manager.nvidia_compatibility([device(driver=driver)], system)
    assert result["compatibility"] == "driver_too_old"
    assert result["local_supported"] is False


@pytest.mark.parametrize("system,driver", [("Windows", "572.61"), ("Linux", "570.124.06")])
def test_exact_driver_floor_is_accepted(system, driver):
    assert manager.nvidia_compatibility([device(driver=driver)], system)["local_supported"]


def test_wsl_checks_the_windows_host_driver_floor_not_linux_package_numbering():
    result = manager.nvidia_compatibility([device(driver="572.16")], "WSL")
    assert result["compatibility"] == "driver_too_old"
    assert result["minimum_driver"] == "572.61"
    assert manager.nvidia_compatibility([device(driver="572.61")], "WSL")["local_supported"]


def test_missing_memory_is_not_fabricated():
    result = manager.nvidia_compatibility([device(memory=None)], "Windows")
    assert result["compatibility"] == "memory_unknown"
    assert result["local_supported"] is True


def test_multi_gpu_memory_is_not_added_and_ambiguous_default_is_not_certified(monkeypatch):
    cards = [device(memory=8 * 1024**3), device(memory=8 * 1024**3, index="1")]
    assert manager.nvidia_compatibility(cards, "Windows")["compatibility"] == "selection_unknown"
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "GPU-test-1")
    result = manager.nvidia_compatibility(cards, "Windows")
    assert result["selected_device"]["index"] == "1"
    assert result["compatibility"] == "low_vram"
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "1")
    assert manager.nvidia_compatibility(cards, "Windows")["compatibility"] == "selection_unknown"
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    assert not manager.nvidia_compatibility(cards, "Windows")["local_supported"]


def test_explicit_pci_device_order_selects_zero_without_changing_environment(monkeypatch):
    monkeypatch.setenv("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    result = manager.nvidia_compatibility([device(index="1"), device(index="0")], "Windows")
    assert result["selected_device"]["index"] == "0"


def test_query_reads_architecture_and_memory_and_uses_old_driver_fallback(monkeypatch):
    monkeypatch.setattr(manager.shutil, "which", lambda _: "nvidia-smi")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(
            returncode=0, stdout='0, GPU-one, "NVIDIA, Test", 580.00, 8.6, 8192\n'
        )

    monkeypatch.setattr(manager.subprocess, "run", run)
    result = manager.nvidia_devices()
    assert result[0]["name"] == "NVIDIA, Test"
    assert result[0]["vram_bytes"] == 8 * 1024**3
    assert "compute_cap" in calls[0][1] and "nounits" in calls[0][2]
    outputs = iter(
        [
            SimpleNamespace(returncode=1, stdout=""),
            SimpleNamespace(returncode=0, stdout="Old GPU, 470.00\n"),
        ]
    )
    monkeypatch.setattr(manager.subprocess, "run", lambda *a, **kw: next(outputs))
    assert manager.nvidia_devices() == [{"name": "Old GPU", "driver": "470.00"}]


@pytest.mark.parametrize("memory", ["N/A", "nan", "inf", "-1"])
def test_malformed_vram_is_unknown_not_a_zero_or_success(monkeypatch, memory):
    monkeypatch.setattr(manager.shutil, "which", lambda _: "nvidia-smi")
    monkeypatch.setattr(
        manager.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(
            returncode=0, stdout=f"0, GPU-one, GPU, 580.00, 8.6, {memory}\n"
        ),
    )
    assert manager.nvidia_devices()[0]["vram_bytes"] is None
