"""Transport boundaries for Korean field regeneration use only in-memory providers."""

import json
from types import SimpleNamespace

import httpx
import pytest

from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderRoute,
    KoreanProviderTask,
)
from multilang.services.text_generation import SentenceTranslationRequest


def route(provider="openai", model="gpt-4.1-mini"):
    return KoreanProviderRoute(task=KoreanProviderTask.TRANSLATION, provider=provider, model=model,
        budget=KoreanProviderBudget(max_attempts=3, max_input_tokens=4096, max_output_tokens=128,
            max_total_tokens=4224, max_estimated_cost_usd=1, max_latency_ms=1500, timeout_seconds=1,
            max_batch_items=1, max_concurrency=1), cache_namespace="test", response_schema_sha256="a" * 64)


def test_openai_field_transport_uses_exact_route_and_no_hidden_retries(monkeypatch):
    from multilang.services.korean_field_provider import KoreanFieldProvider
    calls = []
    def complete(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": '{"translation":"Há uma casa."}'}}],
                "usage": {"prompt_tokens": 33, "completion_tokens": 8, "total_tokens": 41}}
    provider = KoreanFieldProvider(SimpleNamespace(openai_api_key="test-key"), "translation", route(),
        completion_func=complete, cost_estimator=lambda **kwargs: 0.001, token_counter=lambda **kwargs: 33)
    result = provider.translate_sentence(SentenceTranslationRequest(sentence="집이 있어요.", translation_target_language="pt"))
    assert result.translation == "Há uma casa."
    assert calls[0]["model"] == "openai/gpt-4.1-mini"
    assert calls[0]["num_retries"] == 0
    assert calls[0]["timeout"] == 1
    assert calls[0]["max_tokens"] == 128
    assert result.provenance["input_tokens"] == 33


def test_estimated_cost_limit_refuses_before_provider_call():
    from multilang.services.korean_field_provider import KoreanFieldProvider
    calls = []
    provider = KoreanFieldProvider(SimpleNamespace(openai_api_key="test-key"), "translation", route(),
        completion_func=lambda **kwargs: calls.append(kwargs), cost_estimator=lambda **kwargs: 2,
        token_counter=lambda **kwargs: 33)
    with pytest.raises(ValueError, match="budget"):
        provider.translate_sentence(SentenceTranslationRequest(sentence="집이 있어요.", translation_target_language="pt"))
    assert calls == []


def test_deepl_field_transport_is_one_request_with_pt_br_and_bounded_timeout():
    from multilang.services.korean_field_provider import KoreanFieldProvider
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={"translations": [{"text": "Há uma casa."}]})
    provider = KoreanFieldProvider(SimpleNamespace(deepl_api_key="test-key:fx", deepl_cost_per_character_usd=0), "translation",
        route("deepl", "deepl-api-PT-BR"), http_transport=httpx.MockTransport(respond))
    result = provider.translate_sentence(SentenceTranslationRequest(sentence="집이 있어요.", translation_target_language="pt"))
    assert result.translation == "Há uma casa."
    assert calls[0].url == "https://api-free.deepl.com/v2/translate"
    assert json.loads(calls[0].content) == {"text": ["집이 있어요."], "source_lang": "KO", "target_lang": "PT-BR"}
    assert calls[0].extensions["timeout"]["read"] == 1


def test_deepl_timeout_never_retries():
    from multilang.services.korean_field_provider import KoreanFieldProvider
    calls = []
    def fail(request):
        calls.append(request)
        raise httpx.ReadTimeout("private provider detail", request=request)
    provider = KoreanFieldProvider(SimpleNamespace(deepl_api_key="test-key", deepl_cost_per_character_usd=0.00002), "translation",
        route("deepl", "deepl-api-PT-BR"), http_transport=httpx.MockTransport(fail))
    with pytest.raises(httpx.ReadTimeout):
        provider.translate_sentence(SentenceTranslationRequest(sentence="집이 있어요.", translation_target_language="pt"))
    assert len(calls) == 1


