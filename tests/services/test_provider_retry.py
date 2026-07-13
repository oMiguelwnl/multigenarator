from __future__ import annotations

import pytest

from multilang.services.provider_retry import (
    ProviderCircuitBreaker,
    ProviderCircuitOpenError,
    ProviderRetryContext,
    ProviderRetryError,
    classify_provider_error,
    is_temporary_provider_error,
    retry_provider_call,
)


def test_retry_provider_call_recovers_from_temporary_error() -> None:
    calls = {"count": 0}
    success_attempts: list[int] = []

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("timeout api_key=secret raw prompt text")
        return "ok"

    assert retry_provider_call(flaky, wait_seconds=0, success_attempt_callback=success_attempts.append) == "ok"
    assert calls["count"] == 2
    assert success_attempts == [2]


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


def test_quota_exhaustion_is_not_retried() -> None:
    # Exhausted quota/credits will not recover within the retry window, so it
    # must be treated as non-retryable even though it has its own classification.
    quota_error = RuntimeError("insufficient credits")
    assert classify_provider_error(quota_error) == "quota_exceeded"
    assert is_temporary_provider_error(quota_error) is False

    calls = {"count": 0}
    sleeps: list[float] = []

    def exhausted() -> None:
        calls["count"] += 1
        raise RuntimeError("quota exceeded")

    with pytest.raises(RuntimeError, match="quota exceeded"):
        retry_provider_call(
            exhausted,
            attempts=3,
            base_delay_seconds=1,
            sleeper=sleeps.append,
        )

    # Raised immediately on the first attempt with no backoff sleeps.
    assert calls["count"] == 1
    assert sleeps == []


def test_transient_forbidden_remains_retryable() -> None:
    # Some providers surface throttling as 403; keep it retryable.
    assert is_temporary_provider_error(RuntimeError("403 forbidden")) is True


def test_circuit_breaker_opens_half_opens_and_closes() -> None:
    clock = {"now": 0.0}
    breaker = ProviderCircuitBreaker(failure_threshold=1, cooldown_seconds=5)
    context = ProviderRetryContext(provider="litellm", model="m", operation="sentence")

    with pytest.raises(ProviderCircuitOpenError):
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


def test_retry_provider_call_stops_when_circuit_opens_before_attempts_exhaust() -> None:
    calls = {"count": 0}
    sleeps: list[float] = []
    breaker = ProviderCircuitBreaker(failure_threshold=1, cooldown_seconds=60)
    context = ProviderRetryContext(provider="openrouter", model="blocked", operation="sentence")

    def blocked() -> None:
        calls["count"] += 1
        raise RuntimeError("403 forbidden")

    with pytest.raises(ProviderCircuitOpenError):
        retry_provider_call(
            blocked,
            attempts=3,
            base_delay_seconds=1,
            sleeper=sleeps.append,
            context=context,
            circuit_breaker=breaker,
            monotonic_clock=lambda: 0.0,
        )

    assert calls["count"] == 1
    assert sleeps == []
    assert breaker.state_for(context) == "open"
