"""Tests for Latin Portuguese translation generation contracts."""

from __future__ import annotations

from multilang.services.latin_source_pack import load_latin_mvp_source_pack
from multilang.services.latin_translation_generation import LatinTranslationGenerationService


def test_latin_translation_generation_builds_approved_aligned_entry() -> None:
    source_entry = load_latin_mvp_source_pack().entries[0]
    service = LatinTranslationGenerationService(
        lambda _entry: {
            "short_translation_pt": "palavra",
            "sentence_translation_pt": "A palavra ama.",
            "translation_notes": "Tradução didática validada.",
        }
    )

    result = service.translate_entry(source_entry)

    assert result.item_key == source_entry.item_key
    assert result.review_status == "approved"
    assert result.latin_sentence == source_entry.latin_sentence
