"""Automated translation candidate generation for the local GUI."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Literal, cast

from ewp_transcripts.application import AutomatedTranslationOutcome, apply_automated_translation
from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.automated_translation import AutomatedTranslationProvider
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.translation import Language, TranslationStyle
from ewp_transcripts.translation_dictionary import load_project_translation_dictionary
from ewp_transcripts.translation_lm_studio import (
    LmStudioTranslationConfig,
    LmStudioTranslationProvider,
)
from ewp_transcripts.translation_openrouter import (
    OpenRouterTranslationConfig,
    OpenRouterTranslationProvider,
)
from ewp_transcripts.web_workflows import require_completed_canonical_result


class GuiTranslationError(ApplicationError):
    """Controlled browser translation failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


PathResolver = Callable[..., Path]
TranslationRunner = Callable[..., AutomatedTranslationOutcome]
ProviderPreflight = Callable[[Any, Mapping[str, str] | None], None]


class GuiTranslationController:
    """Create one immutable, explicitly non-final local or cloud translation candidate."""

    def __init__(
        self,
        *,
        config: ApplicationConfig,
        resolve_path: PathResolver,
        runner: TranslationRunner = apply_automated_translation,
        preflight: ProviderPreflight | None = None,
        operation_lock: threading.Lock | None = None,
    ) -> None:
        self._config = config
        self._resolve_path = resolve_path
        self._runner = runner
        self._preflight = preflight or _preflight_provider
        self._lock = operation_lock or threading.Lock()

    def check_provider(
        self,
        *,
        provider_name: str,
        model: str,
        endpoint: str,
        allow_remote_endpoint: bool,
        reasoning_max_tokens: int | None,
        api_key: str = "",
    ) -> dict[str, Any]:
        """Check one exact translation backend without transferring transcript text."""

        provider, environment = self._create_provider(
            provider_name=provider_name,
            model=model,
            endpoint=endpoint,
            allow_remote_endpoint=allow_remote_endpoint,
            reasoning_max_tokens=reasoning_max_tokens,
            output_mode="json-schema",
            api_key=api_key,
        )
        self._preflight(provider, environment)
        return {
            "status": "ok",
            "provider": provider.provider_id,
            "model": provider.model_id,
            "endpoint_kind": provider.endpoint_kind,
        }

    def generate(
        self,
        *,
        result: str,
        source_revision: str,
        output_directory: str,
        resume_directory: str,
        target_language: str,
        provider_name: str,
        model: str,
        endpoint: str,
        allow_remote_endpoint: bool,
        allow_cloud: bool,
        reasoning_max_tokens: int | None,
        output_mode: str,
        dictionary_path: str,
        confirmed: bool,
        api_key: str = "",
    ) -> dict[str, Any]:
        if not confirmed:
            raise GuiTranslationError(
                "GUI_TRANSLATION_CONFIRMATION_REQUIRED",
                "Confirm API disclosure and non-final translation review requirements.",
            )
        if target_language not in {"pl", "en"}:
            raise GuiTranslationError(
                "GUI_TRANSLATION_LANGUAGE_INVALID", "Target language must be pl or en."
            )
        if provider_name == "openrouter" and not allow_cloud:
            raise GuiTranslationError(
                "GUI_TRANSLATION_CLOUD_OPT_IN_REQUIRED",
                "OpenRouter requires explicit cloud opt-in.",
            )
        if output_mode not in {"json-schema", "json-text", "plain-text"}:
            raise GuiTranslationError(
                "GUI_TRANSLATION_OUTPUT_MODE_INVALID", "Unknown translation output mode."
            )
        result_path = self._resolve_path(result)
        try:
            require_completed_canonical_result(result_path)
        except ValueError as error:
            raise GuiTranslationError("GUI_TRANSLATION_RESULT_INVALID", str(error)) from error
        revision_path = self._resolve_path(source_revision) if source_revision else None
        output_path = self._resolve_path(output_directory, directory=True)
        resume_path = self._resolve_path(resume_directory, directory=True)
        dictionary = None
        dictionary_sha256 = None
        if dictionary_path:
            dictionary, dictionary_sha256 = load_project_translation_dictionary(
                self._resolve_path(dictionary_path)
            )
        provider, environment = self._create_provider(
            provider_name=provider_name,
            model=model,
            endpoint=endpoint,
            allow_remote_endpoint=allow_remote_endpoint,
            reasoning_max_tokens=reasoning_max_tokens,
            output_mode=output_mode,
            api_key=api_key,
        )
        self._preflight(provider, environment)
        execution_config = self._config.model_copy(
            update={
                "general": self._config.general.model_copy(
                    update={"offline": not allow_cloud, "interactive": False}
                )
            }
        )
        if not self._lock.acquire(blocking=False):
            raise GuiTranslationError(
                "GUI_TRANSLATION_BUSY", "Another GUI translation is already running."
            )
        try:
            outcome = self._runner(
                result_path,
                config=execution_config,
                provider=provider,
                target_language=cast(Language, target_language),
                revision_path=revision_path,
                style=TranslationStyle(register="preserve", discourse="preserve"),
                resume_directory=resume_path,
                output_directory=output_path,
                consent_choice="accept_once",
                context_units=0,
                dictionary=dictionary,
                dictionary_sha256=dictionary_sha256,
            )
        finally:
            self._lock.release()
        translation = outcome.translation
        if outcome.translation_path is None:
            raise GuiTranslationError(
                "GUI_TRANSLATION_REQUEST_INVALID",
                "Translation candidate was not published.",
            )
        llm = translation.provenance.llm
        assert llm is not None
        return {
            "candidate_path": str(outcome.translation_path),
            "result_path": str(outcome.result_path),
            "job_id": translation.job_id,
            "translation_number": translation.translation_number,
            "direction": translation.direction.model_dump(mode="json"),
            "source_verification": translation.source.verification,
            "provider": llm.provider,
            "model": llm.model,
            "statistics": translation.statistics.model_dump(mode="json"),
            "warnings": [warning.model_dump(mode="json") for warning in translation.warnings],
            "dictionary": (
                translation.dictionary.model_dump(mode="json")
                if translation.dictionary is not None
                else None
            ),
            "final": False,
        }

    @staticmethod
    def _create_provider(
        *,
        provider_name: str,
        model: str,
        endpoint: str,
        allow_remote_endpoint: bool,
        reasoning_max_tokens: int | None,
        output_mode: str,
        api_key: str,
    ) -> tuple[AutomatedTranslationProvider, Mapping[str, str] | None]:
        if provider_name not in {"lm-studio", "openrouter"}:
            raise GuiTranslationError(
                "GUI_TRANSLATION_PROVIDER_INVALID", "Unknown translation provider."
            )
        if not model.strip():
            raise GuiTranslationError("GUI_TRANSLATION_MODEL_REQUIRED", "Model is required.")
        if reasoning_max_tokens is not None and (
            isinstance(reasoning_max_tokens, bool) or reasoning_max_tokens < 0
        ):
            raise GuiTranslationError(
                "GUI_TRANSLATION_REASONING_INVALID",
                "Reasoning-token budget must be a non-negative integer.",
            )
        normalized_mode = cast(Literal["json-schema", "json-text", "plain-text"], output_mode)
        if provider_name == "lm-studio":
            return (
                LmStudioTranslationProvider(
                    LmStudioTranslationConfig(
                        model_id=model.strip(),
                        endpoint=endpoint.strip(),
                        allow_remote_endpoint=allow_remote_endpoint,
                        output_mode=normalized_mode,
                        temperature=0.0,
                    )
                ),
                None,
            )
        environment = {"OPENROUTER_API_KEY": api_key} if api_key else None
        return (
            OpenRouterTranslationProvider(
                OpenRouterTranslationConfig(
                    model_id=model.strip(),
                    endpoint=endpoint.strip(),
                    output_mode=normalized_mode,
                    temperature=0.0,
                    reasoning_max_tokens=reasoning_max_tokens,
                ),
                environment=environment,
            ),
            environment,
        )


