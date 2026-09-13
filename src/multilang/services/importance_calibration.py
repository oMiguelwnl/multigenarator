"""Bounded calibration with authenticated labels and untouched evaluation data."""

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from functools import wraps
from typing import Literal

from pydantic import Field, computed_field

from multilang.domain.form_evidence import LEXICAL_UPOS
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.domain.lexical_identity import ImportantFormCriteria, canonical_sha256
from multilang.services.native_evidence import EvidenceStore
from multilang.services.qualification_review import (
    FormDecision,
    FormReviewItem,
    HumanReviewSubmission,
    ReviewPacket,
    validate_review,
)


class ConfusionMetrics(NativeContract):
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int
    precision: Decimal | None
    recall: Decimal | None
    evaluated: int
    excluded: dict[str, str]
    selected_item_ids: tuple[str, ...]
    false_accepts: tuple[str, ...]
    false_rejects: tuple[str, ...]


class CalibrationResult(NativeContract):
    calibration_packet: ReviewPacket
    calibration_submission: HumanReviewSubmission
    candidate_criteria: tuple[ImportantFormCriteria, ...] = Field(min_length=1, max_length=256)
    language: SupportedLanguage
    profile_sha256: Sha256
    rubric_sha256: Sha256
    packet_sha256: Sha256
    submission_sha256: Sha256
    criteria: ImportantFormCriteria
    metrics: ConfusionMetrics
    candidate_scores: dict[Sha256, Decimal]
    false_positive_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    false_negative_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    source_keys: tuple[Sha256, ...]
    production_eligible: Literal[False] = False
    arithmetic_policy: Literal["decimal-50-half-even-1"] = "decimal-50-half-even-1"

    @computed_field
    @property
    def calibration_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class ImportanceEvaluation(NativeContract):
    calibration_sha256: Sha256
    criteria_sha256: Sha256
    packet_sha256: Sha256
    submission_sha256: Sha256
    metrics: ConfusionMetrics
    production_eligible: Literal[False] = False


def _source_keys(packet):
    keys = set()
    for item in packet.items:
        if isinstance(item, FormReviewItem):
            keys.update(item.evidence_source_keys)
        for source in item.sources:
            keys.add(canonical_sha256(["source", source.source_sha256]))
            keys.add(
                canonical_sha256([source.source_sha256, source.document_id or source.record_id])
            )
            if source.sentence_id and source.excerpt:
                from hashlib import sha256

                keys.add(
                    canonical_sha256(["sentence-text", sha256(source.excerpt.encode()).hexdigest()])
                )
    return tuple(sorted(keys))


def _stable_arithmetic(function):
    @wraps(function)
    def run(*args, **kwargs):
        with localcontext() as arithmetic:
            arithmetic.prec = 50
            arithmetic.rounding = ROUND_HALF_EVEN
            return function(*args, **kwargs)

    return run


def _authenticated(packet, submission, verifier, expected_reviewer):
    review = validate_review(
        packet, submission, verifier=verifier, expected_reviewer=expected_reviewer
    )
    if review.status != "authenticated":
        raise ValueError("calibration and evaluation require authenticated human review")
    return review


def _metrics(criteria, packet, submission):
    decisions = {d.item_id: d for d in submission.decisions}
    excluded, selected, false_accepts, false_rejects = {}, [], [], []
    tp = fp = fn = tn = 0
    for item in packet.items:
        if not isinstance(item, FormReviewItem):
            continue
        decision = decisions.get(item.item_id)
        if not isinstance(decision, FormDecision) or decision.include is None:
            excluded[item.item_id] = "No definite human include/exclude label"
            continue
        sense = decision.canonical_sense_id or item.canonical_sense_id
        confidence = decision.analysis_confidence
        count = item.measurements.get("observed_count")
        if not sense or item.pos not in LEXICAL_UPOS or confidence is None or count is None:
            excluded[item.item_id] = (
                "Resolved sense/POS, observed count and reviewed analysis confidence required"
            )
            continue
        if count != count.to_integral_value() or count > 10**12:
            raise ValueError("observed count must be a bounded integer")
        values = {**item.proposed_ratings, **decision.ratings}
        predicted = criteria.score_evidence(values, int(count), confidence) is not None
        if predicted:
            selected.append(item.item_id)
        if predicted and decision.include:
            tp += 1
        elif predicted:
            fp += 1
            false_accepts.append(item.item_id)
        elif decision.include:
            fn += 1
            false_rejects.append(item.item_id)
        else:
            tn += 1
    return ConfusionMetrics(
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        true_negative=tn,
        precision=Decimal(tp) / (tp + fp) if tp + fp else None,
        recall=Decimal(tp) / (tp + fn) if tp + fn else None,
        evaluated=tp + fp + fn + tn,
        excluded=dict(sorted(excluded.items())),
        selected_item_ids=tuple(sorted(selected)),
        false_accepts=tuple(sorted(false_accepts)),
        false_rejects=tuple(sorted(false_rejects)),
    )


