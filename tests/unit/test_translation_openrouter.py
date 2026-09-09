"""Network-isolated OpenRouter translation adapter tests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from ewp_transcripts.automated_translation import build_automated_translation_request
from ewp_transcripts.domain.errors import PermanentTranslationProviderError
from ewp_transcripts.translation_openrouter import (
    OpenRouterTranslationConfig,
    OpenRouterTranslationProvider,
)
from ewp_transcripts.translation_review_service import prepare_translation_review

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/results.example.json"


def _request(provider: OpenRouterTranslationProvider):
    review = prepare_translation_review(EXAMPLE, target_language="pl")
    return build_automated_translation_request(review, 0, provider=provider)


def test_adapter_sends_bearer_request_and_records_provider_parameters() -> None:
    captured: dict[str, Any] = {}

    def transport(
        url: str, headers: Mapping[str, str], payload: bytes, timeout: float
    ) -> dict[str, Any]:
        captured.update(
            url=url, headers=dict(headers), payload=json.loads(payload), timeout=timeout
        )
        return {
            "choices": [{"message": {"content": '{"target_text":"Witamy."}'}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 2, "cost": "0.0001234"},
        }

    provider = OpenRouterTranslationProvider(
        OpenRouterTranslationConfig(model_id="google/gemini-2.5-flash", reasoning_max_tokens=0),
        transport=transport,
        environment={"OPENROUTER_API_KEY": "private-key"},
    )

    response = provider.translate(_request(provider), timeout_seconds=12)

    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer private-key"
    assert captured["payload"]["provider"] == {
        "require_parameters": True,
        "allow_fallbacks": False,
    }
    assert captured["payload"]["reasoning"] == {"max_tokens": 0}
    assert response.target_text == "Witamy."
    assert response.usage is not None
    assert response.usage.cost_usd_micros == 123
    assert provider.provenance_parameters["request_contract"] == "single-owner-unit-v1"


def test_missing_key_fails_without_provider_request() -> None:
    called = False

    def transport(*args: object) -> dict[str, Any]:
        nonlocal called
        called = True
        return {}

    provider = OpenRouterTranslationProvider(
        OpenRouterTranslationConfig(model_id="model"), transport=transport, environment={}
    )

    with pytest.raises(PermanentTranslationProviderError, match="OPENROUTER_API_KEY"):
        provider.translate(_request(provider), timeout_seconds=2)
    assert not called


def test_adapter_rejects_unsafe_endpoint() -> None:
    with pytest.raises(ValueError, match="OpenRouter endpoint"):
        OpenRouterTranslationConfig(model_id="model", endpoint="http://openrouter.ai/api/v1")
