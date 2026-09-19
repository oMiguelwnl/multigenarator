"""Bounded, source-verified document evaluation commands; no provider execution."""

from decimal import Decimal
from pathlib import Path

import typer
from pydantic import AwareDatetime, Field

from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import ImportantFormCriteria
from multilang.services.qualification_pipeline import ArtifactReference


class PartitionReviewInput(NativeContract):
    partition: ArtifactReference
    references: ArtifactReference
    group_sha256s: tuple[Sha256, ...] = Field(min_length=1, max_length=64)
    profile_sha256: Sha256
    rubric_sha256: Sha256
    packet_id: Identifier


class PartitionExperimentInput(NativeContract):
    calibration: ArtifactReference
    evaluation: ArtifactReference
    candidate_criteria: tuple[ImportantFormCriteria, ...] = Field(min_length=1, max_length=256)
    false_positive_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    false_negative_cost: Decimal = Field(ge=0, le=1000000, allow_inf_nan=False)
    frozen_at: AwareDatetime


class PartitionCalibrationInput(NativeContract):
    experiment: ArtifactReference
    qualification: ArtifactReference


class PartitionEvaluationInput(PartitionCalibrationInput):
    calibration: ArtifactReference


def create_partition_evaluation_app():
    from multilang.services.qualification_evaluation_partitions import (
        DocumentPartitionInput,
        EvaluationDocumentPartition,
        export_evaluation_partition,
        prepare_evaluation_partition,
    )
    from multilang.services.qualification_evaluation_references import (
        DictionaryReferenceInput,
        DictionaryReferenceRegistry,
        prepare_dictionary_references,
    )
    from multilang.services.qualification_machine import MachineQualificationResult
    from multilang.services.qualification_machine_runner import (
        json_bytes,
        persist_artifact,
        read_json,
    )
    from multilang.services.qualification_partition_evaluation import (
        PartitionExperiment,
        PartitionImportanceCalibration,
        calibrate_partition_importance,
        evaluate_partition_importance,
        freeze_partition_experiment,
    )
    from multilang.services.qualification_partition_review import (
        PartitionReviewBundle,
        prepare_partition_review,
    )
    from multilang.vocabulary_cli import _guard, _print

    cli = typer.Typer(
        help="Frozen document partitions and independently reviewed importance evaluation.",
        pretty_exceptions_show_locals=False,
    )

    def load(reference, model):
        return model.model_validate(read_json(reference.path, reference.sha256))

    def save(output, kind, binding, filename, value, **extra):
        return persist_artifact(
            output, kind=kind, binding=binding, files={filename: json_bytes(value), **extra}
        )

    @cli.command("prepare-partition")
    @_guard
    def partition(input: Path, input_sha256: str, output: Path):
        spec = DocumentPartitionInput.model_validate(read_json(input, input_sha256))
        _print(export_evaluation_partition(prepare_evaluation_partition(spec), output))

    @cli.command("prepare-references")
    @_guard
    def references(input: Path, input_sha256: str, output: Path):
        spec = DictionaryReferenceInput.model_validate(read_json(input, input_sha256))
        value = prepare_dictionary_references(spec)
        _print(
            save(
                output,
                "evaluation-dictionary-references",
                value.registry_sha256,
                "references.json",
                value,
            )
        )

    @cli.command("prepare-review")
    @_guard
    def review(input: Path, input_sha256: str, output: Path):
        spec = PartitionReviewInput.model_validate(read_json(input, input_sha256))
        value = prepare_partition_review(
            load(spec.partition, EvaluationDocumentPartition),
            load(spec.references, DictionaryReferenceRegistry),
            group_sha256s=spec.group_sha256s,
            profile_sha256=spec.profile_sha256,
            rubric_sha256=spec.rubric_sha256,
            packet_id=spec.packet_id,
        )
        _print(
            save(
                output,
                "partition-review",
                value.bundle_sha256,
                "bundle.json",
                value,
                **{"packet.json": json_bytes(value.packet)},
            )
        )

    @cli.command("freeze")
    @_guard
    def freeze(input: Path, input_sha256: str, output: Path):
        spec = PartitionExperimentInput.model_validate(read_json(input, input_sha256))
        value = freeze_partition_experiment(
            load(spec.calibration, PartitionReviewBundle),
            load(spec.evaluation, PartitionReviewBundle),
            candidates=spec.candidate_criteria,
            false_positive_cost=spec.false_positive_cost,
            false_negative_cost=spec.false_negative_cost,
            frozen_at=spec.frozen_at,
        )
        _print(
            save(output, "partition-experiment", value.experiment_sha256, "experiment.json", value)
        )

    @cli.command("calibrate")
    @_guard
    def calibrate(input: Path, input_sha256: str, output: Path):
        spec = PartitionCalibrationInput.model_validate(read_json(input, input_sha256))
        value = calibrate_partition_importance(
            load(spec.experiment, PartitionExperiment),
            load(spec.qualification, MachineQualificationResult),
        )
        _print(
            save(output, "partition-calibration", value.calibration_sha256, "result.json", value)
        )

    @cli.command("evaluate")
    @_guard
    def evaluate(input: Path, input_sha256: str, output: Path):
        spec = PartitionEvaluationInput.model_validate(read_json(input, input_sha256))
        value = evaluate_partition_importance(
            load(spec.experiment, PartitionExperiment),
            load(spec.calibration, PartitionImportanceCalibration),
            load(spec.qualification, MachineQualificationResult),
        )
        _print(save(output, "partition-evaluation", value.evaluation_sha256, "result.json", value))

    return cli
