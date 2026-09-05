"""Tests for trust-first lexical grounding."""

from __future__ import annotations

import unicodedata

from multilang.domain.korean import (
    KoreanAnalysisAlternative,
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanMorphemeEvidence,
    KoreanMorphologyResult,
    KoreanMorphologyStatus,
    KoreanReasonCode,
    KoreanSignatureItem,
    KoreanWordAnalysis,
    canonicalize_korean,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.highlights import HighlightCandidate
from multilang.domain.lexicon import (
    GroundingStatus,
    KoreanFrequencyLexicalEvidence,
    LexicalCardCandidate,
    LexicalProvenance,
)
from multilang.services.lexical_lookup import LexicalRecord
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.text_generation import DefinitionGenerationResult
from multilang.services.word_list_parser import ParsedWordListItem


class StubLookup:
    def __init__(self, mapping: dict[str, LexicalRecord | None]) -> None:
        self._mapping = mapping

    def lookup(self, *, language_code: str, term: str) -> LexicalRecord | None:
        return self._mapping.get(term.casefold())


class MissingIndexLookup(StubLookup):
    def has_index(self, *, language_code: str) -> bool:
        return False


class StubPronunciationGenerator:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def generate_pronunciation(self, request: object) -> object:
        self.calls.append(request)
        return type(
            "Pronunciation",
            (),
            {
                "ipa": "/right/",
                "spoken_form": "RYT",
                "provenance": {"source": "provider-pronunciation-generator"},
            },
        )()


class FailingPronunciationGenerator:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def generate_pronunciation(self, request: object) -> object:
        self.calls.append(request)
        raise ValueError("all pronunciation adapters failed")


class StubDefinitionGenerator:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def generate_definition(self, request: object) -> DefinitionGenerationResult:
        self.calls.append(request)
        label = request.part_of_speech or "term"
        return DefinitionGenerationResult(
            definitions_html=f"{label}: LLM definition for {request.lemma}",
            provenance={"source": "stub-llm-definition-generator"},
        )


class FixedDefinitionGenerator:
    def __init__(self, definitions_html: str) -> None:
        self.definitions_html = definitions_html
        self.calls: list[object] = []

    def generate_definition(self, request: object) -> DefinitionGenerationResult:
        self.calls.append(request)
        return DefinitionGenerationResult(
            definitions_html=self.definitions_html,
            provenance={"source": "fixed-definition-generator"},
        )


class RecordingRateLimiter:
    def __init__(self) -> None:
        self.wait_count = 0

    def wait(self) -> None:
        self.wait_count += 1


def test_grounding_prefers_study_form_and_manual_language_policy() -> None:
    generator = StubDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "lavar": LexicalRecord(
                    term="lavar",
                    display_form="lavarse",
                    lemma="lavar",
                    definitions=["to wash something or clean it with water", "to wash oneself"],
                    part_of_speech="verb",
                    grammar_tags=["infinitive"],
                    ipa="/laˈβaɾ/",
                )
            }
        ),
        definition_generator=generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.ES,
        item=ParsedWordListItem(
            line_number=1,
            submitted_form="lavar",
            display_form="lavar",
            item_key="lavar",
        ),
    )

    assert candidate.display_form == "lavarse"
    assert candidate.lemma == "lavar"
    assert candidate.lemma_key == "lavar"
    assert candidate.definitions_html == "verb: LLM definition for lavar"
    assert candidate.definition_language == "es"
    assert candidate.translation_target_language == "es"
    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert generator.calls
    assert generator.calls[0].target_language == "es"
    assert candidate.provenance.definition is not None
    assert candidate.provenance.definition.source == "stub-llm-definition-generator"


def test_grounding_rate_limits_definition_and_pronunciation_provider_calls() -> None:
    definition_generator = StubDefinitionGenerator()
    pronunciation_generator = StubPronunciationGenerator()
    limiter = RecordingRateLimiter()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "wash": LexicalRecord(
                    term="wash",
                    display_form="wash",
                    lemma="wash",
                    definitions=[],
                    part_of_speech="verb",
                    ipa=None,
                )
            }
        ),
        definition_generator=definition_generator,
        pronunciation_generator=pronunciation_generator,
    )

    service.ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(line_number=1, submitted_form="wash", display_form="wash", item_key="wash"),
        rate_limiter=limiter,
    )

    assert limiter.wait_count == 2
    assert len(definition_generator.calls) == 1
    assert len(pronunciation_generator.calls) == 1


def test_grounding_uses_canonical_display_when_lookup_resolves_source_form() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "remercia": LexicalRecord(
                    term="remercia",
                    display_form="remercier",
                    lemma="remercier",
                    definitions=["to thank someone"],
                    part_of_speech="verb",
                    ipa="/ʁə.mɛʁ.sje/",
                )
            }
        )
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.FR,
        item=ParsedWordListItem(
            line_number=3,
            submitted_form="Remercia",
            display_form="Remercia",
            item_key="remercia",
        ),
    )

    assert candidate.submitted_form == "Remercia"
    assert candidate.display_form == "remercier"
    assert candidate.lemma == "remercier"
    assert candidate.definitions_html == "verb: to thank someone"


def test_frequency_grounding_keeps_default_english_definition_policy() -> None:
    generator = StubDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["a building where people live"],
                    part_of_speech="noun",
                    ipa="/casa/",
                )
            }
        ),
        definition_generator=generator,
    )
    seed = LexicalCardCandidate(
        submitted_form="casa",
        display_form="casa",
        lemma="casa",
        lemma_key="casa",
        frequency_rank=1,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(language=SupportedLanguage.ES, candidate=seed)

    assert candidate.definitions_html == "noun: LLM definition for casa"
    assert candidate.definition_language == "en"
    assert generator.calls[0].target_language == "en"


def test_highlight_grounding_localizes_definition_to_deck_language() -> None:
    generator = StubDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "lavar": LexicalRecord(
                    term="lavar",
                    display_form="lavar",
                    lemma="lavar",
                    definitions=["to wash"],
                    part_of_speech="verb",
                    ipa="/laˈβaɾ/",
                )
            }
        ),
        definition_generator=generator,
    )

    candidate = service.ground_highlight_candidate(
        language=SupportedLanguage.ES,
        candidate=HighlightCandidate(
            item_key="highlight:abc:lavar",
            display_form="lavar",
            lemma_key="lavar",
            source_content_hash="a" * 64,
            first_highlight_id="h1",
            first_source_index=1,
            occurrence_count=1,
        ),
    )

    assert candidate.definitions_html == "verb: LLM definition for lavar"
    assert candidate.definition_language == "es"
    assert generator.calls[0].target_language == "es"


