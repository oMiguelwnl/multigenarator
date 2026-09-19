"""Opt-in document-scoped evaluation; historical source-key checks stay intact."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, Field, computed_field

from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.domain.lexical_identity import ImportantFormCriteria, canonical_sha256
from multilang.services.importance_calibration import _stable_arithmetic
from multilang.services.qualification_evaluation_partitions import compare_evaluation_partitions
from multilang.services.qualification_machine import MachineQualificationResult
from multilang.services.qualification_machine_calibration import (
    MachineCalibrationResult,
    MachineImportanceEvaluation,
    _candidate_grid,
    _metrics,
    _population,
    _verified,
    calibrate_machine_importance,
)
from multilang.services.qualification_partition_review import (
    PartitionReviewBundle,
    verify_partition_review,
)


class PartitionExperiment(NativeContract):
    schema_version: Literal["document-partition-evaluation-1"] = "document-partition-evaluation-1"
    calibration: PartitionReviewBundle
    evaluation: PartitionReviewBundle
    candidate_criteria: tuple[ImportantFormCriteria, ...] = Field(min_length=1, max_length=256)
    false_positive_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    false_negative_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    frozen_at: AwareDatetime
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def experiment_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class PartitionImportanceCalibration(NativeContract):
    schema_version: Literal["partition-calibration-1"] = "partition-calibration-1"
    experiment_sha256: Sha256
    calibration: MachineCalibrationResult
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def calibration_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class PartitionImportanceEvaluation(NativeContract):
    schema_version: Literal["partition-evaluation-1"] = "partition-evaluation-1"
    experiment_sha256: Sha256
    calibration_sha256: Sha256
    evaluation: MachineImportanceEvaluation
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def evaluation_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def freeze_partition_experiment(
    calibration: PartitionReviewBundle,
    evaluation: PartitionReviewBundle,
    *,
    candidates,
    false_positive_cost: Decimal,
    false_negative_cost: Decimal,
    frozen_at: datetime,
) -> PartitionExperiment:
    calibration, evaluation = (
        verify_partition_review(calibration),
        verify_partition_review(evaluation),
    )
    if (calibration.packet.split, evaluation.packet.split) != ("calibration", "evaluation"):
        raise ValueError("experiment needs separate calibration and evaluation splits")
    left, right = calibration.packet, evaluation.packet
    if (left.language, left.profile_sha256, left.rubric_sha256) != (
        right.language,
        right.profile_sha256,
        right.rubric_sha256,
    ):
        raise ValueError("experiment language/profile/rubric mismatch")
    if calibration.references != evaluation.references:
        raise ValueError("experiment requires the exact same frozen reference registry")
    compare_evaluation_partitions(calibration.partition, evaluation.partition)
    grid = _candidate_grid(candidates)
    experiment = PartitionExperiment(
        calibration=calibration,
        evaluation=evaluation,
        candidate_criteria=tuple(grid.values()),
        false_positive_cost=false_positive_cost,
        false_negative_cost=false_negative_cost,
        frozen_at=frozen_at,
    )
    if experiment.false_positive_cost + experiment.false_negative_cost == 0:
        raise ValueError("experiment needs nonzero error costs")
    return experiment


def verify_partition_experiment(experiment: PartitionExperiment) -> PartitionExperiment:
    experiment = PartitionExperiment.model_validate(
        experiment.model_dump(mode="json", exclude_computed_fields=True)
    )
    replay = freeze_partition_experiment(
        experiment.calibration,
        experiment.evaluation,
        candidates=experiment.candidate_criteria,
        false_positive_cost=experiment.false_positive_cost,
        false_negative_cost=experiment.false_negative_cost,
        frozen_at=experiment.frozen_at,
    )
    if replay != experiment:
        raise ValueError("frozen experiment replay detected drift")
    return replay


def _bound_result(experiment, bundle, qualification):
    qualification = _verified(qualification)
    if qualification.packet != bundle.packet:
        raise ValueError("qualification does not bind the exact frozen packet")
    if any(
        submission.metadata.executed_at < experiment.frozen_at
        for submission in (qualification.proposal, qualification.judgment)
    ):
        raise ValueError("declared review timestamp is before frozen experiment")
    return qualification


def calibrate_partition_importance(
    experiment: PartitionExperiment,
    qualification: MachineQualificationResult,
) -> PartitionImportanceCalibration:
    experiment = verify_partition_experiment(experiment)
    qualification = _bound_result(experiment, experiment.calibration, qualification)
    calibration = calibrate_machine_importance(
        qualification,
        candidates=experiment.candidate_criteria,
        false_positive_cost=experiment.false_positive_cost,
        false_negative_cost=experiment.false_negative_cost,
    )
    return PartitionImportanceCalibration(
        experiment_sha256=experiment.experiment_sha256, calibration=calibration
    )


@_stable_arithmetic
def evaluate_partition_importance(
    experiment: PartitionExperiment,
    calibration: PartitionImportanceCalibration,
    qualification: MachineQualificationResult,
) -> PartitionImportanceEvaluation:
    experiment = verify_partition_experiment(experiment)
    calibration = PartitionImportanceCalibration.model_validate(
        calibration.model_dump(mode="json", exclude_computed_fields=True)
    )
    if calibration.experiment_sha256 != experiment.experiment_sha256:
        raise ValueError("calibration experiment binding changed")
    original = _bound_result(
        experiment, experiment.calibration, calibration.calibration.calibration_qualification
    )
    replay = calibrate_machine_importance(
        original,
        candidates=experiment.candidate_criteria,
        false_positive_cost=experiment.false_positive_cost,
        false_negative_cost=experiment.false_negative_cost,
    )
    if replay != calibration.calibration:
        raise ValueError("partition calibration replay detected drift")
    qualification = _bound_result(experiment, experiment.evaluation, qualification)
    readiness, eligible = _population(
        qualification,
        replay.required_evidence,
        tuple(criteria.policy_sha256 for criteria in replay.candidate_criteria),
    )
    evaluation = MachineImportanceEvaluation(
        metrics_policy="common-grid-evidence-v2",
        required_evidence=replay.required_evidence,
        evaluation_qualification=qualification,
        calibration_sha256=replay.calibration_sha256,
        criteria_sha256=replay.criteria.policy_sha256,
        packet_sha256=qualification.packet.packet_sha256,
        qualification_sha256=qualification.result_sha256,
        metrics=_metrics(replay.criteria, readiness, eligible),
    )
    return PartitionImportanceEvaluation(
        experiment_sha256=experiment.experiment_sha256,
        calibration_sha256=calibration.calibration_sha256,
        evaluation=evaluation,
    )
