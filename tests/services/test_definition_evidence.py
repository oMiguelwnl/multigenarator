"""Offline adversarial definition cases; fixtures are synthetic, never human approval."""

import json
from hashlib import sha256

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.services.content.definition_evidence import DefinitionReviewVerdict, evidence_digest
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.lexical_lookup import LexicalLookup, LexicalRecord
from multilang.services.text_generation import DefinitionGenerationResult
from multilang.services.word_list_parser import ParsedWordListItem


class Lookup:
    def __init__(self, record):
        self.record = record

    def lookup(self, **kwargs):
        return self.record

    def has_index(self, **kwargs):
        return False


class Generator:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def generate_definition(self, request):
        self.calls.append(request)
        if isinstance(self.output, Exception):
            raise self.output
        return DefinitionGenerationResult(
            definitions_html=self.output, provenance={"source": "synthetic-test"}
        )


class AdvisoryDefinitionReviewer:
    """Exercise generated drafts without granting a model semantic authority."""

    def review(self, request, draft):
        return DefinitionReviewVerdict(
            decision="advisory", evidence_sha256=evidence_digest(request),
            draft_sha256=sha256(draft.encode()).hexdigest(), reference="synthetic-review-only",
        )


def source(**updates):
    return LexicalRecord.model_validate(
        dict(
            term="house",
            display_form="house",
            lemma="house",
            definitions=["a dwelling"],
            part_of_speech="noun",
            definition_language="en",
            source="synthetic-lexicon",
            **updates,
        )
    )


def seed():
    return LexicalCardCandidate(
        submitted_form="house",
        display_form="house",
        lemma="house",
        lemma_key="house",
        translation_target_language="pt",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )


@pytest.mark.parametrize(
    ("updates", "decision", "reason"),
    [
        ({}, "source_verified", None),
        ({"definitions": []}, "review_required", "missing_source_meaning"),
        ({"definitions": ["a dwelling", "a dynasty"]}, "review_required", "ambiguous_source_meanings"),
        ({"definition_language": "pt"}, "review_required", "target_language_evidence_unavailable"),
        ({"definition_language": None}, "review_required", "source_language_unknown"),
    ],
)
def test_source_evidence_path_never_generates_unreviewable_definition(updates, decision, reason):
    generator = Generator("noun: a different meaning")
    record = source().model_copy(update=updates)
    result = LexicalGroundingService(
        lookup=Lookup(record), definition_generator=generator
    ).ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(
            line_number=1, submitted_form="house", display_form="house", item_key="house"
        ),
    )
    evidence = result.provenance.definition
    assert generator.calls == []
    assert evidence.quality_decision == decision
    assert evidence.fallback_reason == reason
    assert not evidence.fallback_used
    assert evidence.generated_draft is None
    assert evidence.source == "synthetic-lexicon"
    assert evidence.actual_language == record.definition_language


@pytest.mark.parametrize(
    "output",
    ["noun: a dog", "noun: a dwelling that is a dog", "noun: uma casa", "noun: not a dwelling"],
)
def test_wrong_meaning_and_language_recover_to_source(output):
    service = LexicalGroundingService(
        lookup=Lookup(source()), definition_generator=Generator(output),
        definition_reviewer=AdvisoryDefinitionReviewer(),
    )
    result = service.ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(
            line_number=1, submitted_form="house", display_form="house", item_key="house"
        ),
    )
    assert result.definitions_html == "noun: a dwelling"
    assert result.provenance.definition.fallback_used
    assert result.provenance.definition.source == "synthetic-lexicon"
    assert result.provenance.definition.quality_decision == "source_fallback"


def test_fallback_records_actual_language_and_requires_review():
    portuguese_source = source().model_copy(update={
        "definitions": ["uma moradia"], "definition_language": "pt",
    })
    result = LexicalGroundingService(
        lookup=Lookup(portuguese_source), definition_generator=Generator("noun: a dog"),
        definition_reviewer=AdvisoryDefinitionReviewer(),
    ).ground_frequency_candidate(language=SupportedLanguage.EN, candidate=seed())
    assert result.definition_language == "pt"
    assert result.grounding_status != GroundingStatus.GROUNDED
    assert result.provenance.definition.fallback_used
    assert result.provenance.definition.quality_decision == "review_required"
    assert result.provenance.definition.fallback_reason == "target_language_evidence_unavailable"