def test_grounding_uses_llm_definition_generator_instead_of_cache_definitions() -> None:
    generator = StubDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["a building where people live"],
                    part_of_speech="noun",
                ),
                "bonito": LexicalRecord(
                    term="bonito",
                    display_form="bonito",
                    lemma="bonito",
                    definitions=["beautiful; pleasant to look at or experience"],
                    part_of_speech="adj",
                ),
                "em": LexicalRecord(
                    term="em",
                    display_form="em",
                    lemma="em",
                    definitions=["used to show location, time, or position inside something"],
                    part_of_speech="prep",
                ),
            }
        ),
        definition_generator=generator,
    )

    expected = {
        "casa": "noun: LLM definition for casa",
        "bonito": "adjective: LLM definition for bonito",
        "em": "preposition: LLM definition for em",
    }
    for item_key, definition in expected.items():
        candidate = service.ground_word_list_item(
            language=SupportedLanguage.PT,
            item=ParsedWordListItem(
                line_number=1,
                submitted_form=item_key,
                display_form=item_key,
                item_key=item_key,
            ),
        )

        assert candidate.definitions_html == definition
        assert "building where people live" not in candidate.definitions_html


def test_grounding_omits_verb_tense_from_definition_template() -> None:
    generator = StubDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "lava": LexicalRecord(
                    term="lava",
                    display_form="lava",
                    lemma="lavar",
                    definitions=["washes; cleans something with water"],
                    part_of_speech="verb",
                    grammar_tags=["present", "third", "singular"],
                )
            }
        ),
        definition_generator=generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.PT,
        item=ParsedWordListItem(
            line_number=1,
            submitted_form="lava",
            display_form="lava",
            item_key="lava",
        ),
    )

    assert candidate.definitions_html == "verb: LLM definition for lavar"
    assert "present" not in candidate.definitions_html
    assert "third" not in candidate.definitions_html
    assert "singular" not in candidate.definitions_html


def test_definition_formatter_covers_supported_basic_part_of_speech_labels() -> None:
    cases = [
        ("adv", "in a fast way", "adverb: in a fast way"),
        ("article", "used before a specific thing", "article: used before a specific thing"),
        ("conj", "used to connect ideas", "conjunction: used to connect ideas"),
        ("det", "used to point to a specific thing", "determiner: used to point to a specific thing"),
        ("interj", "used to greet someone", "interjection: used to greet someone"),
        ("num", "the number three", "numeral: the number three"),
        ("particle", "used to mark negation", "particle: used to mark negation"),
        ("pron", "used instead of a noun", "pronoun: used instead of a noun"),
        ("proper", "the name of a country", "proper noun: the name of a country"),
    ]

    for part_of_speech, meaning, expected in cases:
        assert (
            LexicalGroundingService._format_definitions([meaning], part_of_speech=part_of_speech)
            == expected
        )


def test_grounding_uses_word_fallback_when_authoritative_ipa_is_missing() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["house"],
                    ipa=None,
                )
            }
        )
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.ES,
        item=ParsedWordListItem(
            line_number=1,
            submitted_form="casa",
            display_form="casa",
            item_key="casa",
        ),
    )

    assert candidate.ipa == "casa"
    assert candidate.spoken_form == "casa"
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.value == "casa"
    assert candidate.provenance.pronunciation.source == "manual_missing"
    assert candidate.provenance.pronunciation.authoritative is False
    assert any("word fallback" in note for note in candidate.provenance.notes)


def test_custom_word_list_failures_stay_pending() -> None:
    service = LexicalGroundingService(lookup=StubLookup({}))

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.ES,
        item=ParsedWordListItem(
            line_number=4,
            submitted_form="  perro  ",
            display_form="perro",
            item_key="perro",
        ),
    )

    assert candidate.grounding_status is GroundingStatus.PENDING
    assert candidate.warning_code == "lexical_lookup_missing"
    assert "line 4" in (candidate.warning_detail or "")
    assert candidate.submitted_form == "  perro  "
    assert candidate.display_form == "perro"


def test_frequency_failures_are_flagged_for_backfill() -> None:
    service = LexicalGroundingService(lookup=StubLookup({}))

    seed = LexicalCardCandidate(
        submitted_form="perro",
        display_form="perro",
        lemma="perro",
        lemma_key="perro",
        frequency_rank=12,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(
        language=SupportedLanguage.ES,
        candidate=seed,
    )

    assert candidate.grounding_status is GroundingStatus.BACKFILL_REQUIRED
    assert candidate.warning_code == "backfill_required"
    assert candidate.frequency_rank == 12
    assert candidate.frequency_level == 1


def test_frequency_can_fallback_to_wordfreq_seed_when_lookup_index_is_missing() -> None:
    generator = StubDefinitionGenerator()
    pronunciation_generator = StubPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=MissingIndexLookup({}),
        pronunciation_generator=pronunciation_generator,
        definition_generator=generator,
        allow_frequency_seed_fallback=True,
    )
    seed = LexicalCardCandidate(
        submitted_form="perro",
        display_form="perro",
        lemma="perro",
        lemma_key="perro",
        frequency_rank=12,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(
        language=SupportedLanguage.ES,
        candidate=seed,
    )

    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert candidate.frequency_rank == 12
    assert candidate.frequency_level == 1
    assert candidate.definitions_html == "term: LLM definition for perro"
    assert candidate.ipa == "/right/"
    assert candidate.spoken_form == "RYT"
    assert candidate.provenance.source == "wordfreq"
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.source == "provider-pronunciation-generator"
    assert generator.calls[0].lemma == "perro"
    assert generator.calls[0].source_language == "es"
    assert generator.calls[0].target_language == "en"
    assert pronunciation_generator.calls


def test_frequency_uses_lexical_lookup_without_cache_definition_for_card_definition() -> None:
    generator = StubDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casas": LexicalRecord(
                    term="casas",
                    display_form="casas",
                    lemma="casas",
                    definitions=["nominative plural of casa"],
                    ipa="/casas/",
                )
            }
        ),
        definition_generator=generator,
    )
    seed = LexicalCardCandidate(
        submitted_form="casas",
        display_form="casas",
        lemma="casas",
        lemma_key="casas",
        frequency_rank=14,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(
        language=SupportedLanguage.ES,
        candidate=seed,
    )

    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert candidate.definitions_html == "term: LLM definition for casas"
    assert generator.calls[0].lemma == "casas"


def test_grounding_standardizes_german_article_definition_label() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "die": LexicalRecord(
                    term="die",
                    display_form="die",
                    lemma="die",
                    definitions=[],
                    part_of_speech="unknown",
                    ipa=None,
                    source="wordfreq",
                )
            }
        ),
        definition_generator=FixedDefinitionGenerator("noun: the definite article used for feminine nouns in German"),
    )
    seed = LexicalCardCandidate(
        submitted_form="die",
        display_form="die",
        lemma="die",
        lemma_key="die",
        frequency_rank=1,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(language=SupportedLanguage.DE, candidate=seed)

    assert candidate.definitions_html == "article: the definite article used for feminine nouns in German"


def test_grounding_preserves_provider_verb_label_when_asset_pos_is_unknown() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "blieb": LexicalRecord(
                    term="blieb",
                    display_form="blieb",
                    lemma="blieb",
                    definitions=[],
                    part_of_speech="unknown",
                    ipa=None,
                    source="wordfreq",
                )
            }
        ),
        definition_generator=FixedDefinitionGenerator("verb: remained"),
    )
    seed = LexicalCardCandidate(
        submitted_form="blieb",
        display_form="blieb",
        lemma="blieb",
        lemma_key="blieb",
        frequency_rank=1001,
        frequency_level=2,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(language=SupportedLanguage.DE, candidate=seed)

    assert candidate.display_form == "blieb"
    assert candidate.definitions_html == "verb: remained"


def test_grounding_passes_inferred_function_word_pos_to_definition_generator() -> None:
    generator = StubDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "et": LexicalRecord(
                    term="et",
                    display_form="et",
                    lemma="et",
                    definitions=[],
                    part_of_speech="unknown",
                    ipa=None,
                    source="wordfreq",
                )
            }
        ),
        definition_generator=generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.FR,
        item=ParsedWordListItem(line_number=1, submitted_form="et", display_form="et", item_key="et"),
    )

    assert candidate.definitions_html == "conjunction: LLM definition for et"
    assert generator.calls[0].part_of_speech == "conjunction"


