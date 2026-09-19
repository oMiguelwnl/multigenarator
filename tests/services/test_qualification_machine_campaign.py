"""A later machine review must never erase history or replace unrelated decisions."""

import importlib

import pytest
from test_qualification_machine_draft import draft_fixture


def api():
    name = "multilang.services.qualification_machine_campaign"
    assert importlib.util.find_spec(name) is not None, "campaign coordination is missing"
    return importlib.import_module(name)


def test_base_campaign_retains_decision_and_original_evidence(tmp_path):
    _, result = draft_fixture(tmp_path)
    campaign = api().build_machine_campaign(result, campaign_id="pt-followup")
    assert len(campaign.entries) == 1
    entry = campaign.entries[0]
    assert entry.status == "machine_agreement"
    assert entry.source_result_sha256 == result.result_sha256
    assert entry.item_sha256 == result.packet.items[0].item_sha256
    assert campaign.changes == ()
    assert campaign.origin == "machine" and campaign.production_eligible is False
    assert api().MachineCampaign.model_validate_json(campaign.model_dump_json()) == campaign


def test_campaign_rejects_forged_effective_decision(tmp_path):
    _, result = draft_fixture(tmp_path)
    campaign = api().build_machine_campaign(result, campaign_id="pt-followup")
    raw = campaign.model_dump(mode="json", exclude_computed_fields=True)
    raw["entries"][0]["source_result_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="projection"):
        api().MachineCampaign.model_validate(raw)


def test_campaign_draft_is_source_bound_and_keeps_native_decisions_pending(tmp_path):
    original, result = draft_fixture(tmp_path)
    campaign = api().build_machine_campaign(result, campaign_id="pt-followup")
    draft = api().build_campaign_vocabulary_draft(
        campaign,
        preparation_dir=original["preparation_dir"],
        profile=original["profile"],
        source_id="synthetic",
        source_version="1",
    )
    assert len(draft.proposed_lexical_mappings) == 1
    assert draft.proposed_lexical_mappings[0].decision.proposed_sense_id == "motion"
    assert draft.pending_native_review.senses[0].decision == "pending"
    assert draft.pending_native_review.senses[0].receipt_id is None
    assert draft.campaign_sha256 == campaign.campaign_sha256
    assert draft.production_eligible is False


def test_campaign_report_has_no_active_content(tmp_path):
    _, result = draft_fixture(tmp_path)
    campaign = api().build_machine_campaign(result, campaign_id="<script>alert(1)</script>")
    html = api().render_machine_campaign(campaign)
    assert "<script" not in html
    assert "&lt;script&gt;" in html
    assert "Content-Security-Policy" in html


def machine_result(packet, *, tag, pending_forms=False, pending_ids=(), lexical_glosses=None):
    from test_qualification_machine_runner import metadata_fixture

    from multilang.services.qualification_machine import (
        MachineActor,
        accept_machine_response,
        build_machine_request,
        reconcile_machine_reviews,
    )

    decisions = []
    for item in packet.items:
        pending = (pending_forms and item.kind == "form") or item.item_id in pending_ids
        source = item.sources[0]
        row = dict(
            item_id=item.item_id,
            item_sha256=item.item_sha256,
            kind=item.kind,
            decision="inconclusive" if pending else "accepted",
            reason="Synthetic fixture: source-backed identity and inclusion assessment.",
            uncertainties=["context_missing"] if pending else [],
            citations=[
                dict(
                    source_index=0,
                    source_sha256=source.source_sha256,
                    start=0,
                    end=min(30, len(source.excerpt)),
                    quote=source.excerpt[:30],
                )
            ],
        )
        if not pending:
            if item.kind == "lexical":
                row.update(
                    proposed_lemma=item.lemma,
                    proposed_pos=item.pos,
                    proposed_sense_id="day",
                    proposed_gloss=(lexical_glosses or {}).get(item.item_id, "day"),
                )
            elif item.kind == "form":
                row.update(include=False, proposed_sense_id="day", machine_analysis_rating=1)
        decisions.append(row)
    proposal_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id=tag, context_id=tag, execution_surface="mock"),
        run_id=tag,
    )
    proposal = accept_machine_response(
        proposal_request, {"decisions": decisions}, metadata=metadata_fixture()
    )
    judgment_request = build_machine_request(
        packet,
        actor=MachineActor(
            actor_id=tag + "-judge", context_id=tag + "-judge", execution_surface="mock"
        ),
        run_id=tag + "-judge",
        proposal=proposal,
    )
    judgment = accept_machine_response(
        judgment_request, {"decisions": decisions}, metadata=metadata_fixture()
    )
    return reconcile_machine_reviews(packet, proposal, judgment)


