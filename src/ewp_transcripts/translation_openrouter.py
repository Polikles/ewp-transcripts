"""Explicit OpenRouter adapter for automated transcript translation."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Literal

from ewp_transcripts.domain.automated_translation import (
    AutomatedTranslationRequest,
    AutomatedTranslationResponse,
    AutomatedTranslationUsage,
)
from ewp_transcripts.domain.errors import (
    InvalidTranslationResponseError,
    PermanentTranslationHttpError,
    PermanentTranslationProviderError,
    RetryableTranslationProviderError,
)
from ewp_transcripts.openrouter_adapter import _normalized_endpoint
from ewp_transcripts.translation_lm_studio import (
    LmStudioTranslationConfig,
    _chat_request,
    _parse_chat_response,
)

JsonObject = dict[str, Any]
HttpTransport = Callable[[str, Mapping[str, str], bytes, float], JsonObject]
_REQUEST_CONTRACT = "single-owner-unit-v1"


@dataclass(frozen=True, slots=True)
class OpenRouterTranslationConfig:
    """Non-secret OpenRouter settings for one exact translation model."""

    model_id: str
    endpoint: str = "https://openrouter.ai/api/v1"
    api_key_env: str = "OPENROUTER_API_KEY"
    output_mode: Literal["json-schema", "json-text", "plain-text"] = "json-schema"
    temperature: float = 0.0
    reasoning_max_tokens: int | None = None

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("OpenRouter translation model_id must not be empty")
        if not 0 <= self.temperature <= 2:
            raise ValueError("OpenRouter translation temperature must be between 0 and 2")
        if self.output_mode not in {"json-schema", "json-text", "plain-text"}:
            raise ValueError("OpenRouter translation output_mode is invalid")
        if (
            not self.api_key_env
            or not self.api_key_env.replace("_", "A").isalnum()
            or self.api_key_env[0].isdigit()
        ):
            raise ValueError("OpenRouter api_key_env must be an environment-variable name")
        if self.reasoning_max_tokens is not None and self.reasoning_max_tokens < 0:
            raise ValueError("OpenRouter reasoning_max_tokens must not be negative")
        _normalized_endpoint(self.endpoint)


class OpenRouterTranslationProvider:
    """Cloud provider with explicit key lookup and no model fallback."""

    def __init__(
        self,
        config: OpenRouterTranslationConfig,
        *,
        transport: HttpTransport | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._config = config
        self._endpoint = _normalized_endpoint(config.endpoint)
        self._transport = transport or _urllib_transport
        self._environment = environment if environment is not None else os.environ

    @property
    def provider_id(self) -> str:
        return "openrouter"

    @property
    def model_id(self) -> str:
        return self._config.model_id

    @property
    def endpoint_kind(self) -> Literal["cloud"]:
        return "cloud"

    @property
    def endpoint_identity(self) -> str:
        return self._endpoint

    @property
    def provenance_parameters(self) -> dict[str, str | int | float | bool | None]:
        return {
            "temperature": self._config.temperature,
            "request_contract": _REQUEST_CONTRACT,
            "output_mode": self._config.output_mode,
            "require_parameters": True,
            "allow_fallbacks": False,
            "reasoning_max_tokens": self._config.reasoning_max_tokens,
        }

    def prompt_sha256(self, prompt_id: str) -> str:
        local = LmStudioTranslationConfig(
            model_id=self.model_id,
            output_mode=self._config.output_mode,
            temperature=self._config.temperature,
        )
        from ewp_transcripts.translation_lm_studio import LmStudioTranslationProvider

        base = LmStudioTranslationProvider(local).prompt_sha256(prompt_id)
        return hashlib.sha256(
            json.dumps(
                {"base_prompt_sha256": base, "provider_parameters": self.provenance_parameters},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

    def translate(
        self,
        request: AutomatedTranslationRequest,
        *,
        timeout_seconds: float | None = None,
    ) -> AutomatedTranslationResponse:
        if timeout_seconds is None or timeout_seconds <= 0:
            raise ValueError("OpenRouter translation calls require a positive timeout")
        api_key = self._environment.get(self._config.api_key_env, "").strip()
        if not api_key:
            raise PermanentTranslationProviderError(
                f"OpenRouter API key is missing; set {self._config.api_key_env}"
            )
        local = LmStudioTranslationConfig(
            model_id=self.model_id,
            output_mode=self._config.output_mode,
            temperature=self._config.temperature,
        )
        payload = _chat_request(local, request)
        payload["provider"] = {"require_parameters": True, "allow_fallbacks": False}
        if self._config.reasoning_max_tokens is not None:
            payload["reasoning"] = {"max_tokens": self._config.reasoning_max_tokens}
        document = self._transport(
            f"{self._endpoint}/chat/completions",
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(),
            timeout_seconds,
        )
        response = _parse_chat_response(
            document,
            request,
            output_mode=self._config.output_mode,
            provider_label="OpenRouter",
        )
        usage = document.get("usage")
        if not isinstance(usage, dict):
            return response
        return response.model_copy(
            update={
                "usage": AutomatedTranslationUsage(
                    input_tokens=_optional_nonnegative_int(usage.get("prompt_tokens")),
                    output_tokens=_optional_nonnegative_int(usage.get("completion_tokens")),
                    cost_usd_micros=_optional_cost_micros(usage.get("cost")),
                )
            }
        )


def _optional_nonnegative_int(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PermanentTranslationProviderError("OpenRouter returned invalid usage data")
    return value


def _optional_cost_micros(value: object) -> int | None:
    if value is None:
        return None
    try:
        cost = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise PermanentTranslationProviderError("OpenRouter returned invalid usage data") from error
    if not cost.is_finite() or cost < 0:
        raise PermanentTranslationProviderError("OpenRouter returned invalid usage data")
    return int((cost * Decimal(1_000_000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _urllib_transport(
    url: str,
    headers: Mapping[str, str],
    payload: bytes,
    timeout_seconds: float,
) -> JsonObject:
    request = urllib.request.Request(url, data=payload, headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            document = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code in {408, 409, 425, 429} or error.code >= 500:
            raise RetryableTranslationProviderError(
                "OpenRouter translation request failed"
            ) from None
        raise PermanentTranslationHttpError(error.code) from None
    except (TimeoutError, urllib.error.URLError):
        raise RetryableTranslationProviderError("OpenRouter is temporarily unavailable") from None
    except (UnicodeError, json.JSONDecodeError):
        raise InvalidTranslationResponseError(
            "OpenRouter returned an invalid translation response"
        ) from None
    if not isinstance(document, dict):
        raise InvalidTranslationResponseError("OpenRouter returned an invalid translation response")
    return document
