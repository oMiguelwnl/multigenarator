"""Tests for local runtime helpers that support shipped smoke flows."""

from __future__ import annotations

import pytest

from multilang.runtime import build_runtime_service
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.fallback_audio_adapter import FallbackAudioAdapter
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

    assert isinstance(
        service.grounding_service._pronunciation_generator,
        LiteLLMPronunciationAdapter,
    )


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
