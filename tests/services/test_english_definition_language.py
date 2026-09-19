"""English meanings must not inherit the Portuguese sentence-translation policy."""

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest
from test_native_content_audio import content_request
from test_native_definition_contract import evidence

from multilang.domain.definitions import DefinitionConsistencyVerdict
from multilang.domain.highlights import HighlightCandidate
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.services.content.definition_evidence import DefinitionReviewVerdict, evidence_digest
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.lexical_lookup import LexicalRecord
from multilang.services.native_content import (
    ExistingTextContentAdapter,
    NativeProviderContentAdapter,
)
from multilang.services.text_generation import (
    DefinitionGenerationResult,
    SentenceGenerationResult,
    SentenceTranslationResult,
)
from multilang.services.word_list_parser import ParsedWordListItem
from multilang.settings import Settings


def record(language="en"):
    return LexicalRecord(
        term="house",
        display_form="house",
        lemma="house",
        part_of_speech="noun",
        definitions=[
            "a building where people live"
            if language == "en"
            else "uma construção onde as pessoas moram"
        ],
        definition_language=language,
        ipa="/haʊs/",
        source="synthetic-lexicon",
    )


def seed():
    return LexicalCardCandidate(
        submitted_form="house",
        display_form="house",
        lemma="house",
        lemma_key="house",
        frequency_rank=42,
        frequency_level=1,
        translation_target_language="pt",
        grounding_status="pending",
        provenance=LexicalProvenance(source="wordfreq"),
    )


@pytest.mark.parametrize("mode", ["frequency", "word-list", "kindle-highlights"])
def test_english_modes_request_english_meaning(mode):
    requests = []

    def generate(request):
        requests.append(request)
        return DefinitionGenerationResult(definitions_html="noun: a building where people live")

    def review(request, draft):
        return DefinitionReviewVerdict(
            decision="advisory",
            evidence_sha256=evidence_digest(request),
            draft_sha256=sha256(draft.encode()).hexdigest(),
            reference="test-only",
        )

    service = LexicalGroundingService(
        lookup=SimpleNamespace(lookup=lambda **_: record()),
        definition_generator=SimpleNamespace(generate_definition=generate),
        definition_reviewer=SimpleNamespace(review=review),
    )
    if mode == "frequency":
        candidate = service.ground_frequency_candidate(
            language=SupportedLanguage.EN, candidate=seed()
        )
    elif mode == "word-list":
        candidate = service.ground_word_list_item(
            language=SupportedLanguage.EN,
            item=ParsedWordListItem(
                line_number=1, submitted_form="house", display_form="house", item_key="house"
            ),
        )
    else:
        candidate = service.ground_highlight_candidate(
            language=SupportedLanguage.EN,
            candidate=HighlightCandidate(
                item_key="highlight-en-house",
                source_content_hash="a" * 64,
                display_form="house",
                lemma_key="house",
                first_highlight_id="highlight-1",
                first_source_index=0,
                occurrence_count=1,
            ),
        )
    assert requests[0].target_language == "en"
    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert candidate.definition_language == "en"
    assert candidate.definitions_html == "noun: a building where people live"
    assert candidate.translation_target_language == ("en" if mode == "word-list" else "pt")


def test_source_only_english_definition_is_accepted_for_normal_cards():
    service = LexicalGroundingService(lookup=SimpleNamespace(lookup=lambda **_: record()))
    candidate = service.ground_frequency_candidate(language=SupportedLanguage.EN, candidate=seed())
    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert candidate.provenance.definition.quality_decision == "source_verified"
    assert candidate.definition_language == "en"
    assert candidate.translation_target_language == "pt"


def test_portuguese_source_cannot_be_silently_accepted_as_english_definition():
    service = LexicalGroundingService(lookup=SimpleNamespace(lookup=lambda **_: record("pt")))
    candidate = service.ground_frequency_candidate(language=SupportedLanguage.EN, candidate=seed())
    assert candidate.grounding_status is GroundingStatus.PENDING
    assert candidate.definition_language == "pt"
    assert candidate.provenance.definition.quality_decision == "review_required"
    assert candidate.provenance.definition.fallback_reason == "target_language_evidence_unavailable"


def test_native_existing_adapter_separates_definition_and_translation_languages():
    definitions, translations = [], []

    def define(request):
        definitions.append(request)
        return DefinitionGenerationResult(definitions_html="verb: to move quickly on foot")

    def translate(request):
        translations.append(request)
        return SentenceTranslationResult(translation="Eu corri para casa antes da chuva.")

    adapter = ExistingTextContentAdapter(
        definition_adapter=SimpleNamespace(generate_definition=define),
        sentence_adapter=SimpleNamespace(
            generate_sentence=lambda _: SentenceGenerationResult(
                sentence="I ran home before the rain."
            )
        ),
        translation_adapter=SimpleNamespace(translate_sentence=translate),
    )
    adapter(content_request(explanation_language="pt", definition_evidence=evidence()))
    assert definitions[0].target_language == "en"
    assert translations[0].translation_target_language == "pt"


def test_native_prompt_and_review_use_english_definition_with_portuguese_translation():
    calls, reviews = [], []
    payload = {
        "definition": "verb: to move quickly on foot",
        "example_sentence": "I ran home before the rain.",
        "translation": "Eu corri para casa antes da chuva.",
    }

    def complete(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": json.dumps(payload)}}]}

    def check(request):
        reviews.append(request)
        return DefinitionConsistencyVerdict(decision="consistent")

    adapter = NativeProviderContentAdapter(
        settings=Settings(_env_file=None), completion=complete, definition_checker=check
    )
    result = adapter(content_request(explanation_language="pt", definition_evidence=evidence()))
    assert reviews[0].definition_language == "en"
    assert (
        "Write the definition in English when the target language is English"
        in calls[0]["messages"][0]["content"]
    )
    assert json.loads(calls[0]["messages"][1]["content"])["explanation_language"] == "pt"
    assert result.translation == payload["translation"]
