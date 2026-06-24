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
            source="manual",
            definition=DefinitionRecord(source="manual", value=definition),
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


def test_local_highlight_sentence_is_richer_and_source_aware() -> None:
    result = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="wash",
            lemma="wash",
            definitions_html="to wash",
            target_language="en",
            translation_target_language="pt",
            source_type="kindle-highlights",
            highlight_context="Readers wash every cup before dawn",
        )
    )

    tokens = result.sentence.split()
    assert "wash" in result.sentence.casefold()
    assert 6 <= len(tokens) <= 16
    assert "discuss wash" not in result.sentence.casefold()
    assert result.provenance["source_type"] == "kindle-highlights"
    assert result.provenance["template_kind"] == "highlight"


def test_local_sentence_uses_lemma_not_title_cased_source_form_for_french_verbs() -> None:
    result = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="Remercia",
            lemma="remercier",
            definitions_html="verb: to thank someone",
            target_language="fr",
            translation_target_language="fr",
            source_type="word-list",
        )
    )

    assert result.sentence == "Mon frère veut remercier demain."
    assert "Remercia" not in result.sentence
    assert result.provenance["template_kind"] == "verb"


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


def test_local_translation_adapter_localizes_definition_requests() -> None:
    result = LocalTranslationAdapter().translate_sentence(
        SentenceTranslationRequest(
            sentence="noun: definition for casa",
            translation_target_language="es",
            template_kind="definition",
        )
    )

    assert result.translation == "sustantivo: definición de casa"
    assert result.provenance["source"] == "runtime-local-definition-translator"


def test_local_runtime_supports_norwegian_bokmal_without_live_providers() -> None:
    sentence = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="bruke",
            lemma="bruke",
            definitions_html="verb: to use",
            target_language="nb",
            translation_target_language="en",
        )
    )
    translation = LocalTranslationAdapter().translate_sentence(
        SentenceTranslationRequest.from_sentence(
            sentence_result=sentence,
            translation_target_language="en",
        )
    )

    assert sentence.sentence == "Broren min vil bruke i morgen."
    assert translation.translation == "My brother wants to use tomorrow."


def test_local_adapter_supports_swedish() -> None:
    sentence = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="använda",
            lemma="använda",
            definitions_html="verb: to use",
            target_language="sv",
            translation_target_language="en",
        )
    )
    translation = LocalTranslationAdapter().translate_sentence(
        SentenceTranslationRequest.from_sentence(
            sentence_result=sentence,
            translation_target_language="en",
        )
    )

    assert sentence.sentence == "Min bror vill använda i morgon."
    assert translation.translation == "My brother wants to use tomorrow."


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


def test_service_generates_accepted_spanish_verb_with_english_translation() -> None:
    candidate = make_candidate("usar", language=SupportedLanguage.ES, definition="to use")
    service = TextGenerationService(
        sentence_adapter=LocalSentenceAdapter(),
        translation_adapter=LocalTranslationAdapter(),
    )

    bundle = service.generate_bundle(candidate=candidate, deck_language=SupportedLanguage.ES)
    result = TextValidationService().validate(
        sentence=bundle.sentence,
        translation=bundle.translation,
        display_form=candidate.display_form,
        lemma=candidate.lemma,
        definitions_html=candidate.definitions_html,
    )

    assert result.validation_status.value == "passed"
    assert "usar" in bundle.sentence.text.casefold()
    assert bundle.translation.target_language == "en"
    assert bundle.translation.text
    assert bundle.translation.text != bundle.sentence.text
