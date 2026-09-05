"""SQLAlchemy repository for exact private-processing disclosure authority."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from multilang.db.models import (
    PrivateContextCapabilityModel,
    PrivateDisclosureAttemptModel,
    PrivateProcessingReceiptModel,
)
from multilang.domain.private_processing import (
    MAX_PRIVATE_CONTEXT_TOKENS,
    PRIVATE_TOKENIZATION_RULE_ID,
    PrivateDisclosureAttempt,
    PrivateDisclosureState,
    PrivateProcessingCapability,
    PrivateProcessingPolicy,
    PrivateProcessingReceipt,
    PrivateProcessingRefusal,
    PrivateProcessingRefusalReason,
    PrivateProviderIdempotency,
    private_text_sha256,
)
from multilang.services.private_context import PrivateDisclosureCasConflict


class PrivateProcessingRepositoryConflict(PrivateDisclosureCasConflict):
    """A capability, reservation, or finalization CAS expectation was not current."""


class PrivateProcessingRepositoryValidationError(ValueError):
    """A private-processing request exceeded the locked policy bounds."""


class PrivateProcessingRepository:
    """Persistent capability store with content-free attempts and receipts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def issue_capability(
        self,
        *,
        job_id: str,
        run_id: str,
        item_id: str,
        excerpt_revision_id: str,
        excerpt_sha256: str,
        target_start: int,
        target_end: int,
        target_text_sha256: str,
        provider_id: str,
        provider: str,
        model: str,
        route_id: str,
        provider_route_sha256: str,
        purpose: str,
        policy: PrivateProcessingPolicy,
        actual_context_token_count: int,
        idempotency: PrivateProviderIdempotency,
        issued_at: datetime,
        expires_at: datetime,
        issuer_id: str,
        issuer_intent_sha256: str,
    ) -> PrivateProcessingCapability:
        self._validate_issue_policy(policy, actual_context_token_count)
        idempotency_key_sha256 = private_text_sha256(idempotency.key) if idempotency.key else None
        payload = {
            "job_id": job_id,
            "run_id": run_id,
            "item_id": item_id,
            "excerpt_revision_id": excerpt_revision_id,
            "excerpt_sha256": excerpt_sha256,
            "target_start": target_start,
            "target_end": target_end,
            "target_text_sha256": target_text_sha256,
            "provider_id": provider_id,
            "provider": provider,
            "model": model,
            "route_id": route_id,
            "provider_route_sha256": provider_route_sha256,
            "purpose": purpose,
            "policy_version": policy.policy_version,
            "policy_sha256": policy.policy_sha256,
            "tokenization_rule_id": policy.tokenization_rule_id,
            "max_context_tokens": policy.max_context_tokens,
            "max_context_code_points": policy.max_context_code_points,
            "max_context_utf8_bytes": policy.max_context_utf8_bytes,
            "max_provider_attempts": policy.max_provider_attempts,
            "max_estimated_cost_usd": policy.max_estimated_cost_usd,
            "idempotency_support": idempotency.support,
            "idempotency_key_sha256": idempotency_key_sha256,
            "issuer_id": issuer_id,
            "issuer_intent_sha256": issuer_intent_sha256,
            "issued_at": _datetime_key(issued_at),
            "expires_at": _datetime_key(expires_at),
            "actual_context_token_count": actual_context_token_count,
        }
        existing = self._existing_idempotent_capability(idempotency_key_sha256)
        if existing is not None:
            if self._stored_issue_payload(existing) == payload:
                return _capability_from_row(existing, idempotency_key=idempotency.key)
            raise PrivateProcessingRepositoryConflict("private capability idempotency conflict")

        capability = PrivateProcessingCapability(
            capability_id="cap-" + uuid4().hex,
            job_id=job_id,
            run_id=run_id,
            item_id=item_id,
            excerpt_revision_id=excerpt_revision_id,
            excerpt_sha256=excerpt_sha256,
            target_start=target_start,
            target_end=target_end,
            target_text_sha256=target_text_sha256,
            provider_id=provider_id,
            provider=provider,
            model=model,
            route_id=route_id,
            provider_route_sha256=provider_route_sha256,
            purpose=purpose,
            policy_version=policy.policy_version,
            policy_sha256=policy.policy_sha256,
            tokenization_rule_id=policy.tokenization_rule_id,
            max_context_tokens=policy.max_context_tokens,
            max_context_code_points=policy.max_context_code_points,
            max_context_utf8_bytes=policy.max_context_utf8_bytes,
            max_provider_attempts=policy.max_provider_attempts,
            max_estimated_cost_usd=policy.max_estimated_cost_usd,
            idempotency=idempotency,
            issued_at=issued_at,
            expires_at=expires_at,
            issuer_id=issuer_id,
            issuer_intent_sha256=issuer_intent_sha256,
            state=PrivateDisclosureState.PENDING,
            version=0,
        )
        self.session.add(_capability_model(capability, idempotency_key_sha256))
        self.session.add(
            PrivateDisclosureAttemptModel(
                id=str(uuid4()),
                capability_id=capability.capability_id,
                state=PrivateDisclosureState.PENDING.value,
                version=0,
                context_sha256=None,
                context_token_count=actual_context_token_count,
                refusal_reason_code=None,
                attempted_at=None,
                processed_at=None,
            )
        )
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            existing_after_conflict = self._existing_idempotent_capability(idempotency_key_sha256)
            if (
                existing_after_conflict is not None
                and self._stored_issue_payload(existing_after_conflict) == payload
            ):
                return _capability_from_row(existing_after_conflict, idempotency_key=idempotency.key)
            raise PrivateProcessingRepositoryConflict("private capability conflict") from exc
        return capability

    def get_attempt(self, capability_id: str) -> PrivateDisclosureAttempt | None:
        row = self.session.scalar(
            select(PrivateDisclosureAttemptModel)
            .where(PrivateDisclosureAttemptModel.capability_id == capability_id)
            .order_by(PrivateDisclosureAttemptModel.version.desc())
            .limit(1)
        )
        if row is None:
            return None
        return self._attempt_from_row(row)

    def reserve_disclosure(
        self,
        *,
        capability_id: str,
        expected_version: int,
        context_sha256: str | None = None,
        context_token_count: int | None = None,
    ) -> PrivateDisclosureAttempt:
        if context_token_count is not None and not 1 <= context_token_count <= MAX_PRIVATE_CONTEXT_TOKENS:
            raise PrivateProcessingRepositoryValidationError("context token count exceeds private token cap")
        if context_sha256 is not None:
            _require_sha256(context_sha256, "context_sha256")
        next_version = expected_version + 1
        updated = self.session.execute(
            update(PrivateContextCapabilityModel)
            .where(
                PrivateContextCapabilityModel.capability_id == capability_id,
                PrivateContextCapabilityModel.state == PrivateDisclosureState.PENDING.value,
                PrivateContextCapabilityModel.version == expected_version,
            )
            .values(state=PrivateDisclosureState.DISCLOSING.value, version=next_version)
        ).rowcount
        if updated != 1:
            self.session.rollback()
            raise PrivateProcessingRepositoryConflict("private disclosure reservation conflict")
        attempt = PrivateDisclosureAttemptModel(
            id=str(uuid4()),
            capability_id=capability_id,
            state=PrivateDisclosureState.DISCLOSING.value,
            version=next_version,
            context_sha256=context_sha256,
            context_token_count=context_token_count,
            refusal_reason_code=None,
            attempted_at=_now_utc(),
            processed_at=None,
        )
        self.session.add(attempt)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise PrivateProcessingRepositoryConflict("private disclosure reservation conflict") from exc
        return self._attempt_from_row(attempt)

    def finalize_disclosed(
        self,
        *,
        capability_id: str,
        expected_version: int,
        receipt: PrivateProcessingReceipt,
    ) -> PrivateDisclosureAttempt:
        next_version = expected_version + 1
        updated = self.session.execute(
            update(PrivateContextCapabilityModel)
            .where(
                PrivateContextCapabilityModel.capability_id == capability_id,
                PrivateContextCapabilityModel.state == PrivateDisclosureState.DISCLOSING.value,
                PrivateContextCapabilityModel.version == expected_version,
            )
            .values(state=PrivateDisclosureState.DISCLOSED.value, version=next_version)
        ).rowcount
        if updated != 1:
            self.session.rollback()
            raise PrivateProcessingRepositoryConflict("private disclosure finalization conflict")
        self.session.add(
            PrivateProcessingReceiptModel(
                id=str(uuid4()),
                receipt_id=receipt.receipt_id,
                capability_id=capability_id,
                receipt_sha256=receipt.receipt_sha256,
                context_sha256=receipt.context_sha256,
                context_token_count=receipt.context_token_count,
                provider=receipt.provider,
                model=receipt.model,
                route_id=receipt.route_id,
                policy_sha256=receipt.policy_sha256,
            )
        )
        attempt = PrivateDisclosureAttemptModel(
            id=str(uuid4()),
            capability_id=capability_id,
            state=PrivateDisclosureState.DISCLOSED.value,
            version=next_version,
            context_sha256=receipt.context_sha256,
            context_token_count=receipt.context_token_count,
            refusal_reason_code=None,
            attempted_at=None,
            processed_at=_now_utc(),
        )
        self.session.add(attempt)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise PrivateProcessingRepositoryConflict("private disclosure finalization conflict") from exc
        return self._attempt_from_row(attempt)

    def finalize_failed_unknown(
        self,
        *,
        capability_id: str,
        expected_version: int,
        refusal: PrivateProcessingRefusal | None = None,
        refusal_reason: PrivateProcessingRefusalReason | None = None,
    ) -> PrivateDisclosureAttempt:
        reason = refusal.reason_code if refusal is not None else refusal_reason
        if reason is None:
            raise PrivateProcessingRepositoryValidationError("failed_unknown requires a refusal reason")
        next_version = expected_version + 1
        updated = self.session.execute(
            update(PrivateContextCapabilityModel)
            .where(
                PrivateContextCapabilityModel.capability_id == capability_id,
                PrivateContextCapabilityModel.state == PrivateDisclosureState.DISCLOSING.value,
                PrivateContextCapabilityModel.version == expected_version,
            )
            .values(state=PrivateDisclosureState.FAILED_UNKNOWN.value, version=next_version)
        ).rowcount
        if updated != 1:
            self.session.rollback()
            raise PrivateProcessingRepositoryConflict("private disclosure finalization conflict")
        attempt = PrivateDisclosureAttemptModel(
            id=str(uuid4()),
            capability_id=capability_id,
            state=PrivateDisclosureState.FAILED_UNKNOWN.value,
            version=next_version,
            context_sha256=None,
            context_token_count=None,
            refusal_reason_code=reason.value,
            attempted_at=None,
            processed_at=_now_utc(),
        )
        self.session.add(attempt)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise PrivateProcessingRepositoryConflict("private disclosure finalization conflict") from exc
        return self._attempt_from_row(attempt)

    def release_transaction(self) -> None:
        if self.session.in_transaction():
            self.session.rollback()

    def _validate_issue_policy(self, policy: PrivateProcessingPolicy, actual_context_token_count: int) -> None:
        if policy.tokenization_rule_id != PRIVATE_TOKENIZATION_RULE_ID:
            raise PrivateProcessingRepositoryValidationError("unsupported private tokenization rule")
        if policy.max_context_tokens < 1 or policy.max_context_tokens > MAX_PRIVATE_CONTEXT_TOKENS:
            raise PrivateProcessingRepositoryValidationError("private context token cap exceeds 24")
        if actual_context_token_count < 1 or actual_context_token_count > policy.max_context_tokens:
            raise PrivateProcessingRepositoryValidationError("actual context token count exceeds capability cap")

    def _existing_idempotent_capability(
        self,
        idempotency_key_sha256: str | None,
    ) -> PrivateContextCapabilityModel | None:
        if idempotency_key_sha256 is None:
            return None
        return self.session.scalar(
            select(PrivateContextCapabilityModel).where(
                PrivateContextCapabilityModel.idempotency_key_sha256 == idempotency_key_sha256
            )
        )

    def _stored_issue_payload(self, row: PrivateContextCapabilityModel) -> dict[str, object]:
        initial_attempt = self.session.scalar(
            select(PrivateDisclosureAttemptModel).where(
                PrivateDisclosureAttemptModel.capability_id == row.capability_id,
                PrivateDisclosureAttemptModel.version == 0,
            )
        )
        return {
            "job_id": row.job_id,
            "run_id": row.run_id,
            "item_id": row.item_id,
            "excerpt_revision_id": row.excerpt_revision_id,
            "excerpt_sha256": row.excerpt_sha256,
            "target_start": row.target_start,
            "target_end": row.target_end,
            "target_text_sha256": row.target_text_sha256,
            "provider_id": row.provider_id,
            "provider": row.provider,
            "model": row.model,
            "route_id": row.route_id,
            "provider_route_sha256": row.provider_route_sha256,
            "purpose": row.purpose,
            "policy_version": row.policy_version,
            "policy_sha256": row.policy_sha256,
            "tokenization_rule_id": row.tokenization_rule_id,
            "max_context_tokens": row.max_context_tokens,
            "max_context_code_points": row.max_context_code_points,
            "max_context_utf8_bytes": row.max_context_utf8_bytes,
            "max_provider_attempts": row.max_provider_attempts,
            "max_estimated_cost_usd": row.max_estimated_cost_usd,
            "idempotency_support": row.idempotency_support,
            "idempotency_key_sha256": row.idempotency_key_sha256,
            "issuer_id": row.issuer_id,
            "issuer_intent_sha256": row.issuer_intent_sha256,
            "issued_at": _datetime_key(row.issued_at),
            "expires_at": _datetime_key(row.expires_at),
            "actual_context_token_count": initial_attempt.context_token_count if initial_attempt is not None else None,
        }

    def _attempt_from_row(self, row: PrivateDisclosureAttemptModel) -> PrivateDisclosureAttempt:
        receipt = None
        refusal = None
        if row.state == PrivateDisclosureState.DISCLOSED.value:
            receipt_model = self.session.scalar(
                select(PrivateProcessingReceiptModel).where(PrivateProcessingReceiptModel.capability_id == row.capability_id)
            )
            capability_model = self._capability_model(row.capability_id)
            if receipt_model is not None and capability_model is not None:
                receipt = _receipt_from_rows(capability_model, receipt_model)
        elif row.state == PrivateDisclosureState.FAILED_UNKNOWN.value and row.refusal_reason_code is not None:
            capability_model = self._capability_model(row.capability_id)
            refusal = PrivateProcessingRefusal(
                reason_code=PrivateProcessingRefusalReason(row.refusal_reason_code),
                capability_id_sha256=private_text_sha256(row.capability_id),
                policy_sha256=capability_model.policy_sha256 if capability_model is not None else None,
            )
        return PrivateDisclosureAttempt(
            capability_id=row.capability_id,
            state=PrivateDisclosureState(row.state),
            version=row.version,
            receipt=receipt,
            refusal=refusal,
        )

    def _capability_model(self, capability_id: str) -> PrivateContextCapabilityModel | None:
        return self.session.scalar(
            select(PrivateContextCapabilityModel).where(PrivateContextCapabilityModel.capability_id == capability_id)
        )


