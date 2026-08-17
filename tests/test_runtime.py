"""Tests for local runtime helpers that support shipped smoke flows."""

from __future__ import annotations

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import KoreanMorphologyStatus
from multilang.runtime import _default_deck_name, build_runtime_service
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.fallback_audio_adapter import FallbackAudioAdapter
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.library_pronunciation_adapters import (
    FallbackPronunciationAdapter,
    LibraryPronunciationAdapter,
)
from multilang.services.local_text_adapter import LocalSentenceAdapter, LocalTranslationAdapter
from multilang.services.provider_pronunciation_adapters import LiteLLMPronunciationAdapter
from multilang.services.text_generation import SentenceGenerationRequest, SentenceTranslationRequest
from multilang.settings import Settings


class FakeElevenLabsSpeechAdapter:
    instances = []

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings
        type(self).instances.append(self)

    def available_voice_ids(self) -> set[str] | None:
        return None

    def synthesize(self, **kwargs: object) -> AudioSynthesisResponse:
        raise AssertionError("not called")


class FakeAzureSpeechAdapter(FakeElevenLabsSpeechAdapter):
    instances = []


class FakeGoogleTranslateSpeechAdapter(FakeElevenLabsSpeechAdapter):
    instances = []


def test_local_runtime_uses_curated_smoke_sentence_and_translation_for_lantern() -> None:
    sentence_adapter = LocalSentenceAdapter()
    translation_adapter = LocalTranslationAdapter()

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


def test_runtime_fails_loudly_when_litellm_is_configured_without_credentials(tmp_path) -> None:
    with pytest.raises(ValueError, match="LiteLLM sentence generation requires"):
        build_runtime_service(
            Settings(
                _env_file=None,
                database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
                text_generation_provider="litellm",
                translation_provider="local",
            )
        )


def test_runtime_fails_loudly_when_deepl_is_configured_without_credentials(tmp_path) -> None:
    with pytest.raises(ValueError, match="DeepL translation requires"):
        build_runtime_service(
            Settings(
                _env_file=None,
                database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
                text_generation_provider="local",
                translation_provider="deepl",
            )
        )


def test_runtime_allows_local_text_services_only_when_explicitly_configured(tmp_path) -> None:
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        )
    )

    assert service is not None
    assert isinstance(service.grounding_service._pronunciation_generator, LibraryPronunciationAdapter)


def test_runtime_wires_litellm_pronunciation_adapter_when_configured(tmp_path) -> None:
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="litellm",
            translation_provider="local",
            openai_api_key="test-key",
        )
    )

    adapter = service.grounding_service._pronunciation_generator

    assert isinstance(adapter, FallbackPronunciationAdapter)
    assert isinstance(adapter.adapters[0], LibraryPronunciationAdapter)
    assert isinstance(adapter.adapters[1], LiteLLMPronunciationAdapter)


def test_runtime_wires_elevenlabs_audio_provider(tmp_path, monkeypatch) -> None:
    import multilang.runtime as runtime_module

    FakeElevenLabsSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "ElevenLabsSpeechAdapter", FakeElevenLabsSpeechAdapter)

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
            audio_provider="elevenlabs",
            elevenlabs_api_key="test-key",
            elevenlabs_voice_id="voice-123",
        )
    )

    assert service is not None
    assert len(FakeElevenLabsSpeechAdapter.instances) == 1
    assert FakeElevenLabsSpeechAdapter.instances[0].settings.audio_provider == "elevenlabs"


def test_runtime_wires_google_translate_audio_provider(tmp_path, monkeypatch) -> None:
    import multilang.runtime as runtime_module

    FakeGoogleTranslateSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "GoogleTranslateSpeechAdapter", FakeGoogleTranslateSpeechAdapter)

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
            audio_provider="google_translate",
        )
    )

    assert service is not None
    assert len(FakeGoogleTranslateSpeechAdapter.instances) == 1
    assert FakeGoogleTranslateSpeechAdapter.instances[0].settings.audio_provider == "google_translate"