def round_fixture(tmp_path):
    from test_qualification_machine_evidence import published, sha

    from multilang.services.qualification_machine_followup import build_machine_followup

    root, packet = published(tmp_path)
    base = machine_result(packet, tag="initial", pending_forms=True)
    plan = build_machine_followup(
        base, pipeline=root, manifest_sha256=sha(root / "manifest.json"), round_id="round-2"
    )
    result = machine_result(plan.enrichment.packet, tag="followup")
    return base, plan, result


def test_followup_only_replaces_its_pending_items_and_retains_full_history(tmp_path):
    api()
    base, plan, result = round_fixture(tmp_path)
    campaign = api().build_machine_campaign(base, campaign_id="pt")
    updated = api().append_machine_round(campaign, plan, (result,))
    initial_lexical = next(row for row in updated.entries if row.kind == "lexical")
    assert initial_lexical.source_result_sha256 == base.result_sha256
    assert all(
        row.source_result_sha256 == result.result_sha256
        for row in updated.entries
        if row.kind == "form"
    )
    assert len(updated.entries) == len(base.packet.items)
    assert {change.before_status for change in updated.changes} == {"blocked_uncertainty"}
    assert {change.after_status for change in updated.changes} == {"machine_agreement"}
    assert updated.base_result == base and updated.rounds[0].qualifications == (result,)
    assert campaign.rounds == ()


def test_campaign_prepares_third_round_from_verified_history(tmp_path):
    from test_qualification_machine_evidence import sha

    base, plan, _ = round_fixture(tmp_path)
    pending = machine_result(plan.enrichment.packet, tag="second", pending_forms=True)
    campaign = api().append_machine_round(
        api().build_machine_campaign(base, campaign_id="pt"), plan, (pending,)
    )
    next_plan = api().prepare_campaign_followup(
        campaign,
        parent_result_sha256=pending.result_sha256,
        pipeline=tmp_path / "pipeline",
        manifest_sha256=sha(tmp_path / "pipeline" / "manifest.json"),
        round_id="round-3",
    )
    assert next_plan.base_result_sha256 == pending.result_sha256
    assert next_plan.enrichment.packet.items == pending.packet.items
    resolved = machine_result(next_plan.enrichment.packet, tag="third")
    final = api().append_machine_round(campaign, next_plan, (resolved,))
    assert len(final.rounds) == 2
    assert {row.status for row in final.entries} == {"machine_agreement"}
    assert final.base_result == base


def test_campaign_followup_rejects_stale_unknown_parent_and_used_round(tmp_path):
    from test_qualification_machine_evidence import sha

    base, plan, result = round_fixture(tmp_path)
    campaign = api().append_machine_round(
        api().build_machine_campaign(base, campaign_id="pt"), plan, (result,)
    )
    args = dict(
        pipeline=tmp_path / "pipeline",
        manifest_sha256=sha(tmp_path / "pipeline" / "manifest.json"),
        round_id="round-3",
    )
    with pytest.raises(ValueError, match="stale"):
        api().prepare_campaign_followup(campaign, parent_result_sha256=base.result_sha256, **args)
    with pytest.raises(ValueError, match="not in campaign"):
        api().prepare_campaign_followup(campaign, parent_result_sha256="f" * 64, **args)
    args["round_id"] = "round-2"
    with pytest.raises(ValueError, match="duplicate"):
        api().prepare_campaign_followup(campaign, parent_result_sha256=result.result_sha256, **args)