def test_seed_without_index_cannot_acquire_authority_from_generator():
    generator = Generator("noun: a dwelling")
    result = LexicalGroundingService(
        lookup=Lookup(None), definition_generator=generator, allow_frequency_seed_fallback=True
    ).ground_frequency_candidate(language=SupportedLanguage.EN, candidate=seed())
    assert result.grounding_status == GroundingStatus.BACKFILL_REQUIRED
    assert generator.calls == []


def test_ambiguous_lookup_does_not_choose_first_sense(tmp_path):
    directory = tmp_path / "en"
    directory.mkdir()
    records = [source(sense_id="building").model_dump(), source(sense_id="dynasty").model_dump()]
    (directory / "lexical-index.json").write_text(json.dumps({"house": records}))
    assert LexicalLookup(tmp_path).lookup(language_code="en", term="house") is None


def test_provider_failure_recovers_and_records_reason():
    result = LexicalGroundingService(
        lookup=Lookup(source()), definition_generator=Generator(TimeoutError("timeout")),
        definition_reviewer=AdvisoryDefinitionReviewer(),
    ).ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(
            line_number=1, submitted_form="house", display_form="house", item_key="house"
        ),
    )
    assert result.definitions_html == "noun: a dwelling"
    assert result.provenance.definition.fallback_reason == "provider_failure"