def test_grounding_normalizes_german_pause_display_and_definition_label() -> None:
    generator = FixedDefinitionGenerator("noun: a temporary stop or break in activity")
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "pause": LexicalRecord(
                    term="pause",
                    display_form="pause",
                    lemma="pause",
                    definitions=[],
                    part_of_speech="unknown",
                    ipa=None,
                    source="wordfreq",
                )
            }
        ),
        definition_generator=generator,
    )
    seed = LexicalCardCandidate(
        submitted_form="pause",
        display_form="pause",
        lemma="pause",
        lemma_key="pause",
        frequency_rank=2001,
        frequency_level=3,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(language=SupportedLanguage.DE, candidate=seed)

    assert candidate.display_form == "Pause"
    assert candidate.lemma == "Pause"
    assert candidate.lemma_key == "pause"
    assert candidate.definitions_html == "noun: a temporary stop or break in activity"
    assert generator.calls[0].display_form == "Pause"
    assert generator.calls[0].lemma == "Pause"
    assert generator.calls[0].part_of_speech == "noun"


def test_grounding_remediates_morphology_only_definition_from_source_meaning() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "большую": LexicalRecord(
                    term="большую",
                    display_form="большую",
                    lemma="большой",
                    definitions=["feminine accusative singular of большой", "big; large; important"],
                    part_of_speech="adjective",
                    ipa="[bɐlʲˈʂuju]",
                )
            }
        ),
        definition_generator=FixedDefinitionGenerator("adjective: feminine accusative singular"),
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.RU,
        item=ParsedWordListItem(line_number=1, submitted_form="большую", display_form="большую", item_key="большую"),
    )

    assert candidate.definitions_html == "adjective: big; large; important"


def test_russian_frequency_rejects_uppercase_duplicate_records() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "и": LexicalRecord(
                    term="И",
                    display_form="И",
                    lemma="И",
                    definitions=["The name of the Cyrillic script letter И."],
                    ipa="[i]",
                )
            }
        )
    )
    seed = LexicalCardCandidate(
        submitted_form="и",
        display_form="и",
        lemma="и",
        lemma_key="и",
        frequency_rank=2,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(
        language=SupportedLanguage.RU,
        candidate=seed,
    )

    assert candidate.grounding_status is GroundingStatus.BACKFILL_REQUIRED


def test_grounding_preserves_authoritative_ipa_for_custom_word_list() -> None:
    generator = StubPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["house"],
                    ipa="/authoritative/",
                )
            }
        ),
        pronunciation_generator=generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.PT,
        item=ParsedWordListItem(line_number=1, submitted_form="casa", display_form="casa", item_key="casa"),
    )

    assert candidate.ipa == "/authoritative/"
    assert candidate.spoken_form == "casa"
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.source == "manual"
    assert generator.calls == []


def test_grounding_uses_ai_pronunciation_when_authoritative_ipa_is_missing() -> None:
    generator = StubPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["house"],
                    ipa=None,
                )
            }
        ),
        pronunciation_generator=generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.PT,
        item=ParsedWordListItem(line_number=1, submitted_form="casa", display_form="casa", item_key="casa"),
    )

    assert candidate.ipa == "/right/"
    assert candidate.spoken_form == "RYT"
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.source == "provider-pronunciation-generator"
    assert generator.calls
    assert "provider IPA used because authoritative IPA was missing" in candidate.provenance.notes


def test_grounding_uses_word_fallback_when_pronunciation_generator_fails() -> None:
    generator = FailingPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["house"],
                    ipa=None,
                )
            }
        ),
        pronunciation_generator=generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.PT,
        item=ParsedWordListItem(line_number=1, submitted_form="casa", display_form="casa", item_key="casa"),
    )

    assert candidate.ipa == "casa"
    assert candidate.spoken_form == "casa"
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.source == "manual_missing"
    assert candidate.provenance.pronunciation.authoritative is False
    assert generator.calls
    assert "pronunciation generator failed; word fallback will be used" in candidate.provenance.notes
    assert "word fallback used because authoritative IPA was missing" in candidate.provenance.notes


