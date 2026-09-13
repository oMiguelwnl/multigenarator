from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from multilang.domain.lexical_identity import ImportantFormCriteria
from multilang.services.native_evidence import EvidenceStore, SignedEvidence


def reviewed(tmp_path, split="calibration", *, prefix="train", signed=True):
    from multilang.services.qualification_review import (
        FormDecision,
        FormReviewItem,
        HumanReviewSubmission,
        ReviewPacket,
        ReviewSource,
        review_signing_payload,
    )

    items = tuple(
        FormReviewItem(
            item_id=f"{prefix}-{i}",
            candidate_id=f"candidate-{i}",
            candidate_sha256="a" * 64,
            lemma="go",
            pos="VERB",
            text=f"form{i}",
            canonical_sense_id="go-motion",
            sources=(
                ReviewSource(
                    source_id="fixture",
                    source_sha256=("b" if prefix == "train" else "c") * 64,
                    record_id=f"{prefix}-{i}",
                    excerpt=f"{prefix} sentence {i}",
                ),
            ),
            measurements={"observed_count": 5},
            proposed_ratings={"frequency": str(value)},
        )
        for i, value in enumerate(("0.9", "0.7", "0.4", "0.1"))
    )
    packet = ReviewPacket(
        packet_id=prefix,
        language="en",
        split=split,
        profile_sha256="d" * 64,
        rubric_sha256="e" * 64,
        items=items,
    )
    decisions = tuple(
        FormDecision(
            item_id=item.item_id,
            item_sha256=item.item_sha256,
            decision="accepted",
            reason="Synthetic test review",
            include=i < 2,
            canonical_sense_id="go-motion",
            analysis_confidence=Decimal(1),
        )
        for i, item in enumerate(items)
    )
    submission = HumanReviewSubmission(
        packet_sha256=packet.packet_sha256,
        reviewer_id="test-reviewer",
        expertise_declaration="Synthetic fixture, not real qualification",
        reviewed_at=datetime.now(UTC),
        decisions=decisions,
    )
    store = EvidenceStore(tmp_path, key=b"x" * 32)
    if signed:
        receipt = SignedEvidence.sign(
            review_signing_payload(packet, submission),
            key=b"x" * 32,
            signer="test-reviewer",
            purpose="qualification-review",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        tmp_path.mkdir(exist_ok=True)
        (tmp_path / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
        submission = submission.model_copy(update={"receipt_id": receipt.receipt_id})
    return packet, submission, store


def criteria(threshold):
    return ImportantFormCriteria(
        policy_id="example",
        version="1",
        weights={"frequency": "1"},
        minimum_score=threshold,
        attestation_threshold=1,
        analysis_confidence_threshold="0.9",
        missing_evidence="reject",
    )


def test_calibration_selects_explicit_grid_and_evaluation_does_not_retune(tmp_path):
    from multilang.services.importance_calibration import calibrate_importance, evaluate_importance

    packet, submission, store = reviewed(tmp_path)
    result = calibrate_importance(
        packet,
        submission,
        candidates=[criteria("0.2"), criteria("0.5")],
        verifier=store,
        expected_reviewer="test-reviewer",
        false_positive_cost=Decimal(2),
        false_negative_cost=Decimal(1),
    )
    assert result.criteria.minimum_score == Decimal("0.5")
    assert (
        result.metrics.true_positive,
        result.metrics.false_positive,
        result.metrics.false_negative,
    ) == (2, 0, 0)
    assert result.production_eligible is False
    assert result == calibrate_importance(
        packet,
        submission,
        candidates=[criteria("0.5"), criteria("0.2")],
        verifier=store,
        expected_reviewer="test-reviewer",
        false_positive_cost=Decimal(2),
        false_negative_cost=Decimal(1),
    )
    evaluation, decisions, _ = reviewed(tmp_path, "evaluation", prefix="test")
    report = evaluate_importance(
        result, evaluation, decisions, verifier=store, expected_reviewer="test-reviewer"
    )
    assert report.criteria_sha256 == result.criteria.policy_sha256
    assert report.metrics.true_negative == 2
    with pytest.raises(ValueError):
        calibrate_importance(
            evaluation,
            decisions,
            candidates=[criteria("0.5")],
            verifier=store,
            expected_reviewer="test-reviewer",
            false_positive_cost=1,
            false_negative_cost=1,
        )


def test_unsigned_reviews_cannot_calibrate_and_grid_is_bounded(tmp_path):
    from multilang.services.importance_calibration import calibrate_importance

    packet, submission, store = reviewed(tmp_path, signed=False)
    with pytest.raises(ValueError, match="authenticated"):
        calibrate_importance(
            packet,
            submission,
            candidates=[criteria("0.5")],
            verifier=store,
            expected_reviewer="test-reviewer",
            false_positive_cost=1,
            false_negative_cost=1,
        )
    packet, submission, store = reviewed(tmp_path)
    with pytest.raises(ValueError, match="candidate"):
        calibrate_importance(
            packet,
            submission,
            candidates=[criteria("0.5")] * 257,
            verifier=store,
            expected_reviewer="test-reviewer",
            false_positive_cost=1,
            false_negative_cost=1,
        )


def test_evaluation_cannot_reuse_source_documents_or_change_rubric(tmp_path):
    from multilang.services.importance_calibration import calibrate_importance, evaluate_importance

    packet, submission, store = reviewed(tmp_path)
    result = calibrate_importance(
        packet,
        submission,
        candidates=[criteria("0.5")],
        verifier=store,
        expected_reviewer="test-reviewer",
        false_positive_cost=1,
        false_negative_cost=1,
    )
    evaluation, decisions, _ = reviewed(tmp_path, "evaluation", prefix="train")
    with pytest.raises(ValueError, match="overlap"):
        evaluate_importance(
            result, evaluation, decisions, verifier=store, expected_reviewer="test-reviewer"
        )


def test_rewritten_calibration_manifest_cannot_hide_training_overlap(tmp_path):
    from multilang.services.importance_calibration import calibrate_importance, evaluate_importance

    packet, submission, store = reviewed(tmp_path)
    result = calibrate_importance(
        packet,
        submission,
        candidates=[criteria("0.5")],
        verifier=store,
        expected_reviewer="test-reviewer",
        false_positive_cost=1,
        false_negative_cost=1,
    )
    evaluation, decisions, _ = reviewed(tmp_path, "evaluation", prefix="train")
    tampered = result.model_copy(update={"source_keys": ()})
    with pytest.raises(ValueError, match="calibration.*(provenance|drift|replay)"):
        evaluate_importance(
            tampered, evaluation, decisions, verifier=store, expected_reviewer="test-reviewer"
        )


def test_calibration_is_independent_of_callers_decimal_context(tmp_path):
    from decimal import localcontext

    from multilang.services.importance_calibration import calibrate_importance

    packet, submission, store = reviewed(tmp_path)
    outputs = []
    for precision in (6, 50):
        with localcontext() as arithmetic:
            arithmetic.prec = precision
            outputs.append(
                calibrate_importance(
                    packet,
                    submission,
                    candidates=[criteria("0.2")],
                    verifier=store,
                    expected_reviewer="test-reviewer",
                    false_positive_cost=1,
                    false_negative_cost=1,
                )
            )
    assert outputs[0] == outputs[1]
