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
    GeneratedTextBundle,
    SentenceGenerationFallback,
    TextGenerationService,
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceGenerationAdapter,
    SentenceTranslationRequest,
    SentenceTranslationResult,
    SentenceTranslationAdapter,
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
            source="manual",
            definition=DefinitionRecord(source="manual", value="to wash<br>to wash oneself"),
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
    assert request.intended_sense == "reflexive daily routine"
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


class FakeSentenceAdapter(SentenceGenerationAdapter):
    def __init__(self) -> None:
        self.requests: list[SentenceGenerationRequest] = []

    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        self.requests.append(request)
        return SentenceGenerationResult(
            sentence="Yo me lavo antes de dormir.",
            intended_sense="reflexive daily routine",
            uncertainty_notes=["medium confidence"],
            provenance={"provider": "litellm", "model": "openai/gpt-4o-mini"},
        )


class EnglishSentenceAdapter(SentenceGenerationAdapter):
    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        return SentenceGenerationResult(
            sentence="I wash my hands before dinner.",
            intended_sense="daily routine",
            uncertainty_notes=[],
            provenance={"provider": "litellm", "model": "openai/gpt-4o-mini"},
        )


class FakeTranslationAdapter(SentenceTranslationAdapter):
    def __init__(self) -> None:
        self.requests: list[SentenceTranslationRequest] = []

    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        self.requests.append(request)
        return SentenceTranslationResult(
            translation="I wash myself before going to sleep.",
            provenance={"provider": "deepl", "model": None},
        )


class TrackingTranslationAdapter(SentenceTranslationAdapter):
    def __init__(self) -> None:
        self.requests: list[SentenceTranslationRequest] = []

    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        self.requests.append(request)
        return SentenceTranslationResult(
            translation="I wash myself before going to sleep.",
            provenance={"provider": "deepl", "model": None},
        )


def test_text_generation_service_returns_sentence_and_translation_provenance() -> None:
    sentence_adapter = FakeSentenceAdapter()
    translation_adapter = FakeTranslationAdapter()
    service = TextGenerationService(
        sentence_adapter=sentence_adapter,
        translation_adapter=translation_adapter,
    )

    result = service.generate_bundle(
        candidate=build_candidate(),
        deck_language=SupportedLanguage.ES,
    )

    assert isinstance(result, GeneratedTextBundle)
    assert result.sentence.text == "Yo me lavo antes de dormir."
    assert result.translation.text == "I wash myself before going to sleep."
    assert result.sentence.provenance.provider == "litellm"
    assert result.translation.provenance.provider == "deepl"


def test_text_generation_service_normalizes_uncertainty_and_sense_notes() -> None:
    service = TextGenerationService(
        sentence_adapter=FakeSentenceAdapter(),
        translation_adapter=FakeTranslationAdapter(),
    )

    result = service.generate_bundle(
        candidate=build_candidate(),
        deck_language=SupportedLanguage.ES,
    )

    assert result.sentence.intended_sense == "reflexive daily routine"
    assert result.sentence.uncertainty_notes == ["medium confidence"]


def test_text_generation_service_uses_candidate_translation_policy() -> None:
    sentence_adapter = FakeSentenceAdapter()
    translation_adapter = FakeTranslationAdapter()
    service = TextGenerationService(
        sentence_adapter=sentence_adapter,
        translation_adapter=translation_adapter,
    )

    candidate = build_candidate().model_copy(update={"translation_target_language": "pt"})

    result = service.generate_bundle(
        candidate=candidate,
        deck_language=SupportedLanguage.ES,
    )

    assert sentence_adapter.requests[0].target_language == SupportedLanguage.ES.value
    assert translation_adapter.requests[0].translation_target_language == "pt"
    assert translation_adapter.requests[0].sentence == result.sentence.text


def test_text_generation_service_uses_generated_sentence_for_same_language_translation() -> None:
    translation_adapter = FakeTranslationAdapter()
    service = TextGenerationService(
        sentence_adapter=EnglishSentenceAdapter(),
        translation_adapter=translation_adapter,
    )

    candidate = build_candidate().model_copy(update={"translation_target_language": "en"})

    result = service.generate_bundle(candidate=candidate, deck_language=SupportedLanguage.EN)

    assert result.sentence.text == "I wash my hands before dinner."
    assert result.translation.text == "I wash my hands before dinner."
    assert result.translation.target_language == "en"
    assert result.translation.provenance.source == "same-language-translator"
    assert translation_adapter.requests == []


def test_tatoeba_fallback_translation_uses_selected_sentence_not_linked_translation_text() -> None:
    translation_adapter = TrackingTranslationAdapter()
    service = TextGenerationService(
        sentence_adapter=FakeSentenceAdapter(),
        translation_adapter=translation_adapter,
    )

    fallback = SentenceGenerationFallback(
        sentence_result=SentenceGenerationResult(
            sentence="Yo me lavo antes de dormir.",
            intended_sense="reflexive daily routine",
            provenance={
                "source": "tatoeba",
                "linked_translation_text": "I linked this from Tatoeba.",
            },
        )
    )

    result = service.generate_bundle_from_fallback(
        candidate=build_candidate(),
        deck_language=SupportedLanguage.ES,
        fallback=fallback,
    )

    assert result.sentence.text == "Yo me lavo antes de dormir."
    assert translation_adapter.requests[0].sentence == "Yo me lavo antes de dormir."
    assert translation_adapter.requests[0].translation_target_language == "en"
    assert result.translation.text == "I wash myself before going to sleep."
