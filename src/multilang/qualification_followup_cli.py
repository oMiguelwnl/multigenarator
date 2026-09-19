"""Explicit local commands for machine review rounds and draft previews."""

from pathlib import Path

from pydantic import Field

from multilang.domain.language_profiles import NativeContract
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact, read_json
from multilang.services.qualification_pipeline import ArtifactReference


class MachineRoundResultsInput(NativeContract):
    results: tuple[ArtifactReference, ...] = Field(min_length=1, max_length=100)


def register_followup_commands(cli):
    from multilang.domain.language_profiles import LanguageProfile
    from multilang.domain.lexical_identity import ImportantFormCriteria, canonical_sha256
    from multilang.services.qualification_machine import MachineQualificationResult
    from multilang.services.qualification_machine_campaign import (
        MachineCampaign,
        append_machine_round,
        build_campaign_vocabulary_draft,
        build_machine_campaign,
        prepare_campaign_followup,
        render_machine_campaign,
    )
    from multilang.services.qualification_machine_followup import (
        MachineFollowupPlan,
        build_machine_followup,
        export_machine_followup,
    )
    from multilang.vocabulary_cli import _guard, _print

    def result_input(path, sha):
        return MachineQualificationResult.model_validate(read_json(path, sha))

    def campaign_input(path, sha):
        return MachineCampaign.model_validate(read_json(path, sha))

    def save_campaign(campaign, output):
        return persist_artifact(
            output,
            kind="machine-campaign",
            binding=campaign.campaign_sha256,
            files={
                "campaign.json": json_bytes(campaign),
                "report.html": render_machine_campaign(campaign).encode(),
            },
        )

    @cli.command("prepare-followup")
    @_guard
    def prepare_followup(
        result: Path,
        result_sha256: str,
        pipeline: Path,
        manifest_sha256: str,
        round_id: str,
        output: Path,
    ):
        plan = build_machine_followup(
            result_input(result, result_sha256),
            pipeline=pipeline,
            manifest_sha256=manifest_sha256,
            round_id=round_id,
        )
        manifest = export_machine_followup(plan, output)
        _print({**manifest, "selected_items": len(plan.tasks)})

    @cli.command("start-campaign")
    @_guard
    def start_campaign(result: Path, result_sha256: str, campaign_id: str, output: Path):
        campaign = build_machine_campaign(
            result_input(result, result_sha256), campaign_id=campaign_id
        )
        _print(save_campaign(campaign, output))

    @cli.command("prepare-next-followup")
    @_guard
    def prepare_next_followup(
        campaign: Path,
        campaign_sha256: str,
        parent_result_sha256: str,
        pipeline: Path,
        manifest_sha256: str,
        round_id: str,
        output: Path,
    ):
        plan = prepare_campaign_followup(
            campaign_input(campaign, campaign_sha256),
            parent_result_sha256=parent_result_sha256,
            pipeline=pipeline,
            manifest_sha256=manifest_sha256,
            round_id=round_id,
        )
        _print({**export_machine_followup(plan, output), "selected_items": len(plan.tasks)})

    @cli.command("consolidate")
    @_guard
    def consolidate(
        campaign: Path,
        campaign_sha256: str,
        plan: Path,
        plan_sha256: str,
        results: Path,
        results_sha256: str,
        output: Path,
    ):
        parent = campaign_input(campaign, campaign_sha256)
        followup = MachineFollowupPlan.model_validate(read_json(plan, plan_sha256))
        references = MachineRoundResultsInput.model_validate(read_json(results, results_sha256))
        children = tuple(result_input(row.path, row.sha256) for row in references.results)
        updated = append_machine_round(parent, followup, children)
        _print(save_campaign(updated, output))

    @cli.command("campaign-draft")
    @_guard
    def campaign_draft(
        campaign: Path,
        campaign_sha256: str,
        preparation: Path,
        profile: Path,
        profile_sha256: str,
        source_id: str,
        source_version: str,
        output: Path,
        preview_limit: int = 10,
    ):
        from multilang.services.qualification_machine_preview import (
            build_machine_card_preview,
            render_machine_card_preview,
        )

        history = campaign_input(campaign, campaign_sha256)
        language_profile = LanguageProfile.model_validate(read_json(profile, profile_sha256))
        draft = build_campaign_vocabulary_draft(
            history,
            preparation_dir=preparation,
            profile=language_profile,
            source_id=source_id,
            source_version=source_version,
        )
        preview = build_machine_card_preview(
            draft.proposed_lexical_mappings,
            language=language_profile.language,
            limit=preview_limit,
        )
        _print(
            persist_artifact(
                output,
                kind="machine-campaign-draft",
                binding=canonical_sha256([draft.draft_sha256, preview.preview_sha256]),
                files={
                    "draft.json": json_bytes(draft),
                    "pending-native-review.json": json_bytes(draft.pending_native_review),
                    "preview.json": json_bytes(preview),
                    "preview.html": render_machine_card_preview(
                        preview, conflicting_mapping_count=len(draft.conflicting_lexical_mappings)
                    ).encode(),
                },
            )
        )

    @cli.command("readiness")
    @_guard
    def readiness(
        result: Path,
        result_sha256: str,
        criteria: Path,
        criteria_sha256: str,
        output: Path,
    ):
        from multilang.services.qualification_machine_calibration import (
            machine_calibration_readiness,
        )

        raw = read_json(criteria, criteria_sha256)
        if not isinstance(raw, list) or not 1 <= len(raw) <= 256:
            raise ValueError("machine readiness requires a bounded criteria array")
        value = machine_calibration_readiness(
            result_input(result, result_sha256),
            candidates=tuple(ImportantFormCriteria.model_validate(item) for item in raw),
        )
        _print(
            persist_artifact(
                output,
                kind="machine-calibration-readiness",
                binding=canonical_sha256(value.model_dump(mode="json")),
                files={"readiness.json": json_bytes(value)},
            )
        )
