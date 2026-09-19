"""A second machine round asks only unresolved, source-bound questions."""

import importlib
import json

import pytest
from test_qualification_machine_evidence import published, sha
from test_qualification_machine_runner import metadata_fixture

from multilang.services.qualification_machine import (
    MachineActor,
    accept_machine_response,
    build_machine_request,
    reconcile_machine_reviews,
)


def api():
    return importlib.import_module("multilang.services.qualification_machine_followup")


def qualification_fixture(tmp_path, *, lexical="accepted", form="inconclusive"):
    root, packet = published(tmp_path)
    responses = []
    for judgment in (False, True):
        decisions = []
        for item in packet.items:
            verdict = lexical if item.kind == "lexical" else form
            source = item.sources[0]
            decision = dict(
                kind=item.kind,
                item_id=item.item_id,
                item_sha256=item.item_sha256,
                decision=verdict,
                reason="Synthetic unresolved sense and insufficient context."
                if verdict == "inconclusive"
                else "Synthetic decision with exact evidence.",
                uncertainties=("sense_context_missing",) if verdict == "inconclusive" else (),
            )
            if verdict == "accepted":
                decision["citations"] = [
                    dict(
                        source_index=0,
                        source_sha256=source.source_sha256,
                        start=0,
                        end=len(source.excerpt),
                        quote=source.excerpt,
                    )
                ]
                if item.kind == "lexical":
                    decision.update(
                        proposed_lemma="dia",
                        proposed_pos="NOUN",
                        proposed_sense_id="day",
                        proposed_gloss="day",
                    )
                else:
                    decision.update(include=not judgment, proposed_sense_id="day")
            decisions.append(decision)
        responses.append(dict(decisions=decisions))
    proposal_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="proposer", context_id="p", execution_surface="mock"),
        run_id="p",
    )
    proposal = accept_machine_response(proposal_request, responses[0], metadata=metadata_fixture())
    judgment_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="judge", context_id="j", execution_surface="mock"),
        run_id="j",
        proposal=proposal,
    )
    judgment = accept_machine_response(judgment_request, responses[1], metadata=metadata_fixture())
    return root, reconcile_machine_reviews(packet, proposal, judgment)


def followup_fixture(tmp_path, **kwargs):
    root, result = qualification_fixture(tmp_path, **kwargs)
    plan = api().build_machine_followup(
        result, pipeline=root, manifest_sha256=sha(root / "manifest.json"), round_id="round-2"
    )
    return root, result, plan


@pytest.mark.parametrize("lexical", ["accepted", "rejected"])
def test_only_pending_items_are_enriched_and_review_tasks_never_become_sources(tmp_path, lexical):
    root, result, plan = followup_fixture(tmp_path, lexical=lexical)
    assert len(plan.tasks) == len(plan.enrichment.packet.items) == 1
    original = next(item for item in result.packet.items if item.kind == "form")
    enriched = plan.enrichment.packet.items[0]
    task = plan.tasks[0]
    assert task.item_id == enriched.item_id == original.item_id
    assert task.parent_item_sha256 == original.item_sha256
    assert task.enriched_item_sha256 == enriched.item_sha256
    assert task.parent_status == "blocked_uncertainty"
    assert task.reason_codes == ("sense_context_missing", "unresolved_evidence")
    assert {"sense_identity", "context_evidence", "importance_evidence"} <= set(task.categories)
    assert (
        task.proposal_reason
        == task.judgment_reason
        == ("Synthetic unresolved sense and insufficient context.")
    )
    assert any("include=false" in question for question in task.questions)
    assert not {question for question in task.questions} & {s.excerpt for s in enriched.sources}
    assert {
        s.excerpt for s in enriched.sources if s.source_id == "calibration-corpus-included"
    } == {"dia 0", "dia 1", "dia 2"}
    assert enriched.measurements == original.measurements
    assert plan.base_result_sha256 == result.result_sha256
    assert plan.enrichment.pipeline_manifest_file_sha256 == sha(root / "manifest.json")
    assert plan.origin == "machine" and plan.production_eligible is False
    assert api().validate_machine_followup(result, plan) == plan


