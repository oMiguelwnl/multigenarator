"""Offline registry and provider contract tests for Mandarin support."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.lexical_lookup import LexicalRecord
from multilang.services.local_text_adapter import LocalSentenceAdapter
from multilang.services.part_of_speech import infer_function_word_part_of_speech
from multilang.services.audio_voice_registry import VOICE_REGISTRY_VERSION, get_voice_registry
from multilang.services.elevenlabs_speech_adapter import ElevenLabsSpeechAdapter
from multilang.services.google_translate_speech_adapter import GoogleTranslateSpeechAdapter
from multilang.services.provider_pronunciation_adapters import (
    PronunciationGenerationRequest,
    _pronunciation_prompt,
)
from multilang.services.provider_text_adapters import (
    DeepLTranslationAdapter,
    _sentence_prompt,
)
from multilang.services.tatoeba_sentence_source import (
    TatoebaApiCandidateProvider,
    TatoebaCandidateRow,
    TatoebaSentenceSource,
)
from multilang.services.text_generation import SentenceGenerationRequest, SentenceTranslationRequest
from multilang.services.word_list_parser import ParsedWordListItem
from multilang.settings import Settings


class _FakeAudioResponse:
    def __init__(self, payload: bytes = b"ID3-mandarin") -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.parametrize(
    ("model_id", "expected_language_code"),
    [
        ("eleven_multilingual_v2", None),
        ("eleven_flash_v2_5", "zh"),
        ("eleven_turbo_v2_5", "zh"),
        ("eleven_v3", "zh"),
        ("future-unknown-model", None),
    ],
)
def test_elevenlabs_mandarin_payload_is_model_capability_aware(
    tmp_path: Path,
    model_id: str,
    expected_language_code: str | None,
) -> None:
    requests = []

    def fake_urlopen(request, timeout: int = 30):
        requests.append(request)
        return _FakeAudioResponse()

    adapter = ElevenLabsSpeechAdapter(
        Settings(
            _env_file=None,
            elevenlabs_api_key="test-key",
            elevenlabs_voice_id="voice-zh",
            elevenlabs_model_id=model_id,
        ),
        urlopen_func=fake_urlopen,
    )
    selection = adapter.select_voice(SupportedLanguage.ZH)
    adapter.synthesize(
        ssml_text="<speak>我去银行。</speak>",
        voice_id=selection.voice_id,
        locale=selection.locale,
        output_path=tmp_path / f"{model_id}.mp3",
        audio_format="mp3_44100_128",
    )

    payload = json.loads((requests[0].data or b"").decode("utf-8"))
    assert selection.language is SupportedLanguage.ZH
    assert selection.locale == "zh-CN"
    assert payload.get("language_code") == expected_language_code
    if expected_language_code is None:
        assert "language_code" not in payload


def test_google_translate_mandarin_preserves_full_locale_in_query(tmp_path: Path) -> None:
    requests = []

    def fake_urlopen(request, timeout: int = 30):
        requests.append(request)
        return _FakeAudioResponse()

    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None), urlopen_func=fake_urlopen)
    selection = adapter.select_voice(SupportedLanguage.ZH)
    adapter.synthesize(
        ssml_text="我去银行。",
        voice_id=selection.voice_id,
        locale=selection.locale,
        output_path=tmp_path / "zh.mp3",
        audio_format="mp3",
    )

    query = parse_qs(urlparse(requests[0].full_url).query)
    assert selection.voice_id == "zh-CN"
    assert selection.locale == "zh-CN"
    assert query["tl"] == ["zh-CN"]


def test_azure_voice_registry_uses_two_same_locale_mandarin_voices() -> None:
    plan = get_voice_registry()[SupportedLanguage.ZH]

    assert VOICE_REGISTRY_VERSION == "2026-07-20a"
    assert plan.preferred.voice_id == "zh-CN-XiaoxiaoNeural"
    assert plan.preferred.locale == "zh-CN"
    assert [(voice.voice_id, voice.locale) for voice in plan.same_locale_alternates] == [
        ("zh-CN-YunxiNeural", "zh-CN")
    ]


def test_mandarin_provider_prompts_and_deepl_target_are_explicitly_simplified() -> None:
    sentence_prompt = _sentence_prompt(
        SentenceGenerationRequest(
            display_form="中国",
            lemma="中国",
            definitions_html="noun: China",
            target_language="zh",
            translation_target_language="en",
            source_type="frequency",
        )
    )
    pronunciation_prompt = _pronunciation_prompt(
        PronunciationGenerationRequest(
            target_language="zh",
            display_form="中国",
            lemma="中国",
        )
    )

    assert "Mandarin Chinese (zh)" in sentence_prompt
    assert "Simplified Chinese" in sentence_prompt
    assert "Traditional Chinese" in sentence_prompt
    assert "pinyin" in sentence_prompt
    assert "Mandarin Chinese (zh)" in pronunciation_prompt

    class FakeTranslator:
        calls: list[str] = []

        def translate_text(self, sentence: str, *, target_lang: str):
            self.calls.append(target_lang)
            return type("Result", (), {"text": "中国"})()

    translator = FakeTranslator()
    adapter = DeepLTranslationAdapter(
        Settings(_env_file=None, deepl_api_key="test-key"),
        translator_factory=lambda _: translator,
    )
    adapter.translate_sentence(
        SentenceTranslationRequest(sentence="China", translation_target_language="zh")
    )
    assert translator.calls == ["ZH-HANS"]


def test_tatoeba_serializes_cmn_and_accepts_matching_unspaced_han(monkeypatch) -> None:
    requested_urls: list[str] = []

    class FakeJsonResponse(_FakeAudioResponse):
        def __init__(self) -> None:
            super().__init__(json.dumps({"results": []}).encode("utf-8"))

    def fake_urlopen(request, timeout: int = 10):
        requested_urls.append(request.full_url)
        return FakeJsonResponse()

    monkeypatch.setattr("multilang.services.tatoeba_sentence_source.urllib.request.urlopen", fake_urlopen)
    provider = TatoebaApiCandidateProvider(page_limit=1)
    provider.search_candidates(
        display_form="银行",
        lemma="银行",
        target_language="zh",
        translation_target_language="en",
    )

    assert parse_qs(urlparse(requested_urls[0]).query)["from"] == ["cmn"]

    source = TatoebaSentenceSource(
        candidate_provider=type(
            "Provider",
            (),
            {
                "search_candidates": lambda self, **kwargs: [
                    TatoebaCandidateRow(
                        sentence_id=1,
                        sentence_text="我每天去中国银行。",
                        target_language="zh",
                        translation_language="en",
                        linked_translations=["I go to the Bank of China every day."],
                    ),
                    TatoebaCandidateRow(
                        sentence_id=2,
                        sentence_text="我每天阅读中文报纸。",
                        target_language="zh",
                        translation_language="en",
                        linked_translations=["I read a Chinese newspaper every day."],
                    ),
                ]
            },
        )()
    )
    selected = source.select_sentence(
        display_form="银行",
        lemma="银行",
        target_language="zh",
        translation_target_language="en",
    )

    assert selected is not None
    assert selected.sentence == "我每天去中国银行。"


def test_mandarin_word_list_grounding_uses_english_policy() -> None:
    class Lookup:
        def lookup(self, *, language_code: str, term: str):
            assert language_code == "zh"
            return LexicalRecord(
                term=term,
                display_form="中国",
                lemma="中国",
                definitions=["China"],
                part_of_speech="proper noun",
                ipa="zhong guo",
                source="fixture",
            )

    calls = []

    class DefinitionGenerator:
        def generate_definition(self, request):
            calls.append(request)
            return type(
                "Definition",
                (),
                {
                    "definitions_html": "proper noun: China",
                    "provenance": {"source": "fake-definition"},
                },
            )()

    candidate = LexicalGroundingService(
        lookup=Lookup(),
        definition_generator=DefinitionGenerator(),
    ).ground_word_list_item(
        language=SupportedLanguage.ZH,
        item=ParsedWordListItem(
            line_number=1,
            submitted_form="中国",
            display_form="中国",
            item_key="中国",
        ),
    )

    assert candidate.definition_language == "en"
    assert candidate.translation_target_language == "en"
    assert calls[0].source_language == "zh"
    assert calls[0].target_language == "en"


@pytest.mark.parametrize(
    ("word", "expected"),
    [("的", "particle"), ("和", "conjunction"), ("我", "pronoun")],
)
def test_mandarin_function_words_have_deterministic_part_of_speech(
    word: str,
    expected: str,
) -> None:
    assert (
        infer_function_word_part_of_speech(
            source_language="zh",
            display_form=word,
            lemma=word,
        )
        == expected
    )


def test_local_mandarin_template_emits_simplified_sentence_with_target() -> None:
    result = LocalSentenceAdapter().generate_sentence(
        SentenceGenerationRequest(
            display_form="中国",
            lemma="中国",
            definitions_html="proper noun: China",
            target_language="zh",
            translation_target_language="en",
            source_type="word-list",
        )
    )

    assert result.sentence == "朋友们在晚饭时讨论中国。"
    assert "中國" not in result.sentence
