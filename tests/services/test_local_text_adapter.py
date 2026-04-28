"""Tests for deterministic local runtime text adapters."""

from __future__ import annotations

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import DefinitionRecord, GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.services.local_text_adapter import LocalSentenceAdapter, LocalTranslationAdapter
from multilang.services.text_generation import (
    SentenceGenerationRequest,
    SentenceTranslationRequest,
    TextGenerationService,
)
from multilang.services.text_validation import TextValidationService


def make_candidate(
    term: str,
    *,
    language: SupportedLanguage = SupportedLanguage.EN,
    definition: str | None = None,
) -> LexicalCardCandidate:
    definition = definition or f"definition for {term}"
    return LexicalCardCandidate(
        submitted_form=term,
        display_form=term,
        lemma=term,
        lemma_key=f"{language.value}:{term}",
        definitions_html=definition,
        definition_language="en",
        translation_target_language="pt" if language is SupportedLanguage.EN else "en",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(
            source="kaikki",
            definition=DefinitionRecord(source="kaikki", value=definition),
        ),
    )


def test_generic_english_sentence_is_natural_and_validatable() -> None:
    result = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="alpha",
            lemma="alpha",
            definitions_html="definition for alpha",
            target_language="en",
            translation_target_language="pt",
        )
    )

    tokens = result.sentence.split()
    assert "alpha" in result.sentence.casefold()
    assert 4 <= len(tokens) <= 12
    assert not result.sentence.casefold().startswith("the word")


def test_curated_smoke_terms_keep_portuguese_translations() -> None:
    sentence_adapter = LocalSentenceAdapter()
    translation_adapter = LocalTranslationAdapter()

    for term in ["harbor", "lantern", "meadow"]:
        sentence = sentence_adapter.generate_sentence(
            SentenceGenerationRequest(
                display_form=term,
                lemma=term,
                definitions_html=f"definition for {term}",
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

        assert term in sentence.sentence.casefold()
        assert translation.translation
        assert translation.translation != sentence.sentence


def test_translation_is_not_source_or_definition_copy() -> None:
    sentence = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="alpha",
            lemma="alpha",
            definitions_html="definition for alpha",
            target_language="en",
            translation_target_language="pt",
        )
    )
    translation = LocalTranslationAdapter().translate_sentence(
        SentenceTranslationRequest.from_sentence(
            sentence_result=sentence,
            translation_target_language="pt",
        )
    )

    assert translation.translation != sentence.sentence
    assert translation.translation.casefold() != "definition for alpha"


def test_text_generation_service_accepts_representative_grounded_candidates() -> None:
    service = TextGenerationService(
        sentence_adapter=LocalSentenceAdapter(),
        translation_adapter=LocalTranslationAdapter(),
    )
    validator = TextValidationService()

    cases = [
        (make_candidate("alpha"), SupportedLanguage.EN),
        (make_candidate("usar", language=SupportedLanguage.ES, definition="to use"), SupportedLanguage.ES),
        (make_candidate("harbor"), SupportedLanguage.EN),
    ]

    for candidate, language in cases:
        bundle = service.generate_bundle(candidate=candidate, deck_language=language)
        result = validator.validate(
            sentence=bundle.sentence,
            translation=bundle.translation,
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions_html=candidate.definitions_html,
        )

        assert result.validation_status.value == "passed"
        assert candidate.display_form.casefold() in bundle.sentence.text.casefold()
        assert not bundle.sentence.text.casefold().startswith(("the word", "la palabra"))
        assert bundle.translation.text != bundle.sentence.text
        assert bundle.translation.text.casefold() != (candidate.definitions_html or "").casefold()
