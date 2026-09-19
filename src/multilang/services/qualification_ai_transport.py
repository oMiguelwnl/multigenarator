"""Bounded, tool-free machine review transport and explicit cost reservations.

The caller persists reservations before invoking the transport. An interrupted or
invalid response never refunds its reservation. This module grants no review,
licensing or production authority and performs no network activity on import.
"""

from __future__ import annotations

import json
import os
import re
from decimal import ROUND_CEILING, Decimal, localcontext
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from typing import Callable, Literal

from pydantic import Field, field_validator

from multilang.domain.language_profiles import NativeContract

_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
_MAX_MESSAGES = 64
_FRAMING_TOKEN_ALLOWANCE = 1024
_ONE_MILLION = Decimal(1_000_000)
_SDK_CALLBACK_COLLECTIONS = (
    "callbacks",
    "input_callback",
    "success_callback",
    "failure_callback",
    "_async_input_callback",
    "_async_success_callback",
    "_async_failure_callback",
    "audit_log_callbacks",
    "pre_call_rules",
    "post_call_rules",
)


class _Frozen(NativeContract):
    """Closed contracts also validate copy updates and freeze nested mappings."""


class AITransportLimits(_Frozen):
    max_input_bytes: int = Field(default=131072, ge=256, le=1048576, strict=True)
    max_input_tokens: int = Field(default=140000, ge=1, le=1100000, strict=True)
    max_output_tokens: int = Field(default=4000, ge=1, le=32000, strict=True)
    timeout_seconds: float = Field(default=60, gt=0, le=600, allow_inf_nan=False)
    max_response_bytes: int = Field(default=262144, ge=256, le=2097152, strict=True)


class AITransportResult(_Frozen):
    payload: dict[str, object]
    requested_model: str
    response_model: str | None
    model_version: None = None
    provider_api_version: None = None
    sdk_version: str | None
    transport_kind: Literal["injected", "litellm"]
    response_id: str | None
    system_fingerprint: str | None
    input_tokens: int | None = Field(default=None, ge=0, strict=True)
    output_tokens: int | None = Field(default=None, ge=0, strict=True)
    total_tokens: int | None = Field(default=None, ge=0, strict=True)
    input_token_upper_bound: int = Field(ge=1, strict=True)
    response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def _json_bytes(value: object, error: str) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError, UnicodeError):
        raise ValueError(error) from None


def _get(value: object, key: str) -> object:
    return value.get(key) if isinstance(value, dict) else getattr(value, key, None)


def _metadata(value: object) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or _MODEL.fullmatch(value) is None
        or "://" in value
        or value.startswith("sk-")
    ):
        raise ValueError("response_metadata_invalid")
    return value


def _strict_payload(content: str) -> dict[str, object]:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def constant(_: str) -> None:
        raise ValueError("nonfinite value")

    try:
        value = json.loads(content, object_pairs_hook=pairs, parse_constant=constant)
        if not isinstance(value, dict):
            raise ValueError("not an object")
        # Also rejects numeric overflow (1e999), unpaired surrogates and deep JSON.
        _json_bytes(value, "response_json_invalid")
        return value
    except (TypeError, ValueError, RecursionError, UnicodeError):
        raise ValueError("response_json_invalid") from None


def _usage(response: object, input_bound: int, output_bound: int) -> dict[str, int | None]:
    usage = _get(response, "usage")
    if (
        usage is not None
        and not isinstance(usage, dict)
        and not any(
            hasattr(usage, key) for key in ("prompt_tokens", "input_tokens", "total_tokens")
        )
    ):
        raise ValueError("response_usage_invalid")
    result: dict[str, int | None] = {}
    for target, keys in (
        ("input_tokens", ("prompt_tokens", "input_tokens")),
        ("output_tokens", ("completion_tokens", "output_tokens")),
        ("total_tokens", ("total_tokens",)),
    ):
        present = [_get(usage, key) for key in keys if _get(usage, key) is not None]
        if any(type(value) is not int or value < 0 for value in present):
            raise ValueError("response_usage_invalid")
        if len(set(present)) > 1:
            raise ValueError("response_usage_invalid")
        result[target] = present[0] if present else None
    input_tokens, output_tokens, total = (
        result["input_tokens"],
        result["output_tokens"],
        result["total_tokens"],
    )
    if (
        (input_tokens is not None and input_tokens > input_bound)
        or (output_tokens is not None and output_tokens > output_bound)
        or (total is not None and total > input_bound + output_bound)
        or (
            input_tokens is not None
            and output_tokens is not None
            and total is not None
            and total != input_tokens + output_tokens
        )
        or (total is not None and input_tokens is not None and total < input_tokens)
        or (total is not None and output_tokens is not None and total < output_tokens)
    ):
        raise ValueError("response_usage_invalid")
    return result


