"""Exact-scope consent for local and cloud automated translation APIs."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ewp_transcripts.correction_consent import ConsentChoice, correction_api_warning
from ewp_transcripts.domain.errors import TranslationProviderError
from ewp_transcripts.platform_runtime import private_descriptor_mode


class ConsentModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class TranslationConsentScope(ConsentModel):
    provider_id: str = Field(min_length=1)
    endpoint_kind: Literal["local", "cloud", "mock"]
    endpoint_identity: str = Field(min_length=1)
    operation_class: Literal["transcript_translation"] = "transcript_translation"
    warning_policy_version: Literal["translation-api-v1"] = "translation-api-v1"


class TranslationConsentRecord(ConsentModel):
    scope: TranslationConsentScope


class TranslationConsentDocument(ConsentModel):
    schema_version: Literal["1.0"] = "1.0"
    records: tuple[TranslationConsentRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class TranslationConsentDecision:
    authorized: bool
    persist_scope: TranslationConsentScope | None
    warning: str | None


def authorize_translation_api(
    scope: TranslationConsentScope,
    *,
    offline: bool,
    interactive: bool,
    choice: ConsentChoice | None,
    stored_records: tuple[TranslationConsentRecord, ...] = (),
) -> TranslationConsentDecision:
    if scope.endpoint_kind == "mock":
        return TranslationConsentDecision(True, None, None)
    warning = correction_api_warning(scope.endpoint_kind)
    assert warning is not None
    if offline and scope.endpoint_kind == "cloud":
        raise TranslationProviderError("Strict offline mode blocks cloud translation APIs")
    if any(record.scope == scope for record in stored_records):
        return TranslationConsentDecision(True, None, warning)
    if choice is None:
        mode = "interactive" if interactive else "non-interactive"
        raise TranslationProviderError(
            f"Translation API consent is required in {mode} mode before transcript transfer"
        )
    if choice == "reject":
        raise TranslationProviderError("Translation API use was rejected; no request was made")
    if choice == "accept_once":
        return TranslationConsentDecision(True, None, warning)
    return TranslationConsentDecision(True, scope, warning)


def load_translation_consents(path: Path) -> tuple[TranslationConsentRecord, ...]:
    if not path.exists():
        return ()
    try:
        document = TranslationConsentDocument.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise TranslationProviderError(
            f"Cannot read valid translation consent store: {path}"
        ) from error
    if len(document.records) != len(
        {record.scope.model_dump_json() for record in document.records}
    ):
        raise TranslationProviderError("Translation consent store contains duplicate scopes")
    return document.records


def persist_translation_consent(path: Path, scope: TranslationConsentScope) -> None:
    records = load_translation_consents(path)
    if any(record.scope == scope for record in records):
        return
    document = TranslationConsentDocument(records=(*records, TranslationConsentRecord(scope=scope)))
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".translation-consent-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        private_descriptor_mode(descriptor)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write((document.model_dump_json(indent=2) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)
