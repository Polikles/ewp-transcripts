"""Explicitly consented automated-correction operation for the local GUI."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ewp_transcripts.application import CorrectionApplyOutcome, apply_correction
from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.correction_dictionary import load_project_correction_dictionary
from ewp_transcripts.correction_providers import create_correction_provider
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.web_workflows import require_completed_canonical_result


class GuiCorrectionError(ApplicationError):
    """Controlled GUI correction failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


PathResolver = Callable[..., Path]
CorrectionRunner = Callable[..., CorrectionApplyOutcome]
ProviderPreflight = Callable[[Any, ApplicationConfig, Mapping[str, str] | None], None]


class GuiCorrectionController:
    """Generate one non-final correction candidate without browser-held secrets."""

    def __init__(
        self,
        *,
        config: ApplicationConfig,
        resolve_path: PathResolver,
        runner: CorrectionRunner = apply_correction,
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
        """Check the exact configured backend and model without sending transcript text."""

        if provider_name not in {"lm-studio", "openrouter"}:
            raise GuiCorrectionError("GUI_CORRECTION_PROVIDER_INVALID", "Unknown provider")
        if not model.strip():
            raise GuiCorrectionError("GUI_CORRECTION_MODEL_REQUIRED", "Model is required")
        updates: dict[str, Any] = {
            "provider": provider_name,
            "model": model.strip(),
            "allow_remote_endpoint": allow_remote_endpoint,
        }
        if provider_name == "lm-studio":
            updates["endpoint"] = endpoint.strip()
        else:
            updates["openrouter_endpoint"] = endpoint.strip()
            updates["openrouter_reasoning_max_tokens"] = reasoning_max_tokens
        config = self._config.model_copy(
            update={"correction": self._config.correction.model_copy(update=updates)}
        )
        environment: Mapping[str, str] | None = None
        if provider_name == "openrouter" and api_key:
            environment = {config.correction.openrouter_api_key_env: api_key}
        provider = create_correction_provider(config, environment=environment)
        self._preflight(provider, config, environment)
        return {
            "status": "ok",
            "provider": provider.provider_id,
            "model": provider.model_id,
            "endpoint_kind": provider.endpoint_kind,
        }

    def model_pricing(
        self,
        *,
        endpoint: str,
        model_ids: list[str],
        api_key: str = "",
    ) -> dict[str, Any]:
        """Read current OpenRouter availability/pricing for a small explicit model set."""

        if not model_ids or len(model_ids) > 10 or any(not item.strip() for item in model_ids):
            raise GuiCorrectionError(
                "GUI_CORRECTION_MODEL_REQUIRED", "Select one to ten exact model IDs."
            )
        updates = {
            "provider": "openrouter",
            "model": model_ids[0],
            "openrouter_endpoint": endpoint.strip(),
        }
        config = self._config.model_copy(
            update={"correction": self._config.correction.model_copy(update=updates)}
        )
        environment = {config.correction.openrouter_api_key_env: api_key} if api_key else None
        provider = create_correction_provider(config, environment=environment)
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        document = _read_provider_document(
            f"{provider.endpoint_identity.rstrip('/')}/models", headers
        )
        records = {
            item.get("id"): item
            for item in document.get("data", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        items = []
        for model_id in model_ids:
            record = records.get(model_id)
            pricing = record.get("pricing", {}) if isinstance(record, dict) else {}
            items.append(
                {
                    "id": model_id,
                    "available": record is not None,
                    "name": record.get("name") if isinstance(record, dict) else None,
                    "input": _price_summary(pricing.get("prompt")),
                    "output": _price_summary(pricing.get("completion")),
                }
            )
        return {"provider": "openrouter", "items": items}

    def generate(
        self,
        *,
        result: str,
        output_directory: str,
        resume_directory: str,
        provider_name: str,
        model: str,
        endpoint: str,
        allow_remote_endpoint: bool,
        allow_cloud: bool,
        reasoning_max_tokens: int | None,
        dictionary_path: str,
        project_id: str,
        confirmed: bool,
        api_key: str = "",
    ) -> dict[str, Any]:
        if not confirmed:
            raise GuiCorrectionError(
                "GUI_CORRECTION_CONFIRMATION_REQUIRED",
                "Confirm provider disclosure and non-final candidate review requirements.",
            )
        if provider_name not in {"lm-studio", "openrouter"}:
            raise GuiCorrectionError("GUI_CORRECTION_PROVIDER_INVALID", "Unknown provider")
        if not model.strip():
            raise GuiCorrectionError("GUI_CORRECTION_MODEL_REQUIRED", "Model is required")
        if provider_name == "openrouter" and not allow_cloud:
            raise GuiCorrectionError(
                "GUI_CORRECTION_CLOUD_OPT_IN_REQUIRED",
                "OpenRouter requires explicit cloud opt-in.",
            )
        result_path = self._resolve_path(result)
        try:
            require_completed_canonical_result(result_path)
        except ValueError as error:
            raise GuiCorrectionError("GUI_CORRECTION_RESULT_INVALID", str(error)) from error
        output_path = self._resolve_path(output_directory, directory=True)
        resume_path = self._resolve_path(resume_directory, directory=True)
        dictionary = None
        dictionary_sha256 = None
        if project_id and not dictionary_path:
            raise GuiCorrectionError(
                "GUI_CORRECTION_DICTIONARY_INVALID",
                "A project ID cannot be selected without a dictionary.",
            )
        if dictionary_path:
            dictionary, dictionary_sha256 = load_project_correction_dictionary(
                self._resolve_path(dictionary_path)
            )
            if project_id and project_id != dictionary.project_id:
                raise GuiCorrectionError(
                    "GUI_CORRECTION_DICTIONARY_INVALID",
                    "The selected project ID does not match the dictionary.",
                )
            project_id = dictionary.project_id
        correction_updates: dict[str, Any] = {
            "provider": provider_name,
            "model": model.strip(),
            "allow_remote_endpoint": allow_remote_endpoint,
        }
        if provider_name == "lm-studio":
            correction_updates["endpoint"] = endpoint.strip()
        else:
            correction_updates["openrouter_endpoint"] = endpoint.strip()
            correction_updates["openrouter_reasoning_max_tokens"] = reasoning_max_tokens
        config = self._config.model_copy(
            update={
                "general": self._config.general.model_copy(
                    update={"offline": not allow_cloud, "interactive": False}
                ),
                "correction": self._config.correction.model_copy(update=correction_updates),
            }
        )
        environment: Mapping[str, str] | None = None
        if provider_name == "openrouter" and api_key:
            environment = {config.correction.openrouter_api_key_env: api_key}
        provider = create_correction_provider(config, environment=environment)
        self._preflight(provider, config, environment)
        if not self._lock.acquire(blocking=False):
            raise GuiCorrectionError(
                "GUI_CORRECTION_BUSY", "Another GUI correction is already running."
            )
        try:
            outcome = self._runner(
                result_path,
                config=config,
                provider=provider,
                consent_choice="accept_once",
                output_directory=output_path,
                resume_directory=resume_path,
                dictionary=dictionary,
                dictionary_sha256=dictionary_sha256,
                dictionary_project_id=project_id or None,
            )
        finally:
            self._lock.release()
        revision = outcome.revision
        return {
            "candidate_path": str(outcome.revision_path),
            "result_path": str(outcome.base_result_path),
            "job_id": revision.job_id,
            "revision_number": revision.revision_number,
            "provider": provider.provider_id,
            "model": provider.model_id,
            "endpoint_kind": provider.endpoint_kind,
            "statistics": revision.statistics.model_dump(mode="json"),
            "warnings": [warning.model_dump(mode="json") for warning in revision.warnings],
            "dictionary": (
                revision.provenance.llm.dictionary.model_dump(mode="json")
                if revision.provenance.llm and revision.provenance.llm.dictionary
                else None
            ),
            "final": False,
        }


def _preflight_provider(
    provider: Any,
    config: ApplicationConfig,
    environment: Mapping[str, str] | None = None,
) -> None:
    """Fail quickly when credentials, backend, or exact model are unavailable."""

    headers = {"Accept": "application/json"}
    if provider.provider_id == "openrouter":
        source = environment if environment is not None else os.environ
        key = source.get(config.correction.openrouter_api_key_env, "").strip()
        if not key:
            raise GuiCorrectionError(
                "GUI_CORRECTION_CREDENTIAL_MISSING",
                "Server environment variable "
                f"{config.correction.openrouter_api_key_env} is missing.",
            )
        headers["Authorization"] = f"Bearer {key}"
    if provider.provider_id == "openrouter":
        key_document = _read_provider_document(
            f"{provider.endpoint_identity.rstrip('/')}/key", headers
        )
        if not isinstance(key_document.get("data"), dict):
            raise GuiCorrectionError(
                "GUI_CORRECTION_CREDENTIAL_REJECTED",
                "Provider connection succeeded, but the API key response was invalid.",
            )
    document = _read_provider_document(f"{provider.endpoint_identity.rstrip('/')}/models", headers)
    models = document.get("data") if isinstance(document, dict) else None
    identifiers = {
        item.get("id") for item in models or () if isinstance(item, dict) and item.get("id")
    }
    if provider.model_id not in identifiers:
        raise GuiCorrectionError(
            "GUI_CORRECTION_MODEL_UNAVAILABLE",
            "The selected exact model is not available from the correction backend.",
        )


def _read_provider_document(url: str, headers: dict[str, str]) -> dict[str, Any]:
    """Read one bounded provider readiness document with specific connection errors."""

    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=3.0) as response:  # noqa: S310
            payload = response.read(1_048_577)
            if len(payload) > 1_048_576:
                raise ValueError("Provider model response is too large")
            document = json.loads(payload)
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            raise GuiCorrectionError(
                "GUI_CORRECTION_CREDENTIAL_REJECTED",
                f"Provider connection succeeded, but the API key was rejected (HTTP {error.code}).",
            ) from error
        raise GuiCorrectionError(
            "GUI_CORRECTION_BACKEND_REJECTED",
            f"Provider connection was rejected with HTTP status {error.code}.",
        ) from error
    except (OSError, ValueError, urllib.error.URLError) as error:
        raise GuiCorrectionError(
            "GUI_CORRECTION_BACKEND_UNAVAILABLE",
            "Correction backend did not pass the three-second readiness check.",
        ) from error
    if not isinstance(document, dict):
        raise GuiCorrectionError(
            "GUI_CORRECTION_BACKEND_UNAVAILABLE",
            "Correction backend returned an invalid readiness document.",
        )
    return document


def _price_summary(value: object) -> dict[str, object] | None:
    """Convert provider dollars/token into readable listed-price evidence."""

    try:
        price = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if price <= 0:
        return None
    return {
        "usd_per_million": float(price * Decimal(1_000_000)),
        "tokens_per_usd": int(Decimal(1) / price),
    }
