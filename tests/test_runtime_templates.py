"""Unit tests for the local runtime text templates."""

from __future__ import annotations

from multilang.runtime import _TemplateSentenceAdapter, _TemplateTranslationAdapter
from multilang.services.text_generation import SentenceGenerationRequest, SentenceTranslationRequest


def test_runtime_sentence_adapter_uses_meaning_aware_english_template() -> None:
    result = _TemplateSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="wash",
            lemma="wash",
            definitions_html="to wash",
            target_language="en",
            translation_target_language="pt",
        )
    )

    assert result.sentence == "It is good to wash every day."
    assert result.intended_sense == "wash"
    assert result.provenance["template_kind"] == "verb"


def test_runtime_translation_adapter_uses_sentence_sense_hint() -> None:
    result = _TemplateTranslationAdapter().translate_sentence(
        SentenceTranslationRequest(
            sentence="It is good to wash every day.",
            translation_target_language="pt",
            intended_sense="wash",
            template_kind="verb",
        )
    )

    assert result.translation == "É bom lavar todos os dias."


def test_runtime_sentence_adapter_uses_generic_term_template_when_sense_is_unknown() -> None:
    result = _TemplateSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="alpha",
            lemma="alpha",
            definitions_html="definition for alpha",
            target_language="en",
            translation_target_language="pt",
        )
    )

    assert result.sentence == "The word alpha is useful in daily life."
    assert result.uncertainty_notes == ["local runtime used a generic term template"]
    assert result.provenance["template_kind"] == "term"