def test_grounding_preserves_authoritative_ipa_for_frequency_candidates() -> None:
    generator = StubPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["house"],
                    ipa="/authoritative/",
                )
            }
        ),
        pronunciation_generator=generator,
    )
    seed = LexicalCardCandidate(
        submitted_form="casa",
        display_form="casa",
        lemma="casa",
        lemma_key="casa",
        frequency_rank=1,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    candidate = service.ground_frequency_candidate(language=SupportedLanguage.PT, candidate=seed)

    assert candidate.ipa == "/authoritative/"
    assert candidate.spoken_form == "casa"
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.source == "manual"
    assert generator.calls == []


def _korean_fingerprint(
    *, analyzer_package_version: str = "0.23.2"
) -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version=analyzer_package_version,
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def _resolved_korean_analysis(
    *,
    fingerprint: KoreanAnalyzerFingerprint,
    surface_form: str,
    signatures: tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]],
) -> KoreanMorphologyResult:
    canonical_surface = canonicalize_korean(surface_form)
    alternatives: list[KoreanAnalysisAlternative] = []
    for rank, signature_pairs in enumerate(signatures, start=1):
        morphemes = tuple(
            KoreanMorphemeEvidence(
                form=form,
                lemma=form,
                pos=pos,
                raw_pos=pos,
                oov=False,
            )
            for form, pos in signature_pairs
        )
        alternatives.append(
            KoreanAnalysisAlternative(
                rank=rank,
                score=-float(rank),
                words=(
                    KoreanWordAnalysis(
                        surface_form=canonical_surface,
                        word_position=0,
                        morphemes=morphemes,
                        lexical_signature=tuple(
                            KoreanSignatureItem(form=form, pos=pos)
                            for form, pos in signature_pairs
                        ),
                    ),
                ),
                has_oov=False,
            )
        )
    return KoreanMorphologyResult(
        status=KoreanMorphologyStatus.RESOLVED,
        analyzer_fingerprint=fingerprint,
        alternatives=tuple(alternatives),
        reason_code=KoreanReasonCode.ANALYSIS_RESOLVED,
    )


def _non_passing_korean_analysis(
    *,
    fingerprint: KoreanAnalyzerFingerprint,
    status: KoreanMorphologyStatus,
) -> KoreanMorphologyResult:
    reason_code = {
        KoreanMorphologyStatus.UNAVAILABLE: KoreanReasonCode.ANALYZER_RUNTIME_ERROR,
        KoreanMorphologyStatus.INVALID: KoreanReasonCode.INVALID_TEXT,
    }[status]
    return KoreanMorphologyResult(
        status=status,
        analyzer_fingerprint=fingerprint,
        alternatives=(),
        reason_code=reason_code,
        exception_class="RuntimeError" if status is KoreanMorphologyStatus.UNAVAILABLE else None,
    )


def _oov_korean_analysis(
    *,
    fingerprint: KoreanAnalyzerFingerprint,
    surface_form: str,
) -> KoreanMorphologyResult:
    canonical_surface = canonicalize_korean(surface_form)
    alternatives = tuple(
        KoreanAnalysisAlternative(
            rank=rank,
            score=-float(rank),
            words=(
                KoreanWordAnalysis(
                    surface_form=canonical_surface,
                    word_position=0,
                    morphemes=(
                        KoreanMorphemeEvidence(
                            form=canonical_surface,
                            lemma=canonical_surface,
                            pos="NNG",
                            raw_pos="NNG",
                            oov=True,
                        ),
                    ),
                    lexical_signature=(
                        KoreanSignatureItem(form=canonical_surface, pos="NNG"),
                    ),
                ),
            ),
            has_oov=True,
        )
        for rank in (1, 2)
    )
    return KoreanMorphologyResult(
        status=KoreanMorphologyStatus.OOV,
        analyzer_fingerprint=fingerprint,
        alternatives=alternatives,
        reason_code=KoreanReasonCode.OOV_TOKEN,
    )


class _KoreanInventoryLookup:
    def __init__(self, records: tuple[LexicalRecord, ...]) -> None:
        self.records = records
        self.iter_calls: list[str] = []

    def iter_candidates(self, *, language_code: str) -> tuple[LexicalRecord, ...]:
        self.iter_calls.append(language_code)
        return self.records

    def lookup(self, *, language_code: str, term: str) -> LexicalRecord | None:
        raise AssertionError("Korean source binding must enumerate explicit source records")


class _FakeKoreanMorphology:
    def __init__(
        self,
        analyses: dict[str, KoreanMorphologyResult],
        *,
        fingerprint: KoreanAnalyzerFingerprint | None = None,
    ) -> None:
        self._fingerprint = fingerprint or _korean_fingerprint()
        self._analyses = {
            canonicalize_korean(text): result for text, result in analyses.items()
        }
        self.calls: list[str] = []

    @property
    def fingerprint(self) -> KoreanAnalyzerFingerprint:
        return self._fingerprint

    def analyze(self, text: str) -> KoreanMorphologyResult:
        canonical_text = canonicalize_korean(text)
        self.calls.append(canonical_text)
        return self._analyses[canonical_text]


class _RecordingKoreanMorphology:
    def __init__(self, delegate: KiwiKoreanMorphologyService) -> None:
        self.delegate = delegate
        self.calls: list[str] = []

    @property
    def fingerprint(self) -> KoreanAnalyzerFingerprint:
        return self.delegate.fingerprint

    def analyze(self, text: str) -> KoreanMorphologyResult:
        self.calls.append(canonicalize_korean(text))
        return self.delegate.analyze(text)


def _korean_record(
    lemma: str,
    *,
    part_of_speech: str | None,
    sense_id: str | None,
    register: str | None = "standard",
) -> LexicalRecord:
    return LexicalRecord(
        term=lemma,
        display_form=lemma,
        lemma=lemma,
        definitions=["synthetic fixture only"],
        part_of_speech=part_of_speech,
        sense_id=sense_id,
        register=register,
        source="reviewed_test_fixture",
    )


def test_korean_compound_source_binding_uses_real_kiwi() -> None:
    morphology = _RecordingKoreanMorphology(KiwiKoreanMorphologyService())
    lookup = _KoreanInventoryLookup(
        (
            _korean_record(
                "공부하다",
                part_of_speech="verb",
                sense_id="fixture:study:1",
            ),
        )
    )
    service = LexicalGroundingService(
        lookup=lookup,
        korean_morphology=morphology,
    )

    result = service.resolve_korean_source_identity(surface_form="공부해요")

    assert result.status == "resolved"
    assert result.reason_code == "source_consensus_resolved"
    assert result.identity is not None
    assert result.identity.lemma == "공부하다"
    assert result.identity.part_of_speech == "VV"
    assert result.identity.sense_id == "fixture:study:1"
    assert tuple(
        (item.form, item.pos) for item in result.identity.morpheme_signature
    ) == (("공부", "NNG"), ("하", "XSV"))
    assert result.identity.analyzer_fingerprint == morphology.fingerprint
    assert morphology.calls == ["공부하다", "공부해요"]
    assert lookup.iter_calls == ["ko"]


