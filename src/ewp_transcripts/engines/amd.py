"""Experimental AMD ROCm ASR; alignment and diarization remain on the CPU."""

from __future__ import annotations

import importlib
import json
import math
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines.protocols import (
    EngineModelInfo,
    TranscriptionDraft,
    TranscriptionSegment,
)
from ewp_transcripts.platform_runtime import background_creation_flags


class _HipAsrEngine:
    """Use the verified HIP CTranslate2 wheel, never an NVIDIA wheel/CPU fallback."""

    def __init__(
        self,
        snapshot: Path,
        *,
        revision: str,
        name: str,
        module_loader: Callable[[str], Any] = importlib.import_module,
    ) -> None:
        self._snapshot = snapshot
        self._revision = revision
        self._loader = module_loader
        self._model: Any = None
        self._model_info = EngineModelInfo(
            role="asr",
            name=name,
            revision=revision,
            local_path=snapshot,
            library_versions={"ctranslate2": "4.9.1", "amd-rocm-sdk": "7.2.0.dev0"},
        )

    @property
    def model_info(self) -> EngineModelInfo:
        return self._model_info

    def transcribe(self, audio_path: Path, *, language: str, batch_size: int) -> TranscriptionDraft:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if not self._snapshot.is_dir() or self._snapshot.name != self._revision:
            raise SpeechEngineError("The selected local ASR model is not installed.")
        try:
            if self._model is None:
                from ewp_transcripts.amd_runtime import require_amd_runtime

                require_amd_runtime()
                backend = self._loader("faster_whisper")
                self._model = backend.WhisperModel(
                    str(self._snapshot),
                    device="cuda",
                    compute_type="float16",
                    local_files_only=True,
                )
            # No WhisperX torch/CUDA VAD: keep all torch stages on CPU on the AMD profile.
            # faster-whisper's ordinary Whisper decoding provides segment/no-speech handling.
            segments, info = self._model.transcribe(
                str(audio_path),
                language=None if language == "auto" else language,
                task="transcribe",
                vad_filter=False,
                word_timestamps=False,
            )
            result = []
            for segment in segments:
                if not isinstance(segment.text, str) or not segment.text.strip():
                    continue
                if not all(math.isfinite(v) and v >= 0 for v in (segment.start, segment.end)):
                    raise ValueError("Invalid AMD ASR timestamps")
                result.append(
                    TranscriptionSegment(
                        text=segment.text,
                        start_ms=round(segment.start * 1000),
                        end_ms=round(segment.end * 1000),
                    )
                )
            if not isinstance(info.language, str) or not info.language:
                raise ValueError("Invalid AMD ASR language")
            return TranscriptionDraft(language=info.language, segments=tuple(result))
        except SpeechEngineError:
            raise
        except Exception as error:
            raise SpeechEngineError(
                "AMD ROCm ASR (experimental) failed; check the AMD runtime and supported "
                "GPU/driver. No CPU fallback was started."
            ) from error

    def close(self) -> None:
        self._model = None


class AmdAsrEngine(_HipAsrEngine):
    """Keep the HIP/OpenMP runtime outside the process running torch CPU stages."""

    def transcribe(self, audio_path: Path, *, language: str, batch_size: int) -> TranscriptionDraft:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        payload = {
            "snapshot": str(self._snapshot),
            "revision": self._revision,
            "name": self.model_info.name,
            "audio": str(audio_path),
            "language": language,
        }
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ewp_transcripts.engines.amd"],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
                creationflags=background_creation_flags(),
            )
            if result.returncode != 0:
                raise SpeechEngineError(
                    "AMD ROCm ASR (experimental) failed. Check AMD diagnostics; "
                    "no CPU ASR fallback was started."
                )
            return TranscriptionDraft.model_validate_json(result.stdout)
        except SpeechEngineError:
            raise
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise SpeechEngineError(
                "AMD ASR worker failed to return a valid transcript."
            ) from error


def _worker() -> None:
    import contextlib

    try:
        payload = json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            engine = _HipAsrEngine(
                Path(payload["snapshot"]), revision=payload["revision"], name=payload["name"]
            )
            try:
                result = engine.transcribe(
                    Path(payload["audio"]), language=payload["language"], batch_size=1
                )
            finally:
                engine.close()
        print(result.model_dump_json())
    except Exception:
        print(
            "AMD_ASR_WORKER_FAILED: check the experimental AMD runtime and diagnostics",
            file=sys.stderr,
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    _worker()