def test_disagreement_gets_a_followup_instead_of_being_treated_as_negative(tmp_path):
    _, _, plan = followup_fixture(tmp_path, form="accepted")
    assert plan.tasks[0].parent_status == "blocked_disagreement"
    assert "review_disagreement" in plan.tasks[0].categories
    assert plan.tasks[0].reason_codes == ("review_disagreement",)


def test_no_pending_items_cannot_create_an_empty_round(tmp_path):
    root, result = qualification_fixture(tmp_path, form="rejected")
    with pytest.raises(ValueError, match="pending|unresolved"):
        api().build_machine_followup(
            result, pipeline=root, manifest_sha256=sha(root / "manifest.json"), round_id="empty"
        )


@pytest.mark.parametrize("field", ["language", "profile_sha256", "rubric_sha256", "split"])
def test_changed_review_scope_is_rejected(tmp_path, field):
    _, result, plan = followup_fixture(tmp_path)
    changed = dict(
        language="en", profile_sha256="e" * 64, rubric_sha256="e" * 64, split="evaluation"
    )
    raw = plan.model_dump(mode="json", exclude_computed_fields=True)
    raw[field] = raw["enrichment"]["packet"][field] = changed[field]
    with pytest.raises(ValueError, match="scope|profile|language|rubric|split"):
        api().validate_machine_followup(result, api().MachineFollowupPlan.model_validate(raw))


@pytest.mark.parametrize("change", ["measurement", "analysis", "tasks", "base", "parent_hash"])
def test_plausible_rehashed_edits_cannot_replace_parent_facts_or_questions(tmp_path, change):
    _, result, plan = followup_fixture(tmp_path)
    raw = plan.model_dump(mode="json", exclude_computed_fields=True)
    if change in {"measurement", "analysis"}:
        item = raw["enrichment"]["packet"]["items"][0]
        if change == "measurement":
            item["measurements"]["observed_count"] = "1000"
        else:
            item["pos"] = "VERB"
        from multilang.services.qualification_review import ReviewPacket

        digest = ReviewPacket.model_validate(raw["enrichment"]["packet"]).items[0].item_sha256
        raw["enrichment"]["item_provenance"][0]["enriched_item_sha256"] = digest
        raw["tasks"][0]["enriched_item_sha256"] = digest
        from multilang.domain.lexical_identity import canonical_sha256

        raw["enrichment"]["packet"]["packet_id"] = "machine-enriched:" + canonical_sha256(
            {
                "parent": raw["enrichment"]["parent_packet_sha256"],
                "pipeline": raw["enrichment"]["pipeline_sha256"],
                "items": [digest],
            }
        )
    elif change == "tasks":
        raw["tasks"][0]["questions"] = ["Approve this regardless of the sources."]
    elif change == "base":
        raw["base_result_sha256"] = "e" * 64
    else:
        raw["enrichment"]["item_provenance"][0]["parent_item_sha256"] = "e" * 64
        raw["tasks"][0]["parent_item_sha256"] = "e" * 64
    with pytest.raises(ValueError):
        api().validate_machine_followup(result, api().MachineFollowupPlan.model_validate(raw))


def test_omitted_pending_item_and_additional_resolved_item_are_rejected(tmp_path):
    _, result, plan = followup_fixture(tmp_path, lexical="inconclusive")
    raw = plan.model_dump(mode="json", exclude_computed_fields=True)
    raw["tasks"] = raw["tasks"][1:]
    raw["enrichment"]["packet"]["items"] = raw["enrichment"]["packet"]["items"][1:]
    raw["enrichment"]["item_provenance"] = raw["enrichment"]["item_provenance"][1:]
    with pytest.raises(ValueError, match="inventory|pending"):
        api().validate_machine_followup(result, api().MachineFollowupPlan.model_validate(raw))
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    _, resolved = qualification_fixture(other_dir)
    with pytest.raises(ValueError):
        api().validate_machine_followup(resolved, plan)


def test_export_has_separate_instructions_and_is_immutable_on_resume(tmp_path):
    _, result, plan = followup_fixture(tmp_path)
    output = tmp_path / "followup"
    first = api().export_machine_followup(plan, output)
    assert api().export_machine_followup(plan, output) == first
    assert set(first["files"]) == {"plan.json", "packet.json", "tasks.json"}
    parsed = api().MachineFollowupPlan.model_validate_json((output / "plan.json").read_bytes())
    assert api().validate_machine_followup(result, parsed).followup_sha256 == plan.followup_sha256
    instructions = json.loads((output / "tasks.json").read_text())
    assert instructions["evidence_role"] == "review_instructions"
    assert len(instructions["tasks"]) == 1
    (output / "tasks.json").write_text("{}")
    with pytest.raises(ValueError, match="hash|drift|checksum"):
        api().export_machine_followup(plan, output)


