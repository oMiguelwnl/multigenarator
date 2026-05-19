from __future__ import annotations

import pytest

from multilang.services.provider_retry import ProviderRetryError, retry_provider_call


def test_retry_provider_call_recovers_from_temporary_error() -> None:
    calls = {"count": 0}

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("timeout api_key=secret raw prompt text")
        return "ok"

    assert retry_provider_call(flaky, wait_seconds=0) == "ok"
    assert calls["count"] == 2


def test_retry_provider_call_exhaustion_is_redacted() -> None:
    with pytest.raises(ProviderRetryError) as exc_info:
        retry_provider_call(lambda: (_ for _ in ()).throw(RuntimeError("429 api_key=secret sentence payload")), attempts=2)

    message = str(exc_info.value)
    assert "rate_limited" in message
    assert "secret" not in message
    assert "sentence payload" not in message