def test_definition_provider_request_is_bounded_and_contains_source():
    from multilang.services.provider_text_adapters import LiteLLMSentenceAdapter
    from multilang.services.text_generation import DefinitionGenerationRequest
    from multilang.settings import Settings

    calls = []

    def completion(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": '{"definitions_html": "noun: a dwelling"}'}}]}

    request = DefinitionGenerationRequest(
        display_form="house",
        lemma="house",
        source_language="en",
        target_language="en",
        part_of_speech="noun",
        source_definitions=("a dwelling",),
        source_definition_language="en",
        evidence_source="synthetic-lexicon",
        source_sense_id="building",
    )
    LiteLLMSentenceAdapter(
        Settings(_env_file=None), completion_func=completion
    ).generate_definition(request)
    assert calls[0]["timeout"] <= 60
    assert calls[0]["max_tokens"] <= 1024
    assert calls[0]["num_retries"] == 0
    assert "a dwelling" in calls[0]["messages"][1]["content"]
    assert "building" in calls[0]["messages"][1]["content"]


def test_definition_transport_retries_cache_invalidation_and_quota():
    from multilang.services.content.definition_generation import DefinitionGenerationService
    from multilang.services.provider_response_cache import ProviderResponseCacheService
    from multilang.services.provider_retry import ProviderCircuitBreaker
    from multilang.services.text_generation import DefinitionGenerationRequest

    class Memory:
        def __init__(self):
            self.values = {}
            self.logs = []

        def get_provider_response(self, key):
            return self.values.get(key)

        def upsert_provider_response(self, record):
            self.values[record.key] = record
            return record

        def insert(self, log):
            self.logs.append(log)

    class Retrying(Generator):
        provider = "test"
        model = "test"

        def generate_definition(self, request):
            if not self.calls:
                self.calls.append(request)
                raise TimeoutError("timeout")
            return super().generate_definition(request)

    adapter = Retrying("noun: a dwelling")
    memory = Memory()
    service = DefinitionGenerationService(
        adapter=adapter,
        provider_cache=ProviderResponseCacheService(memory),
        provider_call_logger=memory,
        circuit_breaker=ProviderCircuitBreaker(),
        retry_base_delay_seconds=0,
    )
    request = DefinitionGenerationRequest(
        display_form="house",
        lemma="house",
        source_language="en",
        target_language="en",
        source_definitions=("a dwelling",),
        source_definition_language="en",
        evidence_source="synthetic-lexicon",
    )
    assert service.generate_definition(request).definitions_html == "noun: a dwelling"
    service.generate_definition(request)
    assert len(adapter.calls) == 2
    service.generate_definition(request.model_copy(update={"source_definitions": ("a dynasty",)}))
    assert len(adapter.calls) == 3
    assert any(log.status == "success" for log in memory.logs)
    quota = Generator(RuntimeError("429 insufficient credits"))
    with pytest.raises(RuntimeError, match="credits"):
        DefinitionGenerationService(adapter=quota, retry_base_delay_seconds=0).generate_definition(
            request
        )
    assert len(quota.calls) == 1


def test_export_rejects_definition_review_even_if_legacy_identity_is_grounded():
    from multilang.domain.lexicon import DefinitionRecord
    from multilang.services.assemble_export_cards import (
        AssembleExportCardsError,
        AssembleExportCardsService,
    )

    candidate = seed().model_copy(
        update={
            "grounding_status": GroundingStatus.GROUNDED,
            "definitions_html": "noun: a dwelling",
            "provenance": LexicalProvenance(
                source="synthetic",
                definition=DefinitionRecord(
                    source="synthetic", value="noun: a dwelling", quality_decision="review_required"
                ),
            ),
        }
    )
    service = AssembleExportCardsService(
        text_repository=None, lexical_repository=None, audio_repository=None, export_repository=None
    )
    with pytest.raises(AssembleExportCardsError, match="review"):
        service._render_definitions(candidate, deck_language=SupportedLanguage.EN)


def test_unknown_source_language_is_not_guessed():
    record = source().model_copy(update={"definition_language": None})
    result = LexicalGroundingService(
        lookup=Lookup(record), definition_generator=Generator("noun: a dwelling")
    ).ground_frequency_candidate(language=SupportedLanguage.EN, candidate=seed())
    assert result.definition_language == "und"
    assert result.provenance.definition.fallback_reason == "source_language_unknown"


def test_independent_review_requires_exact_evidence_and_draft_binding():
    from hashlib import sha256

    from multilang.services.content.definition_evidence import (
        DefinitionReviewVerdict,
        decide_definition,
        evidence_digest,
    )
    from multilang.services.text_generation import DefinitionGenerationRequest

    request = DefinitionGenerationRequest(
        display_form="house",
        lemma="house",
        source_language="en",
        target_language="en",
        source_definitions=("a dwelling",),
        source_definition_language="en",
        evidence_source="synthetic-lexicon",
    )
    draft = DefinitionGenerationResult(definitions_html="noun: a home")

    class Reviewer:
        def __init__(self, decision, digest):
            self.decision, self.digest = decision, digest

        def review(self, request, text):
            return DefinitionReviewVerdict(
                decision=self.decision,
                evidence_sha256=self.digest,
                draft_sha256=sha256(text.encode()).hexdigest(),
                reference="synthetic-evaluation-only",
            )

    for verdict, digest in [("advisory", evidence_digest(request)), ("source_approved", "0" * 64)]:
        outcome = decide_definition(request, draft, reviewer=Reviewer(verdict, digest))
        assert outcome.record.quality_decision == "source_fallback"
        assert outcome.record.generated_draft == draft.definitions_html
    outcome = decide_definition(
        request, draft, reviewer=Reviewer("source_approved", evidence_digest(request))
    )
    assert outcome.definitions_html == draft.definitions_html
    assert outcome.record.quality_decision == "independently_reviewed"


def test_definition_cache_invalidates_prompt_and_schema_changes(monkeypatch):
    from multilang.services.content.definition_generation import DefinitionGenerationService
    from multilang.services.provider_response_cache import ProviderResponseCacheService
    from multilang.services.text_generation import DefinitionGenerationRequest

    class Memory:
        def __init__(self):
            self.values = {}

        def get_provider_response(self, key):
            return self.values.get(key)

        def upsert_provider_response(self, record):
            self.values[record.key] = record
            return record

    adapter = Generator("noun: a dwelling")
    cache = ProviderResponseCacheService(Memory())
    request = DefinitionGenerationRequest(
        display_form="house", lemma="house", source_language="en", target_language="en"
    )
    first = DefinitionGenerationService(adapter=adapter, provider_cache=cache, prompt_version="v1")
    second = DefinitionGenerationService(adapter=adapter, provider_cache=cache, prompt_version="v2")
    first.generate_definition(request)
    second.generate_definition(request)
    assert len(adapter.calls) == 2
    monkeypatch.setattr(
        DefinitionGenerationResult, "model_json_schema", lambda: {"title": "changed schema"}
    )
    second.generate_definition(request)
    assert len(adapter.calls) == 3


def test_definition_circuit_blocks_repeated_outage():
    from multilang.services.content.definition_generation import DefinitionGenerationService
    from multilang.services.provider_retry import ProviderCircuitBreaker, ProviderCircuitOpenError
    from multilang.services.text_generation import DefinitionGenerationRequest

    adapter = Generator(TimeoutError("timeout"))
    service = DefinitionGenerationService(
        adapter=adapter,
        circuit_breaker=ProviderCircuitBreaker(failure_threshold=1),
        retry_base_delay_seconds=0,
    )
    request = DefinitionGenerationRequest(
        display_form="house", lemma="house", source_language="en", target_language="en"
    )
    for _ in range(2):
        with pytest.raises(ProviderCircuitOpenError):
            service.generate_definition(request)
    assert len(adapter.calls) == 1


def test_definition_new_empty_metadata_preserves_historical_payload():
    from multilang.domain.lexicon import DefinitionRecord

    assert DefinitionRecord(source="old", value="meaning").model_dump(mode="json") == {
        "source": "old",
        "value": "meaning",
        "fallback_used": False,
    }


def test_definition_bounds_reject_oversized_evidence_and_output():
    from pydantic import ValidationError

    from multilang.services.text_generation import DefinitionGenerationRequest

    with pytest.raises(ValidationError):
        DefinitionGenerationResult(definitions_html="x" * 4097)
    with pytest.raises(ValidationError):
        DefinitionGenerationRequest(
            display_form="house",
            lemma="house",
            source_language="en",
            target_language="en",
            source_definitions=("x" * 2001,),
        )


def test_frequency_rank_source_cannot_be_semantic_evidence_even_with_text():
    from multilang.services.content.definition_evidence import decide_definition
    from multilang.services.text_generation import DefinitionGenerationRequest

    request = DefinitionGenerationRequest(
        display_form="house",
        lemma="house",
        source_language="en",
        target_language="en",
        part_of_speech="noun",
        source_definitions=("a dwelling",),
        source_definition_language="en",
        evidence_source="wordfreq",
    )
    outcome = decide_definition(
        request, DefinitionGenerationResult(definitions_html="noun: a dwelling")
    )
    assert outcome.review_required
    assert outcome.definitions_html is None


def test_missing_evidence_does_not_claim_successful_fallback():
    from multilang.services.content.definition_evidence import decide_definition
    from multilang.services.text_generation import DefinitionGenerationRequest

    request = DefinitionGenerationRequest(
        display_form="house", lemma="house", source_language="en", target_language="en"
    )
    outcome = decide_definition(
        request, DefinitionGenerationResult(definitions_html="noun: a dwelling")
    )
    assert outcome.review_required
    assert outcome.definitions_html is None
    assert not outcome.record.fallback_used


@pytest.mark.parametrize(
    "meaning", ["a person's home", 'a home called "shelter"', "a home & shelter"]
)
def test_source_text_is_escaped_once_at_export_boundary(meaning):
    from html import escape

    from multilang.services.assemble_export_cards import AssembleExportCardsService

    record = source().model_copy(update={"definitions": [meaning]})
    candidate = LexicalGroundingService(lookup=Lookup(record)).ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(
            line_number=1, submitted_form="house", display_form="house", item_key="house"
        ),
    )
    service = AssembleExportCardsService(
        text_repository=None, lexical_repository=None, audio_repository=None, export_repository=None
    )
    assert service._render_definitions(candidate, deck_language=SupportedLanguage.EN) == escape(
        f"noun: {meaning}"
    )


