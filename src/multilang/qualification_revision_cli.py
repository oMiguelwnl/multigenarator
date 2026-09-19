"""Prepare an explicit review of current pending, conflicting or unrated decisions."""

from pathlib import Path

from pydantic import Field

from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.services.qualification_machine_revision import (
    MachineRevisionSelection,
    MachineRevisionSupplement,
)
from multilang.services.qualification_machine_sources import VerifiedReviewExcerpt
from multilang.services.qualification_pipeline import ArtifactReference


class MachineRevisionInput(NativeContract):
    round_id: Identifier
    selections: tuple[MachineRevisionSelection, ...] = Field(min_length=1, max_length=5000)
    supplements: tuple[MachineRevisionSupplement, ...] = Field(default=(), max_length=128)


class ObservationRevisionInput(NativeContract):
    observation: ArtifactReference
    revision_id: Identifier
    occurrence_sha256s: tuple[Sha256, ...] = Field(min_length=1, max_length=5000)
    profile_sha256: Sha256
    rubric_sha256: Sha256
    supplemental_sources: dict[Sha256, tuple[VerifiedReviewExcerpt, ...]] = Field(
        default_factory=dict, max_length=5000
    )


class ObservationRevisionApplyInput(NativeContract):
    plan: ArtifactReference
    qualification: ArtifactReference


def register_revision_commands(cli):
    from multilang.services.qualification_machine_campaign import MachineCampaign
    from multilang.services.qualification_machine_revision import (
        build_machine_revision,
        export_machine_revision,
    )
    from multilang.services.qualification_machine_runner import (
        json_bytes,
        persist_artifact,
        read_json,
    )
    from multilang.vocabulary_cli import _guard, _print

    @cli.command("prepare-revision")
    @_guard
    def prepare_revision(
        campaign: Path,
        campaign_sha256: str,
        config: Path,
        config_sha256: str,
        output: Path,
    ):
        history = MachineCampaign.model_validate(read_json(campaign, campaign_sha256))
        options = MachineRevisionInput.model_validate(read_json(config, config_sha256))
        plan = build_machine_revision(
            history,
            round_id=options.round_id,
            selections=options.selections,
            supplements=options.supplements,
        )
        _print({**export_machine_revision(plan, output), "selected_items": len(plan.packet.items)})

    @cli.command("prepare-observation-revision")
    @_guard
    def prepare_observation(input: Path, input_sha256: str, output: Path):
        from multilang.domain.lexical_identity import canonical_sha256
        from multilang.services.qualification_machine_observation_revision import (
            build_machine_observation_revision,
        )
        from multilang.services.qualification_observations import CorpusObservationResult

        config = ObservationRevisionInput.model_validate(read_json(input, input_sha256))
        original = CorpusObservationResult.model_validate(
            read_json(config.observation.path, config.observation.sha256)
        )
        plan = build_machine_observation_revision(
            original,
            original_sha256=canonical_sha256(
                original.model_dump(mode="json", exclude_computed_fields=True)
            ),
            revision_id=config.revision_id,
            occurrence_sha256s=config.occurrence_sha256s,
            profile_sha256=config.profile_sha256,
            rubric_sha256=config.rubric_sha256,
            supplemental_sources=config.supplemental_sources,
        )
        _print(
            persist_artifact(
                output,
                kind="machine-observation-revision-plan",
                binding=plan.plan_sha256,
                files={"plan.json": json_bytes(plan), "packet.json": json_bytes(plan.packet)},
            )
        )

    @cli.command("apply-observation-revision")
    @_guard
    def apply_observation(input: Path, input_sha256: str, output: Path):
        from multilang.services.qualification_machine import MachineQualificationResult
        from multilang.services.qualification_machine_observation_revision import (
            MachineObservationRevisionPlan,
            apply_machine_observation_revision,
        )

        config = ObservationRevisionApplyInput.model_validate(read_json(input, input_sha256))
        plan = MachineObservationRevisionPlan.model_validate(
            read_json(config.plan.path, config.plan.sha256)
        )
        qualification = MachineQualificationResult.model_validate(
            read_json(config.qualification.path, config.qualification.sha256)
        )
        result = apply_machine_observation_revision(plan, qualification)
        _print(
            persist_artifact(
                output,
                kind="machine-observation-revision",
                binding=result.revision_sha256,
                files={
                    "revision.json": json_bytes(result),
                    "measurement.json": json_bytes(result.measurement),
                },
            )
        )