def _capability_model(
    capability: PrivateProcessingCapability,
    idempotency_key_sha256: str | None,
) -> PrivateContextCapabilityModel:
    return PrivateContextCapabilityModel(
        id=str(uuid4()),
        capability_id=capability.capability_id,
        job_id=capability.job_id,
        run_id=capability.run_id,
        item_id=capability.item_id,
        excerpt_revision_id=capability.excerpt_revision_id,
        excerpt_sha256=capability.excerpt_sha256,
        target_start=capability.target_start,
        target_end=capability.target_end,
        target_text_sha256=capability.target_text_sha256,
        provider_id=capability.provider_id,
        provider=capability.provider,
        model=capability.model,
        route_id=capability.route_id,
        provider_route_sha256=capability.provider_route_sha256,
        purpose=capability.purpose,
        policy_version=capability.policy_version,
        policy_sha256=capability.policy_sha256,
        tokenization_rule_id=capability.tokenization_rule_id,
        max_context_tokens=capability.max_context_tokens,
        max_context_code_points=capability.max_context_code_points,
        max_context_utf8_bytes=capability.max_context_utf8_bytes,
        max_provider_attempts=capability.max_provider_attempts,
        max_estimated_cost_usd=capability.max_estimated_cost_usd,
        idempotency_support=capability.idempotency.support,
        idempotency_key_sha256=idempotency_key_sha256,
        state=capability.state.value,
        version=capability.version,
        issuer_id=capability.issuer_id,
        issuer_intent_sha256=capability.issuer_intent_sha256,
        issued_at=capability.issued_at,
        expires_at=capability.expires_at,
    )


