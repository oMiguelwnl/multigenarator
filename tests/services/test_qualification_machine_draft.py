"""Machine proposals remain useful without impersonating signed native decisions."""

import pytest
from test_qualification_machine_runner import metadata_fixture, response_fixture


def draft_fixture(tmp_path):
    from test_qualification_bridge import fixture

    from multilang.services.qualification_machine import (
        MachineActor,
        accept_machine_response,
        build_machine_request,
        reconcile_machine_reviews,
    )

    original = fixture(tmp_path)
    packet = original["packet"]
    request = build_machine_request(
        packet,
        actor=MachineActor(
            actor_id="mock", context_id="one", execution_surface="mock", model="mock"
        ),
        run_id="one",
    )
    raw = response_fixture(request)
    raw["decisions"][0]["citations"][0]["source_sha256"] = packet.items[0].sources[0].source_sha256
    proposal = accept_machine_response(request, raw, metadata=metadata_fixture())
    judge_request = build_machine_request(
        packet,
        actor=MachineActor(
            actor_id="mock-judge", context_id="two", execution_surface="mock", model="mock"
        ),
        run_id="two",
        proposal=proposal,
    )
    judgment = accept_machine_response(judge_request, raw, metadata=metadata_fixture())
    result = reconcile_machine_reviews(packet, proposal, judgment)
    return original, result


def test_draft_contains_actionable_mapping_and_pending_native_input(tmp_path):
    from multilang.services.qualification_machine_draft import build_machine_vocabulary_draft

    original, result = draft_fixture(tmp_path)
    before = (original["preparation_dir"] / "candidates.jsonl").read_bytes()
    draft = build_machine_vocabulary_draft(
        preparation_dir=original["preparation_dir"],
        qualification=result,
        profile=original["profile"],
        source_id="synthetic",
        source_version="1",
    )
    assert draft.proposed_lexical_mappings[0].decision.proposed_sense_id == "motion"
    assert draft.pending_native_review.senses[0].decision == "pending"
    assert draft.pending_native_review.senses[0].receipt_id is None
    assert draft.origin == "machine" and not draft.production_eligible
    assert not draft.uncertainty_queue
    assert (original["preparation_dir"] / "candidates.jsonl").read_bytes() == before


def test_draft_rejects_changed_profile_and_preparation(tmp_path):
    from multilang.services.qualification_machine_draft import build_machine_vocabulary_draft

    original, result = draft_fixture(tmp_path)
    with pytest.raises(ValueError, match="profile"):
        build_machine_vocabulary_draft(
            preparation_dir=original["preparation_dir"],
            qualification=result,
            profile=original["profile"].model_copy(update={"source_ids": ("changed",)}),
            source_id="synthetic",
            source_version="1",
        )
    (original["preparation_dir"] / "candidates.jsonl").write_text("{}\n")
    with pytest.raises(ValueError):
        build_machine_vocabulary_draft(
            preparation_dir=original["preparation_dir"],
            qualification=result,
            profile=original["profile"],
            source_id="synthetic",
            source_version="1",
        )


def test_report_escapes_machine_output(tmp_path):
    from multilang.services.qualification_machine_draft import render_machine_report

    original, result = draft_fixture(tmp_path)
    html = render_machine_report(result)
    assert "machine_agreement" in html
    assert "Content-Security-Policy" in html
    assert "<script" not in html
    assert "To move." in html
