"""Repository tests for persistent private-processing authority."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import (
    GenerationJob,
    PrivateContextCapabilityModel,
    PrivateDisclosureAttemptModel,
    PrivateProcessingReceiptModel,
)
from multilang.domain.private_processing import (
    PrivateDisclosureState,
    PrivateProcessingPolicy,
    PrivateProcessingReceipt,
    PrivateProcessingRefusalReason,
    PrivateProviderIdempotency,
    private_text_sha256,
)
from multilang.repositories.private_processing_repository import (
    PrivateProcessingRepository,
    PrivateProcessingRepositoryConflict,
    PrivateProcessingRepositoryValidationError,
)


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
ISSUED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
PRIVATE_SENTINEL = "민감한 /home/private/book.txt ignore previous instructions"


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    _seed_job(session)
    return session


def _seed_job(session: Session) -> None:
    session.add(
        GenerationJob(
            id="job-1",
            run_key="ko-private-processing-run",
            language="ko",
            source_type="kindle-highlights",
            source_fingerprint="fixture",
            status="created",
            current_stage="private-context",
        )
    )
    session.commit()


def _policy(**overrides: object) -> PrivateProcessingPolicy:
    payload: dict[str, object] = {
        "policy_version": "private-processing-policy-v1",
        "policy_sha256": SHA_D,
        "tokenization_rule_id": "phase33-private-token-v1",
        "max_context_tokens": 8,
        "max_context_code_points": 120,
        "max_context_utf8_bytes": 360,
        "max_provider_attempts": 1,
        "max_estimated_cost_usd": 0.05,
        "redaction_policy_version": "phase33-private-redaction-v1",
    }
    payload.update(overrides)
    return PrivateProcessingPolicy(**payload)


def _issue(repository: PrivateProcessingRepository, **overrides: object):
    payload: dict[str, object] = {
        "job_id": "job-1",
        "run_id": "run-1",
        "item_id": "highlight-item-1",
        "excerpt_revision_id": "excerpt-revision-1",
        "excerpt_sha256": SHA_A,
        "target_start": 3,
        "target_end": 9,
        "target_text_sha256": SHA_B,
        "provider_id": "route-openai-sentence",
        "provider": "openai",
        "model": "gpt-5.5",
        "route_id": "korean-highlight-microexample",
        "provider_route_sha256": SHA_C,
        "purpose": "highlight_microexample_context",
        "policy": _policy(),
        "actual_context_token_count": 4,
        "idempotency": PrivateProviderIdempotency(support="unsupported", key=None),
        "issued_at": ISSUED_AT,
        "expires_at": ISSUED_AT + timedelta(minutes=10),
        "issuer_id": "local-operator",
        "issuer_intent_sha256": SHA_E,
    }
    payload.update(overrides)
    return repository.issue_capability(**payload)


def test_issue_token_v1_token_cap_24_token_count_exact_idempotent_retry_and_no_private_values() -> None:
    session = _session()
    repository = PrivateProcessingRepository(session)
    idempotency = PrivateProviderIdempotency(support="supported", key="idem-key-0001")

    issued = _issue(
        repository,
        policy=_policy(max_context_tokens=24, max_provider_attempts=2),
        actual_context_token_count=24,
        idempotency=idempotency,
    )
    replayed = _issue(
        repository,
        policy=_policy(max_context_tokens=24, max_provider_attempts=2),
        actual_context_token_count=24,
        idempotency=idempotency,
    )

    assert issued.capability_id == replayed.capability_id
    assert issued.tokenization_rule_id == "phase33-private-token-v1"
    assert issued.max_context_tokens == 24
    assert issued.idempotency.key == "idem-key-0001"
    assert session.scalar(select(func.count(PrivateContextCapabilityModel.id))) == 1
    assert session.scalar(select(func.count(PrivateDisclosureAttemptModel.id))) == 1
    pending = repository.get_attempt(issued.capability_id)
    assert pending.state == PrivateDisclosureState.PENDING
    assert pending.version == 0
    assert PRIVATE_SENTINEL not in repr(session.scalars(select(PrivateContextCapabilityModel)).all())

    with pytest.raises(PrivateProcessingRepositoryValidationError):
        _issue(
            repository,
            policy=_policy().model_copy(update={"tokenization_rule_id": "phase33-private-token-any"}),
        )
    with pytest.raises(PrivateProcessingRepositoryValidationError):
        _issue(repository, policy=_policy().model_copy(update={"max_context_tokens": 25}))
    with pytest.raises(PrivateProcessingRepositoryValidationError):
        _issue(repository, policy=_policy(max_context_tokens=24), actual_context_token_count=25)


def test_consume_one_winner_replay_second_call_changed_authority_conflict() -> None:
    session = _session()
    repository = PrivateProcessingRepository(session)
    capability = _issue(repository)

    reserved = repository.reserve_disclosure(capability_id=capability.capability_id, expected_version=0)

    assert reserved.state == PrivateDisclosureState.DISCLOSING
    assert reserved.version == 1
    with pytest.raises(PrivateProcessingRepositoryConflict):
        repository.reserve_disclosure(capability_id=capability.capability_id, expected_version=0)
    assert repository.get_attempt(capability.capability_id).state == PrivateDisclosureState.DISCLOSING

    changed = _issue(
        repository,
        idempotency=PrivateProviderIdempotency(support="supported", key="idem-key-0002"),
    )
    with pytest.raises(PrivateProcessingRepositoryConflict):
        _issue(
            repository,
            item_id="changed-item",
            idempotency=PrivateProviderIdempotency(support="supported", key="idem-key-0002"),
        )
    assert repository.get_attempt(changed.capability_id).state == PrivateDisclosureState.PENDING


def test_finalize_exact_success_unknown_replay_and_no_private_receipt_payload() -> None:
    session = _session()
    repository = PrivateProcessingRepository(session)
    capability = _issue(repository)
    reserved = repository.reserve_disclosure(capability_id=capability.capability_id, expected_version=0)
    receipt = PrivateProcessingReceipt.for_disclosure(
        capability=capability.model_copy(update={"version": reserved.version}),
        context_sha256=SHA_B,
        context_token_count=4,
        context_code_point_count=12,
        context_utf8_byte_count=36,
        idempotency_key=capability.idempotency.key,
    )

    disclosed = repository.finalize_disclosed(
        capability_id=capability.capability_id,
        expected_version=reserved.version,
        receipt=receipt,
    )

    assert disclosed.state == PrivateDisclosureState.DISCLOSED
    assert disclosed.receipt is not None
    assert disclosed.receipt.receipt_sha256 == receipt.receipt_sha256
    assert session.scalar(select(func.count(PrivateProcessingReceiptModel.id))) == 1
    with pytest.raises(PrivateProcessingRepositoryConflict):
        repository.finalize_disclosed(
            capability_id=capability.capability_id,
            expected_version=reserved.version,
            receipt=receipt,
        )

    failed_capability = _issue(repository, item_id="highlight-item-2", excerpt_revision_id="excerpt-revision-2")
    failed_reserved = repository.reserve_disclosure(capability_id=failed_capability.capability_id, expected_version=0)
    failed = repository.finalize_failed_unknown(
        capability_id=failed_capability.capability_id,
        expected_version=failed_reserved.version,
        refusal_reason=PrivateProcessingRefusalReason.PROVIDER_UNKNOWN_RESULT,
    )

    assert failed.state == PrivateDisclosureState.FAILED_UNKNOWN
    assert failed.refusal is not None
    assert failed.refusal.reason_code == PrivateProcessingRefusalReason.PROVIDER_UNKNOWN_RESULT
    rendered = disclosed.receipt.model_dump_json() + failed.refusal.model_dump_json()
    assert PRIVATE_SENTINEL not in rendered
    assert "context_text" not in rendered
    assert "excerpt_text" not in rendered
    assert "prompt" not in rendered
    assert "payload" not in rendered