def test_runtime_wires_configured_audio_fallback_chain(tmp_path, monkeypatch) -> None:
    import multilang.runtime as runtime_module

    FakeAzureSpeechAdapter.instances.clear()
    FakeElevenLabsSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    monkeypatch.setattr(runtime_module, "ElevenLabsSpeechAdapter", FakeElevenLabsSpeechAdapter)

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
            audio_provider="azure",
            audio_fallback_providers=["elevenlabs"],
            elevenlabs_api_key="test-key",
        )
    )

    adapter = service.generate_audio_items_service.audio_synthesis_service.adapter
    assert isinstance(adapter, FallbackAudioAdapter)
    assert len(FakeAzureSpeechAdapter.instances) == 1
    assert len(FakeElevenLabsSpeechAdapter.instances) == 1


def test_runtime_injects_one_korean_morphology_object_into_all_consumers(tmp_path) -> None:
    morphology = KiwiKoreanMorphologyService(
        analyzer_factory=lambda: (_ for _ in ()).throw(RuntimeError("not requested"))
    )

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        ),
        korean_morphology_service=morphology,
    )

    generation_validator = service.generate_text_items_service.text_validation_service
    regeneration_validator = service.regenerate_text_item_service.text_validation_service

    assert service.grounding_service._korean_morphology is morphology
    assert generation_validator is regeneration_validator
    assert generation_validator.korean_matcher is morphology
    assert regeneration_validator.korean_matcher is morphology
    assert generation_validator.korean_matcher.fingerprint is morphology.fingerprint


def test_runtime_default_korean_adapter_is_single_and_vendor_construction_is_lazy(
    tmp_path,
    monkeypatch,
) -> None:
    import multilang.runtime as runtime_module

    wrapper_instances: list[KiwiKoreanMorphologyService] = []
    analyzer_factory_calls = 0

    def unavailable_analyzer_factory() -> object:
        nonlocal analyzer_factory_calls
        analyzer_factory_calls += 1
        raise RuntimeError("private vendor detail")

    def morphology_factory() -> KiwiKoreanMorphologyService:
        wrapper = KiwiKoreanMorphologyService(
            analyzer_factory=unavailable_analyzer_factory
        )
        wrapper_instances.append(wrapper)
        return wrapper

    monkeypatch.setattr(
        runtime_module,
        "KiwiKoreanMorphologyService",
        morphology_factory,
        raising=False,
    )

    service = runtime_module.build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        )
    )

    assert len(wrapper_instances) == 1
    assert analyzer_factory_calls == 0
    shared_morphology = wrapper_instances[0]
    assert service.grounding_service._korean_morphology is shared_morphology
    assert (
        service.generate_text_items_service.text_validation_service.korean_matcher
        is shared_morphology
    )
    assert (
        service.regenerate_text_item_service.text_validation_service.korean_matcher
        is shared_morphology
    )

    first = shared_morphology.analyze("학교")
    second = shared_morphology.analyze("학교")

    assert analyzer_factory_calls == 1
    assert first.status is KoreanMorphologyStatus.UNAVAILABLE
    assert second.status is KoreanMorphologyStatus.UNAVAILABLE
    assert "private vendor detail" not in first.model_dump_json()
    assert "private vendor detail" not in second.model_dump_json()


def test_unavailable_korean_factory_does_not_block_non_korean_runtime_startup(
    tmp_path,
) -> None:
    analyzer_factory_calls = 0

    def unavailable_analyzer_factory() -> object:
        nonlocal analyzer_factory_calls
        analyzer_factory_calls += 1
        raise RuntimeError("private vendor detail")

    morphology = KiwiKoreanMorphologyService(
        analyzer_factory=unavailable_analyzer_factory
    )
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        ),
        korean_morphology_service=morphology,
    )

    assert service is not None
    assert analyzer_factory_calls == 0
    assert _default_deck_name(SupportedLanguage.EN) == "Multilang English"

    korean_result = service.grounding_service.resolve_korean_source_identity(
        surface_form="학교"
    )

    assert korean_result.status == "unavailable"
    assert analyzer_factory_calls == 1
    assert _default_deck_name(SupportedLanguage.EN) == "Multilang English"


def test_runtime_has_korean_display_name() -> None:
    assert _default_deck_name(SupportedLanguage.KO) == "Multilang Korean"
