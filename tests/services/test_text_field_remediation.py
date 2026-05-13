"""Tests for deterministic learner-facing text field remediation."""

from __future__ import annotations

import pytest

from multilang.services.text_field_remediation import remediate_definition_html, validate_definition_html


def test_validate_definition_html_rejects_morphology_only_metadata() -> None:
    with pytest.raises(ValueError, match="learner-safe semantic definition"):
        validate_definition_html(
            lemma_key="ru:bolshuyu",
            definitions_html="adjective: masculine animate accusative singular",
        )


@pytest.mark.parametrize(
    "definition",
    [
        "noun: inflection of casa",
        "noun: genitive of dom",
        "adjective: accusative of большой",
    ],
)
def test_validate_definition_html_rejects_relation_only_patterns(definition: str) -> None:
    with pytest.raises(ValueError, match="learner-safe semantic definition"):
        validate_definition_html(lemma_key="item", definitions_html=definition)


def test_remediate_definition_html_applies_known_corrected_sense_for_dostich() -> None:
    assert remediate_definition_html(
        display_form="дости́чь",
        lemma="достичь",
        part_of_speech="verb",
        generated_html="verb: to deliver",
        source_definitions=[],
    ) == "verb: to achieve, to attain, to reach"


def test_remediate_definition_html_uses_substantive_source_definition_when_generated_is_banned() -> None:
    assert remediate_definition_html(
        display_form="большую",
        lemma="большой",
        part_of_speech="adjective",
        generated_html="adjective: feminine accusative singular",
        source_definitions=["feminine accusative singular of большой", "big; large; important"],
    ) == "adjective: big; large; important"


def test_validate_definition_html_accepts_semantic_definition() -> None:
    validate_definition_html(lemma_key="ru:dostich", definitions_html="verb: to achieve, to attain, to reach")
