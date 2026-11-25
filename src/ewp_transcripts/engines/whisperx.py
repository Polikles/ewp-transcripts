"""Lazy WhisperX ASR and alignment adapters for pinned local model snapshots."""

from __future__ import annotations

import gc
import importlib
import math
import sys
from collections.abc import Callable, Mapping
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Protocol, cast

from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines.notices import suppress_accepted_backend_notices
from ewp_transcripts.engines.protocols import (
    AlignedSegment,
    AlignedTranscript,
    AlignedWord,
    EngineModelInfo,
    TranscriptionDraft,
    TranscriptionSegment,
)


class _AsrModel(Protocol):
    def transcribe(self, audio: object, **kwargs: object) -> Mapping[str, object]: ...


class _WhisperXModule(Protocol):
    def load_audio(self, path: str) -> object: ...

    def load_model(self, model: str, device: str, **kwargs: object) -> _AsrModel: ...

    def load_align_model(
        self, *, language_code: str, device: str, **kwargs: object
    ) -> tuple[object, Mapping[str, object]]: ...

    def align(
        self,
        transcript: object,
        model: object,
        metadata: Mapping[str, object],
        audio: object,
        device: str,
        **kwargs: object,
    ) -> Mapping[str, object]: ...


ModuleLoader = Callable[[], _WhisperXModule]


class _CudaModule(Protocol):
    def is_available(self) -> bool: ...

    def empty_cache(self) -> None: ...

    def synchronize(self) -> None: ...


class _TorchModule(Protocol):
    cuda: _CudaModule


def _load_whisperx() -> _WhisperXModule:
    from ewp_transcripts.engines.ffmpeg_compat import prepare_speech_libraries

    prepare_speech_libraries()
    return cast(_WhisperXModule, importlib.import_module("whisperx"))


class WhisperXAsrEngine:
    """Local-only faster-whisper ASR through WhisperX with lazy model loading."""

    def __init__(
        self,
        snapshot: Path,
        *,
        revision: str,
        name: str = "large-v2",
        device: str,
        compute_type: str,
        vad_method: str = "pyannote",
        module_loader: ModuleLoader = _load_whisperx,
    ) -> None:
        self._snapshot = snapshot
        self._device = device
        self._compute_type = compute_type
        self._vad_method = vad_method
        self._module_loader = module_loader
        self._model: _AsrModel | None = None
        self._module: _WhisperXModule | None = None
        self._model_info = EngineModelInfo(
            role="asr",
            name=name,
            revision=revision,
            local_path=snapshot,
            library_versions=_library_versions(),
        )

    @property
    def model_info(self) -> EngineModelInfo:
        return self._model_info

    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str,
        batch_size: int,
    ) -> TranscriptionDraft:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self._require_snapshot("ASR")
        try:
            module = self._module or self._module_loader()
            self._module = module
            backend_language = None if language == "auto" else language
            if self._model is None:
                load_options: dict[str, object] = {
                    "compute_type": self._compute_type,
                    "vad_method": self._vad_method,
                    "local_files_only": True,
                }
                if backend_language is not None:
                    load_options["language"] = backend_language
                with suppress_accepted_backend_notices():
                    self._model = module.load_model(
                        str(self._snapshot),
                        self._device,
                        **load_options,
                    )
            audio = module.load_audio(str(audio_path))
            transcribe_options: dict[str, object] = {
                "batch_size": batch_size,
                "task": "transcribe",
            }
            if backend_language is not None:
                transcribe_options["language"] = backend_language
            with suppress_accepted_backend_notices():
                result = self._model.transcribe(audio, **transcribe_options)
            return _transcription_draft(result, requested_language=language)
        except SpeechEngineError:
            raise
        except Exception as error:
            raise SpeechEngineError("WhisperX ASR execution failed") from error

    def close(self) -> None:
        self._model = None
        self._module = None
        gc.collect()
        _release_cuda()

    def _require_snapshot(self, role: str) -> None:
        if not self._snapshot.is_dir() or self._snapshot.name != self._model_info.revision:
            raise SpeechEngineError(
                f"Pinned local {role} model snapshot is unavailable; "
                "prepare it using WSL config/MODEL_SETUP.md, then run "
                "`transcriber doctor --config <path>`"
            )


