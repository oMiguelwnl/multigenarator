"""Bounded Korean text-review import and authority-gated application."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.text_quality import ReviewStatus


_HEX = frozenset("0123456789abcdef")


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanTextReviewBatchDecision(_FrozenModel):
    """One content-free review decision bound to exact item/candidate hashes."""

    job_id: str = Field(min_length=1, max_length=128)
    item_key: str = Field(min_length=1, max_length=255)
    candidate_sha256: str = Field(min_length=64, max_length=64)
    candidate_identity_sha256: str = Field(min_length=64, max_length=64)
    outcome: Literal["accepted", "rejected"]
    rejection_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=16)

    @field_validator("candidate_sha256", "candidate_identity_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("rejection_codes")
    @classmethod
    def rejection_codes_must_be_controlled(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip() for item in value)
        if normalized != value or len(normalized) != len(set(normalized)):
            raise ValueError("rejection_codes must be controlled")
        if any(
            not item
            or len(item) > 64
            or any(not (character.isascii() and (character.isalnum() or character in "._:-")) for character in item)
            for item in normalized
        ):
            raise ValueError("rejection_codes must be controlled")
        return value

    @model_validator(mode="after")
    def decision_must_match_outcome(self) -> "KoreanTextReviewBatchDecision":
        if self.outcome == "accepted" and self.rejection_codes:
            raise ValueError("accepted decision cannot carry rejection codes")
        if self.outcome == "rejected" and not self.rejection_codes:
            raise ValueError("rejected decision requires rejection codes")
        return self


class KoreanTextReviewBatch(_FrozenModel):
    """At-most-100 private review batch, persisted later as content-free hashes."""

    job_id: str = Field(min_length=1, max_length=128)
    production_run_sha256: str = Field(min_length=64, max_length=64)
    review_receipt_sha256: str = Field(min_length=64, max_length=64)
    decisions: tuple[KoreanTextReviewBatchDecision, ...] = Field(min_length=1, max_length=100)

    @field_validator("production_run_sha256", "review_receipt_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def decisions_must_match_job(self) -> "KoreanTextReviewBatch":
        if any(decision.job_id != self.job_id for decision in self.decisions):
            raise ValueError("all text-review decisions must match the batch job")
        return self


class KoreanTextReviewImportResult(_FrozenModel):
    receipt_sha256: str = Field(min_length=64, max_length=64)
    batch_sha256: str = Field(min_length=64, max_length=64)
    job_id: str = Field(min_length=1, max_length=128)
    decision_count: int = Field(ge=0, le=100)
    accepted_count: int = Field(ge=0, le=100)
    rejected_count: int = Field(ge=0, le=100)
    replayed: bool = False


class KoreanTextReviewImportLedger:
    """Small idempotent import ledger used by tests and CLI adapters."""

    def __init__(self) -> None:
        self._receipts: dict[str, KoreanTextReviewImportResult] = {}
        self.write_count = 0

    def import_batch(
        self,
        batch: KoreanTextReviewBatch,
        *,
        current_records: dict[str, object] | None = None,
    ) -> KoreanTextReviewImportResult:
        if batch.review_receipt_sha256 in self._receipts:
            return self._receipts[batch.review_receipt_sha256].model_copy(update={"replayed": True})
        if current_records is not None:
            for decision in batch.decisions:
                record = current_records.get(decision.item_key)
                if record is None:
                    raise ValueError("unknown Korean text-review item")
                if _record_candidate_sha256(record) != decision.candidate_sha256:
                    raise ValueError("stale Korean text review candidate")
        payload = {
            "job_id": batch.job_id,
            "production_run_sha256": batch.production_run_sha256,
            "review_receipt_sha256": batch.review_receipt_sha256,
            "decisions": [
                {
                    "item_key": decision.item_key,
                    "candidate_sha256": decision.candidate_sha256,
                    "candidate_identity_sha256": decision.candidate_identity_sha256,
                    "outcome": decision.outcome,
                    "rejection_codes": decision.rejection_codes,
                }
                for decision in batch.decisions
            ],
        }
        result = KoreanTextReviewImportResult(
            receipt_sha256=batch.review_receipt_sha256,
            batch_sha256=_canonical_sha256(payload),
            job_id=batch.job_id,
            decision_count=len(batch.decisions),
            accepted_count=sum(1 for decision in batch.decisions if decision.outcome == "accepted"),
            rejected_count=sum(1 for decision in batch.decisions if decision.outcome == "rejected"),
        )
        self._receipts[batch.review_receipt_sha256] = result
        self.write_count += 1
        return result


class KoreanTextReviewAggregate(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    production_run_sha256: str = Field(min_length=64, max_length=64)
    aggregate_sha256: str = Field(min_length=64, max_length=64)
    decisions: tuple[KoreanTextReviewBatchDecision, ...] = Field(min_length=1)

    @field_validator("production_run_sha256", "aggregate_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @classmethod
    def from_decisions(
        cls,
        *,
        job_id: str,
        production_run_sha256: str,
        decisions: tuple[KoreanTextReviewBatchDecision, ...],
    ) -> "KoreanTextReviewAggregate":
        payload = {
            "job_id": job_id,
            "production_run_sha256": production_run_sha256,
            "decisions": [decision.model_dump(mode="json") for decision in decisions],
        }
        return cls(
            job_id=job_id,
            production_run_sha256=production_run_sha256,
            aggregate_sha256=_canonical_sha256(payload),
            decisions=decisions,
        )

    @property
    def item_keys(self) -> tuple[str, ...]:
        return tuple(decision.item_key for decision in self.decisions)

    @property
    def rejected_count(self) -> int:
        return sum(1 for decision in self.decisions if decision.outcome == "rejected")


class KoreanTextReviewApplicationAuthority(_FrozenModel):
    mode: Literal["reject_only", "promote"]
    power: Literal["remediation", "initial_content_promotion", "final_content_promotion"]
    aggregate_sha256: str = Field(min_length=64, max_length=64)
    prestate_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("aggregate_sha256", "prestate_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanTextReviewApplicationResult(_FrozenModel):
    mode: Literal["reject_only", "promote"]
    mutated_count: int = Field(ge=0)
    aggregate_sha256: str = Field(min_length=64, max_length=64)


class KoreanTextReviewApplicationService:
    """Apply review aggregates only after exact authority and prestate checks."""

    def __init__(self, text_repository: object) -> None:
        self.text_repository = text_repository

    def prestate_sha256(self, job_id: str, item_keys: tuple[str, ...]) -> str:
        payload = []
        for item_key in sorted(item_keys):
            record = self._require_record(job_id, item_key)
            payload.append(
                {
                    "job_id": record.job_id,
                    "item_key": record.item_key,
                    "candidate_sha256": _record_candidate_sha256(record),
                    "review_status": record.review_status.value,
                    "validation_status": record.validation_status.value,
                    "text_review_receipt_sha256": record.text_review_receipt_sha256,
                }
            )
        return _canonical_sha256(payload)

    def apply(
        self,
        aggregate: KoreanTextReviewAggregate,
        authority: KoreanTextReviewApplicationAuthority,
    ) -> KoreanTextReviewApplicationResult:
        if aggregate.aggregate_sha256 != authority.aggregate_sha256:
            raise ValueError("Korean text-review aggregate drift")
        if authority.mode == "reject_only" and authority.power != "remediation":
            raise ValueError("reject-only text review requires remediation authority")
        if authority.mode == "promote" and authority.power not in {"initial_content_promotion", "final_content_promotion"}:
            raise ValueError("text review promotion requires content-promotion authority")
        if authority.mode == "promote" and aggregate.rejected_count:
            raise ValueError("text review promotion requires zero rejections")
        if self.prestate_sha256(aggregate.job_id, aggregate.item_keys) != authority.prestate_sha256:
            raise ValueError("Korean text-review prestate drift")

        mutations = []
        for decision in aggregate.decisions:
            record = self._require_record(aggregate.job_id, decision.item_key)
            if _record_candidate_sha256(record) != decision.candidate_sha256:
                raise ValueError("stale Korean text review candidate")
            if authority.mode == "reject_only" and decision.outcome == "rejected":
                mutations.append(
                    record.model_copy(
                        update={
                            "review_status": ReviewStatus.REVIEW_REQUIRED,
                            "review_reason": "rejected:" + ",".join(decision.rejection_codes),
                            "text_review_receipt_sha256": aggregate.aggregate_sha256,
                        }
                    )
                )
            elif authority.mode == "promote" and decision.outcome == "accepted":
                mutations.append(
                    record.model_copy(
                        update={
                            "review_status": ReviewStatus.ACCEPTED,
                            "review_reason": None,
                            "text_review_receipt_sha256": aggregate.aggregate_sha256,
                        }
                    )
                )

        for record in mutations:
            self.text_repository.upsert_text_record(record)
        return KoreanTextReviewApplicationResult(
            mode=authority.mode,
            mutated_count=len(mutations),
            aggregate_sha256=aggregate.aggregate_sha256,
        )

    def _require_record(self, job_id: str, item_key: str) -> object:
        getter = getattr(self.text_repository, "get_text_record", None)
        if not callable(getter):
            raise ValueError("text repository cannot load review records")
        record = getter(job_id, item_key)
        if record is None:
            raise ValueError("unknown Korean text-review item")
        return record


def _record_candidate_sha256(record: object) -> str | None:
    evidence = getattr(record, "candidate_selection_evidence", None)
    return getattr(evidence, "selected_candidate_sha256", None)


__all__ = [
    "KoreanTextReviewAggregate",
    "KoreanTextReviewApplicationAuthority",
    "KoreanTextReviewApplicationResult",
    "KoreanTextReviewApplicationService",
    "KoreanTextReviewBatch",
    "KoreanTextReviewBatchDecision",
    "KoreanTextReviewImportLedger",
    "KoreanTextReviewImportResult",
]