@pytest.mark.parametrize("key", ["test-key", "test-key:fx"])
def test_deepl_requires_explicit_price_for_every_plan_before_request(key):
    from multilang.services.korean_field_provider import KoreanFieldProvider
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={"translations": [{"text": "Há uma casa."}]})
    provider = KoreanFieldProvider(SimpleNamespace(deepl_api_key=key), "translation",
        route("deepl", "deepl-api-PT-BR"), http_transport=httpx.MockTransport(respond))
    with pytest.raises(ValueError, match="explicit character price"):
        provider.translate_sentence(SentenceTranslationRequest(sentence="집이 있어요.", translation_target_language="pt"))
    assert calls == []


@pytest.mark.parametrize("price", [-0.01, float("nan"), float("inf")])
def test_deepl_character_price_setting_rejects_unbounded_or_negative_values(price):
    from pydantic import ValidationError

    from multilang.settings import Settings
    with pytest.raises(ValidationError):
        Settings(_env_file=None, deepl_cost_per_character_usd=price)


def test_deepl_explicit_zero_character_price_is_supported():
    from multilang.settings import Settings
    assert Settings(_env_file=None, deepl_cost_per_character_usd=0).deepl_cost_per_character_usd == 0


def _definition_request():
    from multilang.domain.korean import (
        KoreanAnalyzerFingerprint,
        KoreanLexicalIdentity,
        KoreanSignatureItem,
    )
    from multilang.services.text_generation import DefinitionGenerationRequest

    fingerprint = KoreanAnalyzerFingerprint(analyzer_name="kiwi", analyzer_package_version="fixture",
        model_package_version="fixture", model_type="cong", enabled_dialects="standard", num_workers=1,
        integrate_allomorph=True, top_n=2, split_complex=False, compatible_jamo=False, normalize_coda=False,
        z_coda=False, typos=None, oov_handling="chr", policy_version="kiwi-top2-consensus-v1")
    identity = KoreanLexicalIdentity(submitted_form="집", canonical_nfc="집", lemma="집", part_of_speech="NNG",
        sense_id="house", register="standard", morpheme_signature=(KoreanSignatureItem(form="집", pos="NNG"),),
        analyzer_fingerprint=fingerprint, status="resolved")
    return DefinitionGenerationRequest(display_form="집", lemma="집", source_language="ko", target_language="pt",
        part_of_speech="NNG", korean_identity=identity)


@pytest.mark.parametrize("label", ["substantivo", "noun"])
def test_definition_field_prompt_preserves_identity_and_requests_exportable_format(label):
    from multilang.services.assemble_export_cards import _LEGACY_DEFINITION_TEMPLATE_RE
    from multilang.services.korean_field_provider import KoreanFieldProvider

    calls = []
    def complete(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": json.dumps({"definitions_html": f"{label}: casa"})}}],
                "usage": {"prompt_tokens": 33, "completion_tokens": 8}}
    provider = KoreanFieldProvider(SimpleNamespace(openai_api_key="test-key"), "definition",
        route().model_copy(update={"task": KoreanProviderTask.DEFINITION}), completion_func=complete,
        cost_estimator=lambda **kwargs: 0.001, token_counter=lambda **kwargs: 33)
    request = _definition_request()
    result = provider.generate_definition(request)
    assert _LEGACY_DEFINITION_TEMPLATE_RE.match(result.definitions_html)
    prompt = calls[0]["messages"][0]["content"]
    assert "[part of speech]: [meaning]" in prompt
    assert "Portuguese part-of-speech label" in prompt
    assert "korean_identity.part_of_speech" in prompt
    assert "substantivo: casa" in prompt
    assert json.loads(calls[0]["messages"][1]["content"]) == request.model_dump(mode="json", exclude_none=True)


@pytest.mark.parametrize("definition", ["casa", "substantivo:", "1: casa"])
def test_definition_field_refuses_provider_output_without_exportable_pos_label(definition):
    from multilang.services.korean_field_provider import KoreanFieldProvider

    def complete(**kwargs):
        return {"choices": [{"message": {"content": json.dumps({"definitions_html": definition})}}],
                "usage": {"prompt_tokens": 33, "completion_tokens": 8}}
    provider = KoreanFieldProvider(SimpleNamespace(openai_api_key="test-key"), "definition",
        route().model_copy(update={"task": KoreanProviderTask.DEFINITION}), completion_func=complete,
        cost_estimator=lambda **kwargs: 0.001, token_counter=lambda **kwargs: 33)
    with pytest.raises(ValueError, match="definition format"):
        provider.generate_definition(_definition_request())