def _capability_from_row(
    row: PrivateContextCapabilityModel,
    *,
    idempotency_key: str | None,
) -> PrivateProcessingCapability:
    return PrivateProcessingCapability(
        capability_id=row.capability_id,
        job_id=row.job_id,
        run_id=row.run_id,
        item_id=row.item_id,
        excerpt_revision_id=row.excerpt_revision_id,
        excerpt_sha256=row.excerpt_sha256,
        target_start=row.target_start,
        target_end=row.target_end,
        target_text_sha256=row.target_text_sha256,
        provider_id=row.provider_id,
        provider=row.provider,
        model=row.model,
        route_id=row.route_id,
        provider_route_sha256=row.provider_route_sha256,
        purpose=row.purpose,
        policy_version=row.policy_version,
        policy_sha256=row.policy_sha256,
        tokenization_rule_id=row.tokenization_rule_id,
        max_context_tokens=row.max_context_tokens,
        max_context_code_points=row.max_context_code_points,
        max_context_utf8_bytes=row.max_context_utf8_bytes,
        max_provider_attempts=row.max_provider_attempts,
        max_estimated_cost_usd=row.max_estimated_cost_usd,
        idempotency=PrivateProviderIdempotency(support=row.idempotency_support, key=idempotency_key),
        issued_at=_aware_datetime(row.issued_at),
        expires_at=_aware_datetime(row.expires_at),
        issuer_id=row.issuer_id,
        issuer_intent_sha256=row.issuer_intent_sha256,
        state=PrivateDisclosureState(row.state),
        version=row.version,
    )


