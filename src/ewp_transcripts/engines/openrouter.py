"""Explicit OpenRouter STT with provider word times, bounded uploads and cost accounting."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import urllib.error
import urllib.request
import wave
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ewp_transcripts.cancellation import CancellationToken, check_cancellation
from ewp_transcripts.config import SpeechConfig
from ewp_transcripts.domain.canonical import CanonicalWarning
from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines import cloud_chunks
from ewp_transcripts.engines.cloud_chunks import MixedChunkMerger, plan_audio_chunks
from ewp_transcripts.engines.protocols import (
    AlignedSegment,
    AlignedTranscript,
    AlignedWord,
    DiarizationResult,
    DiarizationTurn,
    EngineModelInfo,
    TranscriptionDraft,
    TranscriptionSegment,
)

BASE = "https://openrouter.ai/api/v1"
HttpCall = Callable[[str, Mapping[str, str], bytes | None, float], dict[str, Any]]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        raise SpeechEngineError(
            "OpenRouter ASR refused a redirect; audio and key were not forwarded"
        )


def request_json(
    url: str, headers: Mapping[str, str], body: bytes | None, timeout: float
) -> dict[str, Any]:
    request = urllib.request.Request(
        url, data=body, headers=dict(headers), method="POST" if body else "GET"
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise SpeechEngineError("OpenRouter ASR response exceeds the safe size limit")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise SpeechEngineError("OpenRouter ASR returned an invalid response object")
            identifier = response.headers.get("X-Generation-Id")
            if identifier:
                value["_generation_id"] = identifier[:200]
            return value
    except urllib.error.HTTPError as error:
        raise SpeechEngineError(
            f"OpenRouter ASR request failed (HTTP {error.code}); "
            "check model, key, credits and supported options"
        ) from None
    except (OSError, ValueError):
        raise SpeechEngineError(
            "OpenRouter ASR request failed or returned unreadable JSON; no automatic retry was made"
        ) from None


def _number(value: object) -> Decimal:
    if isinstance(value, bool):
        raise SpeechEngineError("OpenRouter ASR returned invalid numeric data")
    try:
        number = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise SpeechEngineError("OpenRouter ASR returned invalid numeric data") from None
    if not number.is_finite() or number < 0:
        raise SpeechEngineError("OpenRouter ASR returned invalid numeric data")
    return number


def maximum_rate(model: str, transport: HttpCall = request_json) -> Decimal:
    """Use the most expensive currently listed endpoint, with explicit model billing units."""
    payload = transport(f"{BASE}/models/{model}/endpoints", {}, None, 30)
    data = payload.get("data")
    endpoints = data.get("endpoints") if isinstance(data, dict) else None
    if not isinstance(endpoints, list) or not endpoints:
        raise SpeechEngineError("OpenRouter ASR pricing is unavailable; no audio was sent")
    rates = []
    for endpoint in endpoints:
        pricing = endpoint.get("pricing") if isinstance(endpoint, dict) else None
        if not isinstance(pricing, dict) or "prompt" not in pricing:
            raise SpeechEngineError("OpenRouter ASR pricing is unavailable; no audio was sent")
        rates.append(_number(pricing["prompt"]))
    # These four vetted STT models expose duration prices via the generic prompt field.
    # MAI's unit is hours; the other three use seconds (not text-token units).
    return max(rates) / (3600 if model == "microsoft/mai-transcribe-2" else 1)


@dataclass(frozen=True)
class CloudTranscript:
    aligned: AlignedTranscript
    diarization: DiarizationResult


def parse_transcript(
    document: dict[str, Any], *, duration_ms: int, offset_ms: int, language: str
) -> CloudTranscript:
    """Require actual timed words; no invented alignment/speaker labels or text-only fallback."""
    raw = document.get("words")
    if raw == [] and document.get("text") == "" and language in {"pl", "en"}:
        return CloudTranscript(
            AlignedTranscript(language=language, segments=()), DiarizationResult(turns=())
        )
    if not isinstance(raw, list) or not raw:
        raise SpeechEngineError(
            "OpenRouter ASR returned no word timestamps; this model/endpoint cannot "
            "complete the subtitle workflow"
        )
    detected = document.get("language") or language
    detected = {"english": "en", "polish": "pl", "pol": "pl", "eng": "en"}.get(
        str(detected).lower(), str(detected).lower()
    )
    if detected not in {"pl", "en"}:
        raise SpeechEngineError("OpenRouter ASR must identify Polish or English for this workflow")
    segments = []
    turns = []
    previous = -1
    for item in raw:
        if not isinstance(item, dict):
            raise SpeechEngineError("OpenRouter ASR returned invalid word timing data")
        text = item.get("word", item.get("text"))
        if not isinstance(text, str) or not text.strip():
            raise SpeechEngineError("OpenRouter ASR returned an empty timed word")
        start = round(_number(item.get("start")) * 1000)
        end = round(_number(item.get("end")) * 1000)
        if start < previous or end < start or end > duration_ms + 500:
            raise SpeechEngineError(
                "OpenRouter ASR returned out-of-range or unordered word timestamps"
            )
        previous = start
        # Normalize one provider word at a time: exact timing and speaker boundaries survive
        # cross-talk; review/subtitle presentation does its own sentence-aware grouping.
        word = AlignedWord(text=text.strip(), start_ms=start + offset_ms, end_ms=end + offset_ms)
        segments.append(
            AlignedSegment(
                text=text.strip(), start_ms=start + offset_ms, end_ms=end + offset_ms, words=(word,)
            )
        )
        speaker = item.get("speaker", item.get("speaker_id"))
        if speaker is None:
            # Some endpoints put speaker identity only on enclosing segments.
            for segment in (
                (document.get("segments") or [])
                if isinstance(document.get("segments"), list)
                else []
            ):
                if isinstance(segment, dict) and segment.get("speaker") is not None:
                    left = round(_number(segment.get("start")) * 1000)
                    right = round(_number(segment.get("end")) * 1000)
                    if left <= start < right:
                        speaker = segment["speaker"]
                        break
        if speaker is not None:
            if isinstance(speaker, bool) or not isinstance(speaker, (str, int)):
                raise SpeechEngineError("OpenRouter ASR returned invalid speaker identity")
            turns.append(
                DiarizationTurn(
                    start_ms=start + offset_ms, end_ms=end + offset_ms, speaker_label=str(speaker)
                )
            )
    return CloudTranscript(
        AlignedTranscript(language=detected, segments=tuple(segments)),
        DiarizationResult(turns=tuple(turns)),
    )


class CloudSpeechSession:
    """One job's shared response cache, budget and safe provenance across pipeline stages."""

    def __init__(
        self,
        config: SpeechConfig,
        api_key: str,
        *,
        cancellation: CancellationToken | None = None,
        transport: HttpCall | None = None,
        rate: Decimal | None = None,
    ) -> None:
        self.config, self._key, self._transport = config, api_key, transport or request_json
        self._rate = rate
        self._cancellation = cancellation
        self._cache: dict[Path, CloudTranscript] = {}
        self.calls: list[dict[str, Any]] = []
        self._charged = Decimal(0)
        self.speaker_notes: list[dict[str, Any]] = []

    @property
    def provenance(self) -> dict[str, Any]:
        return {
            "accounting_scope": "job",
            "provider": "openrouter",
            "model": self.config.model,
            "endpoint": f"{BASE}/audio/transcriptions",
            "consent": "explicit-authorization",
            "timing": "provider-word-timestamps",
            "budget_usd": self.config.max_cost_usd,
            "accounted_cost_usd": str(self._charged),
            "calls": list(self.calls),
            "speaker_reconciliation": list(self.speaker_notes),
        }

    def transcribe(self, path: Path, language: str, *, diarize: bool) -> CloudTranscript:
        if not self._key:
            raise SpeechEngineError("OpenRouter API key is missing; set the shared provider key")
        if self._rate is None:
            self._rate = maximum_rate(self.config.model, self._transport)
        if diarize and self.config.model.startswith("openai/whisper"):
            raise SpeechEngineError(
                "Cloud Whisper needs one speaker or separate speaker tracks; choose "
                "Scribe/MAI for mixed-speaker diarization"
            )
        with wave.open(str(path), "rb") as source:
            rate, channels, width = (
                source.getframerate(),
                source.getnchannels(),
                source.getsampwidth(),
            )
            total = source.getnframes()
            chunks = plan_audio_chunks(
                total,
                rate=rate,
                frame_bytes=channels * width,
                seconds=self.config.chunk_seconds,
                diarize=diarize,
            )
            estimate = sum(
                (
                    (Decimal(chunk.end - chunk.start) / rate).to_integral_value(
                        rounding="ROUND_CEILING"
                    )
                    + 1
                )
                * self._rate
                * 2
                for chunk in chunks
            )
            if self._charged + estimate > Decimal(str(self.config.max_cost_usd)):
                raise SpeechEngineError(
                    "Cloud ASR cost estimate exceeds the remaining job budget; "
                    "no further audio was sent"
                )
            merger = MixedChunkMerger() if diarize else None
            aligned: list[AlignedSegment] = []
            turns: list[DiarizationTurn] = []
            detected = language
            language_seen: str | None = None
            for chunk_index, chunk in enumerate(chunks, 1):
                position = chunk.start
                check_cancellation(self._cancellation)
                source.setpos(position)
                data = source.readframes(chunk.end - chunk.start)
                buffer = io.BytesIO()
                with wave.open(buffer, "wb") as output:
                    output.setparams((channels, width, rate, 0, "NONE", "not compressed"))
                    output.writeframes(data)
                audio = buffer.getvalue()
                seconds = Decimal(len(data)) / channels / width / rate
                reserve = (seconds.to_integral_value(rounding="ROUND_CEILING") + 1) * self._rate * 2
                if self._charged + reserve > Decimal(str(self.config.max_cost_usd)):
                    raise SpeechEngineError(
                        "Cloud ASR job budget exhausted; no further audio was sent"
                    )
                payload: dict[str, Any] = {
                    "model": self.config.model,
                    "input_audio": {
                        "data": base64.b64encode(audio).decode("ascii"),
                        "format": "wav",
                    },
                    "response_format": "verbose_json",
                    "timestamp_granularities": ["segment", "word"],
                }
                if language != "auto":
                    payload["language"] = language
                if self.config.model == "elevenlabs/scribe-v2":
                    payload["provider"] = {
                        "options": {
                            "elevenlabs": {
                                "diarize": diarize,
                                "tag_audio_events": False,
                                "timestamps_granularity": "word",
                            }
                        }
                    }
                elif self.config.model == "microsoft/mai-transcribe-2":
                    payload["provider"] = {
                        "options": {
                            "azure": {
                                "diarization": {"enabled": diarize},
                                "enhancedMode": {"modelOptions": {"transcribeStyle": "verbatim"}},
                            }
                        }
                    }
                record = {
                    "audio_sha256": hashlib.sha256(audio).hexdigest(),
                    "seconds": float(seconds),
                    "offset_ms": round(Decimal(position) / rate * 1000),
                    "core_start_ms": round(Decimal(chunk.core_start) / rate * 1000),
                    "core_end_ms": round(Decimal(chunk.core_end) / rate * 1000),
                    "chunk_index": chunk_index,
                    "chunk_count": len(chunks),
                    "reserved_usd": str(reserve),
                    "reported_usd": None,
                    "status": "uncertain",
                }
                body = json.dumps(payload).encode()
                if len(body) > cloud_chunks.MAX_REQUEST_BYTES:
                    raise SpeechEngineError(
                        "Cloud ASR request exceeds the upload size limit; no audio was sent"
                    )
                record["request_bytes"] = len(body)
                self._charged += reserve
                self.calls.append(record)
                self._write_usage(path.parent)
                document = self._transport(
                    f"{BASE}/audio/transcriptions",
                    {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"},
                    body,
                    self.config.timeout_seconds,
                )
                usage = document.get("usage")
                cost = usage.get("cost") if isinstance(usage, dict) else None
                if cost is not None:
                    actual = _number(cost)
                    self._charged += actual - reserve
                    record["reported_usd"] = str(actual)
                record["status"] = "response-received"
                record["generation_id"] = document.get("_generation_id")
                self._write_usage(path.parent)
                if self._charged > Decimal(str(self.config.max_cost_usd)):
                    raise SpeechEngineError(
                        "OpenRouter reported charges above the job budget; "
                        "no further request will be made"
                    )
                parsed = parse_transcript(
                    document,
                    duration_ms=round(seconds * 1000),
                    offset_ms=round(Decimal(position) / rate * 1000),
                    language=language,
                )
                if diarize and len(parsed.diarization.turns) != sum(
                    len(x.words) for x in parsed.aligned.segments
                ):
                    raise SpeechEngineError(
                        "OpenRouter ASR omitted speaker labels; choose a diarization-capable "
                        "model or separate speaker tracks"
                    )
                if (
                    parsed.aligned.segments
                    and language_seen is not None
                    and language_seen != parsed.aligned.language
                ):
                    raise SpeechEngineError(
                        "Cloud ASR detected different languages across chunks; select the "
                        "recording language explicitly"
                    )
                if parsed.aligned.segments:
                    detected = parsed.aligned.language
                    language_seen = detected
                if merger is not None:
                    previous_notes = len(merger.notes)
                    merger.add(
                        parsed.aligned,
                        parsed.diarization,
                        core_start_ms=round(Decimal(chunk.core_start) / rate * 1000),
                        core_end_ms=round(Decimal(chunk.core_end) / rate * 1000),
                        final=chunk_index == len(chunks),
                        chunk_index=chunk_index,
                    )
                    self.speaker_notes.extend(merger.notes[previous_notes:])
                    record["speaker_mapping"] = dict(merger.mapping)
                    self._write_usage(path.parent)
                else:
                    aligned.extend(parsed.aligned.segments)
                    turns.extend(parsed.diarization.turns)
            if merger is not None:
                merged_segments, merged_turns = merger.result()
                aligned.extend(merged_segments)
                turns.extend(merged_turns)
        result = CloudTranscript(
            AlignedTranscript(language=detected, segments=tuple(aligned)),
            DiarizationResult(turns=tuple(turns)),
        )
        self._cache[path] = result
        return result

    def _write_usage(self, directory: Path) -> None:
        # Only the pipeline's managed workdir is used; no raw responses/audio/key in this ledger.
        path = directory / "cloud-asr-usage.json"
        path.write_text(json.dumps(self.provenance, ensure_ascii=False), encoding="utf-8")
        path.chmod(0o600)

    def cached(self, path: Path) -> CloudTranscript:
        if path not in self._cache:
            raise SpeechEngineError("Cloud ASR timing state is unavailable; restart this job")
        return self._cache[path]


class CloudAsr:
    def __init__(self, session: CloudSpeechSession, diarize: bool) -> None:
        self.session, self.diarize = session, diarize
        self._provenance: dict[str, Any] = {}
        self.warnings: tuple[CanonicalWarning, ...] = ()
        self.model_info = EngineModelInfo(role="asr", name=session.config.model)

    @property
    def provenance(self) -> dict[str, Any]:
        return self._provenance

    def transcribe(self, audio_path: Path, *, language: str, batch_size: int) -> TranscriptionDraft:
        first_call = len(self.session.calls)
        first_note = len(self.session.speaker_notes)
        result = self.session.transcribe(audio_path, language, diarize=self.diarize)
        calls = self.session.calls[first_call:]
        self.warnings = tuple(
            CanonicalWarning(
                code="CLOUD_SPEAKER_CONTINUITY_UNCERTAIN",
                severity="warning",
                stage="transcribe",
                message=(
                    "Speaker identities across cloud chunks require manual review; "
                    "unmatched labels were kept separate."
                ),
                context=note,
            )
            for note in self.session.speaker_notes[first_note:]
        )
        # A grouped result contains several transcription stages. Store each paid call
        # once, so summing stream charges does not double-count cumulative job snapshots.
        self._provenance = {
            **self.session.provenance,
            "accounting_scope": "stream",
            "calls": list(calls),
            "speaker_reconciliation": list(self.session.speaker_notes[first_note:]),
            "accounted_cost_usd": str(
                sum(
                    (
                        _number(
                            call["reported_usd"]
                            if call["reported_usd"] is not None
                            else call["reserved_usd"]
                        )
                        for call in calls
                    ),
                    Decimal(0),
                )
            ),
        }
        return TranscriptionDraft(
            language=result.aligned.language,
            segments=tuple(
                TranscriptionSegment(text=x.text, start_ms=x.start_ms, end_ms=x.end_ms)
                for x in result.aligned.segments
            ),
        )

    def close(self) -> None:
        pass


class CloudAlignment:
    def __init__(self, session: CloudSpeechSession) -> None:
        self.session = session
        self.model_info = EngineModelInfo(
            role="alignment", name=f"{session.config.model}:provider-word-timestamps"
        )

    def align(
        self, audio_path: Path, transcription: TranscriptionDraft, *, language: str
    ) -> AlignedTranscript:
        return self.session.cached(audio_path).aligned

    def close(self) -> None:
        pass


class CloudDiarization:
    def __init__(self, session: CloudSpeechSession) -> None:
        self.session = session
        self.model_info = EngineModelInfo(
            role="diarization", name=f"{session.config.model}:provider-speakers"
        )

    def diarize(self, audio_path: Path, *, speaker_count: int | None) -> DiarizationResult:
        return self.session.cached(audio_path).diarization

    def close(self) -> None:
        pass
