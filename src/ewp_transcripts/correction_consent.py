"""Scoped privacy consent policy for local and cloud correction APIs."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from ewp_transcripts.domain.errors import CorrectionConsentError
from ewp_transcripts.platform_runtime import private_descriptor_mode

ConsentChoice = Literal["reject", "accept_once", "accept_persistently"]
EndpointKind = Literal["local", "cloud", "mock"]
WARNING_POLICY_VERSION: Literal["correction-api-v1"] = "correction-api-v1"

LOCAL_API_WARNING = (
    "Transcript text will be sent to a separate local API process. EWP Transcriber "
    "cannot guarantee what that process logs, retains, or forwards."
)
REMOTE_LOCAL_API_WARNING = (
    "Transcript text will be sent over the network to a separately operated API endpoint. "
    "EWP Transcriber cannot guarantee transport confidentiality or what that server logs, "
    "retains, or forwards."
)
CLOUD_API_WARNING = (
    "Transcript text will leave this machine and be sent to a cloud API provider. "
    "This operation is not offline and may be subject to provider retention policies."
)


class ConsentModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class CorrectionConsentScope(ConsentModel):
    provider_id: str = Field(min_length=1)
    endpoint_kind: EndpointKind
    endpoint_identity: str = Field(min_length=1)
    operation_class: Literal["transcript_correction"] = "transcript_correction"
    warning_policy_version: Literal["correction-api-v1"] = WARNING_POLICY_VERSION


class CorrectionConsentRecord(ConsentModel):
    scope: CorrectionConsentScope


class CorrectionConsentDocument(ConsentModel):
    schema_version: Literal["1.0"] = "1.0"
    records: tuple[CorrectionConsentRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class ConsentDecision:
    authorized: bool
    persist_scope: CorrectionConsentScope | None
    warning: str | None


def correction_api_warning(endpoint_kind: EndpointKind) -> str | None:
    if endpoint_kind == "local":
        return LOCAL_API_WARNING
    if endpoint_kind == "cloud":
        return CLOUD_API_WARNING
    return None


def correction_scope_warning(scope: CorrectionConsentScope) -> str | None:
    warning = correction_api_warning(scope.endpoint_kind)
    if (
        warning is not None
        and scope.endpoint_kind == "local"
        and urlsplit(scope.endpoint_identity).hostname not in {"127.0.0.1", "localhost", "::1"}
    ):
        return f"{warning} {REMOTE_LOCAL_API_WARNING}"
    return warning


def authorize_correction_api(
    scope: CorrectionConsentScope,
    *,
    offline: bool,
    interactive: bool,
    choice: ConsentChoice | None,
    stored_records: tuple[CorrectionConsentRecord, ...] = (),
) -> ConsentDecision:
    """Authorize only explicit or exact persisted consent before request serialization."""

    if scope.endpoint_kind == "mock":
        return ConsentDecision(True, None, None)
    warning = correction_scope_warning(scope)
    assert warning is not None
    if offline and scope.endpoint_kind == "cloud":
        raise CorrectionConsentError("Strict offline mode blocks cloud correction APIs")
    if any(record.scope == scope for record in stored_records):
        return ConsentDecision(True, None, warning)
    if choice is None:
        mode = "interactive" if interactive else "non-interactive"
        raise CorrectionConsentError(
            f"Correction API consent is required in {mode} mode before transcript transfer"
        )
    if choice == "reject":
        raise CorrectionConsentError("Correction API use was rejected; no request was made")
    if choice == "accept_once":
        return ConsentDecision(True, None, warning)
    return ConsentDecision(True, scope, warning)


def load_correction_consents(path: Path) -> tuple[CorrectionConsentRecord, ...]:
    """Load a strict consent file; a missing file means no persisted consent."""

    if not path.exists():
        return ()
    try:
        document = CorrectionConsentDocument.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise CorrectionConsentError(
            f"Cannot read valid correction consent store: {path}"
        ) from error
    scopes = [record.scope.model_dump_json() for record in document.records]
    if len(scopes) != len(set(scopes)):
        raise CorrectionConsentError("Correction consent store contains duplicate scopes")
    return document.records


def persist_correction_consent(path: Path, scope: CorrectionConsentScope) -> None:
    """Atomically add one exact non-secret scope with private filesystem permissions."""

    records = load_correction_consents(path)
    if any(record.scope == scope for record in records):
        return
    document = CorrectionConsentDocument(records=(*records, CorrectionConsentRecord(scope=scope)))
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    payload = (document.model_dump_json(indent=2) + "\n").encode()
    descriptor, temporary_name = tempfile.mkstemp(prefix=".consent-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        private_descriptor_mode(descriptor)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)
