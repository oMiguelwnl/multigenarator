"""Tune importance against source-bound machine labels, without human authority.

These metrics describe agreement with machine labels. The analysis score is an
explicit subjective machine diagnostic, not a calibrated correctness probability.
It is passed into the existing criteria's analysis threshold solely to exercise
the same selection arithmetic; no approved policy or linguistic claim is issued.
"""

from collections.abc import Iterable
from decimal import Decimal
from typing import Literal

from pydantic import Field, computed_field

from multilang.domain.form_evidence import LEXICAL_UPOS
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.domain.lexical_identity import ImportantFormCriteria, canonical_sha256
from multilang.services.importance_calibration import (
    ConfusionMetrics,
    _source_keys,
    _stable_arithmetic,
)
from multilang.services.qualification_machine import (
    MachineFormDecision,
    MachineQualificationResult,
    reconcile_machine_reviews,
)
from multilang.services.qualification_review import FormReviewItem


class _MachineMetricsScope(NativeContract):
    label_origin: Literal["machine"] = "machine"
    metrics_scope: Literal["agreement_with_machine_labels"] = "agreement_with_machine_labels"
    analysis_rating_semantics: Literal["subjective_machine_diagnostic_not_probability"] = (
        "subjective_machine_diagnostic_not_probability"
    )
    production_eligible: Literal[False] = False


class MachineCalibrationResult(_MachineMetricsScope):
    calibration_qualification: MachineQualificationResult
    candidate_criteria: tuple[ImportantFormCriteria, ...] = Field(min_length=1, max_length=256)
    language: SupportedLanguage
    profile_sha256: Sha256
    rubric_sha256: Sha256
    packet_sha256: Sha256
    qualification_sha256: Sha256
    criteria: ImportantFormCriteria
    metrics: ConfusionMetrics
    candidate_scores: dict[Sha256, Decimal]
    false_positive_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    false_negative_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    source_keys: tuple[Sha256, ...]
    arithmetic_policy: Literal["decimal-50-half-even-1"] = "decimal-50-half-even-1"

    @computed_field
    @property
    def calibration_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class MachineImportanceEvaluation(_MachineMetricsScope):
    evaluation_qualification: MachineQualificationResult
    calibration_sha256: Sha256
    criteria_sha256: Sha256
    packet_sha256: Sha256
    qualification_sha256: Sha256
    metrics: ConfusionMetrics

    @computed_field
    @property
    def evaluation_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def _verified(qualification: MachineQualificationResult) -> MachineQualificationResult:
    """Revalidate every nested binding and recompute the agreement from both runs."""
    try:
        qualification = MachineQualificationResult.model_validate(
            qualification.model_dump(mode="json", exclude_computed_fields=True, warnings=False)
        )
    except (AttributeError, TypeError):
        raise ValueError("machine qualification replay requires a complete contract") from None
    replay = reconcile_machine_reviews(
        qualification.packet, qualification.proposal, qualification.judgment
    )
    if replay != qualification:
        raise ValueError("machine qualification replay detected drift")
    return replay