def _preflight_provider(provider: Any, environment: Mapping[str, str] | None = None) -> None:
    """Fail before source transfer unless the selected backend and model are usable."""

    if isinstance(provider, LmStudioTranslationProvider):
        provider.preflight(timeout_seconds=3.0)
        return
    source = environment if environment is not None else os.environ
    key = source.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise GuiTranslationError(
            "GUI_TRANSLATION_CREDENTIAL_MISSING",
            "OpenRouter API key is missing for this active GUI server process.",
        )
    headers = {"Accept": "application/json", "Authorization": f"Bearer {key}"}
    key_document = _read_provider_document(f"{provider.endpoint_identity}/key", headers)
    if not isinstance(key_document.get("data"), dict):
        raise GuiTranslationError(
            "GUI_TRANSLATION_CREDENTIAL_REJECTED",
            "Provider connection succeeded, but the API key response was invalid.",
        )
    document = _read_provider_document(f"{provider.endpoint_identity}/models", headers)
    models = document.get("data") if isinstance(document, dict) else None
    identifiers = {
        item.get("id") for item in models or () if isinstance(item, dict) and item.get("id")
    }
    if provider.model_id not in identifiers:
        raise GuiTranslationError(
            "GUI_TRANSLATION_MODEL_UNAVAILABLE",
            "The selected exact model is not available from the translation backend.",
        )


def _read_provider_document(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=3.0) as response:  # noqa: S310
            payload = response.read(1_048_577)
            if len(payload) > 1_048_576:
                raise ValueError("Provider readiness response is too large")
            document = json.loads(payload)
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            raise GuiTranslationError(
                "GUI_TRANSLATION_CREDENTIAL_REJECTED",
                f"Provider connection succeeded, but the API key was rejected (HTTP {error.code}).",
            ) from error
        raise GuiTranslationError(
            "GUI_TRANSLATION_BACKEND_REJECTED",
            f"Translation backend rejected the readiness check (HTTP {error.code}).",
        ) from error
    except (OSError, ValueError, urllib.error.URLError) as error:
        raise GuiTranslationError(
            "GUI_TRANSLATION_BACKEND_UNAVAILABLE",
            "Translation backend did not pass the three-second readiness check.",
        ) from error
    if not isinstance(document, dict):
        raise GuiTranslationError(
            "GUI_TRANSLATION_BACKEND_UNAVAILABLE",
            "Translation backend returned an invalid readiness document.",
        )
    return document
