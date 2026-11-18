"""Lazy local-only pyannote Community-1 diarization adapter."""

from __future__ import annotations

import gc
import importlib
from collections.abc import Callable, Iterable
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Protocol, cast

from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines.ffmpeg_compat import prepare_speech_libraries
from ewp_transcripts.engines.notices import suppress_accepted_backend_notices
from ewp_transcripts.engines.protocols import (
    DiarizationResult,
    DiarizationTurn,
    EngineModelInfo,
)


class _Segment(Protocol):
    start: float
    end: float


class _Annotation(Protocol):
    def itertracks(self, *, yield_label: bool) -> Iterable[tuple[_Segment, object, str]]: ...


class _Output(Protocol):
    speaker_diarization: _Annotation
    exclusive_speaker_diarization: _Annotation | None


class _Pipeline(Protocol):
    def to(self, device: object) -> None: ...

    def __call__(self, audio: Path, **kwargs: object) -> _Output: ...


class _PipelineClass(Protocol):
    @classmethod
    def from_pretrained(cls, checkpoint: Path, **kwargs: object) -> _Pipeline | None: ...


class _PyannoteModule(Protocol):
    Pipeline: _PipelineClass


class _CudaModule(Protocol):
    def is_available(self) -> bool: ...

    def empty_cache(self) -> None: ...

    def synchronize(self) -> None: ...


class _TorchModule(Protocol):
    cuda: _CudaModule

    def device(self, name: str) -> object: ...


PyannoteLoader = Callable[[], _PyannoteModule]
TorchLoader = Callable[[], _TorchModule]


def _load_pyannote() -> _PyannoteModule:
    prepare_speech_libraries()
    return cast(_PyannoteModule, importlib.import_module("pyannote.audio"))


def _load_torch() -> _TorchModule:
    return cast(_TorchModule, importlib.import_module("torch"))


class PyannoteDiarizationEngine:
    """Pinned Community-1 pipeline with no token or repository lookup at runtime."""

    def __init__(
        self,
        snapshot: Path,
        *,
        revision: str,
        device: str,
        module_loader: PyannoteLoader = _load_pyannote,
        torch_loader: TorchLoader = _load_torch,
    ) -> None:
        self._snapshot = snapshot
        self._device = device
        self._module_loader = module_loader
        self._torch_loader = torch_loader
        self._pipeline: _Pipeline | None = None
        self._torch: _TorchModule | None = None
        self._model_info = EngineModelInfo(
            role="diarization",
            name="speaker-diarization-community-1",
            revision=revision,
            local_path=snapshot,
            library_versions=_library_versions(),
        )

    @property
    def model_info(self) -> EngineModelInfo:
        return self._model_info

    def diarize(self, audio_path: Path, *, speaker_count: int | None) -> DiarizationResult:
        if speaker_count is not None and speaker_count < 1:
            raise ValueError("speaker_count must be positive or None")
        self._require_snapshot()
        try:
            module = self._module_loader()
            torch = self._torch or self._torch_loader()
            self._torch = torch
            if self._pipeline is None:
                with suppress_accepted_backend_notices():
                    self._pipeline = module.Pipeline.from_pretrained(self._snapshot, token=False)
                if self._pipeline is None:
                    raise SpeechEngineError("Pinned local diarization pipeline could not load")
                with suppress_accepted_backend_notices():
                    self._pipeline.to(torch.device(self._device))
            kwargs = {} if speaker_count is None else {"num_speakers": speaker_count}
            with suppress_accepted_backend_notices():
                output = self._pipeline(audio_path, **kwargs)
            turns = _turns(output.speaker_diarization)
            exclusive = getattr(output, "exclusive_speaker_diarization", None)
            return DiarizationResult(
                turns=turns,
                exclusive_turns=_turns(exclusive) if exclusive is not None else None,
            )
        except SpeechEngineError:
            raise
        except Exception as error:
            raise SpeechEngineError("Pyannote diarization execution failed") from error

    def close(self) -> None:
        self._pipeline = None
        torch = self._torch
        self._torch = None
        gc.collect()
        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def _require_snapshot(self) -> None:
        if (
            not self._snapshot.is_dir()
            or self._snapshot.name != self._model_info.revision
            or not (self._snapshot / "config.yaml").is_file()
        ):
            raise SpeechEngineError(
                "Pinned local diarization model snapshot is unavailable; "
                "accept the model terms and prepare it using WSL config/MODEL_SETUP.md, "
                "then run `transcriber doctor --config <path>`"
            )


def _turns(annotation: _Annotation) -> tuple[DiarizationTurn, ...]:
    raw = annotation.itertracks(yield_label=True)
    turns = [
        DiarizationTurn(
            start_ms=max(0, round(segment.start * 1000)),
            end_ms=max(0, round(segment.end * 1000)),
            speaker_label=str(label),
        )
        for segment, _, label in raw
    ]
    turns.sort(key=lambda turn: (turn.start_ms, turn.end_ms, turn.speaker_label))
    return tuple(turns)


def _library_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for distribution in ("pyannote.audio", "torch"):
        try:
            versions[distribution] = version(distribution)
        except PackageNotFoundError:
            continue
    return versions
