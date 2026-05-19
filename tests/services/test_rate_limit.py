"""Tests for deterministic provider rate limiting."""

from __future__ import annotations

from multilang.services.rate_limit import SimpleRateLimiter


def test_simple_rate_limiter_spaces_calls_after_first_immediate_call() -> None:
    now = 100.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    def sleeper(seconds: float) -> None:
        nonlocal now
        sleeps.append(seconds)
        now += seconds

    limiter = SimpleRateLimiter(calls_per_minute=30, clock=clock, sleeper=sleeper)

    limiter.wait()
    limiter.wait()
    limiter.wait()

    assert sleeps == [2.0, 2.0]