def test_invalid_cached_definition_is_replaced_after_provider_recovery():
    from multilang.services.content.definition_generation import DefinitionGenerationService
    from multilang.services.provider_response_cache import (
        ProviderCachedResponse,
        ProviderResponseCacheService,
    )
    from multilang.services.text_generation import DefinitionGenerationRequest

    class Memory:
        def __init__(self):
            self.record = None

        def get_provider_response(self, key):
            return self.record

        def upsert_provider_response(self, record):
            self.record = record
            return record

    memory = Memory()
    adapter = Generator("noun: a dwelling")
    service = DefinitionGenerationService(
        adapter=adapter, provider_cache=ProviderResponseCacheService(memory)
    )
    request = DefinitionGenerationRequest(
        display_form="house", lemma="house", source_language="en", target_language="en"
    )
    service.generate_definition(request)
    memory.record = ProviderCachedResponse(key=memory.record.key, response={"definitions_html": ""})
    result = service.generate_definition(request)
    assert result.definitions_html == "noun: a dwelling"
    assert len(adapter.calls) == 2
    service.generate_definition(request)
    assert len(adapter.calls) == 2


@pytest.mark.parametrize(
    "updates",
    [
        {"definitions": [f"meaning {i}" for i in range(9)]},
        {"definitions": ["x" * 2001]},
        {"sense_id": "x" * 129},
    ],
)
def test_oversized_source_evidence_requires_review_without_aborting_job(updates):
    generator = Generator("noun: a dwelling")
    candidate = LexicalGroundingService(
        lookup=Lookup(source().model_copy(update=updates)), definition_generator=generator
    ).ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(
            line_number=1, submitted_form="house", display_form="house", item_key="house"
        ),
    )
    assert candidate.grounding_status == GroundingStatus.PENDING
    assert candidate.provenance.definition.fallback_reason == "source_evidence_invalid"
    assert candidate.definitions_html is None
    assert generator.calls == []


