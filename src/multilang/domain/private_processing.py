"""Private highlight processing authority and receipt contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
import math
import re
import unicodedata
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PRIVATE_TOKENIZATION_RULE_ID = "phase33-private-token-v1"
MAX_PRIVATE_CONTEXT_TOKENS = 24
MAX_PRIVATE_CONTEXT_CODE_POINTS = 512
MAX_PRIVATE_CONTEXT_UTF8_BYTES = 2048

_LOWERCASE_HEX = frozenset("0123456789abcdef")
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_SENSITIVE_IDENTIFIER_RE = re.compile(
    r"(?i)(api[_-]?key|secret|password|token|credential|/home/|/users/|c:\\users)"
)
_BROAD_AUTHORITY_VALUES = frozenset(
    {
        "*",
        "all",
        "any",
        "wildcard",
        "source-wide",
        "job-wide",
        "account-wide",
        "provider-any",
        "model-any",
        "route-any",
        "purpose-any",
    }
)


class _FrozenPrivateProcessingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class PrivateDisclosureState(str, Enum):
    PENDING = "pending"
    DISCLOSING = "disclosing"
    DISCLOSED = "disclosed"
    FAILED_UNKNOWN = "failed_unknown"


class PrivateProcessingRefusalReason(str, Enum):
    MISSING_CAPABILITY = "missing_capability"
    MALFORMED_CAPABILITY = "malformed_capability"
    WILDCARD_AUTHORITY = "wildcard_authority"
    BINDING_MISMATCH = "binding_mismatch"
    STALE_EXCERPT = "stale_excerpt"
    TARGET_MISMATCH = "target_mismatch"
    EXPIRED = "expired"
    REPLAY_OR_CLOSED_STATE = "replay_or_closed_state"
    CONTEXT_OVER_BUDGET = "context_over_budget"
    INVALID_TARGET_SPAN = "invalid_target_span"
    TARGET_ABSENT = "target_absent"
    UNSUPPORTED_TOKENIZATION_RULE = "unsupported_tokenization_rule"
    INVALID_BUDGET = "invalid_budget"
    CAS_CONFLICT = "cas_conflict"
    PROVIDER_UNKNOWN_RESULT = "provider_unknown_result"
    UNSAFE_PROVIDER_OUTPUT = "unsafe_provider_output"


class PrivateContextToken(_FrozenPrivateProcessingModel):
    text: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    kind: Literal["letter_number_mark", "punctuation_symbol"]

    @model_validator(mode="after")
    def span_must_be_ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError("token span must be ordered")
        return self


class PrivateProcessingPolicy(_FrozenPrivateProcessingModel):
    policy_version: str = Field(min_length=1, max_length=160)
    policy_sha256: str = Field(min_length=64, max_length=64)
    tokenization_rule_id: Literal["phase33-private-token-v1"] = PRIVATE_TOKENIZATION_RULE_ID
    max_context_tokens: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_TOKENS)
    max_context_code_points: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_CODE_POINTS)
    max_context_utf8_bytes: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_UTF8_BYTES)
    max_provider_attempts: int = Field(ge=1, le=2)
    max_estimated_cost_usd: float = Field(ge=0.0, le=100.0)
    redaction_policy_version: str = Field(min_length=1, max_length=160)

    @field_validator("policy_version", "redaction_policy_version")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("policy_sha256")
    @classmethod
    def hash_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "sha256"))

    @model_validator(mode="after")
    def budgets_must_be_finite_and_consistent(self) -> Self:
        if not math.isfinite(self.max_estimated_cost_usd):
            raise ValueError("cost budget must be finite")
        if self.max_context_utf8_bytes < self.max_context_code_points:
            raise ValueError("byte budget must cover code-point budget")
        return self


class PrivateProviderIdempotency(_FrozenPrivateProcessingModel):
    support: Literal["supported", "unsupported"]
    key: str | None = Field(default=None, min_length=8, max_length=160)

    @field_validator("key")
    @classmethod
    def key_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _safe_identifier(value, field_name="idempotency_key")

    @model_validator(mode="after")
    def key_must_match_support(self) -> Self:
        if self.support == "supported" and self.key is None:
            raise ValueError("supported idempotency requires an exact key")
        if self.support == "unsupported" and self.key is not None:
            raise ValueError("unsupported idempotency must not include a key")
        return self


class PrivateProcessingCapability(_FrozenPrivateProcessingModel):
    capability_id: str = Field(min_length=32, max_length=160)
    job_id: str = Field(min_length=1, max_length=160)
    run_id: str = Field(min_length=1, max_length=160)
    item_id: str = Field(min_length=1, max_length=160)
    excerpt_revision_id: str = Field(min_length=1, max_length=160)
    excerpt_sha256: str = Field(min_length=64, max_length=64)
    target_start: int = Field(ge=0)
    target_end: int = Field(gt=0)
    target_text_sha256: str = Field(min_length=64, max_length=64)
    provider_id: str = Field(min_length=1, max_length=160)
    provider: str = Field(min_length=1, max_length=160)
    model: str = Field(min_length=1, max_length=160)
    route_id: str = Field(min_length=1, max_length=160)
    provider_route_sha256: str = Field(min_length=64, max_length=64)
    purpose: str = Field(min_length=1, max_length=160)
    policy_version: str = Field(min_length=1, max_length=160)
    policy_sha256: str = Field(min_length=64, max_length=64)
    tokenization_rule_id: Literal["phase33-private-token-v1"] = PRIVATE_TOKENIZATION_RULE_ID
    max_context_tokens: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_TOKENS)
    max_context_code_points: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_CODE_POINTS)
    max_context_utf8_bytes: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_UTF8_BYTES)
    max_provider_attempts: int = Field(ge=1, le=2)
    max_estimated_cost_usd: float = Field(ge=0.0, le=100.0)
    idempotency: PrivateProviderIdempotency
    issued_at: datetime
    expires_at: datetime
    issuer_id: str = Field(min_length=1, max_length=160)
    issuer_intent_sha256: str = Field(min_length=64, max_length=64)
    state: PrivateDisclosureState = PrivateDisclosureState.PENDING
    version: int = Field(ge=0)

    @field_validator(
        "capability_id",
        "job_id",
        "run_id",
        "item_id",
        "excerpt_revision_id",
        "provider_id",
        "provider",
        "model",
        "route_id",
        "purpose",
        "policy_version",
        "issuer_id",
    )
    @classmethod
    def identifiers_must_be_exact_and_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator(
        "excerpt_sha256",
        "target_text_sha256",
        "provider_route_sha256",
        "policy_sha256",
        "issuer_intent_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "sha256"))

    @field_validator("issued_at", "expires_at")
    @classmethod
    def datetimes_must_be_aware(cls, value: datetime, info: object) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{getattr(info, 'field_name', 'datetime')} must be timezone-aware")
        return value

    @model_validator(mode="after")
    def capability_must_be_exact_single_run_scope(self) -> Self:
        if self.target_end <= self.target_start:
            raise ValueError("target span must be ordered")
        if self.expires_at <= self.issued_at:
            raise ValueError("expiry must be after issuance")
        if not math.isfinite(self.max_estimated_cost_usd):
            raise ValueError("cost budget must be finite")
        if self.max_context_utf8_bytes < self.max_context_code_points:
            raise ValueError("byte budget must cover code-point budget")
        if self.idempotency.support == "unsupported" and self.max_provider_attempts != 1:
            raise ValueError("non-idempotent disclosure allows one provider attempt")
        if self.state is not PrivateDisclosureState.PENDING and self.version < 1:
            raise ValueError("closed or in-flight capability state requires a consumed version")
        return self


class PrivateDisclosureStateTransition(_FrozenPrivateProcessingModel):
    capability_id: str = Field(min_length=32, max_length=160)
    from_state: PrivateDisclosureState
    to_state: PrivateDisclosureState
    expected_version: int = Field(ge=0)
    next_version: int = Field(ge=1)

    @field_validator("capability_id")
    @classmethod
    def capability_id_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="capability_id")

    @model_validator(mode="after")
    def transition_must_be_forward_only(self) -> Self:
        allowed = {
            (PrivateDisclosureState.PENDING, PrivateDisclosureState.DISCLOSING),
            (PrivateDisclosureState.DISCLOSING, PrivateDisclosureState.DISCLOSED),
            (PrivateDisclosureState.DISCLOSING, PrivateDisclosureState.FAILED_UNKNOWN),
        }
        if (self.from_state, self.to_state) not in allowed:
            raise ValueError("private disclosure state transition is not allowed")
        if self.next_version != self.expected_version + 1:
            raise ValueError("state transition version must increment by one")
        return self


class PrivateProcessingReceipt(_FrozenPrivateProcessingModel):
    receipt_id: str = Field(min_length=1, max_length=160)
    capability_id_sha256: str = Field(min_length=64, max_length=64)
    job_id_sha256: str = Field(min_length=64, max_length=64)
    item_id_sha256: str = Field(min_length=64, max_length=64)
    excerpt_revision_id_sha256: str = Field(min_length=64, max_length=64)
    excerpt_sha256: str = Field(min_length=64, max_length=64)
    context_sha256: str = Field(min_length=64, max_length=64)
    context_token_count: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_TOKENS)
    context_code_point_count: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_CODE_POINTS)
    context_utf8_byte_count: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_UTF8_BYTES)
    provider_id: str = Field(min_length=1, max_length=160)
    provider: str = Field(min_length=1, max_length=160)
    model: str = Field(min_length=1, max_length=160)
    route_id: str = Field(min_length=1, max_length=160)
    provider_route_sha256: str = Field(min_length=64, max_length=64)
    purpose: str = Field(min_length=1, max_length=160)
    policy_version: str = Field(min_length=1, max_length=160)
    policy_sha256: str = Field(min_length=64, max_length=64)
    tokenization_rule_id: Literal["phase33-private-token-v1"] = PRIVATE_TOKENIZATION_RULE_ID
    idempotency_key_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    state: Literal["disclosed"] = "disclosed"
    receipt_sha256: str = Field(min_length=64, max_length=64)

    @field_validator(
        "receipt_id",
        "provider_id",
        "provider",
        "model",
        "route_id",
        "purpose",
        "policy_version",
    )
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator(
        "capability_id_sha256",
        "job_id_sha256",
        "item_id_sha256",
        "excerpt_revision_id_sha256",
        "excerpt_sha256",
        "context_sha256",
        "provider_route_sha256",
        "policy_sha256",
        "idempotency_key_sha256",
        "receipt_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        return _sha256(value, field_name=getattr(info, "field_name", "sha256"))

    @classmethod
    def for_disclosure(
        cls,
        *,
        capability: PrivateProcessingCapability,
        context_sha256: str,
        context_token_count: int,
        context_code_point_count: int,
        context_utf8_byte_count: int,
        idempotency_key: str | None,
    ) -> "PrivateProcessingReceipt":
        receipt_id = "receipt-" + private_text_sha256(
            f"{capability.capability_id}:{context_sha256}:{capability.version}"
        )[:32]
        receipt = cls(
            receipt_id=receipt_id,
            capability_id_sha256=private_text_sha256(capability.capability_id),
            job_id_sha256=private_text_sha256(capability.job_id),
            item_id_sha256=private_text_sha256(capability.item_id),
            excerpt_revision_id_sha256=private_text_sha256(capability.excerpt_revision_id),
            excerpt_sha256=capability.excerpt_sha256,
            context_sha256=_sha256(context_sha256, field_name="context_sha256"),
            context_token_count=context_token_count,
            context_code_point_count=context_code_point_count,
            context_utf8_byte_count=context_utf8_byte_count,
            provider_id=capability.provider_id,
            provider=capability.provider,
            model=capability.model,
            route_id=capability.route_id,
            provider_route_sha256=capability.provider_route_sha256,
            purpose=capability.purpose,
            policy_version=capability.policy_version,
            policy_sha256=capability.policy_sha256,
            tokenization_rule_id=capability.tokenization_rule_id,
            idempotency_key_sha256=private_text_sha256(idempotency_key) if idempotency_key else None,
            receipt_sha256="0" * 64,
        )
        receipt_sha256 = private_processing_canonical_json_sha256(
            receipt.model_dump(mode="json", exclude={"receipt_sha256"})
        )
        return receipt.model_copy(update={"receipt_sha256": receipt_sha256})


class PrivateProcessingRefusal(_FrozenPrivateProcessingModel):
    reason_code: PrivateProcessingRefusalReason
    capability_id_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    policy_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    adapter_call_status: Literal["not_called"] = "not_called"
    error_code: Literal["private_processing_refused"] = "private_processing_refused"

    @field_validator("capability_id_sha256", "policy_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        return _sha256(value, field_name=getattr(info, "field_name", "sha256"))

    @classmethod
    def for_capability(
        cls,
        reason_code: PrivateProcessingRefusalReason,
        capability: PrivateProcessingCapability | None,
    ) -> "PrivateProcessingRefusal":
        return cls(
            reason_code=reason_code,
            capability_id_sha256=private_text_sha256(capability.capability_id) if capability else None,
            policy_sha256=capability.policy_sha256 if capability else None,
        )


class PrivateDisclosureAttempt(_FrozenPrivateProcessingModel):
    capability_id: str = Field(min_length=32, max_length=160)
    state: PrivateDisclosureState = PrivateDisclosureState.PENDING
    version: int = Field(ge=0)
    receipt: PrivateProcessingReceipt | None = None
    refusal: PrivateProcessingRefusal | None = None

    @field_validator("capability_id")
    @classmethod
    def capability_id_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="capability_id")


def normalize_private_text(value: str) -> str:
    """Return the NFC form used by the Phase 33 private-token rule."""

    return unicodedata.normalize("NFC", value)


def private_text_sha256(value: str) -> str:
    """Hash NFC-normalized private text or identifiers without exposing the value."""

    return sha256(normalize_private_text(value).encode("utf-8")).hexdigest()


def private_processing_canonical_json_sha256(value: object) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def tokenize_private_context_v1(text: str) -> tuple[PrivateContextToken, ...]:
    """Tokenize using the locked Phase 33 private context counter."""

    normalized = normalize_private_text(text)
    tokens: list[PrivateContextToken] = []
    index = 0
    while index < len(normalized):
        character = normalized[index]
        category = unicodedata.category(character)
        if _is_letter_number_mark(category):
            start = index
            index += 1
            while index < len(normalized) and _is_letter_number_mark(
                unicodedata.category(normalized[index])
            ):
                index += 1
            tokens.append(
                PrivateContextToken(
                    text=normalized[start:index],
                    start=start,
                    end=index,
                    kind="letter_number_mark",
                )
            )
            continue
        if character.isspace() or category[0] in {"C", "Z"}:
            index += 1
            continue
        if category[0] in {"P", "S"}:
            tokens.append(
                PrivateContextToken(
                    text=character,
                    start=index,
                    end=index + 1,
                    kind="punctuation_symbol",
                )
            )
        index += 1
    return tuple(tokens)


def count_private_context_tokens_v1(text: str) -> int:
    return len(tokenize_private_context_v1(text))


def validate_private_processing_capability(
    capability: PrivateProcessingCapability | None,
    *,
    job_id: str,
    run_id: str,
    item_id: str,
    excerpt_revision_id: str,
    excerpt_sha256: str,
    target_start: int,
    target_end: int,
    target_text_sha256: str,
    provider: str,
    model: str,
    route_id: str,
    provider_route_sha256: str,
    purpose: str,
    policy_sha256: str,
    now: datetime,
) -> PrivateProcessingRefusal | None:
    """Validate exact per-run authority without revealing private inputs."""

    if capability is None:
        return PrivateProcessingRefusal.for_capability(
            PrivateProcessingRefusalReason.MISSING_CAPABILITY,
            None,
        )
    if capability.state is not PrivateDisclosureState.PENDING:
        return PrivateProcessingRefusal.for_capability(
            PrivateProcessingRefusalReason.REPLAY_OR_CLOSED_STATE,
            capability,
        )
    if now.tzinfo is None or now.utcoffset() is None or now >= capability.expires_at:
        return PrivateProcessingRefusal.for_capability(
            PrivateProcessingRefusalReason.EXPIRED,
            capability,
        )
    if (
        capability.excerpt_revision_id != excerpt_revision_id
        or capability.excerpt_sha256 != _sha256(excerpt_sha256, field_name="excerpt_sha256")
    ):
        return PrivateProcessingRefusal.for_capability(
            PrivateProcessingRefusalReason.STALE_EXCERPT,
            capability,
        )
    if (
        capability.target_start != target_start
        or capability.target_end != target_end
        or capability.target_text_sha256 != _sha256(target_text_sha256, field_name="target_text_sha256")
    ):
        return PrivateProcessingRefusal.for_capability(
            PrivateProcessingRefusalReason.TARGET_MISMATCH,
            capability,
        )
    if (
        capability.job_id != job_id
        or capability.run_id != run_id
        or capability.item_id != item_id
        or capability.provider != provider
        or capability.model != model
        or capability.route_id != route_id
        or capability.provider_route_sha256 != _sha256(
            provider_route_sha256,
            field_name="provider_route_sha256",
        )
        or capability.purpose != purpose
        or capability.policy_sha256 != _sha256(policy_sha256, field_name="policy_sha256")
    ):
        return PrivateProcessingRefusal.for_capability(
            PrivateProcessingRefusalReason.BINDING_MISMATCH,
            capability,
        )
    return None


def _is_letter_number_mark(category: str) -> bool:
    return category[0] in {"L", "N", "M"}


def _sha256(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    if len(value) != 64 or any(character not in _LOWERCASE_HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _safe_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an exact safe identifier")
    normalized = value.strip()
    broad = normalized.casefold()
    if (
        normalized != value
        or not _SAFE_IDENTIFIER_RE.fullmatch(normalized)
        or _SENSITIVE_IDENTIFIER_RE.search(normalized)
        or "*" in normalized
        or broad in _BROAD_AUTHORITY_VALUES
        or broad.endswith("-any")
        or broad.endswith("_any")
        or broad.endswith(":any")
    ):
        raise ValueError(f"{field_name} must be an exact safe identifier")
    return normalized


__all__ = [
    "MAX_PRIVATE_CONTEXT_CODE_POINTS",
    "MAX_PRIVATE_CONTEXT_TOKENS",
    "MAX_PRIVATE_CONTEXT_UTF8_BYTES",
    "PRIVATE_TOKENIZATION_RULE_ID",
    "PrivateContextToken",
    "PrivateDisclosureAttempt",
    "PrivateDisclosureState",
    "PrivateDisclosureStateTransition",
    "PrivateProcessingCapability",
    "PrivateProcessingPolicy",
    "PrivateProcessingReceipt",
    "PrivateProcessingRefusal",
    "PrivateProcessingRefusalReason",
    "PrivateProviderIdempotency",
    "count_private_context_tokens_v1",
    "normalize_private_text",
    "private_processing_canonical_json_sha256",
    "private_text_sha256",
    "tokenize_private_context_v1",
    "validate_private_processing_capability",
]