def test_campaign_requires_complete_nonduplicated_followup_coverage(tmp_path):
    api()
    base, plan, result = round_fixture(tmp_path)
    campaign = api().build_machine_campaign(base, campaign_id="pt")
    with pytest.raises(ValueError, match="duplicate|coverage"):
        api().append_machine_round(campaign, plan, (result, result))
    subset = result.packet.model_copy(update={"items": result.packet.items[:1]})
    if len(result.packet.items) > 1:
        with pytest.raises(ValueError, match="coverage"):
            api().append_machine_round(campaign, plan, (machine_result(subset, tag="subset"),))


def test_campaign_rejects_stale_round_and_changed_packet_facts(tmp_path):
    api()
    base, plan, result = round_fixture(tmp_path)
    campaign = api().build_machine_campaign(base, campaign_id="pt")
    updated = api().append_machine_round(campaign, plan, (result,))
    with pytest.raises(ValueError, match="round|stale"):
        api().append_machine_round(updated, plan, (result,))
    first = result.packet.items[0]
    changed = first.model_copy(update={"lemma": "changed"})
    altered = result.packet.model_copy(update={"items": (changed, *result.packet.items[1:])})
    with pytest.raises(ValueError, match="item|packet"):
        api().append_machine_round(campaign, plan, (machine_result(altered, tag="altered"),))


def test_different_round_id_cannot_overwrite_newer_decisions_from_old_parent(tmp_path):
    from test_qualification_machine_evidence import sha

    from multilang.services.qualification_machine_followup import build_machine_followup

    base, plan, result = round_fixture(tmp_path)
    updated = api().append_machine_round(
        api().build_machine_campaign(base, campaign_id="pt"), plan, (result,)
    )
    other = build_machine_followup(
        base,
        pipeline=tmp_path / "pipeline",
        manifest_sha256=sha(tmp_path / "pipeline/manifest.json"),
        round_id="third",
    )
    with pytest.raises(ValueError, match="stale"):
        api().append_machine_round(
            updated, other, (machine_result(other.enrichment.packet, tag="third"),)
        )


def test_campaign_rejects_reused_context_and_changed_language(tmp_path):
    base, plan, _ = round_fixture(tmp_path)
    campaign = api().build_machine_campaign(base, campaign_id="pt")
    with pytest.raises(ValueError, match="fresh execution contexts"):
        api().append_machine_round(
            campaign, plan, (machine_result(plan.enrichment.packet, tag="initial"),)
        )
    packet = plan.enrichment.packet.model_copy(update={"language": "en"})
    with pytest.raises(ValueError, match="scope"):
        api().append_machine_round(campaign, plan, (machine_result(packet, tag="other"),))


