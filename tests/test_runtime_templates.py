"""Unit tests for the local runtime text templates."""

from __future__ import annotations

from multilang.services.local_text_adapter import LocalSentenceAdapter, LocalTranslationAdapter
from multilang.services.text_generation import SentenceGenerationRequest, SentenceTranslationRequest


def test_runtime_sentence_adapter_uses_meaning_aware_english_template() -> None:
    result = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="wash",
            lemma="wash",
            definitions_html="to wash",
            target_language="en",
            translation_target_language="pt",
        )
    )

    assert result.sentence == "My brother wants to wash tomorrow."
    assert result.intended_sense == "wash"
    assert result.provenance["template_kind"] == "verb"


def test_runtime_translation_adapter_uses_sentence_sense_hint() -> None:
    result = LocalTranslationAdapter().translate_sentence(
        SentenceTranslationRequest(
            sentence="It is good to wash every day.",
            translation_target_language="pt",
            intended_sense="wash",
            template_kind="verb",
        )
    )

    assert result.translation == "Meu irmão quer lavar amanhã."


def test_runtime_sentence_adapter_uses_generic_term_template_when_sense_is_unknown() -> None:
    result = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="alpha",
            lemma="alpha",
            definitions_html="definition for alpha",
            target_language="en",
            translation_target_language="pt",
        )
    )

    assert result.sentence == "Friends discuss alpha during lunch."
    assert result.uncertainty_notes == []
    assert result.provenance["template_kind"] == "term"