class WhisperXAlignmentEngine:
    """Local-only WhisperX word alignment with lazy model loading."""

    def __init__(
        self,
        snapshot: Path,
        *,
        revision: str,
        english_snapshot: Path | None = None,
        english_revision: str | None = None,
        device: str,
        module_loader: ModuleLoader = _load_whisperx,
    ) -> None:
        self._snapshot = snapshot
        self._revision = revision
        self._english_snapshot = english_snapshot
        self._english_revision = english_revision
        self._device = device
        self._module_loader = module_loader
        self._module: _WhisperXModule | None = None
        self._model: object | None = None
        self._metadata: Mapping[str, object] | None = None
        self._model_info = EngineModelInfo(
            role="alignment",
            name="wav2vec2-large-xlsr-53-polish",
            revision=revision,
            local_path=snapshot,
            library_versions=_library_versions(),
        )

    @property
    def model_info(self) -> EngineModelInfo:
        return self._model_info

    def align(
        self,
        audio_path: Path,
        transcription: TranscriptionDraft,
        *,
        language: str,
    ) -> AlignedTranscript:
        snapshot, revision, name = self._select_model(language)
        self._require_snapshot(snapshot, revision)
        self._model_info = EngineModelInfo(
            role="alignment",
            name=name,
            revision=revision,
            local_path=snapshot,
            library_versions=_library_versions(),
        )
        try:
            module = self._module or self._module_loader()
            self._module = module
            if self._model is None or self._metadata is None:
                self._model, self._metadata = module.load_align_model(
                    language_code=language,
                    device=self._device,
                    model_name=str(snapshot),
                    model_cache_only=True,
                )
            audio = module.load_audio(str(audio_path))
            raw_segments = [
                {
                    "start": segment.start_ms / 1000,
                    "end": segment.end_ms / 1000,
                    "text": segment.text,
                }
                for segment in transcription.segments
            ]
            result = module.align(
                raw_segments,
                self._model,
                self._metadata,
                audio,
                self._device,
                return_char_alignments=False,
            )
            return _aligned_transcript(result, language=language)
        except SpeechEngineError:
            raise
        except Exception as error:
            raise SpeechEngineError("WhisperX alignment execution failed") from error

    def close(self) -> None:
        self._model = None
        self._metadata = None
        self._module = None
        gc.collect()
        _release_cuda()

    def _select_model(self, language: str) -> tuple[Path, str, str]:
        if language == "pl":
            return self._snapshot, self._revision, "wav2vec2-large-xlsr-53-polish"
        if language == "en" and self._english_snapshot is not None and self._english_revision:
            return self._english_snapshot, self._english_revision, "wav2vec2-base-960h"
        raise SpeechEngineError(f"No pinned local alignment model is configured for: {language}")

    @staticmethod
    def _require_snapshot(snapshot: Path, revision: str) -> None:
        if not snapshot.is_dir() or snapshot.name != revision:
            raise SpeechEngineError(
                "Pinned local alignment model snapshot is unavailable; "
                "prepare it using WSL config/MODEL_SETUP.md, then run "
                "`transcriber doctor --config <path>`"
            )


def _transcription_draft(
    result: Mapping[str, object], *, requested_language: str
) -> TranscriptionDraft:
    language = result.get("language", requested_language)
    if not isinstance(language, str) or not language:
        raise SpeechEngineError("WhisperX ASR returned an invalid language")
    segments = tuple(_transcription_segment(item) for item in _mapping_list(result, "segments"))
    return TranscriptionDraft(language=language, segments=segments)


def _transcription_segment(item: Mapping[str, object]) -> TranscriptionSegment:
    text = item.get("text")
    if not isinstance(text, str) or not text:
        raise SpeechEngineError("WhisperX ASR returned invalid segment text")
    return TranscriptionSegment(
        text=text,
        start_ms=_required_milliseconds(item.get("start")),
        end_ms=_required_milliseconds(item.get("end")),
    )


def _aligned_transcript(result: Mapping[str, object], *, language: str) -> AlignedTranscript:
    segments = tuple(_aligned_segment(item) for item in _mapping_list(result, "segments"))
    return AlignedTranscript(language=language, segments=segments)


def _aligned_segment(item: Mapping[str, object]) -> AlignedSegment:
    text = item.get("text")
    if not isinstance(text, str) or not text:
        raise SpeechEngineError("WhisperX alignment returned invalid segment text")
    return AlignedSegment(
        text=text,
        start_ms=_required_milliseconds(item.get("start")),
        end_ms=_required_milliseconds(item.get("end")),
        words=tuple(_aligned_word(word) for word in _mapping_list(item, "words")),
    )


def _aligned_word(item: Mapping[str, object]) -> AlignedWord:
    text = item.get("word")
    if not isinstance(text, str) or not text:
        raise SpeechEngineError("WhisperX alignment returned invalid word text")
    return AlignedWord(
        text=text,
        start_ms=_optional_milliseconds(item.get("start")),
        end_ms=_optional_milliseconds(item.get("end")),
        confidence=_confidence(item.get("score")),
    )


def _mapping_list(document: Mapping[str, object], key: str) -> tuple[Mapping[str, object], ...]:
    raw = document.get(key)
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise SpeechEngineError(f"WhisperX returned an invalid {key} list")
    return tuple(cast(Mapping[str, object], item) for item in raw)


def _optional_milliseconds(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpeechEngineError("WhisperX returned an invalid timestamp")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0:
        raise SpeechEngineError("WhisperX returned an invalid timestamp")
    return round(numeric * 1000)


def _required_milliseconds(value: object) -> int:
    converted = _optional_milliseconds(value)
    if converted is None:
        raise SpeechEngineError("WhisperX returned a missing required timestamp")
    return converted


def _confidence(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpeechEngineError("WhisperX returned an invalid confidence")
    confidence = float(value)
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise SpeechEngineError("WhisperX returned an invalid confidence")
    return confidence


def _library_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for distribution in ("whisperx", "torch", "faster-whisper", "ctranslate2"):
        try:
            versions[distribution] = version(distribution)
        except PackageNotFoundError:
            continue
    return versions


def _release_cuda() -> None:
    module = sys.modules.get("torch")
    if module is None:
        return
    try:
        torch = cast(_TorchModule, module)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except (ImportError, AttributeError, RuntimeError):
        return
