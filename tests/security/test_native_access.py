import importlib.util

import pytest
from pydantic import SecretStr

from multilang.settings import Settings


def test_native_flag_is_off_and_supports_both_names(monkeypatch):
    assert hasattr(Settings, "model_fields")
    assert "roadmap_4_enabled" in Settings.model_fields, "native flag missing"
    assert Settings(_env_file=None).roadmap_4_enabled is False
    monkeypatch.setenv("ROADMAP_4_ENABLED", "true")
    assert Settings(_env_file=None).roadmap_4_enabled is True


def test_role_comes_from_configured_credential_and_secret_stays_masked():
    assert importlib.util.find_spec("multilang.security.access") is not None, "native access policy missing"
    from multilang.security.access import AccessPolicy
    credentials = SecretStr('{"abc-long-secret-credential":{"subject":"alice","role":"User"}}')
    policy = AccessPolicy(credentials)
    principal = policy.authenticate("abc-long-secret-credential")
    assert principal.subject == "alice"
    assert policy.permits(principal, "read")
    assert not policy.permits(principal, "import")
    assert policy.authenticate("wrong") is None
    assert "abc-long-secret" not in repr(policy)


def test_client_cannot_select_an_unknown_role():
    assert importlib.util.find_spec("multilang.security.access") is not None, "native access policy missing"
    from multilang.security.access import AccessPolicy
    with pytest.raises(ValueError):
        AccessPolicy(SecretStr('{"key":{"subject":"alice","role":"Superuser"}}'))
