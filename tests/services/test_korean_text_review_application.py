"""Tests for bounded Korean text-review import and authority-gated mutation."""

from __future__ import annotations

from hashlib import sha256
import json

import pytest
from pydantic import ValidationError

from multilang.domain.text_quality import (
    ConfidenceLabel,
    KoreanTextSelectionEvidence,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.services.korean_text_review import (
    KoreanTextReviewAggregate,
    KoreanTextReviewApplicationAuthority,
    KoreanTextReviewApplicationService,
    KoreanTextReviewBatch,
    KoreanTextReviewBatchDecision,
    KoreanTextReviewImportLedger,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _decision(item_key: str, *, outcome: str = "rejected", candidate_hash: str | None = None) -> KoreanTextReviewBatchDecision:
    return KoreanTextReviewBatchDecision(
        job_id="job-ko",
        item_key=item_key,
        candidate_sha256=candidate_hash or _hash(f"candidate-{item_key}"),
        candidate_identity_sha256=_hash(f"identity-{item_key}"),
        outcome=outcome,
        rejection_codes=("wrong_sense",) if outcome == "rejected" else (),
    )


def _record(item_key: str, *, candidate_hash: str | None = None) -> TextQualityRecord:
    return TextQualityRecord(
        job_id="job-ko",
        item_key=item_key,
        lexical_candidate_id=f"lex-{item_key}",
        example_sentence="저는 학교에 가요.",
        translation_text="Eu vou para a escola.",
        generation_status=TextGenerationStatus.GENERATED,
        validation_status=ValidationStatus.PASSED,
        review_status=ReviewStatus.REVIEW_REQUIRED,
        confidence_label=ConfidenceLabel.HIGH,
        sentence_provenance=TextProvenance(source="provider"),
        translation_provenance=TextProvenance(source="provider"),
        candidate_selection_evidence=KoreanTextSelectionEvidence(
            candidate_set_sha256=_hash(f"candidate-set-{item_key}"),
            selected_candidate_sha256=candidate_hash or _hash(f"candidate-{item_key}"),
            selected_ordinal=1,
            initial_candidate_count=2,
            repair_attempt_count=0,
            hard_gate_status="passed",
            selector_version="test-selector-v1",
        ),
    )


class _FakeTextRepository:
    def __init__(self, records: list[TextQualityRecord]) -> None:
        self.records = {record.item_key: record for record in records}
        self.upserts: list[TextQualityRecord] = []

    def get_text_record(self, job_id: str, item_key: str) -> TextQualityRecord | None:
        record = self.records.get(item_key)
        if record is None or record.job_id != job_id:
            return None
        return record

    def upsert_text_record(self, record: TextQualityRecord) -> TextQualityRecord:
        self.upserts.append(record)
        self.records[record.item_key] = record
        return record


def test_text_review_batch_import_is_bounded_content_free_and_exact_retry() -> None:
    with pytest.raises(ValidationError):
        KoreanTextReviewBatchDecision.model_validate(
            {
                **_decision("item-1").model_dump(mode="json"),
                "raw_note": "private reviewer text must not persist",
            }
        )

    with pytest.raises(ValidationError):
        KoreanTextReviewBatch(
            job_id="job-ko",
            production_run_sha256=_hash("production"),
            review_receipt_sha256=_hash("receipt-too-large"),
            decisions=tuple(_decision(f"item-{index}") for index in range(101)),
        )

    ledger = KoreanTextReviewImportLedger()
    batch = KoreanTextReviewBatch(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        review_receipt_sha256=_hash("receipt"),
        decisions=(_decision("item-1"),),
    )

    first = ledger.import_batch(batch, current_records={"item-1": _record("item-1")})
    second = ledger.import_batch(batch, current_records={"item-1": _record("item-1")})

    payload = json.dumps(first.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    assert first.replayed is False
    assert second.replayed is True
    assert ledger.write_count == 1
    assert first.decision_count == 1
    assert first.rejected_count == 1
    assert "저는" not in payload
    assert "private" not in payload


def test_text_review_reject_and_promote_require_distinct_exact_authority() -> None:
    rejected = _record("item-1")
    accepted = _record("item-2")
    repository = _FakeTextRepository([rejected, accepted])
    service = KoreanTextReviewApplicationService(repository)

    reject_decision = _decision("item-1", outcome="rejected")
    reject_aggregate = KoreanTextReviewAggregate.from_decisions(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        decisions=(reject_decision,),
    )
    reject_prestate = service.prestate_sha256("job-ko", reject_aggregate.item_keys)

    with pytest.raises(ValueError, match="remediation"):
        service.apply(
            reject_aggregate,
            KoreanTextReviewApplicationAuthority(
                mode="reject_only",
                power="final_content_promotion",
                aggregate_sha256=reject_aggregate.aggregate_sha256,
                prestate_sha256=reject_prestate,
            ),
        )
    assert repository.upserts == []

    reject_result = service.apply(
        reject_aggregate,
        KoreanTextReviewApplicationAuthority(
            mode="reject_only",
            power="remediation",
            aggregate_sha256=reject_aggregate.aggregate_sha256,
            prestate_sha256=reject_prestate,
        ),
    )

    assert reject_result.mutated_count == 1
    assert repository.records["item-1"].review_status is ReviewStatus.REVIEW_REQUIRED
    assert repository.records["item-1"].text_review_receipt_sha256 == reject_aggregate.aggregate_sha256

    promote_decision = _decision("item-2", outcome="accepted")
    promote_aggregate = KoreanTextReviewAggregate.from_decisions(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        decisions=(promote_decision,),
    )
    promote_prestate = service.prestate_sha256("job-ko", promote_aggregate.item_keys)

    promote_result = service.apply(
        promote_aggregate,
        KoreanTextReviewApplicationAuthority(
            mode="promote",
            power="final_content_promotion",
            aggregate_sha256=promote_aggregate.aggregate_sha256,
            prestate_sha256=promote_prestate,
        ),
    )

    assert promote_result.mutated_count == 1
    assert repository.records["item-2"].review_status is ReviewStatus.ACCEPTED
    assert repository.records["item-2"].text_review_receipt_sha256 == promote_aggregate.aggregate_sha256


def test_text_review_application_blocks_stale_candidate_without_mutation() -> None:
    repository = _FakeTextRepository([_record("item-1", candidate_hash=_hash("current-candidate"))])
    service = KoreanTextReviewApplicationService(repository)
    aggregate = KoreanTextReviewAggregate.from_decisions(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        decisions=(_decision("item-1", candidate_hash=_hash("stale-candidate")),),
    )

    with pytest.raises(ValueError, match="stale Korean text review candidate"):
        service.apply(
            aggregate,
            KoreanTextReviewApplicationAuthority(
                mode="reject_only",
                power="remediation",
                aggregate_sha256=aggregate.aggregate_sha256,
                prestate_sha256=service.prestate_sha256("job-ko", aggregate.item_keys),
            ),
        )

    assert repository.upserts == []
