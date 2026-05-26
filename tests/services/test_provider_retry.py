from __future__ import annotations

import pytest

from multilang.services.provider_retry import (
    ProviderCircuitBreaker,
    ProviderCircuitOpenError,
    ProviderRetryContext,
    ProviderRetryError,
    classify_provider_error,
    retry_provider_call,
)


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


def test_retry_provider_call_uses_exponential_backoff_and_retry_after() -> None:
    calls = {"count": 0}
    sleeps: list[float] = []

    class RetryAfterError(RuntimeError):
        headers = {"Retry-After": "7"}

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("429 rate limit")
        if calls["count"] == 2:
            raise RetryAfterError("429 rate limit")
        return "ok"

    assert retry_provider_call(
        flaky,
        attempts=3,
        base_delay_seconds=2,
        max_delay_seconds=30,
        sleeper=sleeps.append,
    ) == "ok"

    assert sleeps == [2, 7]


def test_retry_provider_call_jitter_is_deterministic() -> None:
    sleeps: list[float] = []

    def always_rate_limited() -> None:
        raise RuntimeError("429")

    with pytest.raises(ProviderRetryError):
        retry_provider_call(
            always_rate_limited,
            attempts=2,
            base_delay_seconds=10,
            jitter_ratio=0.1,
            jitter=lambda: 1.0,
            sleeper=sleeps.append,
        )

    assert sleeps == [11.0]


def test_classification_marks_permanent_errors_non_retryable() -> None:
    assert classify_provider_error(ValueError("bad request")) == "permanent"
    assert classify_provider_error(RuntimeError("500 server error")) == "server_error"


def test_circuit_breaker_opens_half_opens_and_closes() -> None:
    clock = {"now": 0.0}
    breaker = ProviderCircuitBreaker(failure_threshold=1, cooldown_seconds=5)
    context = ProviderRetryContext(provider="litellm", model="m", operation="sentence")

    with pytest.raises(ProviderRetryError):
        retry_provider_call(
            lambda: (_ for _ in ()).throw(RuntimeError("429")),
            attempts=1,
            context=context,
            circuit_breaker=breaker,
            monotonic_clock=lambda: clock["now"],
        )
    assert breaker.state_for(context) == "open"

    with pytest.raises(ProviderCircuitOpenError):
        retry_provider_call(lambda: "blocked", context=context, circuit_breaker=breaker, monotonic_clock=lambda: clock["now"])

    clock["now"] = 6.0
    assert retry_provider_call(lambda: "ok", context=context, circuit_breaker=breaker, monotonic_clock=lambda: clock["now"]) == "ok"
    assert breaker.state_for(context) == "closed"
