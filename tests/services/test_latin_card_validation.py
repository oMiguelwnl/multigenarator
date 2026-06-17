"""Tests for Latin generated-card validation."""

from __future__ import annotations

from multilang.services.latin_card_generation import LatinGeneratedCard
from multilang.services.latin_card_validation import LatinCardValidationService


def test_latin_card_validation_accepts_target_and_grammar() -> None:
    card = LatinGeneratedCard(
        sequence=1,
        lemma="amo",
        target_form="amat",
        latin_sentence="Puella matrem amat.",
        gramatica="v pres ind act 3sg V",
        morphology_note="amat is present indicative active third singular.",
    )

    assert LatinCardValidationService().validate(card) == []


def test_latin_card_validation_rejects_missing_target_and_dummy_content() -> None:
    card = LatinGeneratedCard(
        sequence=1,
        lemma="lemma1",
        target_form="lemma1",
        latin_sentence="Puella matrem amat.",
        gramatica="noun singular subject",
        morphology_note="dummy",
    )

    issues = LatinCardValidationService().validate(card)

    assert {issue.code for issue in issues} >= {"target_form_missing", "dummy_content", "invalid_gramatica"}
