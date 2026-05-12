"""Tests for provider-backed text adapters."""

from __future__ import annotations

import json

from multilang.services.provider_text_adapters import (
    DeepLTranslationAdapter,
    FallbackTranslationAdapter,
    GoogleTranslateAdapter,
    LiteLLMSentenceAdapter,
    can_use_deepl,
    can_use_google_translate,
    can_use_litellm,
)
from multilang.services.text_generation import SentenceGenerationRequest, SentenceTranslationRequest
from multilang.services.text_generation import DefinitionGenerationRequest
from multilang.settings import Settings


def test_litellm_sentence_adapter_uses_openrouter_key_and_json_response() -> None:
    calls: list[dict[str, object]] = []

    def fake_completion(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "sentence": "Я живу в Москве.",
                                "intended_sense": "location preposition",
                                "uncertainty_notes": [],
                            }
                        )
                    }
                }
            ]
        }

    settings = Settings(
        _env_file=None,
        text_generation_model="openai/gpt-4o-mini",
        openrouter_api_key="router-key",
    )
    result = LiteLLMSentenceAdapter(settings, completion_func=fake_completion).generate_sentence(
        SentenceGenerationRequest(
            display_form="в",
            lemma="в",
            definitions_html="in, at, on",
            target_language="ru",
            translation_target_language="en",
        )
    )

    assert result.sentence == "Я живу в Москве."
    assert result.intended_sense == "location preposition"
    assert result.provenance["provider"] == "litellm"
    assert calls[0]["model"] == "openrouter/openai/gpt-4o-mini"
    assert calls[0]["api_key"] == "router-key"
    assert "Study form: в" in calls[0]["messages"][1]["content"]


def test_litellm_definition_adapter_generates_definition_without_cache_definition() -> None:
    calls: list[dict[str, object]] = []

    def fake_completion(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "definitions_html": "noun: a safe place for boats",
                            }
                        )
                    }
                }
            ]
        }

    settings = Settings(
        _env_file=None,
        text_generation_model="openai/gpt-4o-mini",
        openrouter_api_key="router-key",
    )
    result = LiteLLMSentenceAdapter(settings, completion_func=fake_completion).generate_definition(
        DefinitionGenerationRequest(
            display_form="harbor",
            lemma="harbor",
            target_language="en",
            part_of_speech="noun",
        )
    )

    prompt = calls[0]["messages"][1]["content"]
    assert result.definitions_html == "noun: a safe place for boats"
    assert result.provenance["source"] == "provider-definition-generator"
    assert "Generate the definition from your language knowledge" in prompt
    assert "a sheltered place" not in prompt


def test_litellm_highlight_prompt_uses_redacted_context_and_rules() -> None:
    calls: list[dict[str, object]] = []

    def fake_completion(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "sentence": "Readers wash every cup before dawn.",
                                "intended_sense": "reading context",
                                "uncertainty_notes": [],
                            }
                        )
                    }
                }
            ]
        }

    settings = Settings(_env_file=None, text_generation_model="openai/gpt-4o-mini", openrouter_api_key="router-key")
    result = LiteLLMSentenceAdapter(settings, completion_func=fake_completion).generate_sentence(
        SentenceGenerationRequest(
            display_form="wash",
            lemma="wash",
            definitions_html="to wash",
            target_language="en",
            translation_target_language="pt",
            source_type="kindle-highlights",
            highlight_context="Readers wash every cup before dawn REDACTED",
        )
    )

    prompt = calls[0]["messages"][1]["content"]
    assert result.provenance["provider"] == "litellm"
    assert result.provenance["source_type"] == "kindle-highlights"
    assert "Highlight context hint" in prompt
    assert "Readers wash every cup before dawn REDACTED" in prompt
    assert "between 6 and 16 words" in prompt
    assert "study form or a normal inflection" in prompt
    assert "dav/private-export" not in prompt


def test_deepl_translation_adapter_maps_target_language() -> None:
    class FakeResult:
        text = "I live in Moscow."

    class FakeTranslator:
        def __init__(self) -> None:
            self.calls: list[dict[str, str]] = []

        def translate_text(self, sentence: str, *, target_lang: str) -> FakeResult:
            self.calls.append({"sentence": sentence, "target_lang": target_lang})
            return FakeResult()

    translator = FakeTranslator()
    adapter = DeepLTranslationAdapter(
        Settings(_env_file=None, deepl_api_key="deepl-key"),
        translator_factory=lambda api_key: translator,
    )

    result = adapter.translate_sentence(
        SentenceTranslationRequest(
            sentence="Я живу в Москве.",
            translation_target_language="en",
        )
    )

    assert result.translation == "I live in Moscow."
    assert result.provenance["provider"] == "deepl"
    assert result.provenance["target_lang"] == "EN-US"
    assert translator.calls == [{"sentence": "Я живу в Москве.", "target_lang": "EN-US"}]


def test_google_translate_adapter_uses_target_language() -> None:
    class FakeTranslator:
        def __init__(self, *, source: str, target: str) -> None:
            self.source = source
            self.target = target

        def translate(self, sentence: str) -> str:
            assert self.source == "auto"
            assert self.target == "pt"
            assert sentence == "I live in Moscow."
            return "Eu moro em Moscou."

    result = GoogleTranslateAdapter(translator_factory=FakeTranslator).translate_sentence(
        SentenceTranslationRequest(sentence="I live in Moscow.", translation_target_language="pt")
    )

    assert result.translation == "Eu moro em Moscou."
    assert result.provenance["provider"] == "google_translate"


def test_fallback_translation_adapter_uses_google_when_deepl_fails() -> None:
    class BrokenPrimary:
        def translate_sentence(self, request: SentenceTranslationRequest):
            raise ValueError("deepl unavailable")

    class Fallback:
        def translate_sentence(self, request: SentenceTranslationRequest):
            return GoogleTranslateAdapter(
                translator_factory=lambda **kwargs: type(
                    "Translator",
                    (),
                    {"translate": lambda self, sentence: "fallback translation"},
                )()
            ).translate_sentence(request)

    result = FallbackTranslationAdapter(primary=BrokenPrimary(), fallback=Fallback()).translate_sentence(
        SentenceTranslationRequest(sentence="Hello.", translation_target_language="en")
    )

    assert result.translation == "fallback translation"
    assert result.provenance["provider"] == "google_translate"
    assert result.provenance["fallback_reason"] == "deepl unavailable"


def test_provider_detection_requires_configured_keys() -> None:
    local_settings = Settings(_env_file=None)
    provider_settings = Settings(
        _env_file=None,
        text_generation_provider="litellm",
        translation_provider="deepl",
        openrouter_api_key="router-key",
        deepl_api_key="deepl-key",
    )

    assert can_use_litellm(local_settings) is False
    assert can_use_deepl(local_settings) is False
    assert can_use_google_translate(Settings(_env_file=None, translation_provider="google")) is True
    assert can_use_litellm(provider_settings) is True
    assert can_use_deepl(provider_settings) is True
