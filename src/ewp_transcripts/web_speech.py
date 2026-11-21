"""Explicit read-only OpenRouter ASR checks, duration prices and local workload estimates."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from ewp_transcripts.config import SpeechConfig
from ewp_transcripts.domain.errors import SpeechEngineError
from ewp_transcripts.engines.cloud_chunks import plan_audio_chunks
from ewp_transcripts.engines.openrouter import BASE, HttpCall, _number, request_json
from ewp_transcripts.web_inputs import GuiInputs

ASR_MODELS = (
    "openai/whisper-large-v3",
    "openai/whisper-large-v3-turbo",
    "elevenlabs/scribe-v2",
    "microsoft/mai-transcribe-2",
)


class GuiSpeechController:
    def __init__(self, inputs: GuiInputs, transport: HttpCall | None = None) -> None:
        self.inputs, self.transport = inputs, transport or request_json

    def check_key(self, api_key: str) -> dict[str, Any]:
        if not api_key:
            raise ValueError("Set the shared OpenRouter key before checking the connection")
        document = self.transport(f"{BASE}/key", {"Authorization": f"Bearer {api_key}"}, None, 15)
        if not isinstance(document.get("data"), dict):
            raise ValueError("OpenRouter key check returned an invalid response")
        return {"status": "ok", "provider": "openrouter"}

    def _durations(self, items: object) -> tuple[float, float, float, int]:
        if not isinstance(items, list) or len(items) > 50:
            raise ValueError("ASR estimate expects up to 50 recordings")
        media_seconds = minimum_billable = maximum_billable = 0.0
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("ASR estimate recording is invalid")
            paths = item.get("group_paths") or [item.get("path", "")]
            if (
                not isinstance(paths, list)
                or not 1 <= len(paths) <= 6
                or not all(isinstance(path, str) and path.strip() for path in paths)
                or len(set(paths)) != len(paths)
            ):
                raise ValueError("ASR estimate sources are invalid")
            choices = item.get("selected_streams", {})
            if not isinstance(choices, dict) or set(choices) - set(paths):
                raise ValueError("ASR estimate stream selection is invalid")
            for path in paths:
                source = self.inputs.probe(path)
                streams = source["streams"]
                choice = choices.get(path)
                if choice is not None and type(choice) is not int:
                    raise ValueError("ASR estimate stream selection is invalid")
                selected = (
                    next((x for x in streams if x["index"] == choice), None)
                    if choice is not None
                    else streams[0]
                    if len(streams) == 1
                    else None
                )
                if selected is None:
                    raise ValueError("Choose an audio stream before estimating cloud ASR")
                duration = source["duration_ms"]
                if not isinstance(duration, (float, int)) or duration <= 0:
                    raise ValueError("Recording duration is unavailable for the ASR estimate")
                media_seconds += duration / 1000
                mixed = len(paths) == 1 and item.get("speaker_count", "auto") != 1
                parts = plan_audio_chunks(
                    round(duration * 16),
                    rate=16000,
                    frame_bytes=2,
                    seconds=SpeechConfig().chunk_seconds,
                    diarize=mixed,
                )
                billable = sum((part.end - part.start + 15999) // 16000 + 1 for part in parts)
                minimum_billable += billable
                # Before channel analysis, stereo can become two independent speaker streams.
                # Show a range rather than imply a guaranteed price for that unresolved mode.
                maximum_billable += billable * (2 if selected.get("channels") == 2 else 1)
        return media_seconds, minimum_billable, maximum_billable, len(items)

    def _price(self, model: str, available: set[str]) -> dict[str, Any]:
        if model not in available:
            return {"id": model, "available": False, "status": "unavailable"}
        try:
            document = self.transport(f"{BASE}/models/{model}/endpoints", {}, None, 15)
            endpoints = document.get("data", {}).get("endpoints")
            if not isinstance(endpoints, list) or not endpoints:
                raise ValueError("No current endpoint prices")
            rates = [_number(endpoint["pricing"]["prompt"]) for endpoint in endpoints]
            divisor = 3600 if model == "microsoft/mai-transcribe-2" else 1
            low, high = min(rates) / divisor, max(rates) / divisor
            return {
                "id": model,
                "available": True,
                "status": "ok",
                "minimum_usd_per_hour": str(low * 3600),
                "maximum_usd_per_hour": str(high * 3600),
                "_low": low,
                "_high": high,
            }
        except (SpeechEngineError, ValueError, TypeError, KeyError, AttributeError):
            return {"id": model, "available": True, "status": "price-unavailable"}

    def refresh(self, items: object) -> dict[str, Any]:
        seconds, minimum, maximum, count = self._durations(items)
        catalog = self.transport(f"{BASE}/models?output_modalities=transcription", {}, None, 15)
        if not isinstance(catalog.get("data"), list):
            raise ValueError("OpenRouter model list is unavailable")
        available = {
            item["id"]
            for item in catalog["data"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        with ThreadPoolExecutor(max_workers=4) as executor:
            models = list(executor.map(lambda model: self._price(model, available), ASR_MODELS))
        for model in models:
            if model["status"] == "ok":
                model["estimated_minimum_usd"] = str(Decimal(str(minimum)) * model.pop("_low"))
                model["estimated_maximum_usd"] = str(Decimal(str(maximum)) * model.pop("_high"))
        return {
            "refreshed_at": datetime.now(UTC).isoformat(),
            "recordings": count,
            "audio_seconds": seconds,
            "billable_seconds_minimum": minimum,
            "billable_seconds_maximum": maximum,
            "models": models,
        }
