"""Targeted reviews may reopen current agreements without erasing their ancestry."""

import importlib

import pytest
from test_qualification_machine_campaign import machine_result, vocabulary_campaign_fixture

from multilang.services.qualification_machine_campaign import (
    MachineCampaign,
    append_machine_round,
    build_campaign_vocabulary_draft,
)


def api():
    name = "multilang.services.qualification_machine_revision"
    assert importlib.util.find_spec(name), "targeted machine revisions are missing"
    return importlib.import_module(name)


def conflict_plan(tmp_path):
    prepared, profile, campaign = vocabulary_campaign_fixture(tmp_path, conflicting=True)
    plan = api().build_machine_revision(
        campaign,
        round_id="joint-review",
        selections=tuple(
            api().MachineRevisionSelection(item_id=row.item_id, purpose="resolve_identity_conflict")
            for row in campaign.entries
        ),
    )
    return prepared, profile, campaign, plan


def test_joint_revision_preserves_originals_and_resolves_cross_item_conflict(tmp_path):
    prepared, profile, campaign, plan = conflict_plan(tmp_path)
    assert len(plan.parents) == 2
    assert len({row.result_sha256 for row in plan.parents}) == 2
    assert all(row.status == "machine_agreement" for row in plan.parents)
    assert all(len(row.sources) >= 2 for row in plan.packet.items)
    result = machine_result(plan.packet, tag="joint-review")
    updated = append_machine_round(campaign, plan, (result,))
    assert updated.schema_version == 2
    assert updated.base_result == campaign.base_result
    assert updated.rounds[:-1] == campaign.rounds
    assert MachineCampaign.model_validate_json(updated.model_dump_json()) == updated
    draft = build_campaign_vocabulary_draft(
        updated,
        preparation_dir=prepared,
        profile=profile,
        source_id="prepared-dictionary",
        source_version="fixture",
    )
    assert draft.conflicting_lexical_mappings == ()
    assert len(draft.proposed_lexical_mappings) == 2
    assert draft.production_eligible is False


def test_joint_revision_requires_every_member_of_a_conflicting_identity(tmp_path):
    _, _, campaign = vocabulary_campaign_fixture(tmp_path, conflicting=True)
    with pytest.raises(ValueError, match="complete.*conflict|conflict.*coverage"):
        api().build_machine_revision(
            campaign,
            round_id="partial",
            selections=(
                api().MachineRevisionSelection(
                    item_id=campaign.entries[0].item_id, purpose="resolve_identity_conflict"
                ),
            ),
        )


def test_targeted_revision_cannot_replace_a_newer_effective_decision(tmp_path):
    _, _, campaign, plan = conflict_plan(tmp_path)
    another = api().build_machine_revision(
        campaign,
        round_id="another",
        selections=tuple(
            api().MachineRevisionSelection.model_validate(row.model_dump())
            for row in plan.selections
        ),
    )
    newer = append_machine_round(campaign, plan, (machine_result(plan.packet, tag="newer"),))
    with pytest.raises(ValueError, match="stale|parent state"):
        append_machine_round(newer, another, (machine_result(another.packet, tag="stale"),))


def test_targeted_review_does_not_relax_pending_or_rating_selection(tmp_path):
    _, _, campaign = vocabulary_campaign_fixture(tmp_path, conflicting=True)
    for purpose in ("resolve_pending", "complete_importance"):
        with pytest.raises(ValueError, match="purpose|pending|form"):
            api().build_machine_revision(
                campaign,
                round_id="invalid",
                selections=(
                    api().MachineRevisionSelection(
                        item_id=campaign.entries[0].item_id,
                        purpose=purpose,
                    ),
                ),
            )


def test_plan_cannot_change_original_lexical_sources_or_identity(tmp_path):
    _, _, campaign, plan = conflict_plan(tmp_path)
    raw = plan.model_dump(mode="json", exclude_computed_fields=True)
    raw["packet"]["items"][0]["lemma"] = "invented"
    with pytest.raises(ValueError, match="item|source|packet|identity"):
        altered = api().MachineRevisionPlan.model_validate(raw)
        append_machine_round(campaign, altered, (machine_result(altered.packet, tag="tampered"),))
