"""Simple deterministic rate limiting for provider calls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic, sleep
from typing import Protocol


class RateLimiter(Protocol):
    def wait(self) -> None: ...


@dataclass(slots=True)
class SimpleRateLimiter:
    calls_per_minute: int
    clock: Callable[[], float] = monotonic
    sleeper: Callable[[float], None] = sleep
    _next_allowed_at: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.calls_per_minute < 1:
            raise ValueError("calls_per_minute must be greater than or equal to 1")

    @property
    def interval_seconds(self) -> float:
        return 60.0 / self.calls_per_minute

    def wait(self) -> None:
        now = self.clock()
        if self._next_allowed_at is not None and now < self._next_allowed_at:
            self.sleeper(self._next_allowed_at - now)
            now = self.clock()
        self._next_allowed_at = now + self.interval_seconds


__all__ = ["RateLimiter", "SimpleRateLimiter"]
