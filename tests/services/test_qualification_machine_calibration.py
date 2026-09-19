"""Calibration measures agreement with machine labels, never human qualification."""

from datetime import UTC, datetime
from decimal import Decimal, localcontext
from importlib import import_module, util

import pytest

from multilang.domain.lexical_identity import ImportantFormCriteria
from multilang.services.qualification_machine import (
    MachineActor,
    accept_machine_response,
    build_machine_request,
    reconcile_machine_reviews,
)
from multilang.services.qualification_review import FormReviewItem, ReviewPacket, ReviewSource


def _api():
    assert util.find_spec("multilang.services.qualification_machine_calibration") is not None
    return import_module("multilang.services.qualification_machine_calibration")


def _criteria(threshold="0.5", **changes):
    return ImportantFormCriteria(
        **(
            {
                "policy_id": "test-machine-criteria",
                "version": "1",
                "weights": {"frequency": "1"},
                "minimum_score": threshold,
                "attestation_threshold": 1,
                "analysis_confidence_threshold": "0.9",
                "missing_evidence": "reject",
            }
            | changes
        )
    )


def _qualification(
    split="calibration",
    prefix="train",
    *,
    item_changes=None,
    decision_changes=None,
    disagree=(),
    profile_sha256="d" * 64,
):
    item_changes, decision_changes = item_changes or {}, decision_changes or {}
    items = []
    for index, frequency in enumerate(("0.9", "0.7", "0.4", "0.1")):
        data = {
            "item_id": f"{prefix}-{index}",
            "candidate_id": f"candidate-{index}",
            "candidate_sha256": "a" * 64,
            "lemma": "go",
            "pos": "VERB",
            "text": f"form{index}",
            "canonical_sense_id": "motion",
            "sources": (
                ReviewSource(
                    source_id="fixture",
                    record_id=f"{prefix}-{index}",
                    source_sha256=("b" if prefix == "train" else "c") * 64,
                    excerpt=f"{prefix} source sentence {index}",
                ),
            ),
            "measurements": {"observed_count": 5},
            "proposed_ratings": {"frequency": frequency},
        }
        data.update(item_changes.get(index, {}))
        items.append(FormReviewItem(**data))
    packet = ReviewPacket(
        packet_id=prefix,
        language="en",
        split=split,
        profile_sha256=profile_sha256,
        rubric_sha256="e" * 64,
        items=items,
    )
    decisions = []
    for index, item in enumerate(items):
        quote = item.sources[0].excerpt
        data = {
            "kind": "form",
            "item_id": item.item_id,
            "item_sha256": item.item_sha256,
            "decision": "accepted",
            "reason": "Mock source-backed machine assessment.",
            "citations": [
                {
                    "source_index": 0,
                    "source_sha256": item.sources[0].source_sha256,
                    "start": 0,
                    "end": len(quote),
                    "quote": quote,
                }
            ],
            "include": index < 2,
            "proposed_sense_id": "motion",
            "machine_analysis_rating": "1",
        }
        data.update(decision_changes.get(index, {}))
        decisions.append(data)
    proposal_request = build_machine_request(
        packet,
        actor=MachineActor(
            actor_id="proposer", execution_surface="mock", context_id="proposal-context"
        ),
        run_id="proposal-run",
    )
    metadata = {"executed_at": datetime(2026, 9, 13, tzinfo=UTC)}
    proposal = accept_machine_response(
        proposal_request, {"decisions": decisions}, metadata=metadata
    )
    judgment_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="judge", execution_surface="mock", context_id="judge-context"),
        run_id="judge-run",
        proposal=proposal,
    )
    judgments = [dict(decision) for decision in decisions]
    for index in disagree:
        judgments[index]["include"] = not judgments[index]["include"]
    judgment = accept_machine_response(
        judgment_request, {"decisions": judgments}, metadata=metadata
    )
    return reconcile_machine_reviews(packet, proposal, judgment)


def _calibrate(qualification=None, **changes):
    return _api().calibrate_machine_importance(
        qualification or _qualification(),
        **(
            {
                "candidates": [_criteria("0.2"), _criteria("0.5")],
                "false_positive_cost": Decimal(2),
                "false_negative_cost": Decimal(1),
            }
            | changes
        ),
    )


def test_calibration_selects_grid_then_evaluates_without_human_authority():
    api = _api()
    result = _calibrate()
    assert result.criteria.minimum_score == Decimal("0.5")
    assert result.metrics.true_positive == 2
    assert result.metrics.true_negative == 2
    assert result.metrics.false_positive == result.metrics.false_negative == 0
    assert result.label_origin == "machine"
    assert result.metrics_scope == "agreement_with_machine_labels"
    assert result.analysis_rating_semantics == "subjective_machine_diagnostic_not_probability"
    assert result.production_eligible is False
    assert result == _calibrate(candidates=[_criteria("0.5"), _criteria("0.2")])
    assert api.MachineCalibrationResult.model_validate_json(result.model_dump_json()) == result
    evaluation = api.evaluate_machine_importance(result, _qualification("evaluation", "test"))
    assert evaluation.criteria_sha256 == result.criteria.policy_sha256
    assert evaluation.metrics.true_positive == evaluation.metrics.true_negative == 2
    assert evaluation.label_origin == "machine"
    assert evaluation.metrics_scope == "agreement_with_machine_labels"
    assert evaluation.production_eligible is False


