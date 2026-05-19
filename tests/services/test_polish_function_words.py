from __future__ import annotations

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.polish_function_words import POLISH_FUNCTION_WORDS_VERSION, lookup_polish_function_word


class EmptyLookup:
    def lookup(self, *, language_code: str, term: str):
        return None


def test_polish_function_word_data_is_versioned() -> None:
    record = lookup_polish_function_word("nie")
    assert record is not None
    assert record.source == POLISH_FUNCTION_WORDS_VERSION
    assert record.part_of_speech == "particle"
    assert record.ipa == "/ɲɛ/"


def test_polish_function_words_ground_before_provider_or_lookup() -> None:
    service = LexicalGroundingService(lookup=EmptyLookup(), allow_frequency_seed_fallback=True)
    candidate = LexicalCardCandidate(
        submitted_form="w",
        display_form="w",
        lemma="w",
        lemma_key="w",
        frequency_rank=1,
        frequency_level=1,
        definition_language="en",
        translation_target_language="en",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="wordfreq"),
    )

    grounded = service.ground_frequency_candidate(language=SupportedLanguage.PL, candidate=candidate)

    assert grounded.grounding_status is GroundingStatus.GROUNDED
    assert grounded.definitions_html.startswith("preposition:")
    assert grounded.ipa == "/f/"
    assert grounded.provenance.source == POLISH_FUNCTION_WORDS_VERSION
