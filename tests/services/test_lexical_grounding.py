"""Tests for trust-first lexical grounding."""

from __future__ import annotations

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.services.kaikki_lookup import KaikkiRecord
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.word_list_parser import ParsedWordListItem


class StubLookup:
    def __init__(self, mapping: dict[str, KaikkiRecord | None]) -> None:
        self._mapping = mapping

    def lookup(self, *, language_code: str, term: str) -> KaikkiRecord | None:
        assert language_code == SupportedLanguage.ES.value
        return self._mapping.get(term.casefold())


def test_grounding_prefers_study_form_and_definition_template() -> None:
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
        )
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
    assert candidate.definitions_html == (
        "verb: to wash something or clean it with water"
        "<br>verb: to wash oneself"
    )
    assert candidate.definition_language == "en"
    assert candidate.translation_target_language == "en"
    assert candidate.grounding_status is GroundingStatus.GROUNDED



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
            language=SupportedLanguage.ES,
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
        language=SupportedLanguage.ES,
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
