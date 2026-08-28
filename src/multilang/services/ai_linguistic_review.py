"""Versioned, provider-neutral contracts for fail-closed AI linguistic review.

This module deliberately has no model/provider client. Model output crosses this
boundary only as closed, hash-bound data and can never override deterministic
validators or populate human-review authority.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import math
import re
from typing import Annotated, Final, Literal, Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_HEX_64: Final = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_MAX_SUBJECTS: Final = 4_096
_MAX_CLAIMS: Final = 64
_MAX_REFERENCES: Final = 64
_MAX_VALIDATORS: Final = 32
NOT_APPLICABLE_SHA256: Final = sha256(b"not_applicable").hexdigest()

AIReviewStatus: TypeAlias = Literal[
    "ai_review_passed",
    "ai_review_failed",
    "blocked_uncertainty",
    "blocked_disagreement",
    "stale",
]
_ReasonCode: TypeAlias = Literal[
    "none",
    "deterministic-validator-failed",
    "atomic-claim-failed",
    "uncertainty-present",
    "missing-pass",
    "unsupported-evidence",
    "low-confidence",
    "correlation-metadata-missing",
    "attempt-cap-exhausted",
    "review-disagreement",
    "source-binding-stale",
    "linguistic-error",
    "curriculum-invalid",
]
_UncertaintyCode: TypeAlias = Literal[
    "source-insufficient",
    "linguistic-ambiguity",
    "confidence-below-threshold",
    "pass-coverage-incomplete",
    "correlation-unknown",
]


class _FrozenReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def _canonical_payload(value: BaseModel | dict[str, object] | object) -> object:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        value = dict(value)
        value.pop("content_hash", None)
    return value


def ai_review_content_hash(value: BaseModel | dict[str, object] | object) -> str:
    """Return SHA-256 over canonical JSON, excluding a top-level content hash."""

    encoded = json.dumps(
        _canonical_payload(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _identifier(value: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError("identifier_invalid")
    return value


def _hash(value: str) -> str:
    if not isinstance(value, str) or _HEX_64.fullmatch(value) is None:
        raise ValueError("sha256_invalid")
    return value


def _timestamp(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp_invalid") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError("timestamp_invalid")
    return value


def _unique_identifiers(values: tuple[str, ...]) -> tuple[str, ...]:
    values = tuple(_identifier(value) for value in values)
    if len(values) != len(set(values)):
        raise ValueError("identifier_set_invalid")
    return values


class AIReviewPolicy(_FrozenReviewModel):
    """Exact bounded policy used by an orchestration run."""

    schema_version: Literal[1]
    policy_id: Literal["multilang-ai-linguistic-review-v1"]
    policy_version: Literal["1"]
    policy_sha256: str
    standard_pass_count: Literal[2]
    critical_pass_count: Literal[3]
    minimum_confidence: float = Field(ge=0.8, le=1.0)
    max_batch_size: Literal[20]
    max_concurrent_invocations: Literal[4]
    required_invocations: Literal[21]
    max_attempts: Literal[42]
    max_input_tokens: Literal[30000]
    max_output_tokens: Literal[12000]
    timeout_seconds: Literal[600]
    repository_provider_spend_usd: Literal[0]
    content_hash: str

    _hashes = field_validator("policy_sha256", "content_hash")(_hash)

    @model_validator(mode="after")
    def policy_must_be_canonical_and_internally_bounded(self) -> Self:
        batches = math.ceil(139 / self.max_batch_size)
        if (
            batches != 7
            or batches * self.critical_pass_count != self.required_invocations
            or self.required_invocations * 2 != self.max_attempts
        ):
            raise ValueError("policy_ceiling_invalid")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


class AIReviewSubject(_FrozenReviewModel):
    """One fixed, tool-less projection bound to all relevant source state."""

    schema_version: Literal[1]
    actor_type: Literal["ai_review_subject"] = "ai_review_subject"
    subject_id: str
    family: Literal["hangul", "pronunciation"]
    item_key: str
    critical: bool
    generator_actor_id: str
    source_pack_version: str
    source_content_sha256: str
    candidate_sha256: str
    analyzer_sha256: str
    curriculum_sha256: str
    media_sha256: str
    claim_ids: tuple[str, ...] = Field(min_length=1, max_length=_MAX_CLAIMS)
    source_reference_ids: tuple[str, ...] = Field(
        min_length=1, max_length=_MAX_REFERENCES
    )
    projection: dict[str, object]
    projection_sha256: str
    content_hash: str

    _identifiers = field_validator(
        "subject_id", "item_key", "generator_actor_id", "source_pack_version"
    )(_identifier)
    _hashes = field_validator(
        "source_content_sha256",
        "candidate_sha256",
        "analyzer_sha256",
        "curriculum_sha256",
        "media_sha256",
        "projection_sha256",
        "content_hash",
    )(_hash)
    _identifier_sets = field_validator("claim_ids", "source_reference_ids")(
        _unique_identifiers
    )

    @model_validator(mode="after")
    def subject_must_be_exact_and_canonical(self) -> Self:
        prefix = "ko-hangul" if self.family == "hangul" else "ko-pron"
        if self.subject_id != self.item_key or not self.item_key.startswith(f"{prefix}-"):
            raise ValueError("subject_identity_invalid")
        exact_hashes = (
            self.source_content_sha256,
            self.candidate_sha256,
            self.analyzer_sha256,
            self.curriculum_sha256,
        )
        if len(set(exact_hashes)) != len(exact_hashes):
            raise ValueError("subject_hashes_not_distinct")
        if self.media_sha256 != NOT_APPLICABLE_SHA256:
            raise ValueError("media_sentinel_invalid")
        if self.projection_sha256 != ai_review_content_hash(self.projection):
            raise ValueError("projection_hash_mismatch")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


class AIValidatorRun(_FrozenReviewModel):
    """One deterministic validator result that AI cannot override."""

    schema_version: Literal[1]
    subject_id: str
    subject_content_sha256: str
    validator_id: str
    validator_version: str
    result: Literal["passed", "failed", "inconclusive"]
    reason_code: str
    executed_at: str
    content_hash: str

    _identifiers = field_validator(
        "subject_id", "validator_id", "validator_version", "reason_code"
    )(_identifier)
    _hashes = field_validator("subject_content_sha256", "content_hash")(_hash)
    _timestamps = field_validator("executed_at")(_timestamp)

    @model_validator(mode="after")
    def validator_result_must_be_controlled(self) -> Self:
        if (self.result == "passed") != (self.reason_code == "none"):
            raise ValueError("validator_reason_invalid")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


class AtomicClaimVerdict(_FrozenReviewModel):
    """A pass-level verdict over one explicitly named atomic claim."""

    schema_version: Literal[1]
    claim_id: str
    verdict: Literal["passed", "failed", "uncertain"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: _ReasonCode
    uncertainty_codes: tuple[_UncertaintyCode, ...] = Field(max_length=8)
    evidence_reference_ids: tuple[str, ...] = Field(max_length=_MAX_REFERENCES)
    content_hash: str

    _identifiers = field_validator("claim_id")(_identifier)
    _hashes = field_validator("content_hash")(_hash)
    _identifier_sets = field_validator("evidence_reference_ids")(_unique_identifiers)

    @field_validator("uncertainty_codes")
    @classmethod
    def uncertainties_must_be_unique(
        cls, values: tuple[_UncertaintyCode, ...]
    ) -> tuple[_UncertaintyCode, ...]:
        if len(values) != len(set(values)):
            raise ValueError("uncertainty_codes_invalid")
        return values

    @model_validator(mode="after")
    def claim_state_must_be_consistent(self) -> Self:
        if self.verdict == "passed" and (
            self.reason_code != "none"
            or self.uncertainty_codes
            or not self.evidence_reference_ids
        ):
            raise ValueError("passed_claim_invalid")
        if self.verdict == "failed" and (
            self.reason_code == "none" or self.uncertainty_codes
        ):
            raise ValueError("failed_claim_invalid")
        if self.verdict == "uncertain" and (
            self.reason_code == "none" or not self.uncertainty_codes
        ):
            raise ValueError("uncertain_claim_invalid")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


class AIReviewDecision(_FrozenReviewModel):
    """One pass decision; consensus is computed separately and never voted."""

    schema_version: Literal[1]
    subject_id: str
    subject_content_sha256: str
    status: AIReviewStatus
    reason_code: _ReasonCode
    uncertainty_codes: tuple[_UncertaintyCode, ...] = Field(max_length=8)
    atomic_claims: tuple[AtomicClaimVerdict, ...] = Field(
        min_length=1, max_length=_MAX_CLAIMS
    )
    content_hash: str

    _identifiers = field_validator("subject_id")(_identifier)
    _hashes = field_validator("subject_content_sha256", "content_hash")(_hash)

    @model_validator(mode="after")
    def decision_must_match_atomic_claims(self) -> Self:
        claim_ids = tuple(claim.claim_id for claim in self.atomic_claims)
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("claim_set_invalid")
        verdicts = {claim.verdict for claim in self.atomic_claims}
        expected = (
            "blocked_uncertainty"
            if "uncertain" in verdicts
            else "ai_review_failed"
            if "failed" in verdicts
            else "ai_review_passed"
        )
        if self.status != expected:
            raise ValueError("decision_status_invalid")
        if self.status == "ai_review_passed" and (
            self.reason_code != "none" or self.uncertainty_codes
        ):
            raise ValueError("passed_decision_invalid")
        if self.status != "ai_review_passed" and self.reason_code == "none":
            raise ValueError("blocking_decision_invalid")
        if self.status == "blocked_uncertainty" and not self.uncertainty_codes:
            raise ValueError("uncertainty_codes_missing")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


class AIReviewAttempt(_FrozenReviewModel):
    """Orchestrator-enriched immutable result from one fresh tool-less context."""

    schema_version: Literal[1]
    actor_type: Literal["ai_model"]
    is_human: Literal[False]
    actor_id: str
    policy_id: Literal["multilang-ai-linguistic-review-v1"]
    policy_version: Literal["1"]
    policy_sha256: str
    route_id: str
    provider_id: str
    provider_api_version: str
    model_id: str
    model_version: str
    prompt_id: str
    prompt_version: str
    prompt_template_sha256: str
    output_schema_id: str
    output_schema_version: str
    output_schema_sha256: str
    execution_surface: Literal["opencode-agent"]
    batch_id: str
    pass_id: str
    fresh_context_id: str
    independence_scope: Literal[
        "fresh_context_same_model", "fresh_context_cross_model"
    ]
    attempt_number: Literal[1, 2]
    started_at: str
    completed_at: str
    subject_content_hashes: tuple[str, ...] = Field(
        min_length=1, max_length=20
    )
    decisions: tuple[AIReviewDecision, ...] = Field(min_length=1, max_length=20)
    content_hash: str

    _identifiers = field_validator(
        "actor_id",
        "route_id",
        "provider_id",
        "provider_api_version",
        "model_id",
        "model_version",
        "prompt_id",
        "prompt_version",
        "output_schema_id",
        "output_schema_version",
        "batch_id",
        "pass_id",
        "fresh_context_id",
    )(_identifier)
    _hashes = field_validator(
        "policy_sha256",
        "prompt_template_sha256",
        "output_schema_sha256",
        "content_hash",
    )(_hash)
    _timestamps = field_validator("started_at", "completed_at")(_timestamp)

    @field_validator("subject_content_hashes")
    @classmethod
    def subject_hashes_must_be_unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = tuple(_hash(value) for value in values)
        if len(values) != len(set(values)):
            raise ValueError("subject_hashes_invalid")
        return values

    @model_validator(mode="after")
    def attempt_must_be_canonical(self) -> Self:
        if self.completed_at < self.started_at:
            raise ValueError("orchestration_time_invalid")
        decision_hashes = tuple(
            decision.subject_content_sha256 for decision in self.decisions
        )
        if decision_hashes != self.subject_content_hashes:
            raise ValueError("attempt_subject_order_invalid")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


class _ConsensusDecision(_FrozenReviewModel):
    schema_version: Literal[1]
    subject_id: str
    subject_content_sha256: str
    status: AIReviewStatus
    reason_code: _ReasonCode
    required_pass_count: int = Field(ge=2, le=3)
    observed_pass_ids: tuple[str, ...] = Field(max_length=3)
    validator_run_hashes: tuple[str, ...] = Field(max_length=_MAX_VALIDATORS)
    attempt_hashes: tuple[str, ...] = Field(max_length=3)
    content_hash: str

    _identifiers = field_validator("subject_id", "reason_code")(_identifier)
    _hashes = field_validator("subject_content_sha256", "content_hash")(_hash)

    @model_validator(mode="after")
    def consensus_decision_must_be_canonical(self) -> Self:
        for values in (self.validator_run_hashes, self.attempt_hashes):
            if any(_HEX_64.fullmatch(value) is None for value in values):
                raise ValueError("consensus_hash_invalid")
        if self.status == "ai_review_passed" and self.reason_code != "none":
            raise ValueError("consensus_reason_invalid")
        if self.status != "ai_review_passed" and self.reason_code == "none":
            raise ValueError("consensus_reason_invalid")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


class AIReviewAggregate(_FrozenReviewModel):
    """Exact aggregate root with passing and blocked coverage kept explicit."""

    schema_version: Literal[1]
    policy_id: Literal["multilang-ai-linguistic-review-v1"]
    policy_version: Literal["1"]
    policy_sha256: str
    policy_content_sha256: str
    candidate_sha256: str
    request_sha256: str
    validator_manifest_sha256: str
    generated_at: str
    total_subjects: int = Field(ge=0, le=_MAX_SUBJECTS)
    passing_subjects: int = Field(ge=0, le=_MAX_SUBJECTS)
    blocked_subjects: int = Field(ge=0, le=_MAX_SUBJECTS)
    status_counts: dict[AIReviewStatus, int]
    decisions: tuple[_ConsensusDecision, ...] = Field(max_length=_MAX_SUBJECTS)
    aggregate_root: str
    content_hash: str

    _hashes = field_validator(
        "policy_sha256",
        "policy_content_sha256",
        "candidate_sha256",
        "request_sha256",
        "validator_manifest_sha256",
        "aggregate_root",
        "content_hash",
    )(_hash)
    _timestamps = field_validator("generated_at")(_timestamp)

    @model_validator(mode="after")
    def aggregate_must_have_exact_coverage_and_root(self) -> Self:
        if self.total_subjects != len(self.decisions):
            raise ValueError("aggregate_coverage_invalid")
        if self.passing_subjects + self.blocked_subjects != self.total_subjects:
            raise ValueError("aggregate_counts_invalid")
        actual_counts = {
            status: sum(decision.status == status for decision in self.decisions)
            for status in (
                "ai_review_passed",
                "ai_review_failed",
                "blocked_uncertainty",
                "blocked_disagreement",
                "stale",
            )
        }
        if self.status_counts != actual_counts:
            raise ValueError("aggregate_status_counts_invalid")
        expected_root = ai_review_content_hash(
            [decision.content_hash for decision in self.decisions]
        )
        if self.aggregate_root != expected_root:
            raise ValueError("aggregate_root_invalid")
        if self.content_hash != ai_review_content_hash(self):
            raise ValueError("content_hash_mismatch")
        return self


def validate_ai_review_attempt(
    attempt: AIReviewAttempt,
    *,
    policy: AIReviewPolicy,
    subjects: tuple[AIReviewSubject, ...],
) -> None:
    """Validate one attempt against trusted policy and exact fixed projections."""

    if (
        attempt.policy_id,
        attempt.policy_version,
        attempt.policy_sha256,
    ) != (policy.policy_id, policy.policy_version, policy.policy_sha256):
        raise ValueError("policy_binding_mismatch")
    if len(subjects) > policy.max_batch_size:
        raise ValueError("batch_size_exceeded")
    if attempt.actor_id in {subject.generator_actor_id for subject in subjects}:
        raise ValueError("generator_reviewer_separation_required")
    if tuple(subject.content_hash for subject in subjects) != attempt.subject_content_hashes:
        raise ValueError("subject_binding_mismatch")
    if tuple(subject.subject_id for subject in subjects) != tuple(
        decision.subject_id for decision in attempt.decisions
    ):
        raise ValueError("subject_order_mismatch")

    for subject, decision in zip(subjects, attempt.decisions, strict=True):
        if decision.subject_content_sha256 != subject.content_hash:
            raise ValueError("subject_binding_mismatch")
        if tuple(claim.claim_id for claim in decision.atomic_claims) != subject.claim_ids:
            raise ValueError("atomic_claim_coverage_mismatch")
        for claim in decision.atomic_claims:
            if not set(claim.evidence_reference_ids).issubset(
                subject.source_reference_ids
            ):
                raise ValueError("unsupported_evidence")
            if claim.verdict == "passed" and claim.confidence < policy.minimum_confidence:
                raise ValueError("low_confidence")


def _consensus_decision(
    *,
    policy: AIReviewPolicy,
    subject: AIReviewSubject,
    validators: tuple[AIValidatorRun, ...],
    attempts: tuple[AIReviewAttempt, ...],
    exhausted: bool = False,
) -> _ConsensusDecision:
    required = policy.critical_pass_count if subject.critical else policy.standard_pass_count
    matching = tuple(
        (attempt, decision)
        for attempt in attempts
        for decision in attempt.decisions
        if decision.subject_id == subject.subject_id
    )
    status: AIReviewStatus
    reason: _ReasonCode
    if not validators or any(run.result != "passed" for run in validators):
        status, reason = "ai_review_failed", "deterministic-validator-failed"
    elif any(run.subject_content_sha256 != subject.content_hash for run in validators):
        status, reason = "stale", "source-binding-stale"
    elif exhausted:
        status, reason = "blocked_uncertainty", "attempt-cap-exhausted"
    elif len(matching) != required:
        status, reason = "blocked_uncertainty", "missing-pass"
    elif len({attempt.pass_id for attempt, _ in matching}) != required:
        status, reason = "blocked_uncertainty", "missing-pass"
    elif len({attempt.fresh_context_id for attempt, _ in matching}) != required:
        status, reason = "blocked_uncertainty", "correlation-metadata-missing"
    elif any(
        attempt.independence_scope
        not in {"fresh_context_same_model", "fresh_context_cross_model"}
        for attempt, _ in matching
    ):
        status, reason = "blocked_uncertainty", "correlation-metadata-missing"
    else:
        verdict_vectors = tuple(
            tuple(claim.verdict for claim in decision.atomic_claims)
            for _, decision in matching
        )
        if len(set(verdict_vectors)) != 1:
            status, reason = "blocked_disagreement", "review-disagreement"
        elif any(verdict == "uncertain" for verdict in verdict_vectors[0]):
            status, reason = "blocked_uncertainty", "uncertainty-present"
        elif any(verdict == "failed" for verdict in verdict_vectors[0]):
            status, reason = "ai_review_failed", "atomic-claim-failed"
        else:
            status, reason = "ai_review_passed", "none"

    payload: dict[str, object] = {
        "schema_version": 1,
        "subject_id": subject.subject_id,
        "subject_content_sha256": subject.content_hash,
        "status": status,
        "reason_code": reason,
        "required_pass_count": required,
        "observed_pass_ids": tuple(attempt.pass_id for attempt, _ in matching),
        "validator_run_hashes": tuple(run.content_hash for run in validators),
        "attempt_hashes": tuple(attempt.content_hash for attempt, _ in matching),
    }
    payload["content_hash"] = ai_review_content_hash(payload)
    return _ConsensusDecision.model_validate(payload)


def build_ai_review_aggregate(
    *,
    policy: AIReviewPolicy,
    subjects: tuple[AIReviewSubject, ...],
    validator_runs: tuple[AIValidatorRun, ...],
    attempts: tuple[AIReviewAttempt, ...],
    candidate_sha256: str,
    request_sha256: str,
    validator_manifest_sha256: str,
    generated_at: str,
    exhausted_subject_ids: tuple[str, ...] = (),
) -> AIReviewAggregate:
    """Compute unanimous consensus; deterministic failure always wins."""

    _hash(candidate_sha256)
    _hash(request_sha256)
    _hash(validator_manifest_sha256)
    _timestamp(generated_at)
    subject_ids = tuple(subject.subject_id for subject in subjects)
    if len(subject_ids) != len(set(subject_ids)):
        raise ValueError("subject_set_invalid")
    if len(exhausted_subject_ids) != len(set(exhausted_subject_ids)) or not set(
        exhausted_subject_ids
    ).issubset(subject_ids):
        raise ValueError("exhausted_subject_set_invalid")
    if any(subject.candidate_sha256 != candidate_sha256 for subject in subjects):
        raise ValueError("candidate_binding_mismatch")
    for attempt in attempts:
        attempt_subjects = tuple(
            subject
            for subject in subjects
            if subject.content_hash in attempt.subject_content_hashes
        )
        validate_ai_review_attempt(
            attempt, policy=policy, subjects=attempt_subjects
        )
    decisions = tuple(
        _consensus_decision(
            policy=policy,
            subject=subject,
            validators=tuple(
                run for run in validator_runs if run.subject_id == subject.subject_id
            ),
            attempts=attempts,
            exhausted=subject.subject_id in exhausted_subject_ids,
        )
        for subject in subjects
    )
    statuses = (
        "ai_review_passed",
        "ai_review_failed",
        "blocked_uncertainty",
        "blocked_disagreement",
        "stale",
    )
    status_counts = {
        status: sum(decision.status == status for decision in decisions)
        for status in statuses
    }
    payload: dict[str, object] = {
        "schema_version": 1,
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "policy_sha256": policy.policy_sha256,
        "policy_content_sha256": policy.content_hash,
        "candidate_sha256": candidate_sha256,
        "request_sha256": request_sha256,
        "validator_manifest_sha256": validator_manifest_sha256,
        "generated_at": generated_at,
        "total_subjects": len(subjects),
        "passing_subjects": status_counts["ai_review_passed"],
        "blocked_subjects": len(subjects) - status_counts["ai_review_passed"],
        "status_counts": status_counts,
        "decisions": [decision.model_dump(mode="json") for decision in decisions],
        "aggregate_root": ai_review_content_hash(
            [decision.content_hash for decision in decisions]
        ),
    }
    payload["content_hash"] = ai_review_content_hash(payload)
    return AIReviewAggregate.model_validate(payload)


__all__ = [
    "AIReviewAggregate",
    "AIReviewAttempt",
    "AIReviewDecision",
    "AIReviewPolicy",
    "AIReviewSubject",
    "AIValidatorRun",
    "AtomicClaimVerdict",
    "NOT_APPLICABLE_SHA256",
    "ai_review_content_hash",
    "build_ai_review_aggregate",
    "validate_ai_review_attempt",
]
