"""Tests for ordered personal-source domain contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from multilang.domain.personal_sources import (
    PersonalSourceAdaptiveEvidence,
    PersonalSourceDecisionCommand,
    PersonalSourcePrerequisiteDecision,
    PersonalSourceRow,
)


HASH_A = "a" * 64
HASH_B = "b" * 64


def test_personal_source_row_contract_is_frozen_and_forbids_extra_fields() -> None:
    row = PersonalSourceRow(
        input_position=1,
        line_number=3,
        submitted_form="  학교  ",
        display_form="학교",
        normalized_duplicate_key="학교",
    )

    assert row.is_card_bearing is True
    assert row.disposition == "card_bearing"

    with pytest.raises(ValidationError):
        row.input_position = 2  # type: ignore[misc]

    with pytest.raises(ValidationError):
        PersonalSourceRow(
            input_position=1,
            line_number=3,
            submitted_form="학교",
            display_form="학교",
            normalized_duplicate_key="학교",
            unexpected="blocked",
        )


def test_personal_source_duplicate_row_remains_visible_and_not_card_bearing() -> None:
    duplicate = PersonalSourceRow(
        input_position=4,
        line_number=6,
        submitted_form="  학교  ",
        display_form="학교",
        normalized_duplicate_key="학교",
        duplicate_of_position=1,
    )

    assert duplicate.disposition == "duplicate"
    assert duplicate.duplicate_of_position == 1
    assert duplicate.is_card_bearing is False


def test_personal_source_duplicate_must_reference_an_earlier_position() -> None:
    with pytest.raises(ValidationError, match="earlier input position"):
        PersonalSourceRow(
            input_position=2,
            line_number=2,
            submitted_form="학교",
            display_form="학교",
            normalized_duplicate_key="학교",
            duplicate_of_position=2,
        )


def test_adaptive_evidence_records_counts_policy_and_controlled_reasons() -> None:
    evidence = PersonalSourceAdaptiveEvidence(
        observed_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        known_concept_ids=("lexicon:eat",),
        unknown_prerequisite_concept_ids=("grammar:past", "grammar:polite"),
        novelty_count=2,
        threshold=1,
        policy_version="korean-personal-adaptive-prereq-v1",
        policy_hash=HASH_A,
        reason_codes=("excessive_prerequisites",),
    )

    assert evidence.policy == "adaptive"
    assert evidence.requires_decision is True
    assert evidence.novelty_count == 2


def test_adaptive_evidence_rejects_inconsistent_novelty_counts() -> None:
    with pytest.raises(ValidationError, match="novelty count"):
        PersonalSourceAdaptiveEvidence(
            observed_concept_ids=("lexicon:eat", "grammar:past"),
            prerequisite_concept_ids=("lexicon:eat", "grammar:past"),
            known_concept_ids=("lexicon:eat",),
            unknown_prerequisite_concept_ids=("grammar:past",),
            novelty_count=0,
            threshold=1,
            policy_version="korean-personal-adaptive-prereq-v1",
            policy_hash=HASH_A,
            reason_codes=("within_threshold",),
        )


def test_bridge_decision_names_reviewed_prerequisites_without_auto_content() -> None:
    decision = PersonalSourcePrerequisiteDecision(
        decision_id=HASH_B,
        input_position=1,
        row_item_key="먹었어요",
        proposal_id=HASH_A,
        policy_hash=HASH_A,
        prerequisite_concept_ids=("grammar:past", "grammar:polite"),
        decision="bridge",
        reviewed_prerequisite_ids=("grammar:past", "grammar:polite"),
        reason_code="operator_bridge",
        blocks_current_preparation=False,
    )

    assert decision.decision == "bridge"
    assert decision.reviewed_prerequisite_ids == ("grammar:past", "grammar:polite")
    assert decision.blocks_current_preparation is False


def test_decision_command_is_compare_and_set_with_expected_proposal_identity() -> None:
    command = PersonalSourceDecisionCommand(
        input_position=1,
        row_item_key="먹었어요",
        expected_proposal_id=HASH_A,
        expected_policy_hash=HASH_A,
        expected_prerequisite_concept_ids=("grammar:past",),
        decision="defer",
        actor_id="local-reviewer",
        reason_code="operator_defer",
    )

    assert command.decision == "defer"
    assert command.expected_proposal_id == HASH_A