def test_korean_real_kiwi_surface_alternatives_selecting_different_records_fail() -> None:
    morphology = _RecordingKoreanMorphology(KiwiKoreanMorphologyService())
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "걷다",
                    part_of_speech="verb",
                    sense_id="fixture:walk:1",
                ),
                _korean_record(
                    "걸다",
                    part_of_speech="verb",
                    sense_id="fixture:hang:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    result = service.resolve_korean_source_identity(surface_form="걸어요")

    assert result.status == "ambiguous"
    assert result.identity is None
    assert result.reason_code == "surface_source_disagreement"
    assert "걸어요" not in result.model_dump_json()


def test_korean_real_kiwi_matching_morphology_without_source_record_fails() -> None:
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(()),
        korean_morphology=KiwiKoreanMorphologyService(),
    )

    result = service.resolve_korean_source_identity(surface_form="공부해요")

    assert result.status == "insufficient"
    assert result.identity is None
    assert result.reason_code == "source_record_missing"


def test_korean_source_catalog_is_deterministic_and_caches_only_source_projection() -> None:
    fingerprint = _korean_fingerprint()
    verb = (("먹", "VV"),)
    morphology = _FakeKoreanMorphology(
        {
            "가다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="가다",
                signatures=((("가", "VV"),), (("가", "VV"),)),
            ),
            "먹다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="먹다",
                signatures=(verb, verb),
            ),
            "비밀표면": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="비밀표면",
                signatures=(verb, verb),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "먹다",
                    part_of_speech="VV",
                    sense_id="fixture:eat:1",
                ),
                _korean_record(
                    "가다",
                    part_of_speech="verb",
                    sense_id="fixture:go:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    first = service.resolve_korean_source_identity(surface_form="비밀표면")
    second = service.resolve_korean_source_identity(surface_form="비밀표면")

    assert first.status == second.status == "resolved"
    assert morphology.calls == ["가다", "먹다", "비밀표면", "비밀표면"]
    cache_dump = repr(service._korean_source_signature_cache)
    assert "비밀표면" not in cache_dump
    assert "Token(" not in cache_dump


def test_korean_source_binding_requires_exact_full_ordered_signature_and_pos() -> None:
    fingerprint = _korean_fingerprint()
    compound = (("공부", "NNG"), ("하", "XSV"))
    noun_only = (("공부", "NNG"),)
    reversed_compound = tuple(reversed(compound))
    morphology = _FakeKoreanMorphology(
        {
            "공부하다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="공부하다",
                signatures=(compound, compound),
            ),
            "공부": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="공부",
                signatures=(noun_only, noun_only),
            ),
            "하공부": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="하공부",
                signatures=(reversed_compound, reversed_compound),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "공부하다",
                    part_of_speech="verb",
                    sense_id="fixture:study:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    subset = service.resolve_korean_source_identity(surface_form="공부")
    reordered = service.resolve_korean_source_identity(surface_form="하공부")

    assert subset.status == reordered.status == "insufficient"
    assert subset.identity is reordered.identity is None
    assert subset.reason_code == reordered.reason_code == "source_record_missing"

    conflicting_service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "공부하다",
                    part_of_speech="noun",
                    sense_id="fixture:conflict:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )
    conflict = conflicting_service.resolve_korean_source_identity(
        surface_form="공부하다"
    )
    assert conflict.status == "insufficient"
    assert conflict.reason_code == "source_pos_conflict"


def test_korean_source_binding_maps_xsa_to_source_adjective_without_guessing_lemma() -> None:
    fingerprint = _korean_fingerprint()
    adjective_signature = (("깨끗", "XR"), ("하", "XSA"))
    morphology = _FakeKoreanMorphology(
        {
            "깨끗하다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="깨끗하다",
                signatures=(adjective_signature, adjective_signature),
            ),
            "깨끗해요": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="깨끗해요",
                signatures=(adjective_signature, adjective_signature),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "깨끗하다",
                    part_of_speech="adjective",
                    sense_id="fixture:clean:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    result = service.resolve_korean_source_identity(surface_form="깨끗해요")

    assert result.status == "resolved"
    assert result.identity is not None
    assert result.identity.lemma == "깨끗하다"
    assert result.identity.part_of_speech == "VA"
    assert tuple(
        (item.form, item.pos) for item in result.identity.morpheme_signature
    ) == adjective_signature


def test_korean_source_binding_rejects_multiple_senses_and_incomplete_records() -> None:
    fingerprint = _korean_fingerprint()
    signature = (("말", "NNG"),)
    morphology = _FakeKoreanMorphology(
        {
            "말": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="말",
                signatures=(signature, signature),
            ),
        },
        fingerprint=fingerprint,
    )
    ambiguous = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record("말", part_of_speech="noun", sense_id="fixture:speech:1"),
                _korean_record("말", part_of_speech="noun", sense_id="fixture:horse:1"),
            )
        ),
        korean_morphology=morphology,
    ).resolve_korean_source_identity(surface_form="말")
    missing_sense = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record("말", part_of_speech="noun", sense_id=None),
            )
        ),
        korean_morphology=morphology,
    ).resolve_korean_source_identity(surface_form="말")
    missing_pos = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record("말", part_of_speech="", sense_id="fixture:speech:1"),
            )
        ),
        korean_morphology=morphology,
    ).resolve_korean_source_identity(surface_form="말")

    assert ambiguous.status == "ambiguous"
    assert ambiguous.reason_code == "source_record_ambiguous"
    assert ambiguous.identity is None
    assert missing_sense.status == missing_pos.status == "insufficient"
    assert missing_sense.identity is missing_pos.identity is None