def test_builder_rejects_pipeline_drift_before_emitting_a_plan(tmp_path):
    root, result = qualification_fixture(tmp_path)
    digest = sha(root / "manifest.json")
    (root / "pilot" / "measurements.json").write_text("{}")
    with pytest.raises(ValueError):
        api().build_machine_followup(
            result, pipeline=root, manifest_sha256=digest, round_id="round-2"
        )


def test_changed_enriched_packet_identity_is_rejected(tmp_path):
    _, result, plan = followup_fixture(tmp_path)
    raw = plan.model_dump(mode="json", exclude_computed_fields=True)
    raw["enrichment"]["packet"]["packet_id"] = "different-evidence"
    with pytest.raises(ValueError, match="packet.*identity|lineage"):
        api().validate_machine_followup(result, api().MachineFollowupPlan.model_validate(raw))


def test_builder_replays_parent_instead_of_trusting_status_labels(tmp_path):
    root, result = qualification_fixture(tmp_path)
    original = result.decisions[0]
    forged = original.model_copy(
        update={
            "status": "blocked_uncertainty",
            "reason_codes": ("missing_decision",),
            "decision": None,
        }
    )
    object.__setattr__(result, "decisions", (forged, *result.decisions[1:]))
    with pytest.raises(ValueError, match="decision drift"):
        api().build_machine_followup(
            result, pipeline=root, manifest_sha256=sha(root / "manifest.json"), round_id="forged"
        )


def pending_review(packet, run, *, rejected=()):
    """Create actual bound synthetic submissions for a later packet or shard."""
    responses = {
        "decisions": [
            dict(
                kind=item.kind,
                item_id=item.item_id,
                item_sha256=item.item_sha256,
                decision="rejected" if item.item_id in rejected else "inconclusive",
                reason="Synthetic later review; sources remain the same.",
                uncertainties=() if item.item_id in rejected else ("context_missing",),
            )
            for item in packet.items
        ]
    }
    request = build_machine_request(
        packet,
        actor=MachineActor(actor_id=run + "-p", context_id=run + "-p", execution_surface="mock"),
        run_id=run + "-p",
    )
    proposal = accept_machine_response(request, responses, metadata=metadata_fixture())
    judgment_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id=run + "-j", context_id=run + "-j", execution_surface="mock"),
        run_id=run + "-j",
        proposal=proposal,
    )
    judgment = accept_machine_response(judgment_request, responses, metadata=metadata_fixture())
    return reconcile_machine_reviews(packet, proposal, judgment)


def continue_plan(root, result, history, round_id):
    return api().build_machine_followup_from_previous(
        result,
        history=history,
        pipeline=root,
        manifest_sha256=sha(root / "manifest.json"),
        round_id=round_id,
    )


def test_repeated_rounds_reuse_verified_evidence_and_bind_the_actual_enriched_parent(tmp_path):
    root, original, first = followup_fixture(tmp_path, lexical="inconclusive")
    before = first.model_dump_json()
    lexical_id = next(
        item.item_id for item in first.enrichment.packet.items if item.kind == "lexical"
    )
    second_result = pending_review(first.enrichment.packet, "second", rejected=(lexical_id,))
    second = continue_plan(root, second_result, ((original, first),), "round-3")
    assert len(second.tasks) == 1
    assert second.enrichment.packet.items[0].kind == "form"
    current = next(item for item in second_result.packet.items if item.kind == "form")
    proof = second.enrichment.item_provenance[0]
    old_proof = next(
        row for row in first.enrichment.item_provenance if row.item_id == current.item_id
    )
    assert proof.parent_item_sha256 == proof.enriched_item_sha256 == current.item_sha256
    assert proof.parent_source_packet_sha256s == old_proof.parent_source_packet_sha256s
    assert proof.parent_item_sha256 != old_proof.parent_item_sha256
    assert second.enrichment.packet.items == (current,)
    assert proof.measured_count == old_proof.measured_count == 3
    assert proof.occurrences == old_proof.occurrences
    assert second.tasks[0].reason_codes == ("context_missing", "unresolved_evidence")
    assert second.base_result_sha256 == second_result.result_sha256
    assert api().validate_machine_followup(second_result, second) == second
    third_result = pending_review(second.enrichment.packet, "third")
    third = continue_plan(
        root, third_result, ((original, first), (second_result, second)), "round-4"
    )
    assert third.enrichment.packet.items == second.enrichment.packet.items
    assert third.enrichment.parent_packet_sha256 != second.enrichment.parent_packet_sha256
    assert third.followup_sha256 != second.followup_sha256
    assert third.tasks[0].parent_item_sha256 == current.item_sha256
    assert api().validate_machine_followup(third_result, third) == third
    assert first.model_dump_json() == before


