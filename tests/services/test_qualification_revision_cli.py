"""The public CLI can prepare and consolidate a source-bound joint revision."""

import json

from test_qualification_followup_cli import invoke, save, sha
from test_qualification_machine_campaign import machine_result, vocabulary_campaign_fixture
from test_qualification_machine_observation_revision import digest, qualification
from test_qualification_machine_observation_revision import observation as observation

from multilang.services.qualification_machine_revision import MachineRevisionPlan


def test_cli_targeted_revision_replays_without_replacing_old_history(tmp_path):
    _, _, campaign = vocabulary_campaign_fixture(tmp_path, conflicting=True)
    parent = save(tmp_path / "parent.json", campaign)
    options = save(
        tmp_path / "options.json",
        {
            "round_id": "joint-cli",
            "selections": [
                {"item_id": entry.item_id, "purpose": "resolve_identity_conflict"}
                for entry in campaign.entries
            ],
        },
    )
    output = tmp_path / "revision"
    invoke("prepare-revision", *parent, *options, str(output))
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    invoke("prepare-revision", *parent, *options, str(output))
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
    plan = MachineRevisionPlan.model_validate_json((output / "plan.json").read_bytes())
    result = save(tmp_path / "result.json", machine_result(plan.packet, tag="cli-joint"))
    results = save(
        tmp_path / "results.json", {"results": [{"path": result[0], "sha256": result[1]}]}
    )
    combined = tmp_path / "combined"
    invoke(
        "consolidate",
        *parent,
        str(output / "plan.json"),
        sha(output / "plan.json"),
        *results,
        str(combined),
    )
    value = json.loads((combined / "campaign.json").read_text())
    assert value["schema_version"] == 2
    assert value["base_result"] == campaign.base_result.model_dump(mode="json")
    assert len(value["rounds"]) == len(campaign.rounds) + 1
    assert value["production_eligible"] is False


def test_cli_observation_revision_keeps_original_denominator(observation, tmp_path):
    from multilang.services.qualification_machine_observation_revision import (
        MachineObservationRevisionPlan,
    )

    original = save(tmp_path / "observation.json", observation)
    options = save(
        tmp_path / "selection.json",
        {
            "observation": {"path": original[0], "sha256": original[1]},
            "revision_id": "case-cli",
            "occurrence_sha256s": [
                digest(row) for row in observation.occurrences if row.text == "aberto"
            ],
            "profile_sha256": "b" * 64,
            "rubric_sha256": "c" * 64,
        },
    )
    prepared = tmp_path / "prepared"
    invoke("prepare-observation-revision", *options, str(prepared))
    plan = MachineObservationRevisionPlan.model_validate_json((prepared / "plan.json").read_bytes())
    result = save(tmp_path / "review.json", qualification(plan))
    apply_options = save(
        tmp_path / "apply.json",
        {
            "plan": {"path": str(prepared / "plan.json"), "sha256": sha(prepared / "plan.json")},
            "qualification": {"path": result[0], "sha256": result[1]},
        },
    )
    output = tmp_path / "derived"
    invoke("apply-observation-revision", *apply_options, str(output))
    derived = json.loads((output / "revision.json").read_text())
    assert derived["plan"]["original"] == observation.model_dump(mode="json")
    assert derived["measurement"]["effective_token_count"] == 6
    assert derived["production_eligible"] is False
