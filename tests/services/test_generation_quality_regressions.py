"""Regression cases from the generation audit, using offline provider doubles."""

from types import SimpleNamespace

import pytest

from multilang.domain.audio import AudioAssetKind, AudioSynthesisStatus
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
from multilang.services.provider_pronunciation_adapters import PronunciationGenerationResult
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


def test_missing_ipa_never_turns_the_spelling_into_pronunciation():
    item = lexical_candidate()
    assert item.ipa is None
    assert item.grounding_status is GroundingStatus.PENDING
    assert item.warning_code == "pronunciation_review_required"


def test_model_pronunciation_remains_unverified_and_retains_uncertainty():
    item = lexical_candidate(pronunciation=SimpleNamespace(generate_pronunciation=lambda _: PronunciationGenerationResult(
        ipa="/nonsense/", spoken_form="nonsense", uncertainty_notes=["pronunciation uncertain"],
        provenance={"source": "provider-pronunciation-generator", "provider": "litellm"},
    )))
    assert not item.provenance.pronunciation.authoritative
    assert item.grounding_status is GroundingStatus.PENDING
    assert "pronunciation uncertain" in item.provenance.pronunciation.uncertainty_notes


def test_definitions_without_independent_rewrite_review_do_not_call_model():
    calls = []
    def generate(request):
        calls.append(request)
        return DefinitionGenerationResult(definitions_html="noun: a dog")
    item = lexical_candidate(generator=SimpleNamespace(generate_definition=generate))
    assert item.definitions_html == "noun: a dwelling"
    assert calls == []
    assert item.provenance.definition.quality_decision == "source_verified"


def test_audio_normalization_preserves_display_but_accepts_typographic_apostrophe():
    from multilang.services.audio_integrity import assert_word_audio_matches_word
    from multilang.services.audio_synthesis import AudioSynthesisService
    from multilang.settings import Settings
    service = AudioSynthesisService(adapter=SimpleNamespace(available_voice_ids=lambda: None), settings=Settings(_env_file=None))
    asset = service._prepare_asset(language=SupportedLanguage.FR, job_id="job", item_key="item", asset_kind=AudioAssetKind.WORD, display_text="l’homme")
    assert_word_audio_matches_word(asset, "l’homme")
    assert asset.display_text == "l’homme"
    assert asset.normalized_input.tts_text == "l'homme"


def test_sentence_audio_binding_rejects_old_example():
    from multilang.services.audio_integrity import (
        AudioIntegrityError,
        assert_sentence_audio_matches_sentence,
    )
    from multilang.services.audio_synthesis import AudioSynthesisService
    from multilang.settings import Settings
    service = AudioSynthesisService(adapter=SimpleNamespace(available_voice_ids=lambda: None), settings=Settings(_env_file=None))
    asset = service._prepare_asset(language=SupportedLanguage.EN, job_id="job", item_key="item", asset_kind=AudioAssetKind.SENTENCE, display_text="I run every morning.")
    with pytest.raises(AudioIntegrityError):
        assert_sentence_audio_matches_sentence(asset, "I run beside the river.")


def test_synthesis_rejects_non_audio_bytes(tmp_path):
    from multilang.services.audio_synthesis import AudioSynthesisResponse, AudioSynthesisService
    from multilang.settings import Settings
    def synthesize(**kwargs):
        path = kwargs["output_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"not an mp3 recording")
        return AudioSynthesisResponse(storage_path=path, byte_size=path.stat().st_size, duration_ms=900)
    service = AudioSynthesisService(adapter=SimpleNamespace(available_voice_ids=lambda: None, synthesize=synthesize), settings=Settings(_env_file=None, audio_storage_dir=tmp_path))
    asset = service._prepare_asset(language=SupportedLanguage.EN, job_id="job", item_key="item", asset_kind=AudioAssetKind.WORD, display_text="house")
    assert service.synthesize_prepared_asset(asset).provenance.status is AudioSynthesisStatus.FAILED


def test_runtime_export_rechecks_media_bytes_and_recorded_hash(tmp_path):
    from hashlib import sha256

    from support.audio import SILENT_MP3

    from multilang.runtime import _validate_audio_artifact
    from multilang.services.audio_synthesis import AudioSynthesisService
    from multilang.settings import Settings

    service = AudioSynthesisService(adapter=SimpleNamespace(available_voice_ids=lambda: None), settings=Settings(_env_file=None))
    asset = service._prepare_asset(language=SupportedLanguage.EN, job_id="job", item_key="house", asset_kind=AudioAssetKind.WORD, display_text="house")
    path = tmp_path / "house.mp3"
    path.write_bytes(SILENT_MP3)
    asset.provenance = asset.provenance.model_copy(update={
        "storage_path": str(path), "byte_size": len(SILENT_MP3),
        "artifact_sha256": sha256(SILENT_MP3).hexdigest(),
    })
    _validate_audio_artifact(asset)
    asset.provenance.artifact_sha256 = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        _validate_audio_artifact(asset)
    path.write_bytes(b"x" * len(SILENT_MP3))
    with pytest.raises(ValueError, match="invalid or corrupt"):
        _validate_audio_artifact(asset)
