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


def test_grounding_prefers_study_form_and_english_definitions() -> None:
    service = LexicalGroundingService(
        lookup=StubLookup(
            {
                "lavar": KaikkiRecord(
                    term="lavar",
                    display_form="lavarse",
                    lemma="lavar",
                    definitions=["to wash", "to wash oneself"],
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
    assert candidate.definitions_html == "to wash<br>to wash oneself"
    assert candidate.definition_language == "en"
    assert candidate.translation_target_language == "en"
    assert candidate.grounding_status is GroundingStatus.GROUNDED


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
