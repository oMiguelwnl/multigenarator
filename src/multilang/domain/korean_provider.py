"""Offline Korean provider route and budget policy contracts."""

from __future__ import annotations

from enum import Enum
import math
import re
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.korean import canonical_json_sha256


KOREAN_PROVIDER_POLICY_VERSION = "korean-provider-policy-v1"
_HEX = frozenset("0123456789abcdef")
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._:/-]+$")
_SENSITIVE_NAME_RE = re.compile(r"(?i)(api[_-]?key|secret|token|password|sk-|/home/|/users/|c:\\users)")


class KoreanProviderTask(str, Enum):
    DEFINITION = "definition"
    SENTENCE_GENERATION = "sentence_generation"
    REPAIR = "repair"
    TRANSLATION = "translation"
    JUDGE = "judge"
    CATALOG = "catalog"
    WORD_AUDIO = "word_audio"
    SENTENCE_AUDIO = "sentence_audio"


KOREAN_PROVIDER_REQUIRED_TASKS: tuple[KoreanProviderTask, ...] = tuple(KoreanProviderTask)


class _FrozenPolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanProviderBudget(_FrozenPolicyModel):
    max_attempts: int = Field(ge=1, le=5)
    max_input_tokens: int = Field(ge=0, le=200_000)
    max_output_tokens: int = Field(ge=0, le=200_000)
    max_total_tokens: int = Field(ge=0, le=400_000)
    max_estimated_cost_usd: float = Field(ge=0.0, le=1_000.0)
    max_latency_ms: int = Field(ge=0, le=3_600_000)
    timeout_seconds: float = Field(gt=0.0, le=3_600.0)
    max_batch_items: int = Field(ge=1, le=10_000)
    max_concurrency: int = Field(ge=1, le=1_000)

    @model_validator(mode="after")
    def budget_must_be_finite_and_consistent(self) -> Self:
        if not math.isfinite(self.max_estimated_cost_usd) or not math.isfinite(self.timeout_seconds):
            raise ValueError("provider budget values must be finite")
        if self.max_total_tokens < self.max_input_tokens + self.max_output_tokens:
            raise ValueError("max_total_tokens must cover input and output ceilings")
        return self