def test_korean_source_signature_ambiguity_fails_closed() -> None:
    fingerprint = _korean_fingerprint()
    source_signatures = (("먹", "VV"),), (("마시", "VV"),)
    surface_signature = (("먹", "VV"),)
    morphology = _FakeKoreanMorphology(
        {
            "먹다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="먹다",
                signatures=source_signatures,
            ),
            "먹어요": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="먹어요",
                signatures=(surface_signature, surface_signature),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "먹다",
                    part_of_speech="verb",
                    sense_id="fixture:eat:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    result = service.resolve_korean_source_identity(surface_form="먹어요")

    assert result.status == "insufficient"
    assert result.reason_code == "source_signature_ambiguous"
    assert result.identity is None


def test_korean_source_binding_oov_unavailable_and_fingerprint_drift_are_content_free() -> None:
    fingerprint = _korean_fingerprint()
    signature = (("먹", "VV"),)
    source_analysis = _resolved_korean_analysis(
        fingerprint=fingerprint,
        surface_form="먹다",
        signatures=(signature, signature),
    )
    unavailable = _non_passing_korean_analysis(
        fingerprint=fingerprint,
        status=KoreanMorphologyStatus.UNAVAILABLE,
    )
    oov = _oov_korean_analysis(
        fingerprint=fingerprint,
        surface_form="비밀경로",
    )
    drifted = _resolved_korean_analysis(
        fingerprint=_korean_fingerprint(analyzer_package_version="0.23.1"),
        surface_form="비밀경로",
        signatures=(signature, signature),
    )
    record = _korean_record(
        "먹다",
        part_of_speech="verb",
        sense_id="fixture:eat:1",
    )

    unavailable_result = LexicalGroundingService(
        lookup=_KoreanInventoryLookup((record,)),
        korean_morphology=_FakeKoreanMorphology(
            {"먹다": source_analysis, "비밀경로": unavailable},
            fingerprint=fingerprint,
        ),
    ).resolve_korean_source_identity(surface_form="비밀경로")
    drift_result = LexicalGroundingService(
        lookup=_KoreanInventoryLookup((record,)),
        korean_morphology=_FakeKoreanMorphology(
            {"먹다": source_analysis, "비밀경로": drifted},
            fingerprint=fingerprint,
        ),
    ).resolve_korean_source_identity(surface_form="비밀경로")
    oov_result = LexicalGroundingService(
        lookup=_KoreanInventoryLookup((record,)),
        korean_morphology=_FakeKoreanMorphology(
            {"먹다": source_analysis, "비밀경로": oov},
            fingerprint=fingerprint,
        ),
    ).resolve_korean_source_identity(surface_form="비밀경로")

    assert unavailable_result.status == drift_result.status == "unavailable"
    assert unavailable_result.reason_code == "surface_analysis_unavailable"
    assert drift_result.reason_code == "surface_fingerprint_mismatch"
    assert oov_result.status == "insufficient"
    assert oov_result.reason_code == "surface_analysis_oov"
    for result in (unavailable_result, drift_result, oov_result):
        serialized = result.model_dump_json()
        assert result.identity is None
        assert "비밀경로" not in serialized
        assert "private" not in serialized
        assert "traceback" not in serialized


def test_korean_unavailable_source_lemma_analysis_blocks_surface_binding() -> None:
    fingerprint = _korean_fingerprint()
    signature = (("먹", "VV"),)
    morphology = _FakeKoreanMorphology(
        {
            "먹다": _non_passing_korean_analysis(
                fingerprint=fingerprint,
                status=KoreanMorphologyStatus.UNAVAILABLE,
            ),
            "비밀표면": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="비밀표면",
                signatures=(signature, signature),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "먹다",
                    part_of_speech="verb",
                    sense_id="fixture:eat:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    result = service.resolve_korean_source_identity(surface_form="비밀표면")

    assert result.status == "unavailable"
    assert result.reason_code == "source_analysis_unavailable"
    assert result.identity is None
    assert "비밀표면" not in result.model_dump_json()


def _resolved_korean_text_analysis(
    *,
    fingerprint: KoreanAnalyzerFingerprint,
    alternatives: tuple[
        tuple[tuple[str, int, tuple[tuple[str, str], ...]], ...],
        tuple[tuple[str, int, tuple[tuple[str, str], ...]], ...],
    ],
) -> KoreanMorphologyResult:
    projected_alternatives: list[KoreanAnalysisAlternative] = []
    for rank, words in enumerate(alternatives, start=1):
        projected_words: list[KoreanWordAnalysis] = []
        for surface_form, word_position, signature_pairs in words:
            morphemes = tuple(
                KoreanMorphemeEvidence(
                    form=form,
                    lemma=form,
                    pos=pos,
                    raw_pos=pos,
                    oov=False,
                )
                for form, pos in signature_pairs
            )
            projected_words.append(
                KoreanWordAnalysis(
                    surface_form=canonicalize_korean(surface_form),
                    word_position=word_position,
                    morphemes=morphemes,
                    lexical_signature=tuple(
                        KoreanSignatureItem(form=form, pos=pos)
                        for form, pos in signature_pairs
                    ),
                )
            )
        projected_alternatives.append(
            KoreanAnalysisAlternative(
                rank=rank,
                score=-float(rank),
                words=tuple(projected_words),
                has_oov=False,
            )
        )
    return KoreanMorphologyResult(
        status=KoreanMorphologyStatus.RESOLVED,
        analyzer_fingerprint=fingerprint,
        alternatives=tuple(projected_alternatives),
        reason_code=KoreanReasonCode.ANALYSIS_RESOLVED,
    )


def test_korean_source_binding_rejects_multi_eojeol_source_and_surface_analysis() -> None:
    fingerprint = _korean_fingerprint()
    eat = (("먹", "VV"),)
    speech = (("말", "NNG"),)
    source_words = (("먹다", 0, eat), ("말", 1, speech))
    surface_words = (("먹어요", 0, eat), ("말", 1, speech))
    record = _korean_record(
        "먹다",
        part_of_speech="verb",
        sense_id="fixture:eat:1",
    )

    invalid_source = LexicalGroundingService(
        lookup=_KoreanInventoryLookup((record,)),
        korean_morphology=_FakeKoreanMorphology(
            {
                "먹다": _resolved_korean_text_analysis(
                    fingerprint=fingerprint,
                    alternatives=(source_words, source_words),
                ),
                "먹어요": _resolved_korean_analysis(
                    fingerprint=fingerprint,
                    surface_form="먹어요",
                    signatures=(eat, eat),
                ),
            },
            fingerprint=fingerprint,
        ),
    ).resolve_korean_source_identity(surface_form="먹어요")
    invalid_surface = LexicalGroundingService(
        lookup=_KoreanInventoryLookup((record,)),
        korean_morphology=_FakeKoreanMorphology(
            {
                "먹다": _resolved_korean_analysis(
                    fingerprint=fingerprint,
                    surface_form="먹다",
                    signatures=(eat, eat),
                ),
                "먹어요 말": _resolved_korean_text_analysis(
                    fingerprint=fingerprint,
                    alternatives=(surface_words, surface_words),
                ),
            },
            fingerprint=fingerprint,
        ),
    ).resolve_korean_source_identity(surface_form="먹어요 말")

    assert invalid_source.status == invalid_surface.status == "insufficient"
    assert invalid_source.reason_code == "source_analysis_invalid"
    assert invalid_surface.reason_code == "surface_analysis_invalid"
    assert invalid_source.identity is invalid_surface.identity is None


def test_korean_word_list_grounding_preserves_nfd_submission_and_portuguese_policy() -> None:
    fingerprint = _korean_fingerprint()
    compound = (("공부", "NNG"), ("하", "XSV"))
    submitted = unicodedata.normalize("NFD", "공부해요")
    morphology = _FakeKoreanMorphology(
        {
            "공부하다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="공부하다",
                signatures=(compound, compound),
            ),
            "공부해요": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="공부해요",
                signatures=(compound, compound),
            ),
        },
        fingerprint=fingerprint,
    )
    definition_generator = StubDefinitionGenerator()
    pronunciation_generator = StubPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "공부하다",
                    part_of_speech="verb",
                    sense_id="fixture:study:1",
                ),
            )
        ),
        korean_morphology=morphology,
        definition_generator=definition_generator,
        pronunciation_generator=pronunciation_generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.KO,
        item=ParsedWordListItem(
            line_number=7,
            submitted_form=submitted,
            display_form="공부해요",
            item_key="공부해요",
        ),
    )

    assert candidate.submitted_form == submitted
    assert candidate.display_form == candidate.lemma == "공부하다"
    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert candidate.definition_language == "pt"
    assert candidate.translation_target_language == "pt"
    assert candidate.korean_identity is not None
    assert candidate.korean_identity.submitted_form == submitted
    assert candidate.korean_identity.canonical_nfc == "공부해요"
    assert candidate.korean_identity.lemma == "공부하다"
    assert candidate.lemma_key == candidate.korean_identity.lexical_key
    assert candidate.definitions_html == "VV: LLM definition for 공부하다"
    assert len(definition_generator.calls) == 1
    definition_request = definition_generator.calls[0]
    assert definition_request.source_language == "ko"
    assert definition_request.target_language == "pt"
    assert definition_request.part_of_speech == "VV"
    assert definition_request.korean_identity == candidate.korean_identity
    assert (
        definition_request.korean_identity.model_dump(mode="json")
        == candidate.korean_identity.model_dump(mode="json")
    )
    assert pronunciation_generator.calls == []


