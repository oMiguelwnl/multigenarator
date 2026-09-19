"""Tune importance against source-bound machine labels, without human authority.

These metrics describe agreement with machine labels. The analysis score is an
explicit subjective machine diagnostic, not a calibrated correctness probability.
It is passed into the existing criteria's analysis threshold solely to exercise
the same selection arithmetic; no approved policy or linguistic claim is issued.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal, Self

from pydantic import Field, computed_field, model_validator

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


class _VersionedMachineMetrics(_MachineMetricsScope):
    # Deliberately required: legacy artifacts counted unavailable ratings as
    # predictions. Loading them under the new semantics must never be silent.
    metrics_policy: Literal["common-grid-evidence-v2"]
    required_evidence: tuple[str, ...] = Field(min_length=1, max_length=7)

    @model_validator(mode="before")
    @classmethod
    def explicit_metrics_version(cls, value: Any) -> Any:
        if isinstance(value, dict) and "metrics_policy" not in value:
            raise ValueError(
                "legacy machine metrics require recalibration with common-grid-evidence-v2"
            )
        return value


class MachineCalibrationReadiness(_VersionedMachineMetrics):
    qualification_sha256: Sha256
    split: Literal["pilot", "calibration", "evaluation"]
    candidate_criteria_sha256: tuple[Sha256, ...] = Field(min_length=1, max_length=256)
    total_forms: int = Field(ge=0)
    agreed_positive_labels: int = Field(ge=0)
    agreed_negative_labels: int = Field(ge=0)
    usable_positive_labels: int = Field(ge=0)
    usable_negative_labels: int = Field(ge=0)
    excluded_items: dict[str, str]
    missing_evidence: dict[str, tuple[str, ...]]

    @model_validator(mode="after")
    def counts_match_coverage(self) -> Self:
        if (
            self.usable_labels + len(self.excluded_items) != self.total_forms
            or self.agreed_positive_labels + self.agreed_negative_labels > self.total_forms
            or self.usable_positive_labels > self.agreed_positive_labels
            or self.usable_negative_labels > self.agreed_negative_labels
            or set(self.missing_evidence) - set(self.excluded_items)
        ):
            raise ValueError("machine readiness counts do not match evidence coverage")
        return self

    @computed_field
    @property
    def usable_labels(self) -> int:
        return self.usable_positive_labels + self.usable_negative_labels

    @computed_field
    @property
    def abstentions(self) -> int:
        return len(self.excluded_items)

    @computed_field
    @property
    def reason_counts(self) -> dict[str, int]:
        return dict(
            sorted(
                Counter(reason.split(":", 1)[0] for reason in self.excluded_items.values()).items()
            )
        )

    @computed_field
    @property
    def ready_for_calibration(self) -> bool:
        return not self.blocking_reasons

    @computed_field
    @property
    def blocking_reasons(self) -> tuple[str, ...]:
        reasons = []
        if self.split != "calibration":
            reasons.append("calibration_split_required")
        if not self.usable_positive_labels:
            reasons.append("usable_positive_label_required")
        if not self.usable_negative_labels:
            reasons.append("usable_negative_label_required")
        return tuple(reasons)


class MachineCalibrationResult(_VersionedMachineMetrics):
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


class MachineImportanceEvaluation(_VersionedMachineMetrics):
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


def _candidate_grid(
    candidates: Iterable[ImportantFormCriteria],
) -> dict[str, ImportantFormCriteria]:
    grid = {}
    for index, candidate in enumerate(candidates):
        if index >= 256:
            raise ValueError("candidate grid exceeds 256")
        candidate = ImportantFormCriteria.model_validate(candidate.model_dump(mode="json"))
        grid[candidate.policy_sha256] = candidate
    if not grid:
        raise ValueError("candidate grid is empty")
    return dict(sorted(grid.items()))


def _required_evidence(grid: dict[str, ImportantFormCriteria]) -> tuple[str, ...]:
    return tuple(sorted({key for criteria in grid.values() for key in criteria.weights}))


@dataclass(frozen=True)
class _EligibleForm:
    item_id: str
    decision: MachineFormDecision
    values: dict[str, Decimal]
    observed_count: int
    diagnostic: Decimal


def _population(
    qualification: MachineQualificationResult,
    required_evidence: tuple[str, ...],
    candidate_criteria_sha256: tuple[str, ...],
) -> tuple[MachineCalibrationReadiness, tuple[_EligibleForm, ...]]:
    consensuses = {consensus.item_id: consensus for consensus in qualification.decisions}
    excluded, missing_evidence, eligible = {}, {}, []
    total = positive = negative = usable_positive = usable_negative = 0
    for item in qualification.packet.items:
        if not isinstance(item, FormReviewItem):
            continue
        total += 1
        consensus = consensuses.get(item.item_id)
        if consensus is None or consensus.status != "machine_agreement":
            excluded[item.item_id] = "machine_consensus_unavailable"
            continue
        decision = consensus.decision
        if not isinstance(decision, MachineFormDecision) or decision.include is None:
            excluded[item.item_id] = "definite_machine_label_required"
            continue
        positive += int(decision.include)
        negative += int(not decision.include)
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
        missing = tuple(key for key in required_evidence if key not in values)
        if missing:
            excluded[item.item_id] = "missing_required_evidence:" + ",".join(missing)
            missing_evidence[item.item_id] = missing
            continue
        usable_positive += int(decision.include)
        usable_negative += int(not decision.include)
        eligible.append(_EligibleForm(item.item_id, decision, values, int(count), diagnostic))
    readiness = MachineCalibrationReadiness(
        metrics_policy="common-grid-evidence-v2",
        required_evidence=required_evidence,
        qualification_sha256=qualification.result_sha256,
        split=qualification.packet.split,
        candidate_criteria_sha256=candidate_criteria_sha256,
        total_forms=total,
        agreed_positive_labels=positive,
        agreed_negative_labels=negative,
        usable_positive_labels=usable_positive,
        usable_negative_labels=usable_negative,
        excluded_items=dict(sorted(excluded.items())),
        missing_evidence=dict(sorted(missing_evidence.items())),
    )
    return readiness, tuple(eligible)


@_stable_arithmetic
def machine_calibration_readiness(
    qualification: MachineQualificationResult,
    candidates: Iterable[ImportantFormCriteria],
) -> MachineCalibrationReadiness:
    """Explain source-bound label coverage without interpreting missing notes as zero.

    Readiness requires the calibration split and both usable label classes; it
    does not assert statistical sufficiency or linguistic correctness. Coverage
    is also available for other splits without making them calibration-ready.
    The union includes every grid key,
    even zero-weight keys, independently of each policy's missing-evidence mode.
    """
    qualification = _verified(qualification)
    grid = _candidate_grid(candidates)
    readiness, _ = _population(qualification, _required_evidence(grid), tuple(grid))
    return readiness


def _metrics(
    criteria: ImportantFormCriteria,
    readiness: MachineCalibrationReadiness,
    eligible: tuple[_EligibleForm, ...],
) -> ConfusionMetrics:
    selected, false_accepts, false_rejects = [], [], []
    tp = fp = fn = tn = 0
    for item in eligible:
        predicted = (
            criteria.score_evidence(item.values, item.observed_count, item.diagnostic) is not None
        )
        if predicted:
            selected.append(item.item_id)
        if predicted and item.decision.include:
            tp += 1
        elif predicted:
            fp += 1
            false_accepts.append(item.item_id)
        elif item.decision.include:
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
        excluded=readiness.excluded_items,
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
    grid = _candidate_grid(candidates)
    required = _required_evidence(grid)
    readiness, eligible = _population(qualification, required, tuple(grid))
    if not readiness.ready_for_calibration:
        raise ValueError("calibration needs evaluable positive and negative machine labels")
    evaluated = {key: _metrics(value, readiness, eligible) for key, value in grid.items()}
    scores = {
        key: metrics.false_positive * fp_cost + metrics.false_negative * fn_cost
        for key, metrics in evaluated.items()
    }
    winner = min(scores, key=lambda key: (scores[key], key))
    return MachineCalibrationResult(
        metrics_policy="common-grid-evidence-v2",
        required_evidence=required,
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
    readiness, eligible = _population(
        qualification,
        calibration.required_evidence,
        tuple(criteria.policy_sha256 for criteria in calibration.candidate_criteria),
    )
    return MachineImportanceEvaluation(
        metrics_policy="common-grid-evidence-v2",
        required_evidence=calibration.required_evidence,
        evaluation_qualification=qualification,
        calibration_sha256=calibration.calibration_sha256,
        criteria_sha256=calibration.criteria.policy_sha256,
        packet_sha256=packet.packet_sha256,
        qualification_sha256=qualification.result_sha256,
        metrics=_metrics(calibration.criteria, readiness, eligible),
    )


__all__ = [
    "MachineCalibrationResult",
    "MachineCalibrationReadiness",
    "MachineImportanceEvaluation",
    "calibrate_machine_importance",
    "evaluate_machine_importance",
    "machine_calibration_readiness",
]