class KoreanProviderRoute(_FrozenPolicyModel):
    policy_version: str = KOREAN_PROVIDER_POLICY_VERSION
    task: KoreanProviderTask
    provider: str = Field(min_length=1, max_length=160)
    model: str | None = Field(default=None, max_length=160)
    budget: KoreanProviderBudget
    cache_namespace: str = Field(min_length=1, max_length=160)
    response_schema_sha256: str = Field(min_length=64, max_length=64)
    fallback_policy: Literal["none"] = "none"

    @field_validator("policy_version", "provider", "cache_namespace")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_name(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("model")
    @classmethod
    def model_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _safe_name(value, field_name="model")

    @field_validator("response_schema_sha256")
    @classmethod
    def schema_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256(value, field_name="response_schema_sha256")

    @model_validator(mode="after")
    def route_must_be_explicit_or_disabled(self) -> Self:
        if self.provider == "disabled":
            if self.model is not None:
                raise ValueError("disabled route must not include model")
        elif self.model is None:
            raise ValueError("enabled route requires model")
        return self

    @property
    def enabled(self) -> bool:
        return self.provider != "disabled"

    @property
    def route_policy_sha256(self) -> str:
        return canonical_json_sha256(self.model_dump(mode="json"))

    @property
    def budget_snapshot_sha256(self) -> str:
        return canonical_json_sha256(
            {
                "policy_version": self.policy_version,
                "task": self.task.value,
                "budget": self.budget.model_dump(mode="json"),
            }
        )

    def cache_key_sha256(self, *, item_sha256: str, input_sha256: str) -> str:
        return canonical_json_sha256(
            {
                "cache_namespace": self.cache_namespace,
                "task": self.task.value,
                "provider": self.provider,
                "model": self.model,
                "route_policy_sha256": self.route_policy_sha256,
                "item_sha256": _sha256(item_sha256, field_name="item_sha256"),
                "input_sha256": _sha256(input_sha256, field_name="input_sha256"),
            }
        )

    def assert_within_budget(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float,
        latency_ms: int,
        batch_items: int,
        concurrency: int,
        timeout_seconds: float,
    ) -> None:
        if input_tokens < 0 or output_tokens < 0 or input_tokens > self.budget.max_input_tokens or output_tokens > self.budget.max_output_tokens:
            raise ValueError("token budget exceeded")
        if input_tokens + output_tokens > self.budget.max_total_tokens:
            raise ValueError("token budget exceeded")
        if estimated_cost_usd < 0 or not math.isfinite(estimated_cost_usd) or estimated_cost_usd > self.budget.max_estimated_cost_usd:
            raise ValueError("cost budget exceeded")
        if latency_ms < 0 or latency_ms > self.budget.max_latency_ms or timeout_seconds > self.budget.timeout_seconds:
            raise ValueError("latency budget exceeded")
        if batch_items < 1 or batch_items > self.budget.max_batch_items:
            raise ValueError("batch budget exceeded")
        if concurrency < 1 or concurrency > self.budget.max_concurrency:
            raise ValueError("concurrency budget exceeded")

    def retry_allowed(self, *, attempt: int, route_policy_sha256: str) -> bool:
        if _sha256(route_policy_sha256, field_name="route_policy_sha256") != self.route_policy_sha256:
            raise ValueError("retry must use the same route policy")
        if attempt < 1 or attempt > self.budget.max_attempts:
            raise ValueError("attempt budget exceeded")
        return True


class KoreanProviderPolicy(_FrozenPolicyModel):
    policy_version: str = KOREAN_PROVIDER_POLICY_VERSION
    routes: tuple[KoreanProviderRoute, ...]
    fallback_policy: Literal["none"] = "none"
    authority_scope: Literal["offline_policy_contract_only"] = "offline_policy_contract_only"

    @field_validator("policy_version")
    @classmethod
    def policy_version_must_be_safe(cls, value: str) -> str:
        return _safe_name(value, field_name="policy_version")

    @model_validator(mode="after")
    def policy_must_cover_required_tasks_once(self) -> Self:
        tasks = tuple(route.task for route in self.routes)
        if len(tasks) != len(set(tasks)) or set(tasks) != set(KOREAN_PROVIDER_REQUIRED_TASKS):
            raise ValueError("policy requires exactly one route for every Korean provider task")
        return self

    @property
    def policy_sha256(self) -> str:
        return canonical_json_sha256(
            {
                "policy_version": self.policy_version,
                "fallback_policy": self.fallback_policy,
                "authority_scope": self.authority_scope,
                "routes": tuple(
                    sorted(
                        (route.model_dump(mode="json") for route in self.routes),
                        key=lambda item: item["task"],
                    )
                ),
            }
        )

    @property
    def can_authorize_live_calls(self) -> bool:
        return False

    def route_for(self, task: KoreanProviderTask) -> KoreanProviderRoute:
        for route in self.routes:
            if route.task is task:
                return route
        raise ValueError(f"missing Korean provider route: {task.value}")


class KoreanProviderResultSummary(_FrozenPolicyModel):
    task: KoreanProviderTask
    provider: str = Field(min_length=1, max_length=160)
    status: Literal["success", "failure", "cache_hit", "disabled", "budget_exhausted", "circuit_open"]
    availability_denominator: Literal["attempted", "cache_hit", "disabled", "blocked_budget"]
    attempt: int = Field(ge=0, le=5)
    latency_ms: int = Field(ge=0, le=3_600_000)
    route_policy_sha256: str = Field(min_length=64, max_length=64)
    budget_snapshot_sha256: str = Field(min_length=64, max_length=64)
    cache_key_sha256: str = Field(min_length=64, max_length=64)
    response_schema_sha256: str = Field(min_length=64, max_length=64)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)

    @field_validator("provider")
    @classmethod
    def provider_must_be_safe(cls, value: str) -> str:
        return _safe_name(value, field_name="provider")

    @field_validator("route_policy_sha256", "budget_snapshot_sha256", "cache_key_sha256", "response_schema_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def result_summary_must_use_matching_denominator(self) -> Self:
        expected = {
            "success": "attempted",
            "failure": "attempted",
            "circuit_open": "attempted",
            "cache_hit": "cache_hit",
            "disabled": "disabled",
            "budget_exhausted": "blocked_budget",
        }[self.status]
        if self.availability_denominator != expected:
            raise ValueError("provider result denominator does not match status")
        if self.status in {"success", "failure"} and self.attempt < 1:
            raise ValueError("attempted provider result requires an attempt")
        if self.status == "cache_hit" and self.attempt != 0:
            raise ValueError("cache hit must not consume a provider attempt")
        if self.estimated_cost_usd is not None and not math.isfinite(self.estimated_cost_usd):
            raise ValueError("provider cost must be finite")
        return self


class KoreanProviderPolicyProposal(_FrozenPolicyModel):
    policy_version: str
    settings_fingerprint_sha256: str = Field(min_length=64, max_length=64)
    text_generation_provider: str = Field(min_length=1, max_length=160)
    text_generation_model: str = Field(min_length=1, max_length=160)
    translation_provider: str = Field(min_length=1, max_length=160)
    max_attempts: int = Field(ge=1, le=5)
    approval_status: Literal["proposal_only"] = "proposal_only"

    @field_validator("policy_version", "text_generation_provider", "text_generation_model", "translation_provider")
    @classmethod
    def values_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_name(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("settings_fingerprint_sha256")
    @classmethod
    def settings_fingerprint_must_be_sha256(cls, value: str) -> str:
        return _sha256(value, field_name="settings_fingerprint_sha256")

    @property
    def can_authorize_live_calls(self) -> bool:
        return False


def propose_korean_provider_policy_from_settings(settings: object) -> KoreanProviderPolicyProposal:
    payload = {
        "policy_version": str(getattr(settings, "korean_provider_policy_version", KOREAN_PROVIDER_POLICY_VERSION)),
        "text_generation_provider": str(getattr(settings, "text_generation_provider", "local")),
        "text_generation_model": str(getattr(settings, "text_generation_model", "local")),
        "translation_provider": str(getattr(settings, "translation_provider", "local")),
        "max_attempts": int(getattr(settings, "korean_provider_max_attempts", 1)),
    }
    return KoreanProviderPolicyProposal(
        **payload,
        settings_fingerprint_sha256=canonical_json_sha256(payload),
        approval_status="proposal_only",
    )


def _sha256(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _safe_name(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a safe provider identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > 160
        or not _SAFE_NAME_RE.fullmatch(normalized)
        or _SENSITIVE_NAME_RE.search(normalized)
    ):
        raise ValueError(f"{field_name} must be a safe provider identifier")
    return normalized


__all__ = [
    "KOREAN_PROVIDER_POLICY_VERSION",
    "KOREAN_PROVIDER_REQUIRED_TASKS",
    "KoreanProviderBudget",
    "KoreanProviderPolicy",
    "KoreanProviderPolicyProposal",
    "KoreanProviderResultSummary",
    "KoreanProviderRoute",
    "KoreanProviderTask",
    "propose_korean_provider_policy_from_settings",
]
