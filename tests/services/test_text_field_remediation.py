"""Tests for deterministic learner-facing text field remediation."""

from __future__ import annotations

import pytest

from multilang.services.part_of_speech import canonical_part_of_speech_label
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


def test_remediate_definition_html_rewrites_german_article_label() -> None:
    assert remediate_definition_html(
        display_form="die",
        lemma="die",
        part_of_speech="unknown",
        generated_html="noun: the definite article used for feminine nouns in German",
        source_definitions=[],
        source_language="de",
    ) == "article: the definite article used for feminine nouns in German"


def test_remediate_definition_html_preserves_valid_provider_label_when_pos_is_unknown() -> None:
    assert remediate_definition_html(
        display_form="blieb",
        lemma="blieb",
        part_of_speech="unknown",
        generated_html="verb: remained",
        source_definitions=[],
        source_language="de",
    ) == "verb: remained"


def test_remediate_definition_html_infers_german_indefinite_pronoun_label() -> None:
    assert remediate_definition_html(
        display_form="etwas",
        lemma="etwas",
        part_of_speech="unknown",
        generated_html="something or anything",
        source_definitions=[],
        source_language="de",
    ) == "pronoun: something or anything"


def test_remediate_definition_html_uses_neutral_label_when_provider_has_no_label() -> None:
    assert remediate_definition_html(
        display_form="Dingsbums",
        lemma="Dingsbums",
        part_of_speech="unknown",
        generated_html="a placeholder thing",
        source_definitions=[],
        source_language="de",
    ) == "term: a placeholder thing"


def test_remediate_definition_html_canonicalizes_trusted_pos_label() -> None:
    assert remediate_definition_html(
        display_form="em",
        lemma="em",
        part_of_speech="prep",
        generated_html="prep: used to show location or time",
        source_definitions=[],
        source_language="pt",
    ) == "preposition: used to show location or time"


def test_canonical_part_of_speech_label_rejects_unknown_labels() -> None:
    assert canonical_part_of_speech_label("prep") == "preposition"
    assert canonical_part_of_speech_label("proper-noun") == "proper noun"
    assert canonical_part_of_speech_label("unknown") is None
    assert canonical_part_of_speech_label("mystery label") is None


@pytest.mark.parametrize(
    ("source_language", "word", "expected_label"),
    [
        ("pt", "em", "preposition"),
        ("es", "pero", "conjunction"),
        ("en", "the", "article"),
        ("fr", "et", "conjunction"),
        ("de", "etwas", "pronoun"),
        ("it", "non", "adverb"),
        ("pl", "czy", "particle"),
        ("tr", "için", "postposition"),
        ("ro", "și", "conjunction"),
        ("ru", "и", "conjunction"),
        ("nl", "het", "article"),
    ],
)
def test_remediate_definition_html_infers_function_word_labels_across_supported_languages(
    source_language: str,
    word: str,
    expected_label: str,
) -> None:
    assert remediate_definition_html(
        display_form=word,
        lemma=word,
        part_of_speech="unknown",
        generated_html="noun: used as a frequent function word",
        source_definitions=[],
        source_language=source_language,
    ) == f"{expected_label}: used as a frequent function word"


def test_remediate_definition_html_prefers_trusted_pos_over_inference() -> None:
    assert remediate_definition_html(
        display_form="the",
        lemma="the",
        part_of_speech="proper noun",
        generated_html="article: a word used before nouns",
        source_definitions=[],
        source_language="en",
    ) == "proper noun: a word used before nouns"


def test_remediate_definition_html_replaces_unknown_provider_label_with_neutral_label() -> None:
    assert remediate_definition_html(
        display_form="Dingsbums",
        lemma="Dingsbums",
        part_of_speech="unknown",
        generated_html="mystery label: a placeholder thing",
        source_definitions=[],
        source_language="de",
    ) == "term: a placeholder thing"


def test_remediate_definition_html_replaces_local_placeholder_with_source_definition() -> None:
    assert remediate_definition_html(
        display_form="remercier",
        lemma="remercier",
        part_of_speech="verb",
        generated_html="verb: learner definition for remercier",
        source_definitions=["to thank someone"],
    ) == "verb: to thank someone"


def test_validate_definition_html_rejects_local_placeholder_definition() -> None:
    with pytest.raises(ValueError, match="learner-safe semantic definition"):
        validate_definition_html(
            lemma_key="remercier",
            definitions_html="verb: learner definition for remercier",
        )


def test_validate_definition_html_accepts_semantic_definition() -> None:
    validate_definition_html(lemma_key="ru:dostich", definitions_html="verb: to achieve, to attain, to reach")
