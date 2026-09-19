"""An exact-pair semantic check is advisory, never a source/human approval."""

import json
from types import SimpleNamespace

import pytest

from multilang.domain.definitions import DefinitionConsistencyRequest, DefinitionConsistencyVerdict
from multilang.domain.text_quality import TextProvenance, ValidationStatus
from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation


def request(**changes):
    return DefinitionConsistencyRequest(
        **(
            dict(
                lemma="bank",
                display_form="bank",
                source_language="en",
                definition_language="en",
                definition="noun: the land beside a river",
                sentence="She deposited money at the bank.",
            )
            | changes
        )
    )


@pytest.mark.parametrize("decision", ["consistent", "mismatch", "uncertain"])
def test_definition_check_runs_for_same_language_and_binds_call_context(decision):
    from multilang.services.text_validation import TextValidationService

    calls = []

    def check(value, **kwargs):
        calls.append((value, kwargs))
        return DefinitionConsistencyVerdict(decision=decision)

    validator = TextValidationService(
        language_identifier=SimpleNamespace(
            detect=lambda *_, **__: SimpleNamespace(reliable=False, detected_language=None)
        ),
        morphological_analyzer=SimpleNamespace(
            contains_target_lemma=lambda **_: SimpleNamespace(reliable=True, matched=True)
        ),
        require_translation_fidelity=False,
        definition_consistency_checker=check,
        require_definition_consistency=True,
    )
    provenance = TextProvenance(source="fixture")
    limiter = SimpleNamespace(wait=lambda: None)
    result = validator.validate(
        sentence=GeneratedSentence(
            text=request().sentence, target_language="en", provenance=provenance
        ),
        translation=GeneratedTranslation(
            text=request().sentence, target_language="en", provenance=provenance
        ),
        lemma="bank",
        display_form="bank",
        definitions_html=request().definition,
        definition_language="en",
        require_translation=False,
        job_id="j",
        item_key="bank",
        rate_limiter=limiter,
    )
    assert calls == [(request(), {"job_id": "j", "item_key": "bank", "rate_limiter": limiter})]
    assert result.validation_status is (
        ValidationStatus.PASSED if decision == "consistent" else ValidationStatus.FAILED
    )
    if decision != "consistent":
        assert any(flag.code.value == "definition_mismatch" for flag in result.validation_flags)


def test_checker_uses_exact_pair_cache_limiter_and_token_telemetry():
    from multilang.services.provider_response_cache import ProviderResponseCacheService
    from multilang.services.provider_text_adapters import LiteLLMSentenceAdapter
    from multilang.services.text_generation import TextGenerationService
    from multilang.settings import Settings

    calls, logs, rows, limits = [], [], {}, []
    payload = {"decision": "consistent"}

    def complete(**kwargs):
        calls.append(kwargs)
        return {
            "choices": [{"message": {"content": json.dumps(payload)}}],
            "usage": {"prompt_tokens": 40, "completion_tokens": 5, "total_tokens": 45},
        }

    def put(row):
        rows[row.key] = row
        return row

    service = TextGenerationService(
        sentence_adapter=LiteLLMSentenceAdapter(Settings(_env_file=None), completion_func=complete),
        translation_adapter=None,
        provider_call_logger=SimpleNamespace(insert=logs.append),
        provider_cache=ProviderResponseCacheService(
            SimpleNamespace(get_provider_response=rows.get, upsert_provider_response=put)
        ),
    )
    limiter = SimpleNamespace(wait=lambda: limits.append(1))
    for _ in range(2):
        assert (
            service.review_definition(
                request(), job_id="j", item_key="bank", rate_limiter=limiter
            ).decision
            == "consistent"
        )
    assert len(calls) == len(limits) == 1
    assert logs[0].job_id == "j" and logs[0].operation == "definition_consistency"
    assert logs[0].total_tokens == 45
    service.review_definition(request(definition="noun: a financial institution"))
    assert len(calls) == 2
    payload["decision"] = "uncertain"
    for _ in range(2):
        service.review_definition(request(sentence="The bank is nearby."))
    assert len(calls) == 4
    assert json.loads(calls[0]["messages"][1]["content"]) == request().model_dump()
    assert calls[0]["timeout"] == 45 and calls[0]["num_retries"] == 0


def test_consistency_provider_cannot_mint_approval_or_other_fields():
    from multilang.services.provider_text_adapters import LiteLLMSentenceAdapter
    from multilang.settings import Settings

    adapter = LiteLLMSentenceAdapter(
        Settings(_env_file=None),
        completion_func=lambda **_: {
            "choices": [{"message": {"content": '{"decision":"consistent","approved":true}'}}]
        },
    )
    with pytest.raises(ValueError):
        adapter.review_definition(request())


def test_consistency_missing_reviewer_is_uncertain():
    from multilang.services.text_generation import TextGenerationService

    service = TextGenerationService(sentence_adapter=object(), translation_adapter=None)
    assert service.review_definition(request()).decision == "uncertain"


def test_default_runtime_requires_definition_consistency():
    from multilang.runtime import build_runtime_service
    from multilang.settings import Settings

    runtime = build_runtime_service(settings=Settings(_env_file=None, database_url="sqlite+pysqlite:///:memory:"))
    validation = runtime.generate_text_items_service.text_validation_service
    assert validation.require_definition_consistency is True
    assert callable(validation.definition_consistency_checker)
    assert validation.definition_consistency_checker(request()).decision == "uncertain"