def vocabulary_campaign_fixture(tmp_path, *, conflicting=False):
    import json

    from test_qualification_machine_evidence import sha

    from multilang.domain.lexical_identity import canonical_sha256
    from multilang.services.language_profiles import LanguageProfileRegistry
    from multilang.services.qualification_machine_followup import build_machine_followup
    from multilang.services.qualification_pipeline import (
        QualificationPipelineRequest,
        run_qualification_pipeline,
    )
    from multilang.services.qualification_review import ReviewPacket
    from multilang.services.vocabulary_preparation import prepare_vocabulary

    source = tmp_path / "dictionary.jsonl"
    source.write_text(
        "\n".join(
            json.dumps(dict(lang_code="en", word=word, pos="verb", senses=[dict(glosses=[gloss])]))
            for word, gloss in (("go", "move"), ("go" if conflicting else "stop", "cease"))
        )
        + "\n"
    )
    prepared = tmp_path / "prepared"
    prepare_vocabulary(
        language="en", dictionary=source, dictionary_sha256=sha(source), output=prepared
    )
    profile = (
        LanguageProfileRegistry()
        .get("en")
        .model_copy(update={"source_ids": ("prepared-dictionary",)})
    )
    request = QualificationPipelineRequest(
        language="en",
        prepared_inputs=[dict(directory=prepared, manifest_sha256=sha(prepared / "manifest.json"))],
        seed_words=("go", "stop"),
        seed_provenance=dict(
            requested_language="en",
            effective_language="en",
            source="explicit",
            source_version="fixture",
            raw_seed_words=("go", "stop"),
            selection_reason="Fixture",
        ),
        profile_sha256=canonical_sha256(profile.model_dump(mode="json")),
        rubric_sha256="b" * 64,
        headword_count=2,
    )
    root = tmp_path / "pipeline"
    manifest = run_qualification_pipeline(request, root)
    name = next(
        name for name in manifest["files"] if "lexical-" in name and name.endswith("/packet.json")
    )
    packet = ReviewPacket.model_validate_json((root / name).read_text())
    base = machine_result(packet, tag="initial", pending_ids=(packet.items[-1].item_id,))
    plan = build_machine_followup(
        base, pipeline=root, manifest_sha256=sha(root / "manifest.json"), round_id="second"
    )
    result = machine_result(
        plan.enrichment.packet,
        tag="second",
        lexical_glosses={plan.enrichment.packet.items[0].item_id: "conflicting meaning"}
        if conflicting
        else None,
    )
    campaign = api().append_machine_round(
        api().build_machine_campaign(base, campaign_id="en"), plan, (result,)
    )
    return prepared, profile, campaign


def test_consolidated_draft_keeps_both_rounds_and_removes_resolved_issues(tmp_path):
    prepared, profile, campaign = vocabulary_campaign_fixture(tmp_path)
    draft = api().build_campaign_vocabulary_draft(
        campaign,
        preparation_dir=prepared,
        profile=profile,
        source_id="prepared-dictionary",
        source_version="fixture",
    )
    assert {mapping.original_lemma for mapping in draft.proposed_lexical_mappings} == {"go", "stop"}
    assert len(draft.source_draft_sha256s) == 2
    assert draft.uncertainty_queue == ()
    assert len(draft.pending_native_review.senses) == 2
    assert all(sense.decision == "pending" for sense in draft.pending_native_review.senses)


def test_draft_rejects_preparation_changed_between_round_reads(tmp_path, monkeypatch):
    prepared, profile, campaign = vocabulary_campaign_fixture(tmp_path)
    original = api().build_machine_vocabulary_draft
    calls = 0

    def changing_preparation(**kwargs):
        nonlocal calls
        draft = original(**kwargs)
        calls += 1
        if calls == 2:
            # Emulate a complete newer preparation returned by the I/O boundary.
            draft = draft.model_copy(
                update={
                    "preparation_sha256": "f" * 64,
                    "pending_native_review": draft.pending_native_review.model_copy(
                        update={"preparation_sha256": "f" * 64}
                    ),
                }
            )
        return draft

    monkeypatch.setattr(api(), "build_machine_vocabulary_draft", changing_preparation)
    with pytest.raises(ValueError, match="preparation.*changed"):
        api().build_campaign_vocabulary_draft(
            campaign,
            preparation_dir=prepared,
            profile=profile,
            source_id="prepared-dictionary",
            source_version="fixture",
        )


def test_conflicting_meanings_keep_both_reviews_but_quarantine_both_mappings(tmp_path):
    prepared, profile, campaign = vocabulary_campaign_fixture(tmp_path, conflicting=True)
    draft = api().build_campaign_vocabulary_draft(
        campaign,
        preparation_dir=prepared,
        profile=profile,
        source_id="prepared-dictionary",
        source_version="fixture",
    )
    assert {row.status for row in campaign.entries} == {"machine_agreement"}
    assert draft.proposed_lexical_mappings == ()
    assert len(draft.conflicting_lexical_mappings) == 2
    assert {row.decision.proposed_gloss for row in draft.conflicting_lexical_mappings} == {
        "day",
        "conflicting meaning",
    }
    assert {row.reason for row in draft.uncertainty_queue} == {
        "conflicting_machine_lexical_identity"
    }
    assert len(draft.pending_native_review.senses) == 2
