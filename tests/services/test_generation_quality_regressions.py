"""Regression cases from the generation audit, using offline provider doubles."""

from types import SimpleNamespace

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.generate_text_items import GenerateTextItemsService
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.lexical_lookup import LexicalRecord
from multilang.services.provider_response_cache import ProviderResponseCacheService
from multilang.services.text_generation import (
    DefinitionGenerationResult,
    SentenceGenerationResult,
    SentenceTranslationResult,
    TextGenerationService,
)
from multilang.services.text_validation import TextValidationResult


class Cache:
    def __init__(self):
        self.rows = {}

    def get_provider_response(self, key):
        return self.rows.get(key)

    def upsert_provider_response(self, value):
        self.rows[value.key] = value
        return value


def candidate():
    return LexicalCardCandidate(
        submitted_form="house", display_form="house", lemma="house", lemma_key="house",
        definitions_html="noun: a dwelling", definition_language="en", ipa="/haʊs/",
        translation_target_language="pt", grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="synthetic-test"),
    )


class SentenceAdapter:
    def __init__(self):
        self.calls = []

    def generate_sentence(self, request):
        self.calls.append(request)
        return SentenceGenerationResult(sentence="House." if len(self.calls) == 1 else "My house has a blue door.")


class LengthValidator:
    def validate(self, **kwargs):
        passed = len(kwargs["sentence"].text.split()) >= 4
        return TextValidationResult(
            validation_status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            validation_flags=[] if passed else [ValidationFlag(code=ValidationFlagCode.SENTENCE_TOO_SHORT, detail="too short")],
            confidence_score=0.95 if passed else 0.2,
            confidence_label=ConfidenceLabel.HIGH if passed else ConfidenceLabel.LOW,
        )


def test_repair_uses_a_new_cached_request_with_rejection_feedback():
    adapter = SentenceAdapter()
    generation = TextGenerationService(
        sentence_adapter=adapter,
        translation_adapter=SimpleNamespace(translate_sentence=lambda _: SentenceTranslationResult(translation="Minha casa tem uma porta azul.")),
        provider_cache=ProviderResponseCacheService(Cache()),
    )
    service = GenerateTextItemsService(
        job_repository=None, lexical_repository=None, text_repository=None,
        text_generation_service=generation, text_validation_service=LengthValidator(),
        tatoeba_sentence_source=SimpleNamespace(select_sentence=lambda **_: None),
    )
    item = candidate()
    bundle = generation.generate_bundle(candidate=item, deck_language=SupportedLanguage.EN, source_type="frequency")
    validation = service._validate_bundle(bundle=bundle, candidate=item, deck_language=SupportedLanguage.EN, source_type="frequency")
    repaired, result, _ = service._attempt_repair_chain(
        candidate=item, deck_language=SupportedLanguage.EN, generated_bundle=bundle,
        validation=validation, seen_sentences=set(), source_type="frequency",
    )
    assert repaired.sentence.text == "My house has a blue door."
    assert len(adapter.calls) == 2
    assert "sentence_too_short" in adapter.calls[1].repair_context.rejection_codes
    assert result.validation_status is ValidationStatus.PASSED


def test_manual_regeneration_never_replays_the_original_cached_attempt():
    adapter = SentenceAdapter()
    generation = TextGenerationService(
        sentence_adapter=adapter,
        translation_adapter=SimpleNamespace(translate_sentence=lambda _: SentenceTranslationResult(translation="Minha casa tem uma porta azul.")),
        provider_cache=ProviderResponseCacheService(Cache()),
    )
    args = dict(candidate=candidate(), deck_language=SupportedLanguage.EN, source_type="frequency")
    generation.generate_bundle(**args)
    generation.generate_bundle(**args)
    assert len(adapter.calls) == 1
    for _ in range(2):
        generation.regenerate_bundle(**args, previous_sentence="House.")
    assert len(adapter.calls) == 3
    first, second = (call.repair_context for call in adapter.calls[1:])
    assert first.attempt_id != second.attempt_id
    assert first.rejection_codes == ("manual_regeneration",)


def lexical_candidate(*, pronunciation=None, generator=None):
    record = LexicalRecord(term="house", display_form="house", lemma="house", definitions=["a dwelling"], definition_language="en", part_of_speech="noun", source="synthetic-test")
    return LexicalGroundingService(lookup=None, pronunciation_generator=pronunciation, definition_generator=generator)._grounded_candidate(
        language=SupportedLanguage.EN, submitted_form="house", display_form="house", record=record, definition_language="en",
    )






def test_definitions_without_independent_rewrite_review_do_not_call_model():
    calls = []
    def generate(request):
        calls.append(request)
        return DefinitionGenerationResult(definitions_html="noun: a dog")
    item = lexical_candidate(generator=SimpleNamespace(generate_definition=generate))
    assert item.definitions_html == "noun: a dwelling"
    assert calls == []
    assert item.provenance.definition.quality_decision == "source_verified"
