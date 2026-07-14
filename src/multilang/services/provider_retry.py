"""Deterministic retry/backoff and circuit-breaker boundary for provider calls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from random import Random
from time import monotonic, sleep
from typing import TypeVar

from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate
from multilang.security.redaction import redact_sensitive_text

T = TypeVar("T")

DEFAULT_PROVIDER_RETRY_ATTEMPTS = 3


class ProviderRetryError(RuntimeError):
    """Raised after temporary provider failures exhaust retry attempts."""

    def __init__(self, message: str, *, attempts: int) -> None:
        super().__init__(message)
        self.attempts = attempts


class ProviderCircuitOpenError(RuntimeError):
    """Raised when a provider circuit is open and calls are blocked."""


@dataclass(frozen=True, slots=True)
class ProviderRetryContext:
    provider: str
    operation: str
    model: str | None = None
    voice_id: str | None = None
    job_id: str | None = None
    item_key: str | None = None

    @property
    def circuit_key(self) -> str:
        identity = self.model or self.voice_id or "default"
        return f"{self.provider}:{identity}:{self.operation}"


@dataclass(slots=True)
class _CircuitState:
    failure_count: int = 0
    opened_at: float | None = None
    half_open_probe: bool = False


class ProviderCircuitBreaker:
    def __init__(self, *, failure_threshold: int = 3, cooldown_seconds: float = 60.0) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._states: dict[str, _CircuitState] = {}

    def before_call(self, context: ProviderRetryContext, *, now: float) -> None:
        state = self._states.setdefault(context.circuit_key, _CircuitState())
        if state.opened_at is None:
            return
        if now - state.opened_at >= self.cooldown_seconds and not state.half_open_probe:
            state.half_open_probe = True
            return
        raise ProviderCircuitOpenError(f"provider circuit open: {context.circuit_key}")

    def record_success(self, context: ProviderRetryContext) -> None:
        self._states[context.circuit_key] = _CircuitState()

    def record_failure(self, context: ProviderRetryContext, *, now: float) -> None:
        state = self._states.setdefault(context.circuit_key, _CircuitState())
        state.failure_count += 1
        if state.failure_count >= self.failure_threshold or state.half_open_probe:
            state.opened_at = now
            state.half_open_probe = False

    def state_for(self, context: ProviderRetryContext) -> str:
        state = self._states.get(context.circuit_key)
        if state is None or state.opened_at is None:
            return "closed"
        return "half_open" if state.half_open_probe else "open"


def classify_provider_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__} {exc}".casefold()
    status_code = str(getattr(getattr(exc, "response", None), "status_code", "") or getattr(exc, "status_code", ""))
    # Quota/credit exhaustion is non-retryable and must be detected BEFORE the
    # generic 429/rate-limit branch: providers frequently surface it as an HTTP
    # 429 (e.g. "429 insufficient credits"), which would otherwise be retried
    # through the full backoff window before failing anyway.
    if "quota" in text or "insufficient credits" in text:
        return "quota_exceeded"
    if "429" in text or status_code == "429" or "rate limit" in text:
        return "rate_limited"
    if "temporary 403" in text or " 403" in text or status_code == "403" or "forbidden" in text:
        return "temporary_forbidden"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "network" in text or "connection" in text:
        return "network_error"
    if status_code.startswith("5") or any(marker in text for marker in (" 500", " 502", " 503", " 504")):
        return "server_error"
    return "permanent"


# Classifications that must not be retried: they will not recover within the
# retry/backoff window, so retrying only wastes latency before failing anyway.
# ``quota_exceeded`` (exhausted credits/quota) is a hard stop; ``permanent`` is
# the catch-all for unclassified errors. Transient ``temporary_forbidden`` (some
# providers surface throttling as 403) is intentionally left retryable.
NON_RETRYABLE_CLASSIFICATIONS = frozenset({"permanent", "quota_exceeded"})


def is_temporary_provider_error(exc: BaseException) -> bool:
    return classify_provider_error(exc) not in NON_RETRYABLE_CLASSIFICATIONS


def safe_provider_error_summary(exc: BaseException) -> str:
    text = redact_sensitive_text(str(exc) or type(exc).__name__)
    kind = classify_provider_error(exc)
    if kind == "permanent":
        kind = "permanent_provider_error"
    return f"{kind}: provider call failed with redacted temporary error"


def retry_after_seconds(exc: BaseException) -> float | None:
    headers = getattr(exc, "headers", None) or getattr(getattr(exc, "response", None), "headers", None) or {}
    value = None
    if isinstance(headers, dict):
        value = headers.get("Retry-After") or headers.get("retry-after")
    else:
        getter = getattr(headers, "get", None)
        if callable(getter):
            value = getter("Retry-After") or getter("retry-after")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def retry_provider_call(
    operation: Callable[[], T],
    *,
    attempts: int = DEFAULT_PROVIDER_RETRY_ATTEMPTS,
    wait_seconds: float = 0.0,
    base_delay_seconds: float | None = None,
    max_delay_seconds: float = 30.0,
    jitter_ratio: float = 0.0,
    sleeper: Callable[[float], None] = sleep,
    monotonic_clock: Callable[[], float] = monotonic,
    jitter: Callable[[], float] | None = None,
    context: ProviderRetryContext | None = None,
    circuit_breaker: ProviderCircuitBreaker | None = None,
    call_logger: object | None = None,
    success_attempt_callback: Callable[[int], None] | None = None,
) -> T:
    last_error: BaseException | None = None
    base_delay = wait_seconds if base_delay_seconds is None else base_delay_seconds
    jitter_source = jitter or Random(0).random
    if context is not None and circuit_breaker is not None:
        try:
            circuit_breaker.before_call(context, now=monotonic_clock())
        except ProviderCircuitOpenError:
            _log_retry_event(call_logger, context, attempt=1, status="circuit_open", latency_ms=0, error_code="circuit_open")
            raise
    for attempt in range(1, attempts + 1):
        attempt_started = monotonic_clock()
        try:
            result = operation()
            if context is not None and circuit_breaker is not None:
                circuit_breaker.record_success(context)
            if success_attempt_callback is not None:
                success_attempt_callback(attempt)
            return result
        except Exception as exc:  # noqa: BLE001 - provider adapters expose heterogeneous errors.
            classification = classify_provider_error(exc)
            if not is_temporary_provider_error(exc):
                raise
            last_error = exc
            _log_retry_event(
                call_logger,
                context,
                attempt=attempt,
                status="failure",
                latency_ms=_elapsed_ms(attempt_started, monotonic_clock()),
                error_code=classification,
                error_summary=safe_provider_error_summary(exc),
            )
            if context is not None and circuit_breaker is not None:
                circuit_breaker.record_failure(context, now=monotonic_clock())
                if circuit_breaker.state_for(context) == "open":
                    raise ProviderCircuitOpenError(f"provider circuit open: {context.circuit_key}") from exc
            if attempt < attempts:
                delay = _retry_delay(exc, attempt=attempt, base_delay_seconds=base_delay, max_delay_seconds=max_delay_seconds, jitter_ratio=jitter_ratio, jitter=jitter_source)
                if delay > 0:
                    sleeper(delay)
    assert last_error is not None
    raise ProviderRetryError(safe_provider_error_summary(last_error), attempts=attempts) from last_error


def _retry_delay(
    exc: BaseException,
    *,
    attempt: int,
    base_delay_seconds: float,
    max_delay_seconds: float,
    jitter_ratio: float,
    jitter: Callable[[], float],
) -> float:
    retry_after = retry_after_seconds(exc)
    if retry_after is not None:
        return min(max_delay_seconds, retry_after)
    delay = min(max_delay_seconds, max(0.0, base_delay_seconds) * (2 ** max(0, attempt - 1)))
    if delay and jitter_ratio > 0:
        spread = delay * jitter_ratio
        delay = delay - spread + (2 * spread * jitter())
    return max(0.0, delay)


def _elapsed_ms(started: float, finished: float) -> int:
    return max(0, int((finished - started) * 1000))


def _log_retry_event(
    call_logger: object | None,
    context: ProviderRetryContext | None,
    *,
    attempt: int,
    status: str,
    latency_ms: int,
    error_code: str | None = None,
    error_summary: str | None = None,
) -> None:
    insert = getattr(call_logger, "insert", None)
    if not callable(insert) or context is None:
        return
    insert(
        ProviderCallLogCreate(
            job_id=context.job_id,
            item_key=context.item_key,
            operation=context.operation,
            provider=context.provider,
            model=context.model,
            voice_id=context.voice_id,
            attempt=attempt,
            latency_ms=latency_ms,
            status=status,
            error_code=error_code,
            error_summary=error_summary,
        )
    )


__all__ = [
    "DEFAULT_PROVIDER_RETRY_ATTEMPTS",
    "NON_RETRYABLE_CLASSIFICATIONS",
    "ProviderRetryError",
    "ProviderCircuitBreaker",
    "ProviderCircuitOpenError",
    "ProviderRetryContext",
    "classify_provider_error",
    "is_temporary_provider_error",
    "retry_provider_call",
    "retry_after_seconds",
    "safe_provider_error_summary",
]
