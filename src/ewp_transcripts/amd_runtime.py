"""Lazy validation of the separately pinned Windows AMD runtime installation."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import sys
from importlib.resources import files
from pathlib import Path

from ewp_transcripts.domain.errors import SpeechEngineError


def require_amd_runtime() -> int:
    """Verify HIP package identity before importing it; check the actual device API."""
    if sys.platform != "win32":
        raise SpeechEngineError(
            "AMD ROCm (experimental) currently supports managed Windows x64 only."
        )
    pins = json.loads(
        files("ewp_transcripts.resources").joinpath("amd-windows-runtime.json").read_text()
    )
    spec = importlib.util.find_spec("ctranslate2")
    if spec is None or not spec.submodule_search_locations:
        raise SpeechEngineError("AMD runtime is missing; repair this installation.")
    library = Path(next(iter(spec.submodule_search_locations))) / "ctranslate2.dll"
    if not library.is_file():
        raise SpeechEngineError("AMD runtime is missing; repair this installation.")
    with library.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != pins["ctranslate2"]["dll_sha256"]:
        raise SpeechEngineError(
            "The AMD HIP runtime does not match its pinned build; repair this installation."
        )
    backend = importlib.import_module("ctranslate2")
    count = int(backend.get_cuda_device_count())  # CTranslate2 exposes HIP through its CUDA API.
    if count < 1 or "float16" not in backend.get_supported_compute_types("cuda"):
        raise SpeechEngineError(
            "AMD ROCm cannot use this GPU/driver with float16. "
            "AMD support is experimental and untested on physical hardware."
        )
    return count