def _metrics(criteria: ImportantFormCriteria, qualification: MachineQualificationResult):
    consensuses = {consensus.item_id: consensus for consensus in qualification.decisions}
    excluded, selected, false_accepts, false_rejects = {}, [], [], []
    tp = fp = fn = tn = 0
    for item in qualification.packet.items:
        if not isinstance(item, FormReviewItem):
            continue
        consensus = consensuses.get(item.item_id)
        if consensus is None or consensus.status != "machine_agreement":
            excluded[item.item_id] = "machine_consensus_unavailable"
            continue
        decision = consensus.decision
        if not isinstance(decision, MachineFormDecision) or decision.include is None:
            excluded[item.item_id] = "definite_machine_label_required"
            continue
        count = item.measurements.get("observed_count")
        diagnostic = decision.machine_analysis_rating
        if (
            not decision.proposed_sense_id
            or item.pos not in LEXICAL_UPOS
            or count is None
            or diagnostic is None
        ):
            excluded[item.item_id] = "resolved_sense_pos_count_rating_required"
            continue
        if count != count.to_integral_value() or not 0 <= count <= 10**12:
            raise ValueError("observed count must be a bounded integer")
        # Frequency belongs to measured evidence; other ratings must have been
        # explicitly assessed in the agreed decision, never inherited by default.
        values = {key: value for key, value in item.proposed_ratings.items() if key == "frequency"}
        values.update(decision.ratings)
        predicted = criteria.score_evidence(values, int(count), diagnostic) is not None
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
def calibrate_machine_importance(
    qualification: MachineQualificationResult,
    candidates: Iterable[ImportantFormCriteria],
    *,
    false_positive_cost: Decimal,
    false_negative_cost: Decimal,
) -> MachineCalibrationResult:
    qualification = _verified(qualification)
    packet = qualification.packet
    if packet.split != "calibration":
        raise ValueError("only calibration split may select machine criteria")
    fp_cost, fn_cost = Decimal(false_positive_cost), Decimal(false_negative_cost)
    if (
        any(not cost.is_finite() or not 0 <= cost <= 1000000 for cost in (fp_cost, fn_cost))
        or fp_cost + fn_cost == 0
    ):
        raise ValueError("explicit bounded nonzero error costs required")
    grid = {}
    for index, candidate in enumerate(candidates):
        if index >= 256:
            raise ValueError("candidate grid exceeds 256")
        candidate = ImportantFormCriteria.model_validate(candidate.model_dump(mode="json"))
        grid[candidate.policy_sha256] = candidate
    if not grid:
        raise ValueError("candidate grid is empty")
    evaluated = {key: _metrics(value, qualification) for key, value in sorted(grid.items())}
    first = next(iter(evaluated.values()))
    if (
        not first.evaluated
        or not first.true_positive + first.false_negative
        or not first.true_negative + first.false_positive
    ):
        raise ValueError("calibration needs evaluable positive and negative machine labels")
    scores = {
        key: metrics.false_positive * fp_cost + metrics.false_negative * fn_cost
        for key, metrics in evaluated.items()
    }
    winner = min(scores, key=lambda key: (scores[key], key))
    return MachineCalibrationResult(
        calibration_qualification=qualification,
        candidate_criteria=tuple(grid[key] for key in sorted(grid)),
        language=packet.language,
        profile_sha256=packet.profile_sha256,
        rubric_sha256=packet.rubric_sha256,
        packet_sha256=packet.packet_sha256,
        qualification_sha256=qualification.result_sha256,
        criteria=grid[winner],
        metrics=evaluated[winner],
        candidate_scores=scores,
        false_positive_cost=fp_cost,
        false_negative_cost=fn_cost,
        source_keys=_source_keys(packet),
    )


@_stable_arithmetic
def evaluate_machine_importance(
    calibration: MachineCalibrationResult,
    qualification: MachineQualificationResult,
) -> MachineImportanceEvaluation:
    calibration = MachineCalibrationResult.model_validate(
        calibration.model_dump(mode="json", exclude_computed_fields=True, warnings=False)
    )
    replay = calibrate_machine_importance(
        calibration.calibration_qualification,
        candidates=calibration.candidate_criteria,
        false_positive_cost=calibration.false_positive_cost,
        false_negative_cost=calibration.false_negative_cost,
    )
    if replay != calibration:
        raise ValueError("machine calibration provenance replay detected drift")
    qualification = _verified(qualification)
    packet = qualification.packet
    if packet.split != "evaluation":
        raise ValueError("machine evaluation requires the evaluation split")
    if (packet.language, packet.profile_sha256, packet.rubric_sha256) != (
        calibration.language,
        calibration.profile_sha256,
        calibration.rubric_sha256,
    ):
        raise ValueError("evaluation language/profile/rubric changed")
    if set(_source_keys(packet)) & set(calibration.source_keys):
        raise ValueError("machine calibration/evaluation source overlap")
    return MachineImportanceEvaluation(
        evaluation_qualification=qualification,
        calibration_sha256=calibration.calibration_sha256,
        criteria_sha256=calibration.criteria.policy_sha256,
        packet_sha256=packet.packet_sha256,
        qualification_sha256=qualification.result_sha256,
        metrics=_metrics(calibration.criteria, qualification),
    )


__all__ = [
    "MachineCalibrationResult",
    "MachineImportanceEvaluation",
    "calibrate_machine_importance",
    "evaluate_machine_importance",
]