def test_korean_definition_output_cannot_replace_resolved_identity() -> None:
    fingerprint = _korean_fingerprint()
    signature = (("배우", "NNG"),)
    morphology = _FakeKoreanMorphology(
        {
            "배우": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="배우",
                signatures=(signature, signature),
            ),
        },
        fingerprint=fingerprint,
    )

    class ForgingDefinitionGenerator:
        def __init__(self) -> None:
            self.calls: list[object] = []
            self.morphology_calls_at_handoff: tuple[str, ...] = ()

        def generate_definition(self, request: object) -> object:
            self.calls.append(request)
            self.morphology_calls_at_handoff = tuple(morphology.calls)
            return type(
                "ForgedDefinitionResult",
                (),
                {
                    "definitions_html": "verb: forged provider definition",
                    "provenance": {
                        "source": "deterministic-forging-fake",
                        "lemma": "공격자",
                        "part_of_speech": "VV",
                        "sense_id": "attacker",
                        "morpheme_signature": [{"form": "공격", "pos": "VV"}],
                        "analyzer_fingerprint": {"policy_version": "attacker"},
                        "approval_status": "approved",
                    },
                    "lemma": "공격자",
                    "part_of_speech": "VV",
                    "sense_id": "attacker",
                    "approval_status": "approved",
                },
            )()

    generator = ForgingDefinitionGenerator()
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "배우",
                    part_of_speech="noun",
                    sense_id="fixture:actor:1",
                ),
            )
        ),
        korean_morphology=morphology,
        definition_generator=generator,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.KO,
        item=ParsedWordListItem(
            line_number=1,
            submitted_form="배우",
            display_form="배우",
            item_key="배우",
        ),
    )

    assert generator.morphology_calls_at_handoff == ("배우", "배우")
    assert len(generator.calls) == 1
    request = generator.calls[0]
    assert request.korean_identity is not None
    assert request.korean_identity == candidate.korean_identity
    assert candidate.lemma == "배우"
    assert candidate.lemma_key == request.korean_identity.lexical_key
    assert candidate.korean_identity.part_of_speech == "NNG"
    assert candidate.korean_identity.sense_id == "fixture:actor:1"
    assert candidate.korean_identity.morpheme_signature == (
        KoreanSignatureItem(form="배우", pos="NNG"),
    )
    assert candidate.korean_identity.analyzer_fingerprint == fingerprint
    assert not hasattr(candidate, "approval_status")


def test_korean_word_list_non_consensus_stays_pending_with_controlled_diagnostics() -> None:
    fingerprint = _korean_fingerprint()
    signature = (("비밀", "NNG"),)
    private_surface = "비밀입력"
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(()),
        korean_morphology=_FakeKoreanMorphology(
            {
                private_surface: _resolved_korean_analysis(
                    fingerprint=fingerprint,
                    surface_form=private_surface,
                    signatures=(signature, signature),
                )
            },
            fingerprint=fingerprint,
        ),
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.KO,
        item=ParsedWordListItem(
            line_number=99,
            submitted_form=private_surface,
            display_form=private_surface,
            item_key=private_surface,
        ),
    )

    assert candidate.grounding_status is GroundingStatus.PENDING
    assert candidate.korean_identity is None
    assert candidate.warning_code == "korean_source_binding_insufficient"
    assert candidate.warning_detail == "source_record_missing"
    assert "line 99" not in (candidate.warning_detail or "")


def test_korean_frequency_grounding_uses_source_selector_and_never_seed_fallback() -> None:
    fingerprint = _korean_fingerprint()
    signature = (("먹", "VV"),)
    morphology = _FakeKoreanMorphology(
        {
            "먹다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="먹다",
                signatures=(signature, signature),
            ),
            "먹어요": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="먹어요",
                signatures=(signature, signature),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "먹다",
                    part_of_speech="verb",
                    sense_id="fixture:eat:1",
                ),
            )
        ),
        korean_morphology=morphology,
        allow_frequency_seed_fallback=True,
    )
    seed = LexicalCardCandidate(
        submitted_form="먹어요",
        display_form="먹어요",
        lemma="먹어요",
        lemma_key="먹어요",
        frequency_rank=142,
        frequency_level=1,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="temporary_test_fixture"),
    )

    candidate = service.ground_frequency_candidate(
        language=SupportedLanguage.KO,
        candidate=seed,
    )

    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert candidate.frequency_rank == 142
    assert candidate.frequency_level == 1
    assert candidate.lemma == "먹다"
    assert candidate.definition_language == "pt"
    assert candidate.translation_target_language == "pt"
    assert candidate.korean_identity is not None
    assert candidate.provenance.source != "wordfreq"

    blocked_service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(()),
        korean_morphology=morphology,
        allow_frequency_seed_fallback=True,
    )
    blocked = blocked_service.ground_frequency_candidate(
        language=SupportedLanguage.KO,
        candidate=seed,
    )
    assert blocked.grounding_status is GroundingStatus.BACKFILL_REQUIRED
    assert blocked.korean_identity is None
    assert blocked.warning_detail == "source_record_missing"