@_stable_arithmetic
def calibrate_importance(
    packet: ReviewPacket,
    submission: HumanReviewSubmission,
    *,
    candidates: Iterable[ImportantFormCriteria],
    verifier: EvidenceStore,
    expected_reviewer: str,
    false_positive_cost: Decimal,
    false_negative_cost: Decimal,
) -> CalibrationResult:
    if packet.split != "calibration":
        raise ValueError("only calibration split may select criteria")
    _authenticated(packet, submission, verifier, expected_reviewer)
    fp_cost, fn_cost = Decimal(false_positive_cost), Decimal(false_negative_cost)
    if (
        any(not c.is_finite() or not 0 <= c <= 1000000 for c in (fp_cost, fn_cost))
        or fp_cost + fn_cost == 0
    ):
        raise ValueError("explicit bounded nonzero error costs required")
    grid = {}
    for index, candidate in enumerate(candidates):
        if index >= 256:
            raise ValueError("candidate grid exceeds 256")
        # Approved policies cannot masquerade as an unapproved search candidate.
        candidate = ImportantFormCriteria.model_validate(candidate.model_dump(mode="json"))
        grid[candidate.policy_sha256] = candidate
    if not grid:
        raise ValueError("candidate grid is empty")
    evaluated = {key: _metrics(value, packet, submission) for key, value in sorted(grid.items())}
    first = next(iter(evaluated.values()))
    if (
        not first.evaluated
        or not first.true_positive + first.false_negative
        or not first.true_negative + first.false_positive
    ):
        raise ValueError("calibration needs evaluable positive and negative human labels")
    scores = {
        key: m.false_positive * fp_cost + m.false_negative * fn_cost for key, m in evaluated.items()
    }
    winner = min(scores, key=lambda key: (scores[key], key))
    return CalibrationResult(
        calibration_packet=packet,
        calibration_submission=submission,
        candidate_criteria=tuple(grid[key] for key in sorted(grid)),
        language=packet.language,
        profile_sha256=packet.profile_sha256,
        rubric_sha256=packet.rubric_sha256,
        packet_sha256=packet.packet_sha256,
        submission_sha256=canonical_sha256(submission.model_dump(mode="json")),
        criteria=grid[winner],
        metrics=evaluated[winner],
        candidate_scores=scores,
        false_positive_cost=fp_cost,
        false_negative_cost=fn_cost,
        source_keys=_source_keys(packet),
    )


@_stable_arithmetic
def evaluate_importance(
    calibration: CalibrationResult,
    packet: ReviewPacket,
    submission: HumanReviewSubmission,
    *,
    verifier: EvidenceStore,
    expected_reviewer: str,
) -> ImportanceEvaluation:
    replay = calibrate_importance(
        calibration.calibration_packet,
        calibration.calibration_submission,
        candidates=calibration.candidate_criteria,
        verifier=verifier,
        expected_reviewer=calibration.calibration_submission.reviewer_id,
        false_positive_cost=calibration.false_positive_cost,
        false_negative_cost=calibration.false_negative_cost,
    )
    if replay != calibration:
        raise ValueError("calibration provenance replay detected drift")
    if packet.split != "evaluation":
        raise ValueError("evaluation requires the evaluation split")
    if (packet.language, packet.profile_sha256, packet.rubric_sha256) != (
        calibration.language,
        calibration.profile_sha256,
        calibration.rubric_sha256,
    ):
        raise ValueError("evaluation language/profile/rubric changed")
    _authenticated(packet, submission, verifier, expected_reviewer)
    if set(_source_keys(packet)) & set(calibration.source_keys):
        raise ValueError("calibration/evaluation source overlap")
    return ImportanceEvaluation(
        calibration_sha256=calibration.calibration_sha256,
        criteria_sha256=calibration.criteria.policy_sha256,
        packet_sha256=packet.packet_sha256,
        submission_sha256=canonical_sha256(submission.model_dump(mode="json")),
        metrics=_metrics(calibration.criteria, packet, submission),
    )
