"""Small deterministic retry boundary for temporary provider failures."""

from __future__ import annotations

from collections.abc import Callable
from time import sleep
from typing import TypeVar

from multilang.security.redaction import redact_sensitive_text

T = TypeVar("T")

DEFAULT_PROVIDER_RETRY_ATTEMPTS = 3


class ProviderRetryError(RuntimeError):
    """Raised after temporary provider failures exhaust retry attempts."""

    def __init__(self, message: str, *, attempts: int) -> None:
        super().__init__(message)
        self.attempts = attempts


def is_temporary_provider_error(exc: BaseException) -> bool:
    text = f"{type(exc).__name__} {exc}".casefold()
    return any(marker in text for marker in ("temporary 403", " 403", "429", "timeout", "timed out", "network"))


def safe_provider_error_summary(exc: BaseException) -> str:
    text = redact_sensitive_text(str(exc) or type(exc).__name__)
    lowered = text.casefold()
    if "429" in lowered:
        kind = "rate_limited"
    elif "403" in lowered:
        kind = "temporary_forbidden"
    elif "timeout" in lowered or "timed out" in lowered:
        kind = "timeout"
    elif "network" in lowered:
        kind = "network_error"
    else:
        kind = "temporary_provider_error"
    return f"{kind}: provider call failed with redacted temporary error"


def retry_provider_call(
    operation: Callable[[], T],
    *,
    attempts: int = DEFAULT_PROVIDER_RETRY_ATTEMPTS,
    wait_seconds: float = 0.0,
    sleeper: Callable[[float], None] = sleep,
) -> T:
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - provider adapters expose heterogeneous errors.
            if not is_temporary_provider_error(exc):
                raise
            last_error = exc
            if attempt < attempts and wait_seconds > 0:
                sleeper(wait_seconds)
    assert last_error is not None
    raise ProviderRetryError(safe_provider_error_summary(last_error), attempts=attempts) from last_error


__all__ = [
    "DEFAULT_PROVIDER_RETRY_ATTEMPTS",
    "ProviderRetryError",
    "is_temporary_provider_error",
    "retry_provider_call",
    "safe_provider_error_summary",
]
