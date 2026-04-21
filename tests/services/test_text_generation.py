"""Tests for Phase 3 text generation boundaries."""

from __future__ import annotations

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
)
from multilang.services.text_generation import (
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceTranslationRequest,
    SentenceTranslationResult,
)
from multilang.settings import Settings


def build_candidate() -> LexicalCardCandidate:
    return LexicalCardCandidate(
        submitted_form="lavar",
        display_form="lavarse",
        lemma="lavar",
        lemma_key="lavar",
        definitions_html="to wash<br>to wash oneself",
        definition_language="en",
        translation_target_language="en",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(
            source="kaikki",
            definition=DefinitionRecord(source="kaikki", value="to wash<br>to wash oneself"),
        ),
    )


def test_sentence_generation_request_uses_grounded_lexical_context() -> None:
    candidate = build_candidate()

    request = SentenceGenerationRequest.from_candidate(
        candidate=candidate,
        deck_language=SupportedLanguage.ES,
    )

    assert request.display_form == "lavarse"
    assert request.lemma == "lavar"
    assert request.definitions_html == "to wash<br>to wash oneself"
    assert request.target_language == SupportedLanguage.ES.value
    assert request.translation_target_language == "en"


def test_translation_is_built_from_generated_sentence() -> None:
    generated_sentence = SentenceGenerationResult(
        sentence="Yo me lavo antes de dormir.",
        intended_sense="reflexive daily routine",
        uncertainty_notes=["Used the reflexive form for natural phrasing."],
        provenance={"provider": "fake-generator"},
    )

    request = SentenceTranslationRequest.from_sentence(
        sentence_result=generated_sentence,
        translation_target_language="en",
    )

    assert request.sentence == "Yo me lavo antes de dormir."
    assert request.translation_target_language == "en"
    assert not hasattr(request, "definitions_html")


def test_settings_expose_phase_three_provider_configuration() -> None:
    settings = Settings(
        text_generation_model="openai/gpt-4o-mini",
        text_generation_provider="litellm",
        translation_provider="deepl",
        deepl_api_key="test-key",
    )

    assert settings.text_generation_model == "openai/gpt-4o-mini"
    assert settings.text_generation_provider == "litellm"
    assert settings.translation_provider == "deepl"
    assert settings.deepl_api_key == "test-key"


def test_translation_result_keeps_provider_metadata() -> None:
    result = SentenceTranslationResult(
        translation="I wash myself before going to sleep.",
        provenance={"provider": "deepl", "model": None},
    )

    assert result.translation == "I wash myself before going to sleep."
    assert result.provenance["provider"] == "deepl"
