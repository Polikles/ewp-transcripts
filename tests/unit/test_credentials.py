"""Shared OS entries, explicit access, safe fallback and backend error redaction."""

from unittest.mock import Mock

import pytest

from ewp_transcripts.credentials import ACCOUNT, SERVICE, CredentialStoreError, OSCredentialStore


def test_one_os_entry_is_reused_across_server_lifetimes_and_can_be_removed():
    backend = Mock()
    values = {}
    backend.set_password.side_effect = lambda service, user, key: values.update(
        {(service, user): key}
    )
    backend.get_password.side_effect = lambda service, user: values.get((service, user))
    backend.delete_password.side_effect = lambda service, user: values.pop((service, user))
    factory = Mock(return_value=backend)
    first = OSCredentialStore(factory)
    factory.assert_not_called()  # No discovery/read/unlock merely from GUI startup.
    assert first.perform("save", "synthetic-key") == "synthetic-key"
    second = OSCredentialStore(factory)
    assert second.perform("use") == "synthetic-key"
    assert list(values) == [(SERVICE, ACCOUNT)]
    assert second.perform("remove") == ""
    assert not values
    with pytest.raises(CredentialStoreError, match="No OpenRouter key"):
        second.perform("use")


def test_backend_failure_never_echoes_key_and_has_session_fallback():
    backend = Mock()
    backend.set_password.side_effect = RuntimeError("failed secret-value-do-not-log")
    store = OSCredentialStore(lambda: backend)
    with pytest.raises(CredentialStoreError) as error:
        store.perform("save", "secret-value-do-not-log")
    assert "secret-value-do-not-log" not in str(error.value)
    assert "session-only" in str(error.value)
    unavailable = OSCredentialStore(Mock(side_effect=RuntimeError("offline")))
    assert not unavailable.available()
