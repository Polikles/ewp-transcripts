"""Opt-in OS credentials; never select third-party/plaintext keyring backends."""

from __future__ import annotations

import importlib
import sys
import threading
from collections.abc import Callable
from typing import Protocol, cast

SERVICE = "ewp-transcripts"
ACCOUNT = "openrouter"


class SecureBackend(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...
    def set_password(self, service: str, username: str, password: str) -> None: ...
    def delete_password(self, service: str, username: str) -> None: ...


class CredentialStoreError(ValueError):
    """Sanitized storage failure; backend exceptions may contain secrets."""


def validate_api_key(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 512
        or any(character.isspace() for character in value)
    ):
        raise ValueError("Enter one non-empty API key without whitespace.")
    return value


def _secure_backend() -> SecureBackend:
    # Ignore arbitrary keyring configuration/plugins: only explicit OS stores qualify.
    module_name, class_name = (
        ("keyring.backends.Windows", "WinVaultKeyring")
        if sys.platform == "win32"
        else ("keyring.backends.SecretService", "Keyring")
    )
    backend = getattr(importlib.import_module(module_name), class_name)()
    if sys.platform == "win32":
        backend.persist = "local machine"
    else:
        backend.appid = SERVICE
    if backend.priority <= 0:
        raise CredentialStoreError("OS credential storage is unavailable; use a session-only key.")
    return cast(SecureBackend, backend)


class OSCredentialStore:
    """Access the same provider entry for all operations, only after an explicit action."""

    def __init__(self, factory: Callable[[], SecureBackend] = _secure_backend) -> None:
        self._factory = factory
        self._lock = threading.Lock()

    def available(self) -> bool:
        try:
            self._factory()
            return True
        except Exception:
            return False

    def perform(self, action: str, key: str = "") -> str:
        with self._lock:
            try:
                backend = self._factory()
                if action == "save":
                    backend.set_password(SERVICE, ACCOUNT, validate_api_key(key))
                    return key
                if action == "use":
                    stored = backend.get_password(SERVICE, ACCOUNT)
                    if stored is None:
                        raise CredentialStoreError("No OpenRouter key is saved in the OS store.")
                    return validate_api_key(stored)
                if action == "remove":
                    if backend.get_password(SERVICE, ACCOUNT) is not None:
                        backend.delete_password(SERVICE, ACCOUNT)
                    return ""
                raise CredentialStoreError("Unknown credential action.")
            except CredentialStoreError:
                raise
            except Exception:
                raise CredentialStoreError(
                    "OS credential storage is unavailable; use a session-only key."
                ) from None
