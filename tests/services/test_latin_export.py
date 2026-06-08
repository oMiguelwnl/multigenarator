from __future__ import annotations

import pytest

from multilang.services.latin_export import LATIN_EXPORT_FIELD_NAMES, LatinExportRow


def test_latin_export_field_order_excludes_classe() -> None:
    assert LATIN_EXPORT_FIELD_NAMES == (
        "SortIndex",
        "Latin Word",
        "Latin Sentence",
        "Lemma",
        "Translation",
        "Sentence Translation",
        "Gramatica",
        "Source",
        "word_audio",
        "sentence_audio",
        "Image",
    )
    forbidden = {"Classe", "class", "part_of_speech"}
    assert forbidden.isdisjoint(LATIN_EXPORT_FIELD_NAMES)


def test_latin_export_row_mapping_preserves_blank_image_and_no_classe() -> None:
    row = LatinExportRow(
        sort_index=1,
        item_key="latin-mvp-0001",
        latin_word="puella",
        latin_sentence="Puella legit.",
        lemma="puella",
        translation="menina",
        sentence_translation="A menina lê.",
        gramatica="subst Nominativus sg Suj",
        source="adapted_didactic | Multilang | latin-mvp-0001 | project-authored",
        word_audio="[sound:latin-mvp-0001-word.wav]",
        sentence_audio="[sound:latin-mvp-0001-sentence.wav]",
    )

    mapping = row.ordered_field_mapping()

    assert tuple(mapping) == LATIN_EXPORT_FIELD_NAMES
    assert mapping["Image"] == ""
    assert {"Classe", "class", "part_of_speech"}.isdisjoint(mapping)


def test_latin_export_row_rejects_nonblank_image() -> None:
    with pytest.raises(ValueError, match="Image must remain blank"):
        LatinExportRow(
            sort_index=1,
            item_key="latin-mvp-0001",
            latin_word="puella",
            latin_sentence="Puella legit.",
            lemma="puella",
            translation="menina",
            sentence_translation="A menina lê.",
            gramatica="subst Nominativus sg Suj",
            source="adapted_didactic | Multilang | latin-mvp-0001 | project-authored",
            word_audio="[sound:latin-mvp-0001-word.wav]",
            sentence_audio="[sound:latin-mvp-0001-sentence.wav]",
            image="not-blank",
        )