def test_disagreement_missing_sense_rating_and_count_are_excluded():
    result = _calibrate(_qualification(disagree=(0,)))
    assert result.metrics.evaluated == 3
    assert result.metrics.excluded["train-0"] == "machine_consensus_unavailable"
    for changes in ({"machine_analysis_rating": None}, {"proposed_sense_id": None}):
        result = _calibrate(_qualification(decision_changes={0: changes}))
        assert result.metrics.evaluated == 3
        assert result.metrics.excluded["train-0"] == "resolved_sense_pos_count_rating_required"
    result = _calibrate(_qualification(item_changes={0: {"measurements": {}}}))
    assert result.metrics.excluded["train-0"] == "resolved_sense_pos_count_rating_required"


def test_machine_ratings_do_not_reuse_unreviewed_item_ratings():
    qualification = _qualification(
        item_changes={
            index: {"proposed_ratings": {"frequency": "0.9", "irregularity": "1"}}
            for index in range(4)
        }
    )
    result = _calibrate(qualification, candidates=[_criteria(weights={"irregularity": "1"})])
    assert result.metrics.selected_item_ids == ()
    assert result.metrics.false_negative == 2
    qualification = _qualification(
        decision_changes={
            index: {"ratings": {"irregularity": "1" if index < 2 else "0"}} for index in range(4)
        }
    )
    result = _calibrate(qualification, candidates=[_criteria(weights={"irregularity": "1"})])
    assert result.metrics.true_positive == result.metrics.true_negative == 2


@pytest.mark.parametrize("count", ["1.5", "1000000000001"])
def test_observed_count_requires_bounded_integer(count):
    with pytest.raises(ValueError, match="observed count"):
        _calibrate(_qualification(item_changes={0: {"measurements": {"observed_count": count}}}))


def test_training_split_and_two_label_classes_are_required():
    with pytest.raises(ValueError, match="calibration split"):
        _calibrate(_qualification("evaluation"))
    with pytest.raises(ValueError, match="positive and negative"):
        _calibrate(
            _qualification(decision_changes={index: {"include": True} for index in range(4)})
        )
    with pytest.raises(ValueError, match="positive and negative"):
        _calibrate(
            _qualification(decision_changes={index: {"include": False} for index in range(4)})
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"candidates": []},
        {"candidates": [_criteria()] * 257},
        {"false_positive_cost": Decimal("NaN")},
        {"false_negative_cost": Decimal("-1")},
        {"false_positive_cost": Decimal(0), "false_negative_cost": Decimal(0)},
    ],
)
def test_grid_and_cost_objective_are_bounded(changes):
    with pytest.raises(ValueError):
        _calibrate(**changes)


def test_source_overlap_including_hidden_full_lineage_blocks_evaluation():
    api = _api()
    result = _calibrate()
    with pytest.raises(ValueError, match="source overlap"):
        api.evaluate_machine_importance(result, _qualification("evaluation", "train"))
    shared = "f" * 64
    changes = {0: {"evidence_source_keys": (shared,)}}
    result = _calibrate(_qualification(item_changes=changes))
    with pytest.raises(ValueError, match="source overlap"):
        api.evaluate_machine_importance(
            result, _qualification("evaluation", "test", item_changes=changes)
        )


@pytest.mark.filterwarnings("error")
def test_source_packet_and_forged_calibration_are_replayed():
    api = _api()
    qualification = _qualification()
    from multilang.services.qualification_machine import MachineQualificationResult

    data = qualification.model_dump(mode="json", exclude_computed_fields=True)
    data["packet"]["items"][0]["sources"][0]["excerpt"] = "tampered source"
    with pytest.raises(ValueError):
        api.calibrate_machine_importance(
            MachineQualificationResult.model_construct(**data),
            candidates=[_criteria()],
            false_positive_cost=1,
            false_negative_cost=1,
        )
    result = _calibrate()
    for updates in (
        {"source_keys": ()},
        {"criteria": _criteria("0.9")},
        {"candidate_scores": {result.criteria.policy_sha256: Decimal(999)}},
    ):
        forged = result.model_copy(update=updates)
        with pytest.raises(ValueError, match="replay"):
            api.evaluate_machine_importance(forged, _qualification("evaluation", "test"))


def test_decimal_arithmetic_is_stable_across_global_contexts():
    expected = _calibrate(false_positive_cost=Decimal("0.1234567890123456789"))
    with localcontext() as context:
        context.prec = 5
        result = _calibrate(false_positive_cost=Decimal("0.1234567890123456789"))
    assert result == expected


def test_evaluation_requires_evaluation_split_and_same_profile():
    api = _api()
    calibration = _calibrate()
    with pytest.raises(ValueError, match="evaluation split"):
        api.evaluate_machine_importance(calibration, _qualification("pilot", "test"))
    with pytest.raises(ValueError, match="profile"):
        api.evaluate_machine_importance(
            calibration, _qualification("evaluation", "test", profile_sha256="a" * 64)
        )
