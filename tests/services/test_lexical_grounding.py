"""Tests for trust-first lexical grounding."""

from __future__ import annotations

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.highlights import HighlightCandidate
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.services.kaikki_lookup import KaikkiRecord
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.text_generation import SentenceTranslationResult
from multilang.services.word_list_parser import ParsedWordListItem


class StubLookup:
    def __init__(self, mapping: dict[str, KaikkiRecord | None]) -> None:
        self._mapping = mapping

    def lookup(self, *, language_code: str, term: str) -> KaikkiRecord | None:
        return self._mapping.get(term.casefold())


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


class StubDefinitionTranslator:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def translate_sentence(self, request: object) -> SentenceTranslationResult:
        self.calls.append(request)
        return SentenceTranslationResult(
            translation="verbo: lavarse con agua",
            provenance={"source": "stub-definition-translator"},
        )


def test_grounding_prefers_study_form_and_manual_language_policy() -> None:
    translator = StubDefinitionTranslator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "lavar": KaikkiRecord(
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
        definition_translator=translator,
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
    assert candidate.definitions_html == "verbo: lavarse con agua"
    assert candidate.definition_language == "es"
    assert candidate.translation_target_language == "es"
    assert candidate.grounding_status is GroundingStatus.GROUNDED
    assert translator.calls
    assert translator.calls[0].translation_target_language == "es"
    assert translator.calls[0].template_kind == "definition"


def test_frequency_grounding_keeps_default_english_definition_policy() -> None:
    translator = StubDefinitionTranslator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": KaikkiRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["a building where people live"],
                    part_of_speech="noun",
                    ipa="/casa/",
                )
            }
        ),
        definition_translator=translator,
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

    assert candidate.definitions_html == "noun: a building where people live"
    assert candidate.definition_language == "en"
    assert translator.calls == []


def test_highlight_grounding_localizes_definition_to_deck_language() -> None:
    translator = StubDefinitionTranslator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "lavar": KaikkiRecord(
                    term="lavar",
                    display_form="lavar",
                    lemma="lavar",
                    definitions=["to wash"],
                    part_of_speech="verb",
                    ipa="/laˈβaɾ/",
                )
            }
        ),
        definition_translator=translator,
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

    assert candidate.definitions_html == "verbo: lavarse con agua"
    assert candidate.definition_language == "es"
    assert translator.calls[0].translation_target_language == "es"


def test_grounding_formats_simple_grammar_labels_for_common_parts_of_speech() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": KaikkiRecord(
                    term="casa",
                    display_form="casa",
                    lemma="casa",
                    definitions=["a building where people live"],
                    part_of_speech="noun",
                ),
                "bonito": KaikkiRecord(
                    term="bonito",
                    display_form="bonito",
                    lemma="bonito",
                    definitions=["beautiful; pleasant to look at or experience"],
                    part_of_speech="adj",
                ),
                "em": KaikkiRecord(
                    term="em",
                    display_form="em",
                    lemma="em",
                    definitions=["used to show location, time, or position inside something"],
                    part_of_speech="prep",
                ),
            }
        )
    )

    expected = {
        "casa": "noun: a building where people live",
        "bonito": "adjective: beautiful; pleasant to look at or experience",
        "em": "preposition: used to show location, time, or position inside something",
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


def test_grounding_omits_verb_tense_from_definition_template() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "lava": KaikkiRecord(
                    term="lava",
                    display_form="lava",
                    lemma="lavar",
                    definitions=["washes; cleans something with water"],
                    part_of_speech="verb",
                    grammar_tags=["present", "third", "singular"],
                )
            }
        )
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

    assert candidate.definitions_html == "verb: washes; cleans something with water"
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


def test_grounding_does_not_invent_ipa() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": KaikkiRecord(
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

    assert candidate.ipa is None
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.value is None
    assert candidate.provenance.pronunciation.source == "kaikki_missing"
    assert candidate.provenance.pronunciation.authoritative is True


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


def test_frequency_rejects_morphological_only_lexical_records() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casas": KaikkiRecord(
                    term="casas",
                    display_form="casas",
                    lemma="casas",
                    definitions=["nominative plural of casa"],
                    ipa="/casas/",
                )
            }
        )
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

    assert candidate.grounding_status is GroundingStatus.BACKFILL_REQUIRED
    assert candidate.warning_code == "backfill_required"
    assert "not a primary card entry" in (candidate.warning_detail or "")


def test_russian_frequency_rejects_uppercase_duplicate_records() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "и": KaikkiRecord(
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
                "casa": KaikkiRecord(
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
    assert candidate.provenance.pronunciation.source == "kaikki"
    assert generator.calls == []


def test_grounding_uses_ai_pronunciation_when_authoritative_ipa_is_missing() -> None:
    generator = StubPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": KaikkiRecord(
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


def test_grounding_preserves_authoritative_ipa_for_frequency_candidates() -> None:
    generator = StubPronunciationGenerator()
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "casa": KaikkiRecord(
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
    assert candidate.provenance.pronunciation.source == "kaikki"
    assert generator.calls == []
