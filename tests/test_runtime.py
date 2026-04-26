"""Tests for local runtime helpers that support shipped smoke flows."""

from __future__ import annotations

from multilang.runtime import _TemplateSentenceAdapter, _TemplateTranslationAdapter
from multilang.services.text_generation import SentenceGenerationRequest, SentenceTranslationRequest


def test_local_runtime_uses_curated_smoke_sentence_and_translation_for_lantern() -> None:
    sentence_adapter = _TemplateSentenceAdapter()
    translation_adapter = _TemplateTranslationAdapter()

    sentence = sentence_adapter.generate_sentence(
        SentenceGenerationRequest(
            display_form="lantern",
            lemma="lantern",
            definitions_html="a portable light protected by a transparent case",
            target_language="en",
            translation_target_language="pt",
        )
    )
    translation = translation_adapter.translate_sentence(
        SentenceTranslationRequest.from_sentence(
            sentence_result=sentence,
            translation_target_language="pt",
        )
    )

    assert sentence.sentence == "She hung the lantern beside the cabin door."
    assert translation.translation == "Ela pendurou a lanterna ao lado da porta da cabana."
    assert sentence.provenance["template_kind"] == "curated:lantern"