def _sdk_version() -> str:
    try:
        return "litellm-" + version("litellm")
    except PackageNotFoundError:
        return "litellm-version-unavailable"


def _live_completion(**kwargs: object) -> object:
    # Import only at the explicit invocation boundary. Refuse global controls
    # that could add hidden requests, alter fixed params or replay another run.
    import litellm

    if (
        litellm.model_fallbacks
        or litellm.drop_params
        or litellm.cache is not None
        or any(getattr(litellm, name, None) for name in _SDK_CALLBACK_COLLECTIONS)
    ):
        raise ValueError("provider_global_controls_unsupported")
    return litellm.completion(**kwargs)


class QualificationAITransport:
    """One invocation with fixed controls; all evidence is quoted text data.

    Token reservations conservatively use serialized UTF-8 bytes (including the
    schema) plus framing allowance, rather than whitespace or language guesses.
    Returned usage exceeding this ceiling blocks the result; the caller retains
    its entire reservation. Exact model revision/API version remain unknown when
    the completion envelope does not provide an authoritative version field.
    """

    def __init__(
        self,
        model: str,
        limits: AITransportLimits,
        completion_func: Callable[..., object] | None = None,
        api_key: str | None = None,
    ) -> None:
        if (
            not isinstance(model, str)
            or _MODEL.fullmatch(model) is None
            or "://" in model
            or ".." in model
            or model.startswith("sk-")
        ):
            raise ValueError("provider_model_invalid")
        self.model = model
        self.limits = AITransportLimits.model_validate(limits.model_dump())
        self._completion_func = completion_func
        self._api_key = api_key

    def _request(self, messages: object, response_schema: object) -> tuple[dict, int]:
        if not isinstance(messages, (list, tuple)) or not 1 <= len(messages) <= _MAX_MESSAGES:
            raise ValueError("request_messages_invalid")
        if any(
            not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or message["role"] not in {"system", "user"}
            or not isinstance(message["content"], str)
            for message in messages
        ):
            raise ValueError("request_messages_invalid")
        if (
            not isinstance(response_schema, dict)
            or response_schema.get("type") != "object"
            or response_schema.get("additionalProperties") is not False
        ):
            raise ValueError("request_schema_invalid")
        schema_text = _json_bytes(response_schema, "request_schema_invalid").decode("utf-8")
        schema_message = {
            "role": "system",
            "content": (
                "Return exactly one JSON object conforming to this schema. "
                "It is the output data contract; do not add execution metadata or tools. "
                "The application independently validates the returned object.\nJSON schema:\n"
                + schema_text
            ),
        }
        request = {
            "model": self.model,
            "messages": [schema_message, *messages],
            # JSON mode keeps dynamic morphology maps and nullable/default fields
            # intact across providers. The schema is guidance here; the machine
            # review service performs the closed, authoritative local validation.
            "response_format": {"type": "json_object"},
            "max_tokens": self.limits.max_output_tokens,
            "timeout": self.limits.timeout_seconds,
            "num_retries": 0,
            "max_retries": 0,
            "n": 1,
            "stream": False,
            "tools": [],
            "tool_choice": "none",
            "parallel_tool_calls": False,
            "caching": False,
        }
        serialized = _json_bytes(request, "request_json_invalid")
        if len(serialized) > self.limits.max_input_bytes:
            raise ValueError("input_bytes_exceeded")
        token_bound = len(serialized) + _FRAMING_TOKEN_ALLOWANCE
        if token_bound > self.limits.max_input_tokens:
            raise ValueError("input_tokens_exceeded")
        # Round-trip detaches nested dictionaries owned by the caller.
        return json.loads(serialized), token_bound

    def input_token_upper_bound(self, messages: object, response_schema: object) -> int:
        return self._request(messages, response_schema)[1]

    def complete(self, messages: object, response_schema: object) -> AITransportResult:
        request, input_bound = self._request(messages, response_schema)
        if self._completion_func is None and (
            os.environ.get("MULTILANG_FORBID_PROVIDERS") == "1"
            or os.environ.get("MULTILANG_FORBID_NETWORK") == "1"
        ):
            raise ValueError("provider_calls_forbidden")
        if self._api_key is not None:
            request["api_key"] = self._api_key
        try:
            response = (self._completion_func or _live_completion)(**request)
        except Exception as exc:
            # Never expose the original SDK exception, request, credential or URL.
            kind = "timeout" if isinstance(exc, TimeoutError) else "provider_error"
            raise ValueError(f"provider_call_failed: {kind}") from None
        choices = _get(response, "choices")
        if not isinstance(choices, (list, tuple)) or len(choices) != 1:
            raise ValueError("response_envelope_invalid")
        choice = choices[0]
        message = _get(choice, "message")
        content = _get(message, "content")
        if (
            _get(choice, "finish_reason") != "stop"
            or not isinstance(content, str)
            or _get(message, "tool_calls")
            or _get(message, "function_call")
            or _get(message, "refusal")
        ):
            raise ValueError("response_envelope_invalid")
        try:
            raw = content.encode("utf-8")
        except UnicodeError:
            raise ValueError("response_json_invalid") from None
        if len(raw) > self.limits.max_response_bytes:
            raise ValueError("response_bytes_exceeded")
        return AITransportResult(
            payload=_strict_payload(content),
            requested_model=self.model,
            response_model=_metadata(_get(response, "model")),
            sdk_version=_sdk_version() if self._completion_func is None else None,
            transport_kind="litellm" if self._completion_func is None else "injected",
            response_id=_metadata(_get(response, "id")),
            system_fingerprint=_metadata(_get(response, "system_fingerprint")),
            input_token_upper_bound=input_bound,
            response_sha256=sha256(raw).hexdigest(),
            **_usage(response, input_bound, self.limits.max_output_tokens),
        )


