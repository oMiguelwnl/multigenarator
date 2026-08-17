"""Tests for Phase 3 text generation boundaries."""

from __future__ import annotations

from types import SimpleNamespace
import unicodedata

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
    KoreanTextError,
)
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
)
from multilang.services.text_generation import (
    DefinitionGenerationRequest,
    GeneratedTextBundle,
    SentenceGenerationFallback,
    TextGenerationService,
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceGenerationAdapter,
    SentenceTranslationRequest,
    SentenceTranslationResult,
    SentenceTranslationAdapter,
    _cache_key_for_request,
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


def build_korean_fingerprint(
    *, analyzer_package_version: str = "0.23.2"
) -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version=analyzer_package_version,
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def build_korean_identity(
    *,
    part_of_speech: str = "NNG",
    sense_id: str = "fixture:actor:1",
    signature: tuple[tuple[str, str], ...] = (("배우", "NNG"),),
    analyzer_package_version: str = "0.23.2",
) -> KoreanLexicalIdentity:
    return KoreanLexicalIdentity(
        submitted_form="배우",
        canonical_nfc="배우",
        lemma="배우",
        part_of_speech=part_of_speech,
        sense_id=sense_id,
        register="standard",
        morpheme_signature=tuple(
            KoreanSignatureItem(form=form, pos=pos) for form, pos in signature
        ),
        analyzer_fingerprint=build_korean_fingerprint(
            analyzer_package_version=analyzer_package_version
        ),
        status="resolved",
    )


def build_korean_candidate(
    identity: KoreanLexicalIdentity | None = None,
) -> LexicalCardCandidate:
    resolved_identity = identity or build_korean_identity()
    return LexicalCardCandidate(
        submitted_form=resolved_identity.submitted_form or resolved_identity.canonical_nfc,
        display_form=resolved_identity.lemma,
        lemma=resolved_identity.lemma,
        lemma_key=resolved_identity.lexical_key,
        definitions_html="ator",
        definition_language="pt",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="reviewed_test_fixture"),
        korean_identity=resolved_identity,
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
    assert hasattr(request, "korean_identity")
    assert request.korean_identity is None
    assert "korean_identity" not in request.model_dump(mode="json")


def test_korean_requests_copy_the_complete_persisted_identity() -> None:
    identity = build_korean_identity()
    candidate = build_korean_candidate(identity)

    sentence_request = SentenceGenerationRequest.from_candidate(
        candidate=candidate,
        deck_language=SupportedLanguage.KO,
    )
    definition_request = DefinitionGenerationRequest(
        display_form=candidate.display_form,
        lemma=candidate.lemma,
        source_language="ko",
        target_language="pt",
        part_of_speech=identity.part_of_speech,
        korean_identity=identity,
    )

    expected = identity.model_dump(mode="json")
    assert hasattr(sentence_request, "korean_identity")
    assert hasattr(definition_request, "korean_identity")
    assert sentence_request.korean_identity == identity
    assert definition_request.korean_identity == identity
    assert sentence_request.model_dump(mode="json")["korean_identity"] == expected
    assert definition_request.model_dump(mode="json")["korean_identity"] == expected


def test_complete_korean_identity_isolates_request_dumps_and_cache_keys() -> None:
    identities = (
        build_korean_identity(),
        build_korean_identity(part_of_speech="VV"),
        build_korean_identity(sense_id="fixture:actor:2"),
        build_korean_identity(signature=(("배우", "NNG"), ("하", "XSV"))),
        build_korean_identity(analyzer_package_version="0.23.3"),
    )
    requests = tuple(
        SentenceGenerationRequest.from_candidate(
            candidate=build_korean_candidate(identity),
            deck_language=SupportedLanguage.KO,
        )
        for identity in identities
    )
    adapter = KoreanSentenceAdapter("배우가 와요.")

    dumps = tuple(request.model_dump_json() for request in requests)
    keys = tuple(
        _cache_key_for_request(
            "sentence",
            request,
            adapter=adapter,
            prompt_version="test-v1",
        )
        for request in requests
    )

    assert len(set(dumps)) == len(identities)
    assert len(set(keys)) == len(identities)


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


class FlakySentenceAdapter(FakeSentenceAdapter):
    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            raise TimeoutError("timeout api_key=secret raw prompt text")
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


class KoreanSentenceAdapter(SentenceGenerationAdapter):
    provider = "deterministic-fake"
    model = "korean-sentence-v1"

    def __init__(self, sentence: str) -> None:
        self.sentence = sentence
        self.requests: list[SentenceGenerationRequest] = []

    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        self.requests.append(request)
        return SentenceGenerationResult(
            sentence=self.sentence,
            intended_sense="source-backed test sense",
            uncertainty_notes=[],
            provenance={"provider": self.provider, "model": self.model},
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


class InMemoryProviderCache:
    def __init__(self) -> None:
        self.records: dict[object, dict[str, object]] = {}
        self.puts: list[tuple[object, dict[str, object], dict[str, object]]] = []

    @staticmethod
    def _key(key: object) -> object:
        return key

    def get(self, key: object) -> SimpleNamespace | None:
        response = self.records.get(self._key(key))
        if response is None:
            return None
        return SimpleNamespace(response=dict(response))

    def put(
        self,
        key: object,
        response: dict[str, object],
        *,
        metadata: dict[str, object],
    ) -> None:
        copied_response = dict(response)
        copied_metadata = dict(metadata)
        self.puts.append((key, copied_response, copied_metadata))
        self.records[self._key(key)] = copied_response


class RecordingRateLimiter:
    def __init__(self) -> None:
        self.wait_count = 0

    def wait(self) -> None:
        self.wait_count += 1


class RecordingProviderCallLogger:
    def __init__(self) -> None:
        self.records = []

    def insert(self, record):
        self.records.append(record)
        return record


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


def test_korean_sentence_output_is_nfc_before_cache_and_bundle_handoff() -> None:
    nfc_sentence = "배우가 와요."
    adapter = KoreanSentenceAdapter(unicodedata.normalize("NFD", nfc_sentence))
    cache = InMemoryProviderCache()
    service = TextGenerationService(
        sentence_adapter=adapter,
        translation_adapter=FakeTranslationAdapter(),
        provider_cache=cache,  # type: ignore[arg-type]
    )

    first = service.generate_bundle(
        candidate=build_korean_candidate(),
        deck_language=SupportedLanguage.KO,
    )

    sentence_put = cache.puts[0]
    assert sentence_put[1]["sentence"] == nfc_sentence
    assert unicodedata.is_normalized("NFC", str(sentence_put[1]["sentence"]))
    assert first.sentence.text == nfc_sentence
    assert first.sentence.intended_sense == "fixture:actor:1"
    assert sentence_put[1]["intended_sense"] == "fixture:actor:1"

    sentence_cache_key = cache._key(sentence_put[0])
    cache.records[sentence_cache_key]["sentence"] = unicodedata.normalize(
        "NFD", nfc_sentence
    )
    restored = service.generate_bundle(
        candidate=build_korean_candidate(),
        deck_language=SupportedLanguage.KO,
    )

    assert len(adapter.requests) == 1
    assert restored.sentence.text == nfc_sentence
    assert unicodedata.is_normalized("NFC", restored.sentence.text)
    assert restored.sentence.intended_sense == "fixture:actor:1"


def test_korean_fallback_output_is_nfc_before_bundle_handoff() -> None:
    nfc_sentence = "배우가 와요."
    service = TextGenerationService(
        sentence_adapter=KoreanSentenceAdapter("unused"),
        translation_adapter=FakeTranslationAdapter(),
    )

    bundle = service.generate_bundle_from_fallback(
        candidate=build_korean_candidate(),
        deck_language=SupportedLanguage.KO,
        fallback=SentenceGenerationFallback(
            sentence_result=SentenceGenerationResult(
                sentence=unicodedata.normalize("NFD", nfc_sentence),
                provenance={"source": "deterministic-fake"},
            )
        ),
    )

    assert bundle.sentence.text == nfc_sentence
    assert unicodedata.is_normalized("NFC", bundle.sentence.text)
    assert bundle.sentence.intended_sense == "fixture:actor:1"


@pytest.mark.parametrize("source", ["adapter", "cache"])
def test_forbidden_korean_provider_output_fails_content_free_before_handoff(
    source: str,
) -> None:
    forbidden_output = "ㄱ 비밀 provider output"
    adapter = KoreanSentenceAdapter(forbidden_output)
    cache = InMemoryProviderCache()
    service = TextGenerationService(
        sentence_adapter=adapter,
        translation_adapter=FakeTranslationAdapter(),
        provider_cache=cache,  # type: ignore[arg-type]
    )
    candidate = build_korean_candidate()
    if source == "cache":
        request = SentenceGenerationRequest.from_candidate(
            candidate=candidate,
            deck_language=SupportedLanguage.KO,
        )
        key = _cache_key_for_request(
            "sentence",
            request,
            adapter=adapter,
            prompt_version="text-generation-v1",
        )
        cache.records[cache._key(key)] = {
            "sentence": forbidden_output,
            "intended_sense": None,
            "uncertainty_notes": [],
            "provenance": {"provider": "deterministic-fake"},
        }

    with pytest.raises(KoreanTextError) as exc_info:
        service.generate_bundle(
            candidate=candidate,
            deck_language=SupportedLanguage.KO,
        )

    assert forbidden_output not in str(exc_info.value)
    assert "비밀" not in str(exc_info.value)
    assert cache.puts == []


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


def test_text_generation_service_rate_limits_sentence_and_translation_calls() -> None:
    limiter = RecordingRateLimiter()
    service = TextGenerationService(
        sentence_adapter=FakeSentenceAdapter(),
        translation_adapter=FakeTranslationAdapter(),
    )

    service.generate_bundle(
        candidate=build_candidate(),
        deck_language=SupportedLanguage.ES,
        rate_limiter=limiter,
    )

    assert limiter.wait_count == 2


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


def test_text_generation_service_rate_limits_only_provider_calls_for_same_language_translation() -> None:
    limiter = RecordingRateLimiter()
    service = TextGenerationService(
        sentence_adapter=EnglishSentenceAdapter(),
        translation_adapter=FakeTranslationAdapter(),
    )

    service.generate_bundle(
        candidate=build_candidate().model_copy(update={"translation_target_language": "en"}),
        deck_language=SupportedLanguage.EN,
        rate_limiter=limiter,
    )

    assert limiter.wait_count == 1


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


def test_text_generation_service_logs_provider_calls_without_raw_text() -> None:
    logger = RecordingProviderCallLogger()
    service = TextGenerationService(
        sentence_adapter=FakeSentenceAdapter(),
        translation_adapter=FakeTranslationAdapter(),
        provider_call_logger=logger,
    )

    service.generate_bundle(candidate=build_candidate(), deck_language=SupportedLanguage.ES, job_id="job-1")

    assert [record.operation for record in logger.records] == ["sentence", "translation"]
    assert logger.records[0].job_id == "job-1"
    assert logger.records[0].prompt_hash
    assert not hasattr(logger.records[0], "prompt")
    assert logger.records[0].provider == "litellm"


def test_text_generation_service_logs_successful_retry_attempt_count() -> None:
    logger = RecordingProviderCallLogger()
    service = TextGenerationService(
        sentence_adapter=FlakySentenceAdapter(),
        translation_adapter=FakeTranslationAdapter(),
        provider_call_logger=logger,
        retry_attempts=2,
        retry_base_delay_seconds=0,
    )

    service.generate_bundle(candidate=build_candidate(), deck_language=SupportedLanguage.ES, job_id="job-1")

    sentence_records = [record for record in logger.records if record.operation == "sentence"]
    assert [(record.status, record.attempt) for record in sentence_records] == [("failure", 1), ("success", 2)]
