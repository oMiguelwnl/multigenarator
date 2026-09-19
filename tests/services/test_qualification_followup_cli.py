"""Exercise immutable round artifacts through the public qualification CLI."""

import hashlib
import json

from test_qualification_machine_campaign import round_fixture
from test_qualification_machine_draft import draft_fixture
from typer.testing import CliRunner

from multilang.qualification_machine_cli import create_machine_qualification_app
from multilang.services.qualification_machine_runner import json_bytes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_bytes(json_bytes(value))
    return str(path), sha(path)


def invoke(*args):
    result = CliRunner().invoke(create_machine_qualification_app(), list(args))
    assert result.exit_code == 0, result.output
    return result


def test_cli_campaign_draft_includes_nonexportable_preview_and_pending_native_review(tmp_path):
    original, result = draft_fixture(tmp_path)
    source = save(tmp_path / "result.json", result)
    campaign = tmp_path / "campaign"
    invoke("start-campaign", *source, "demo", str(campaign))
    profile = save(tmp_path / "profile.json", original["profile"])
    out = tmp_path / "draft"
    args = (
        "campaign-draft",
        str(campaign / "campaign.json"),
        sha(campaign / "campaign.json"),
        str(original["preparation_dir"]),
        *profile,
        "synthetic",
        "1",
        str(out),
    )
    invoke(*args)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    invoke(*args)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}
    preview = json.loads((out / "preview.json").read_text())
    assert preview["cards"][0]["fields"]["word"] == "go"
    assert len(preview["cards"][0]["fields"]) == 9
    assert preview["exportable"] is False
    native = json.loads((out / "pending-native-review.json").read_text())
    assert native["senses"][0]["decision"] == "pending"


def test_cli_consolidates_exact_followup_and_reports_coverage(tmp_path):
    base, plan, result = round_fixture(tmp_path)
    source = save(tmp_path / "base.json", base)
    campaign = tmp_path / "campaign"
    invoke("start-campaign", *source, "pt", str(campaign))
    pipeline = tmp_path / "pipeline"
    prepared = tmp_path / "followup"
    invoke(
        "prepare-followup",
        *source,
        str(pipeline),
        sha(pipeline / "manifest.json"),
        "round-2",
        str(prepared),
    )
    child = save(tmp_path / "result.json", result)
    refs = save(tmp_path / "results.json", {"results": [{"path": child[0], "sha256": child[1]}]})
    out = tmp_path / "consolidated"
    invoke(
        "consolidate",
        str(campaign / "campaign.json"),
        sha(campaign / "campaign.json"),
        str(prepared / "plan.json"),
        sha(prepared / "plan.json"),
        *refs,
        str(out),
    )
    combined = json.loads((out / "campaign.json").read_text())
    assert len(combined["entries"]) == len(base.packet.items)
    assert {row["status"] for row in combined["entries"]} == {"machine_agreement"}
    assert (out / "report.html").exists()
    wrong = CliRunner().invoke(
        create_machine_qualification_app(),
        [
            "consolidate",
            str(campaign / "campaign.json"),
            "f" * 64,
            str(prepared / "plan.json"),
            sha(prepared / "plan.json"),
            *refs,
            str(tmp_path / "bad"),
        ],
    )
    assert wrong.exit_code != 0 and not (tmp_path / "bad").exists()


def test_cli_readiness_exposes_abstentions_instead_of_calibrating_missing_labels(tmp_path):
    from test_qualification_machine_calibration import _criteria

    base, _, _ = round_fixture(tmp_path)
    source = save(tmp_path / "result.json", base)
    grid = save(tmp_path / "criteria.json", [_criteria().model_dump(mode="json")])
    out = tmp_path / "readiness"
    invoke("readiness", *source, *grid, str(out))
    report = json.loads((out / "readiness.json").read_text())
    assert report["ready_for_calibration"] is False
    assert report["usable_labels"] == 0
    assert report["abstentions"] >= 1


def test_cli_prepares_next_followup_using_campaign_ancestry(tmp_path):
    from test_qualification_machine_campaign import machine_result

    from multilang.services.qualification_machine_campaign import (
        append_machine_round,
        build_machine_campaign,
    )

    base, plan, _ = round_fixture(tmp_path)
    pending = machine_result(plan.enrichment.packet, tag="second-cli", pending_forms=True)
    campaign = append_machine_round(
        build_machine_campaign(base, campaign_id="pt"), plan, (pending,)
    )
    source = save(tmp_path / "campaign.json", campaign)
    output = tmp_path / "third"
    args = (
        "prepare-next-followup",
        *source,
        pending.result_sha256,
        str(tmp_path / "pipeline"),
        sha(tmp_path / "pipeline" / "manifest.json"),
        "round-3",
        str(output),
    )
    invoke(*args)
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    invoke(*args)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
    next_plan = json.loads((output / "plan.json").read_text())
    assert next_plan["base_result_sha256"] == pending.result_sha256
    assert len(next_plan["tasks"]) == len(pending.packet.items)


def test_cli_preserves_conflicting_proposals_without_previewing_either(tmp_path):
    from test_qualification_machine_campaign import vocabulary_campaign_fixture

    prepared, profile, campaign = vocabulary_campaign_fixture(tmp_path, conflicting=True)
    source = save(tmp_path / "campaign.json", campaign)
    profile_input = save(tmp_path / "profile.json", profile)
    out = tmp_path / "draft"
    invoke(
        "campaign-draft",
        *source,
        str(prepared),
        *profile_input,
        "prepared-dictionary",
        "fixture",
        str(out),
    )
    draft = json.loads((out / "draft.json").read_text())
    assert len(draft["conflicting_lexical_mappings"]) == 2
    assert json.loads((out / "preview.json").read_text())["cards"] == []
    assert "Mapeamentos em conflito, fora da prévia: 2" in (out / "preview.html").read_text()
