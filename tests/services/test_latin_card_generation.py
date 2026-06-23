"""Tests for provider-ready Latin card generation contracts."""

from __future__ import annotations

import pytest

from multilang.services.latin_card_generation import LatinCardGenerationSeed, LatinCardGenerationService


def test_latin_card_generation_validates_and_preserves_seed_order() -> None:
    seeds = [LatinCardGenerationSeed(sequence=1, lemma="amo", target_form="amat", part_of_speech="v")]
    service = LatinCardGenerationService(
        lambda requested: [
            {
                "sequence": requested[0].sequence,
                "lemma": "amo",
                "target_form": "amat",
                "definition": "ama (3sg)",
                "latin_sentence": "Puella matrem amat.",
                "gramatica": "v pres ind act 3sg V",
                "morphology_note": "amat is present indicative active third singular.",
            }
        ]
    )

    cards = service.generate(seeds)

    assert cards[0].lemma == "amo"
    assert cards[0].target_form == "amat"


def test_latin_card_generation_rejects_order_drift() -> None:
    seeds = [LatinCardGenerationSeed(sequence=1, lemma="amo", target_form="amat", part_of_speech="v")]
    service = LatinCardGenerationService(
        lambda _requested: [
            {
                "sequence": 2,
                "lemma": "amo",
                "target_form": "amat",
                "definition": "ama (3sg)",
                "latin_sentence": "Puella matrem amat.",
                "gramatica": "v pres ind act 3sg V",
                "morphology_note": "amat is present indicative active third singular.",
            }
        ]
    )

    with pytest.raises(ValueError, match="sequence"):
        service.generate(seeds)