class MachineBudgetReservation(_Frozen):
    call_number: int = Field(ge=1, strict=True)
    input_token_upper_bound: int = Field(ge=0, strict=True)
    output_token_upper_bound: int = Field(ge=0, strict=True)
    upper_bound_cost: Decimal = Field(ge=0, allow_inf_nan=False)
    cumulative_reserved_cost: Decimal = Field(ge=0, allow_inf_nan=False)
    budget_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class MachineRunBudget(_Frozen):
    total_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    max_calls: int = Field(ge=1, le=100000, strict=True)
    input_cost_per_million: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    output_cost_per_million: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    price_basis: str = Field(min_length=1, max_length=2000)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    arithmetic_policy: Literal["decimal-80-ceiling-v1"] = "decimal-80-ceiling-v1"

    @field_validator("total_cost", "input_cost_per_million", "output_cost_per_million")
    @classmethod
    def bounded_decimal(cls, value: Decimal) -> Decimal:
        if len(value.as_tuple().digits) > 40 or abs(value.as_tuple().exponent) > 40:
            raise ValueError("budget_decimal_precision_exceeded")
        return value

    @field_validator("price_basis")
    @classmethod
    def nonempty_basis(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("price_basis_required")
        return value

    @property
    def budget_sha256(self) -> str:
        return sha256(_json_bytes(self.model_dump(mode="json"), "budget_json_invalid")).hexdigest()

    def reserve(
        self,
        *,
        input_tokens: int,
        max_output_tokens: int,
        reserved_calls: int = 0,
        reserved_cost: Decimal = Decimal(0),
    ) -> MachineBudgetReservation:
        """Return a new conservative reservation; never mutate or release prior cost.

        Rates and currency are caller-declared assumptions, not fetched prices.
        Reservations cover every output token, including reasoning tokens when the
        selected provider accounts for them in its completion-token ceiling.
        """
        if any(
            type(value) is not int or value < 0
            for value in (input_tokens, max_output_tokens, reserved_calls)
        ):
            raise ValueError("budget_usage_invalid")
        if input_tokens > 1100000 or max_output_tokens > 32000:
            raise ValueError("budget_tokens_exceeded")
        if reserved_calls >= self.max_calls:
            raise ValueError("call_budget_exceeded")
        if (
            not isinstance(reserved_cost, Decimal)
            or not reserved_cost.is_finite()
            or reserved_cost < 0
        ):
            raise ValueError("budget_reserved_cost_invalid")
        if len(reserved_cost.as_tuple().digits) > 80 or abs(reserved_cost.as_tuple().exponent) > 80:
            raise ValueError("budget_reserved_cost_invalid")
        with localcontext() as context:
            context.prec = 80
            context.rounding = ROUND_CEILING
            cost = (
                Decimal(input_tokens) * self.input_cost_per_million
                + Decimal(max_output_tokens) * self.output_cost_per_million
            ) / _ONE_MILLION
            cumulative = reserved_cost + cost
            if cumulative > self.total_cost:
                raise ValueError("cost_budget_exceeded")
        return MachineBudgetReservation(
            call_number=reserved_calls + 1,
            input_token_upper_bound=input_tokens,
            output_token_upper_bound=max_output_tokens,
            upper_bound_cost=cost,
            cumulative_reserved_cost=cumulative,
            budget_sha256=self.budget_sha256,
            currency=self.currency,
        )


__all__ = [
    "AITransportLimits",
    "AITransportResult",
    "MachineBudgetReservation",
    "MachineRunBudget",
    "QualificationAITransport",
]
