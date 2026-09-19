"""Fidelity is an exact-pair advisory check, independent of structural validation."""

from types import SimpleNamespace

import pytest

from multilang.domain.text_quality import TextProvenance, ValidationStatus
from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation
from multilang.services.text_validation import TextValidationService


def pair():
    provenance = TextProvenance(source="synthetic-test")
    return dict(
        sentence=GeneratedSentence(text="My house has a blue door.", target_language="en", provenance=provenance),
        translation=GeneratedTranslation(text="Meu cachorro gosta de brincar no parque.", target_language="pt", provenance=provenance),
        display_form="house", lemma="house", definitions_html="noun: a dwelling",
    )


def validator(**kwargs):
    # These independent tests isolate semantic admission from local NLP loading.
    return TextValidationService(
        language_identifier=SimpleNamespace(detect=lambda *_, **__: SimpleNamespace(reliable=False, detected_language=None)),
        morphological_analyzer=SimpleNamespace(contains_target_lemma=lambda **_: SimpleNamespace(reliable=True, matched=True)),
        require_translation_fidelity=True, **kwargs,
    )


@pytest.mark.parametrize("decision", ["mismatch", "uncertain"])
def test_unrelated_or_uncertain_translation_cannot_be_accepted(decision):
    from multilang.domain.translation_quality import TranslationFidelityVerdict
    requests = []
    def check(request):
        requests.append(request)
        return TranslationFidelityVerdict(decision=decision)
    result = validator(translation_fidelity_checker=check).validate(**pair())
    assert result.validation_status is ValidationStatus.FAILED
    assert any(flag.code.value == "translation_mismatch" for flag in result.validation_flags)
    assert requests[0].sentence == pair()["sentence"].text
    assert requests[0].translation == pair()["translation"].text


def test_required_fidelity_fails_closed_when_reviewer_is_missing_or_unavailable():
    def unavailable(_):
        raise TimeoutError("provider unavailable")
    for checker in (None, unavailable):
        result = validator(translation_fidelity_checker=checker).validate(**pair())
        assert result.validation_status is ValidationStatus.FAILED


def test_fidelity_cache_is_bound_to_both_texts_and_languages():
    from multilang.domain.translation_quality import (
        TranslationFidelityRequest,
        TranslationFidelityVerdict,
    )
    from multilang.services.provider_response_cache import ProviderResponseCacheService
    from multilang.services.text_generation import TextGenerationService
    rows, calls = {}, []
    def review(request):
        calls.append(request)
        return TranslationFidelityVerdict(decision="equivalent")
    def put(record):
        rows[record.key] = record
        return record
    service = TextGenerationService(
        sentence_adapter=SimpleNamespace(review_translation=review), translation_adapter=None,
        provider_cache=ProviderResponseCacheService(SimpleNamespace(get_provider_response=rows.get, upsert_provider_response=put)),
    )
    request = TranslationFidelityRequest(sentence="My house has a blue door.", translation="Minha casa tem uma porta azul.", source_language="en", target_language="pt")
    assert service.review_translation(request).decision == "equivalent"
    assert service.review_translation(request).decision == "equivalent"
    service.review_translation(request.model_copy(update={"translation": "Meu cachorro gosta de brincar no parque."}))
    service.review_translation(request.model_copy(update={"source_language": "fr"}))
    assert len(calls) == 3


def test_real_provider_adapter_requests_exact_pair_and_rejects_extra_authority():
    import json

    from multilang.domain.translation_quality import TranslationFidelityRequest
    from multilang.services.provider_text_adapters import LiteLLMSentenceAdapter
    from multilang.settings import Settings
    calls = []
    payload = {"decision": "mismatch"}
    def complete(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": json.dumps(payload)}}]}
    adapter = LiteLLMSentenceAdapter(Settings(_env_file=None), completion_func=complete)
    request = TranslationFidelityRequest(sentence="My house has a blue door.", translation="Meu cachorro gosta de brincar no parque.", source_language="en", target_language="pt")
    assert adapter.review_translation(request).decision == "mismatch"
    assert json.loads(calls[0]["messages"][1]["content"]) == request.model_dump()
    assert calls[0]["max_tokens"] == 128
    assert calls[0]["timeout"] == 45
    assert calls[0]["num_retries"] == 0
    payload["human_approved"] = True
    with pytest.raises(ValueError):
        adapter.review_translation(request)


def test_fidelity_uses_generation_limiter_and_logs_bound_provider_usage():
    import json

    from multilang.domain.translation_quality import TranslationFidelityRequest
    from multilang.services.provider_response_cache import ProviderResponseCacheService
    from multilang.services.provider_text_adapters import LiteLLMSentenceAdapter
    from multilang.services.text_generation import TextGenerationService
    from multilang.settings import Settings

    events, logs, rows = [], [], {}
    def complete(**kwargs):
        events.append("provider")
        return {
            "choices": [{"message": {"content": json.dumps({"decision": "equivalent"})}}],
            "usage": {"prompt_tokens": 37, "completion_tokens": 5, "total_tokens": 42},
        }
    def put(record):
        rows[record.key] = record
        return record
    service = TextGenerationService(
        sentence_adapter=LiteLLMSentenceAdapter(Settings(_env_file=None), completion_func=complete),
        translation_adapter=None,
        provider_call_logger=SimpleNamespace(insert=logs.append),
        provider_cache=ProviderResponseCacheService(SimpleNamespace(
            get_provider_response=rows.get, upsert_provider_response=put,
        )),
    )
    limiter = SimpleNamespace(wait=lambda: events.append("limit"))
    request = TranslationFidelityRequest(
        sentence="My house has a blue door.", translation="Minha casa tem uma porta azul.",
        source_language="en", target_language="pt",
    )
    for _ in range(2):
        verdict = service.review_translation(request, job_id="job-a", item_key="house", rate_limiter=limiter)
        assert verdict.model_dump() == {"decision": "equivalent"}
    assert events == ["limit", "provider"]
    assert len(logs) == 1
    assert (logs[0].job_id, logs[0].item_key, logs[0].operation) == ("job-a", "house", "translation_fidelity")
    assert (logs[0].input_tokens, logs[0].output_tokens, logs[0].total_tokens) == (37, 5, 42)
    assert next(iter(rows.values())).response == {"decision": "equivalent"}


@pytest.mark.parametrize("decision", ["equivalent", "mismatch", "uncertain"])
def test_validation_passes_fidelity_call_context_without_changing_admission(decision):
    from multilang.domain.translation_quality import TranslationFidelityVerdict
    calls = []
    limiter = SimpleNamespace(wait=lambda: None)
    def checker(request, **kwargs):
        calls.append(kwargs)
        return TranslationFidelityVerdict(decision=decision)
    result = validator(translation_fidelity_checker=checker).validate(
        **pair(), job_id="job-a", item_key="house", rate_limiter=limiter,
    )
    assert calls == [{"job_id": "job-a", "item_key": "house", "rate_limiter": limiter}]
    assert result.validation_status is (ValidationStatus.PASSED if decision == "equivalent" else ValidationStatus.FAILED)


def test_fidelity_context_failure_never_retries_without_context():
    calls = []
    def checker(request, **kwargs):
        calls.append(kwargs)
        raise TypeError("context-bound checker unavailable")
    result = validator(translation_fidelity_checker=checker).validate(**pair(), job_id="job-a")
    assert result.validation_status is ValidationStatus.FAILED
    assert calls == [{"job_id": "job-a"}]