def _receipt_from_rows(
    capability: PrivateContextCapabilityModel,
    receipt: PrivateProcessingReceiptModel,
) -> PrivateProcessingReceipt:
    return PrivateProcessingReceipt(
        receipt_id=receipt.receipt_id,
        capability_id_sha256=private_text_sha256(capability.capability_id),
        job_id_sha256=private_text_sha256(capability.job_id),
        item_id_sha256=private_text_sha256(capability.item_id),
        excerpt_revision_id_sha256=private_text_sha256(capability.excerpt_revision_id),
        excerpt_sha256=capability.excerpt_sha256,
        context_sha256=receipt.context_sha256,
        context_token_count=receipt.context_token_count,
        context_code_point_count=receipt.context_token_count,
        context_utf8_byte_count=receipt.context_token_count,
        provider_id=capability.provider_id,
        provider=receipt.provider,
        model=receipt.model,
        route_id=receipt.route_id,
        provider_route_sha256=capability.provider_route_sha256,
        purpose=capability.purpose,
        policy_version=capability.policy_version,
        policy_sha256=receipt.policy_sha256,
        tokenization_rule_id=capability.tokenization_rule_id,
        idempotency_key_sha256=capability.idempotency_key_sha256,
        state="disclosed",
        receipt_sha256=receipt.receipt_sha256,
    )


def _datetime_key(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _aware_datetime(value).isoformat()


def _aware_datetime(value: datetime | None) -> datetime:
    if value is None:
        raise PrivateProcessingRepositoryValidationError("private capability expiry is required")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise PrivateProcessingRepositoryValidationError(f"{field_name} must be lowercase SHA-256")


__all__ = [
    "PrivateProcessingRepository",
    "PrivateProcessingRepositoryConflict",
    "PrivateProcessingRepositoryValidationError",
]