def test_later_round_accepts_an_exact_shard_but_not_a_changed_analysis_or_source(tmp_path):
    root, original, first = followup_fixture(tmp_path, lexical="inconclusive")
    source_packet = first.enrichment.packet
    form = next(item for item in source_packet.items if item.kind == "form")
    shard = source_packet.model_copy(update={"packet_id": "exact-shard", "items": (form,)})
    current = pending_review(shard, "shard")
    following = continue_plan(root, current, ((original, first),), "round-3")
    assert following.enrichment.packet.items == (form,)
    changes = (
        {"pos": "VERB"},
        {"sources": (form.sources[0].model_copy(update={"excerpt": "invented evidence"}),)},
    )
    for item_change in changes:
        altered = shard.model_copy(update={"items": (form.model_copy(update=item_change),)})
        result = pending_review(altered, "altered")
        with pytest.raises(ValueError, match="ancestry|previous|exact"):
            continue_plan(root, result, ((original, first),), "round-3")


@pytest.mark.parametrize("position", ["root", "later"])
def test_self_consistent_forged_source_lineage_is_rejected_by_history_replay(tmp_path, position):
    root, original, first = followup_fixture(tmp_path)
    current = pending_review(first.enrichment.packet, "second")
    history = [(original, first)]
    if position == "later":
        second = continue_plan(root, current, tuple(history), "round-3")
        history.append((current, second))
        current = pending_review(second.enrichment.packet, "third")
    parent, plan = history[-1]
    raw = plan.model_dump(mode="json", exclude_computed_fields=True)
    raw["enrichment"]["item_provenance"][0]["parent_source_packet_sha256s"] = ["f" * 64]
    forged = api().MachineFollowupPlan.model_validate(raw)
    # A locally consistent artifact is not authenticated source ancestry.
    assert api().validate_machine_followup(parent, forged) == forged
    history[-1] = parent, forged
    with pytest.raises(ValueError, match="replay|ancestry"):
        continue_plan(root, current, tuple(history), "round-4")


@pytest.mark.parametrize("invalid", ["empty", "repeated", "old_result", "old_round", "too_long"])
def test_invalid_or_stale_histories_cannot_prepare_another_round(tmp_path, invalid):
    root, original, first = followup_fixture(tmp_path)
    current = pending_review(first.enrichment.packet, "second")
    history, round_id = ((original, first),), "round-3"
    if invalid == "empty":
        history = ()
    elif invalid == "repeated":
        history = history * 2
    elif invalid == "old_result":
        current = original
    elif invalid == "old_round":
        round_id = first.round_id
    else:
        history = history * 129
    with pytest.raises(ValueError, match="history|ancestry|repeated|round|stale"):
        continue_plan(root, current, history, round_id)


def test_later_round_rechecks_pipeline_and_rejects_another_scope(tmp_path):
    root, original, first = followup_fixture(tmp_path)
    changed_packet = first.enrichment.packet.model_copy(update={"language": "en"})
    with pytest.raises(ValueError, match="scope|language"):
        continue_plan(
            root, pending_review(changed_packet, "scope"), ((original, first),), "round-3"
        )
    current = pending_review(first.enrichment.packet, "second")
    (root / "pilot" / "measurements.json").write_text("{}")
    with pytest.raises(ValueError):
        continue_plan(root, current, ((original, first),), "round-3")
