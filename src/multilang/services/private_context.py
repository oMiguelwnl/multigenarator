"""Offline broker for exact-authorized private highlight context disclosure."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from multilang.domain.private_processing import (
    MAX_PRIVATE_CONTEXT_TOKENS,
    PRIVATE_TOKENIZATION_RULE_ID,
    PrivateDisclosureAttempt,
    PrivateDisclosureState,
    PrivateDisclosureStateTransition,
    PrivateProcessingCapability,
    PrivateProcessingReceipt,
    PrivateProcessingRefusal,
    PrivateProcessingRefusalReason,
    count_private_context_tokens_v1,
    normalize_private_text,
    private_text_sha256,
    tokenize_private_context_v1,
    validate_private_processing_capability,
)


class _FrozenPrivateContextModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class PrivateContextDerivationError(ValueError):
    def __init__(self, reason_code: PrivateProcessingRefusalReason) -> None:
        super().__init__(reason_code.value)
        self.reason_code = reason_code


class PrivateDisclosureCasConflict(RuntimeError):
    pass


class PrivateProviderUnknownResult(RuntimeError):
    pass


class PrivateContextArtifact(_FrozenPrivateContextModel):
    context: str = Field(min_length=1)
    context_sha256: str = Field(min_length=64, max_length=64)
    tokenization_rule_id: Literal["phase33-private-token-v1"] = PRIVATE_TOKENIZATION_RULE_ID
    token_count: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_TOKENS)
    code_point_count: int = Field(ge=1)
    utf8_byte_count: int = Field(ge=1)
    target_start: int = Field(ge=0)
    target_end: int = Field(gt=0)

    @model_validator(mode="after")
    def artifact_must_match_locked_counter(self) -> Self:
        if self.context_sha256 != private_text_sha256(self.context):
            raise ValueError("context hash mismatch")
        if self.token_count != count_private_context_tokens_v1(self.context):
            raise ValueError("context token count mismatch")
        if self.code_point_count != len(self.context):
            raise ValueError("context code-point count mismatch")
        if self.utf8_byte_count != len(self.context.encode("utf-8")):
            raise ValueError("context byte count mismatch")
        if self.target_end <= self.target_start:
            raise ValueError("target span must be ordered")
        return self


class PrivateContextDisclosureRequest(_FrozenPrivateContextModel):
    capability: PrivateProcessingCapability | None = None
    job_id: str = Field(min_length=1, max_length=160)
    run_id: str = Field(min_length=1, max_length=160)
    item_id: str = Field(min_length=1, max_length=160)
    excerpt_revision_id: str = Field(min_length=1, max_length=160)
    excerpt_text: str = Field(min_length=1)
    excerpt_sha256: str = Field(min_length=64, max_length=64)
    target_start: int = Field(ge=0)
    target_end: int = Field(gt=0)
    target_text: str = Field(min_length=1)
    target_text_sha256: str = Field(min_length=64, max_length=64)
    provider: str = Field(min_length=1, max_length=160)
    model: str = Field(min_length=1, max_length=160)
    route_id: str = Field(min_length=1, max_length=160)
    provider_route_sha256: str = Field(min_length=64, max_length=64)
    purpose: str = Field(min_length=1, max_length=160)
    policy_sha256: str = Field(min_length=64, max_length=64)
    now: datetime
    expected_attempt_version: int = Field(ge=0)

    @field_validator("excerpt_sha256", "target_text_sha256", "provider_route_sha256", "policy_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("hash must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def request_span_must_be_ordered(self) -> Self:
        if self.target_end <= self.target_start:
            raise ValueError("target span must be ordered")
        return self


class PrivateContextPersistentDisclosureRequest(_FrozenPrivateContextModel):
    capability: PrivateProcessingCapability | None = None
    job_id: str = Field(min_length=1, max_length=160)
    run_id: str = Field(min_length=1, max_length=160)
    item_id: str = Field(min_length=1, max_length=160)
    excerpt_revision_id: str = Field(min_length=1, max_length=160)
    excerpt_sha256: str = Field(min_length=64, max_length=64)
    target_start: int = Field(ge=0)
    target_end: int = Field(gt=0)
    target_text_sha256: str = Field(min_length=64, max_length=64)
    provider: str = Field(min_length=1, max_length=160)
    model: str = Field(min_length=1, max_length=160)
    route_id: str = Field(min_length=1, max_length=160)
    provider_route_sha256: str = Field(min_length=64, max_length=64)
    purpose: str = Field(min_length=1, max_length=160)
    policy_sha256: str = Field(min_length=64, max_length=64)
    now: datetime
    expected_attempt_version: int = Field(ge=0)

    @field_validator("excerpt_sha256", "target_text_sha256", "provider_route_sha256", "policy_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("hash must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def request_span_must_be_ordered(self) -> Self:
        if self.target_end <= self.target_start:
            raise ValueError("target span must be ordered")
        return self


class PrivateContextExcerptPayload(_FrozenPrivateContextModel):
    excerpt_text: str = Field(min_length=1)
    target_text: str = Field(min_length=1)


class PrivateProviderContextRequest(_FrozenPrivateContextModel):
    capability_id: str
    context: str
    context_sha256: str = Field(min_length=64, max_length=64)
    tokenization_rule_id: Literal["phase33-private-token-v1"] = PRIVATE_TOKENIZATION_RULE_ID
    token_count: int = Field(ge=1, le=MAX_PRIVATE_CONTEXT_TOKENS)
    provider_id: str
    provider: str
    model: str
    route_id: str
    provider_route_sha256: str = Field(min_length=64, max_length=64)
    purpose: str
    policy_sha256: str = Field(min_length=64, max_length=64)
    idempotency_key: str | None = None
    context_role: Literal["untrusted_private_context_data"] = "untrusted_private_context_data"


class PrivateProviderCallbackResult(_FrozenPrivateContextModel):
    status: Literal["success", "unknown"]
    output_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("output_sha256")
    @classmethod
    def output_hash_must_be_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("output hash must be lowercase SHA-256")
        return value


class PrivateContextBrokerResult(_FrozenPrivateContextModel):
    status: Literal["disclosed", "refused", "inspect_required", "failed_unknown"]
    receipt: PrivateProcessingReceipt | None = None
    refusal: PrivateProcessingRefusal | None = None


class InMemoryPrivateDisclosureStore:
    """Small CAS store for offline tests; real persistence can implement the same seam."""

    def __init__(self, attempts: dict[str, PrivateDisclosureAttempt]) -> None:
        self._attempts = dict(attempts)
        self.transaction_open = False
        self.history: list[str] = []

    @classmethod
    def from_capability(
        cls,
        capability: PrivateProcessingCapability,
        *,
        state: str | PrivateDisclosureState | None = None,
        version: int | None = None,
        receipt: PrivateProcessingReceipt | None = None,
        refusal: PrivateProcessingRefusal | None = None,
    ) -> "InMemoryPrivateDisclosureStore":
        attempt = PrivateDisclosureAttempt(
            capability_id=capability.capability_id,
            state=state or capability.state,
            version=capability.version if version is None else version,
            receipt=receipt,
            refusal=refusal,
        )
        return cls({capability.capability_id: attempt})

    def get_attempt(self, capability_id: str) -> PrivateDisclosureAttempt | None:
        return self._attempts.get(capability_id)

    def reserve_disclosure(
        self,
        *,
        capability_id: str,
        expected_version: int,
    ) -> PrivateDisclosureAttempt:
        self._begin()
        try:
            attempt = self._attempts.get(capability_id)
            if (
                attempt is None
                or attempt.state is not PrivateDisclosureState.PENDING
                or attempt.version != expected_version
            ):
                raise PrivateDisclosureCasConflict("private disclosure reservation conflict")
            transition = PrivateDisclosureStateTransition(
                capability_id=capability_id,
                from_state=PrivateDisclosureState.PENDING,
                to_state=PrivateDisclosureState.DISCLOSING,
                expected_version=expected_version,
                next_version=expected_version + 1,
            )
            updated = attempt.model_copy(
                update={"state": transition.to_state, "version": transition.next_version}
            )
            self._attempts[capability_id] = updated
            self.history.append("cas:pending->disclosing")
            self._commit()
            return updated
        except Exception:
            self._rollback()
            raise

    def finalize_disclosed(
        self,
        *,
        capability_id: str,
        expected_version: int,
        receipt: PrivateProcessingReceipt,
    ) -> PrivateDisclosureAttempt:
        self._begin()
        try:
            attempt = self._require_disclosing(capability_id, expected_version)
            transition = PrivateDisclosureStateTransition(
                capability_id=capability_id,
                from_state=PrivateDisclosureState.DISCLOSING,
                to_state=PrivateDisclosureState.DISCLOSED,
                expected_version=expected_version,
                next_version=expected_version + 1,
            )
            updated = attempt.model_copy(
                update={
                    "state": transition.to_state,
                    "version": transition.next_version,
                    "receipt": receipt,
                }
            )
            self._attempts[capability_id] = updated
            self.history.append("cas:disclosing->disclosed")
            self._commit()
            return updated
        except Exception:
            self._rollback()
            raise

    def finalize_failed_unknown(
        self,
        *,
        capability_id: str,
        expected_version: int,
        refusal: PrivateProcessingRefusal,
    ) -> PrivateDisclosureAttempt:
        self._begin()
        try:
            attempt = self._require_disclosing(capability_id, expected_version)
            transition = PrivateDisclosureStateTransition(
                capability_id=capability_id,
                from_state=PrivateDisclosureState.DISCLOSING,
                to_state=PrivateDisclosureState.FAILED_UNKNOWN,
                expected_version=expected_version,
                next_version=expected_version + 1,
            )
            updated = attempt.model_copy(
                update={
                    "state": transition.to_state,
                    "version": transition.next_version,
                    "refusal": refusal,
                }
            )
            self._attempts[capability_id] = updated
            self.history.append("cas:disclosing->failed_unknown")
            self._commit()
            return updated
        except Exception:
            self._rollback()
            raise

    def _require_disclosing(self, capability_id: str, expected_version: int) -> PrivateDisclosureAttempt:
        attempt = self._attempts.get(capability_id)
        if (
            attempt is None
            or attempt.state is not PrivateDisclosureState.DISCLOSING
            or attempt.version != expected_version
        ):
            raise PrivateDisclosureCasConflict("private disclosure finalization conflict")
        return attempt

    def _begin(self) -> None:
        if self.transaction_open:
            raise RuntimeError("nested private disclosure transaction")
        self.transaction_open = True
        self.history.append("begin")

    def _commit(self) -> None:
        self.transaction_open = False
        self.history.append("commit")

    def _rollback(self) -> None:
        if self.transaction_open:
            self.transaction_open = False
            self.history.append("rollback")


AdapterCallback = Callable[[PrivateProviderContextRequest], object]
PrivateExcerptLoader = Callable[[PrivateContextPersistentDisclosureRequest], PrivateContextExcerptPayload | None]


class PrivateContextBroker:
    def __init__(
        self,
        *,
        store: InMemoryPrivateDisclosureStore,
        adapter_callback: AdapterCallback,
        private_excerpt_loader: PrivateExcerptLoader | None = None,
    ) -> None:
        self.store = store
        self.adapter_callback = adapter_callback
        self.private_excerpt_loader = private_excerpt_loader

    def disclose(self, request: PrivateContextDisclosureRequest) -> PrivateContextBrokerResult:
        if request.capability is None:
            return PrivateContextBrokerResult(
                status="refused",
                refusal=PrivateProcessingRefusal.for_capability(
                    PrivateProcessingRefusalReason.MISSING_CAPABILITY,
                    None,
                ),
            )
        context = self._derive_or_refuse(request)
        if isinstance(context, PrivateProcessingRefusal):
            return PrivateContextBrokerResult(status="refused", refusal=context)

        refusal = validate_private_processing_capability(
            request.capability,
            job_id=request.job_id,
            run_id=request.run_id,
            item_id=request.item_id,
            excerpt_revision_id=request.excerpt_revision_id,
            excerpt_sha256=request.excerpt_sha256,
            target_start=request.target_start,
            target_end=request.target_end,
            target_text_sha256=request.target_text_sha256,
            provider=request.provider,
            model=request.model,
            route_id=request.route_id,
            provider_route_sha256=request.provider_route_sha256,
            purpose=request.purpose,
            policy_sha256=request.policy_sha256,
            now=request.now,
        )
        if refusal is not None:
            return PrivateContextBrokerResult(status="refused", refusal=refusal)

        budget_refusal = self._validate_context_budget(request.capability, context)
        if budget_refusal is not None:
            return PrivateContextBrokerResult(status="refused", refusal=budget_refusal)

        attempt = self.store.get_attempt(request.capability.capability_id)
        replay = self._replay_result(request.capability, attempt)
        if replay is not None:
            return replay

        try:
            reserved = self.store.reserve_disclosure(
                capability_id=request.capability.capability_id,
                expected_version=request.expected_attempt_version,
            )
        except PrivateDisclosureCasConflict:
            return PrivateContextBrokerResult(
                status="refused",
                refusal=PrivateProcessingRefusal.for_capability(
                    PrivateProcessingRefusalReason.CAS_CONFLICT,
                    request.capability,
                ),
            )

        provider_request = PrivateProviderContextRequest(
            capability_id=request.capability.capability_id,
            context=context.context,
            context_sha256=context.context_sha256,
            token_count=context.token_count,
            provider_id=request.capability.provider_id,
            provider=request.capability.provider,
            model=request.capability.model,
            route_id=request.capability.route_id,
            provider_route_sha256=request.capability.provider_route_sha256,
            purpose=request.capability.purpose,
            policy_sha256=request.capability.policy_sha256,
            idempotency_key=request.capability.idempotency.key,
        )
        return self._call_and_finalize(request.capability, reserved, context, provider_request)

    def disclose_persistent(
        self,
        request: PrivateContextPersistentDisclosureRequest,
    ) -> PrivateContextBrokerResult:
        if request.capability is None:
            return PrivateContextBrokerResult(
                status="refused",
                refusal=PrivateProcessingRefusal.for_capability(
                    PrivateProcessingRefusalReason.MISSING_CAPABILITY,
                    None,
                ),
            )
        refusal = self._validate_persistent_authority(request)
        if refusal is not None:
            return PrivateContextBrokerResult(status="refused", refusal=refusal)

        attempt = self.store.get_attempt(request.capability.capability_id)
        replay = self._replay_result(request.capability, attempt)
        if replay is not None:
            return replay

        try:
            reserved = self.store.reserve_disclosure(
                capability_id=request.capability.capability_id,
                expected_version=request.expected_attempt_version,
            )
        except PrivateDisclosureCasConflict:
            return PrivateContextBrokerResult(
                status="refused",
                refusal=PrivateProcessingRefusal.for_capability(
                    PrivateProcessingRefusalReason.CAS_CONFLICT,
                    request.capability,
                ),
            )

        payload = self._load_private_excerpt(request)
        if payload is None:
            return self._finalize_failed_unknown(
                request.capability,
                reserved,
                PrivateProcessingRefusalReason.STALE_EXCERPT,
            )
        if private_text_sha256(payload.target_text) != request.target_text_sha256:
            return self._finalize_failed_unknown(
                request.capability,
                reserved,
                PrivateProcessingRefusalReason.TARGET_MISMATCH,
            )
        try:
            context = derive_bounded_private_context(
                excerpt_text=payload.excerpt_text,
                target_start=request.target_start,
                target_end=request.target_end,
                target_text=payload.target_text,
                max_context_tokens=request.capability.max_context_tokens,
            )
        except PrivateContextDerivationError as exc:
            return self._finalize_failed_unknown(request.capability, reserved, exc.reason_code)

        budget_refusal = self._validate_context_budget(request.capability, context)
        if budget_refusal is not None:
            return self._finalize_failed_unknown(request.capability, reserved, budget_refusal.reason_code)

        provider_request = PrivateProviderContextRequest(
            capability_id=request.capability.capability_id,
            context=context.context,
            context_sha256=context.context_sha256,
            token_count=context.token_count,
            provider_id=request.capability.provider_id,
            provider=request.capability.provider,
            model=request.capability.model,
            route_id=request.capability.route_id,
            provider_route_sha256=request.capability.provider_route_sha256,
            purpose=request.capability.purpose,
            policy_sha256=request.capability.policy_sha256,
            idempotency_key=request.capability.idempotency.key,
        )
        self._release_store_transaction()
        return self._call_and_finalize(request.capability, reserved, context, provider_request)

    def _validate_persistent_authority(
        self,
        request: PrivateContextPersistentDisclosureRequest,
    ) -> PrivateProcessingRefusal | None:
        return validate_private_processing_capability(
            request.capability,
            job_id=request.job_id,
            run_id=request.run_id,
            item_id=request.item_id,
            excerpt_revision_id=request.excerpt_revision_id,
            excerpt_sha256=request.excerpt_sha256,
            target_start=request.target_start,
            target_end=request.target_end,
            target_text_sha256=request.target_text_sha256,
            provider=request.provider,
            model=request.model,
            route_id=request.route_id,
            provider_route_sha256=request.provider_route_sha256,
            purpose=request.purpose,
            policy_sha256=request.policy_sha256,
            now=request.now,
        )

    def _load_private_excerpt(
        self,
        request: PrivateContextPersistentDisclosureRequest,
    ) -> PrivateContextExcerptPayload | None:
        if self.private_excerpt_loader is None:
            return None
        raw_payload = self.private_excerpt_loader(request)
        if raw_payload is None:
            return None
        return PrivateContextExcerptPayload.model_validate(raw_payload)

    def _release_store_transaction(self) -> None:
        release = getattr(self.store, "release_transaction", None)
        if callable(release):
            release()

    def _derive_or_refuse(
        self,
        request: PrivateContextDisclosureRequest,
    ) -> PrivateContextArtifact | PrivateProcessingRefusal:
        if request.capability is None:
            return PrivateProcessingRefusal.for_capability(
                PrivateProcessingRefusalReason.MISSING_CAPABILITY,
                None,
            )
        try:
            return derive_bounded_private_context(
                excerpt_text=request.excerpt_text,
                target_start=request.target_start,
                target_end=request.target_end,
                target_text=request.target_text,
                max_context_tokens=request.capability.max_context_tokens,
            )
        except PrivateContextDerivationError as exc:
            return PrivateProcessingRefusal.for_capability(exc.reason_code, request.capability)

    def _validate_context_budget(
        self,
        capability: PrivateProcessingCapability,
        context: PrivateContextArtifact,
    ) -> PrivateProcessingRefusal | None:
        if (
            context.token_count > capability.max_context_tokens
            or context.token_count > MAX_PRIVATE_CONTEXT_TOKENS
            or context.code_point_count > capability.max_context_code_points
            or context.utf8_byte_count > capability.max_context_utf8_bytes
        ):
            return PrivateProcessingRefusal.for_capability(
                PrivateProcessingRefusalReason.CONTEXT_OVER_BUDGET,
                capability,
            )
        return None

    def _replay_result(
        self,
        capability: PrivateProcessingCapability,
        attempt: PrivateDisclosureAttempt | None,
    ) -> PrivateContextBrokerResult | None:
        if attempt is None:
            return PrivateContextBrokerResult(
                status="refused",
                refusal=PrivateProcessingRefusal.for_capability(
                    PrivateProcessingRefusalReason.MISSING_CAPABILITY,
                    capability,
                ),
            )
        if attempt.state is PrivateDisclosureState.PENDING:
            return None
        if attempt.state is PrivateDisclosureState.DISCLOSED and attempt.receipt is not None:
            return PrivateContextBrokerResult(status="disclosed", receipt=attempt.receipt)
        return PrivateContextBrokerResult(
            status="inspect_required",
            refusal=PrivateProcessingRefusal.for_capability(
                PrivateProcessingRefusalReason.REPLAY_OR_CLOSED_STATE,
                capability,
            ),
        )

    def _call_and_finalize(
        self,
        capability: PrivateProcessingCapability,
        reserved: PrivateDisclosureAttempt,
        context: PrivateContextArtifact,
        provider_request: PrivateProviderContextRequest,
    ) -> PrivateContextBrokerResult:
        for attempt_index in range(1, capability.max_provider_attempts + 1):
            result = self._call_adapter(provider_request)
            if result is None:
                return self._finalize_failed_unknown(
                    capability,
                    reserved,
                    PrivateProcessingRefusalReason.UNSAFE_PROVIDER_OUTPUT,
                )
            if result.status == "success":
                if result.output_sha256 == provider_request.context_sha256:
                    return self._finalize_failed_unknown(
                        capability,
                        reserved,
                        PrivateProcessingRefusalReason.UNSAFE_PROVIDER_OUTPUT,
                    )
                receipt = PrivateProcessingReceipt.for_disclosure(
                    capability=capability,
                    context_sha256=context.context_sha256,
                    context_token_count=context.token_count,
                    context_code_point_count=context.code_point_count,
                    context_utf8_byte_count=context.utf8_byte_count,
                    idempotency_key=capability.idempotency.key,
                )
                self.store.finalize_disclosed(
                    capability_id=capability.capability_id,
                    expected_version=reserved.version,
                    receipt=receipt,
                )
                return PrivateContextBrokerResult(status="disclosed", receipt=receipt)
            if (
                result.status == "unknown"
                and capability.idempotency.support == "supported"
                and attempt_index < capability.max_provider_attempts
            ):
                continue
            return self._finalize_failed_unknown(
                capability,
                reserved,
                PrivateProcessingRefusalReason.PROVIDER_UNKNOWN_RESULT,
            )
        return self._finalize_failed_unknown(
            capability,
            reserved,
            PrivateProcessingRefusalReason.PROVIDER_UNKNOWN_RESULT,
        )

    def _call_adapter(
        self,
        provider_request: PrivateProviderContextRequest,
    ) -> PrivateProviderCallbackResult | None:
        try:
            raw_result = self.adapter_callback(provider_request)
        except (PrivateProviderUnknownResult, TimeoutError):
            return PrivateProviderCallbackResult(status="unknown", output_sha256="0" * 64)
        except Exception:
            return PrivateProviderCallbackResult(status="unknown", output_sha256="0" * 64)
        try:
            return PrivateProviderCallbackResult.model_validate(raw_result)
        except ValidationError:
            return None

    def _finalize_failed_unknown(
        self,
        capability: PrivateProcessingCapability,
        reserved: PrivateDisclosureAttempt,
        reason_code: PrivateProcessingRefusalReason,
    ) -> PrivateContextBrokerResult:
        refusal = PrivateProcessingRefusal.for_capability(reason_code, capability)
        self.store.finalize_failed_unknown(
            capability_id=capability.capability_id,
            expected_version=reserved.version,
            refusal=refusal,
        )
        return PrivateContextBrokerResult(status="failed_unknown", refusal=refusal)


def normalize_private_context_text(value: str) -> str:
    return normalize_private_text(value)


def derive_bounded_private_context(
    *,
    excerpt_text: str,
    target_start: int,
    target_end: int,
    target_text: str,
    max_context_tokens: int,
) -> PrivateContextArtifact:
    if max_context_tokens < 1 or max_context_tokens > MAX_PRIVATE_CONTEXT_TOKENS:
        raise PrivateContextDerivationError(PrivateProcessingRefusalReason.CONTEXT_OVER_BUDGET)
    excerpt = normalize_private_context_text(excerpt_text)
    target = normalize_private_context_text(target_text)
    if target_start < 0 or target_end <= target_start or target_end > len(excerpt):
        raise PrivateContextDerivationError(PrivateProcessingRefusalReason.INVALID_TARGET_SPAN)
    if excerpt[target_start:target_end] != target:
        if target not in excerpt:
            raise PrivateContextDerivationError(PrivateProcessingRefusalReason.TARGET_ABSENT)
        found_at = excerpt.find(target)
        if found_at != excerpt.rfind(target):
            raise PrivateContextDerivationError(PrivateProcessingRefusalReason.INVALID_TARGET_SPAN)
        target_start = found_at
        target_end = found_at + len(target)

    tokens = tokenize_private_context_v1(excerpt)
    target_indexes = tuple(
        index
        for index, token in enumerate(tokens)
        if token.start < target_end and token.end > target_start
    )
    if not target_indexes:
        raise PrivateContextDerivationError(PrivateProcessingRefusalReason.INVALID_TARGET_SPAN)
    if len(target_indexes) > max_context_tokens:
        raise PrivateContextDerivationError(PrivateProcessingRefusalReason.CONTEXT_OVER_BUDGET)

    left = target_indexes[0]
    right = target_indexes[-1]
    remaining = max_context_tokens - len(target_indexes)
    while remaining > 0 and (left > 0 or right < len(tokens) - 1):
        if left > 0:
            left -= 1
            remaining -= 1
        if remaining > 0 and right < len(tokens) - 1:
            right += 1
            remaining -= 1

    context = excerpt[tokens[left].start : tokens[right].end].strip()
    return PrivateContextArtifact(
        context=context,
        context_sha256=private_text_sha256(context),
        token_count=count_private_context_tokens_v1(context),
        code_point_count=len(context),
        utf8_byte_count=len(context.encode("utf-8")),
        target_start=max(0, target_start - tokens[left].start),
        target_end=max(0, target_end - tokens[left].start),
    )


__all__ = [
    "InMemoryPrivateDisclosureStore",
    "PrivateContextArtifact",
    "PrivateContextBroker",
    "PrivateContextBrokerResult",
    "PrivateContextDerivationError",
    "PrivateContextDisclosureRequest",
    "PrivateContextExcerptPayload",
    "PrivateContextPersistentDisclosureRequest",
    "PrivateDisclosureCasConflict",
    "PrivateProviderCallbackResult",
    "PrivateProviderContextRequest",
    "PrivateProviderUnknownResult",
    "derive_bounded_private_context",
    "normalize_private_context_text",
]