def test_known_russian_correction_remains_explicit_editorial_evidence():
    from multilang.services.assemble_export_cards import AssembleExportCardsService

    record = source().model_copy(
        update={
            "term": "достичь",
            "display_form": "достичь",
            "lemma": "достичь",
            "definitions": ["to reach"],
            "part_of_speech": "verb",
        }
    )
    candidate = LexicalGroundingService(lookup=Lookup(record)).ground_frequency_candidate(
        language=SupportedLanguage.RU,
        candidate=seed().model_copy(
            update={
                "submitted_form": "достичь",
                "display_form": "достичь",
                "lemma": "достичь",
                "lemma_key": "достичь",
            }
        ),
    )
    exporter = AssembleExportCardsService(
        text_repository=None, lexical_repository=None, audio_repository=None, export_repository=None
    )
    assert (
        exporter._render_definitions(candidate, deck_language=SupportedLanguage.RU)
        == "verb: to achieve, to attain, to reach"
    )
    assert candidate.provenance.definition.source == "builtin-definition-corrections-v1"
    assert candidate.provenance.definition.actual_language == "en"


@pytest.mark.parametrize("provenance", [{"source": "synthetic", "definition": {"source": "synthetic", "quality_decision": "review_required"}}, {"definition": "malformed"}])
def test_persisted_json_definition_review_metadata_fails_closed(provenance):
    from types import SimpleNamespace

    from multilang.services.assemble_export_cards import (
        AssembleExportCardsError,
        AssembleExportCardsService,
    )
    candidate = SimpleNamespace(**seed().model_dump())
    candidate.provenance = provenance
    candidate.definitions_html = "noun: a dwelling"
    service = AssembleExportCardsService(text_repository=None, lexical_repository=None, audio_repository=None, export_repository=None)
    with pytest.raises(AssembleExportCardsError, match="review|provenance"):
        service._render_definitions(candidate, deck_language=SupportedLanguage.EN)