def test_korean_frequency_consensus_candidate_with_frozen_evidence_is_not_reanalyzed_or_rewritten() -> None:
    fingerprint = _korean_fingerprint()
    identity = KoreanLexicalIdentity(
        submitted_form="학교",
        canonical_nfc="학교",
        lemma="학교",
        part_of_speech="NNG",
        sense_id="nikl:1",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="학교", pos="NNG"),),
        analyzer_fingerprint=fingerprint,
        status="resolved",
    )
    evidence = KoreanFrequencyLexicalEvidence(
        source_id="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        source_rank=7,
        final_rank=1,
        level=1,
        part_of_speech="NNG",
        sense_id="nikl:1",
        grounding_confidence="source-backed",
        license_decision="approved-local-use",
        curation_decision="accepted",
        bundle_sha256="a" * 64,
        source_sha256="b" * 64,
        source_review_receipt_sha256="c" * 64,
        source_review_aggregate_sha256="d" * 64,
        analyzer_fingerprint=fingerprint,
    )
    candidate = LexicalCardCandidate(
        submitted_form="학교",
        display_form="학교",
        lemma="학교",
        lemma_key=identity.lexical_key,
        frequency_rank=1,
        frequency_level=1,
        definition_language="pt",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="korean-frequency-bundle"),
        korean_identity=identity,
        korean_frequency_evidence=evidence,
    )
    morphology = _FakeKoreanMorphology({}, fingerprint=fingerprint)
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(()),
        korean_morphology=morphology,
        allow_frequency_seed_fallback=True,
    )

    grounded = service.ground_frequency_candidate(
        language=SupportedLanguage.KO,
        candidate=candidate,
    )

    assert grounded == candidate
    assert grounded.korean_identity == identity
    assert grounded.korean_frequency_evidence == evidence
    assert morphology.calls == []


def test_korean_highlight_text_resolves_each_eojeol_from_one_local_analysis() -> None:
    fingerprint = _korean_fingerprint()
    water = (("물", "NNG"),)
    unknown = (("미지어", "NNG"),)
    study = (("공부", "NNG"), ("하", "XSV"))
    highlight_text = "물은 미지어를 공부해요"
    words = (
        ("물은", 0, water),
        ("미지어를", 1, unknown),
        ("공부해요", 2, study),
    )
    morphology = _FakeKoreanMorphology(
        {
            "물": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="물",
                signatures=(water, water),
            ),
            "공부하다": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="공부하다",
                signatures=(study, study),
            ),
            highlight_text: _resolved_korean_text_analysis(
                fingerprint=fingerprint,
                alternatives=(words, words),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "공부하다",
                    part_of_speech="verb",
                    sense_id="fixture:study:1",
                ),
                _korean_record(
                    "물",
                    part_of_speech="noun",
                    sense_id="fixture:water:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    resolved = service.resolve_korean_highlight_text(highlight_text)

    assert [(item.surface_form, item.word_position) for item in resolved] == [
        ("물은", 0),
        ("공부해요", 2),
    ]
    assert [item.identity.lemma for item in resolved] == ["물", "공부하다"]
    assert [item.identity.sense_id for item in resolved] == [
        "fixture:water:1",
        "fixture:study:1",
    ]
    assert morphology.calls == ["공부하다", "물", highlight_text]
    assert all("미지어" not in item.model_dump_json() for item in resolved)


def test_korean_highlight_grounding_uses_exact_source_identity_and_safe_failure() -> None:
    fingerprint = _korean_fingerprint()
    school = (("학교", "NNG"),)
    private_surface = "비밀경로"
    morphology = _FakeKoreanMorphology(
        {
            "학교": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="학교",
                signatures=(school, school),
            ),
            "학교에서": _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form="학교에서",
                signatures=(school, school),
            ),
            private_surface: _resolved_korean_analysis(
                fingerprint=fingerprint,
                surface_form=private_surface,
                signatures=((('비밀', 'NNG'),), (('비밀', 'NNG'),)),
            ),
        },
        fingerprint=fingerprint,
    )
    service = LexicalGroundingService(
        lookup=_KoreanInventoryLookup(
            (
                _korean_record(
                    "학교",
                    part_of_speech="noun",
                    sense_id="fixture:school:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )

    grounded = service.ground_highlight_candidate(
        language=SupportedLanguage.KO,
        candidate=HighlightCandidate(
            item_key="highlight-ko-safe-school",
            display_form="학교에서",
            lemma_key="학교에서",
            source_content_hash="a" * 64,
            first_highlight_id="safe-id",
            first_source_index=2,
            occurrence_count=1,
        ),
    )
    blocked = service.ground_highlight_candidate(
        language=SupportedLanguage.KO,
        candidate=HighlightCandidate(
            item_key="highlight-ko-safe-private",
            display_form=private_surface,
            lemma_key=private_surface,
            source_content_hash="b" * 64,
            first_highlight_id="safe-id-2",
            first_source_index=3,
            occurrence_count=1,
        ),
    )

    assert grounded.grounding_status is GroundingStatus.GROUNDED
    assert grounded.display_form == grounded.lemma == "학교"
    assert grounded.korean_identity is not None
    assert grounded.korean_identity.sense_id == "fixture:school:1"
    assert blocked.grounding_status is GroundingStatus.INSUFFICIENT
    assert blocked.korean_identity is None
    blocked_json = blocked.model_dump_json()
    assert private_surface not in blocked_json
    assert "traceback" not in blocked_json
    assert "prompt" not in blocked_json


def test_non_korean_grounding_never_invokes_korean_selector() -> None:
    morphology = _FakeKoreanMorphology({}, fingerprint=_korean_fingerprint())
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": LexicalRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["house"],
                    part_of_speech="noun",
                    source="manual",
                )
            }
        ),
        korean_morphology=morphology,
    )

    candidate = service.ground_word_list_item(
        language=SupportedLanguage.PT,
        item=ParsedWordListItem(
            line_number=1,
            submitted_form="casa",
            display_form="casa",
            item_key="casa",
        ),
    )

    assert candidate.lemma == "casa"
    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert morphology.calls == []
