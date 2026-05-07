"""Integration coverage for the refreshed Russian phoneme template export flow."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from multilang.services.russian_phoneme_deck import (
    PHONEME_FIELD_NAMES,
    RUSSIAN_PHONEME_CARDS,
    RussianPhonemeCard,
    build_russian_phoneme_model,
    build_russian_phoneme_note,
    export_russian_phoneme_deck,
)


_FIELD_REFERENCE_RE = re.compile(r"{{[#/^]?([^}:]+)}}|{{hint:([^}]+)}}")
_FORBIDDEN_REFERENCES = {
    "Notes",
    "is_priming",
    "is_sentence",
    "Definitions",
    "image",
    "IPA",
    "Exemple Sentence",
    "Translation",
}


def _template_references(template: str) -> set[str]:
    return {match.group(1) or match.group(2) for match in _FIELD_REFERENCE_RE.finditer(template)}


def test_russian_phoneme_template_refresh_exports_apkg_with_safe_references(tmp_path: Path) -> None:
    output_path = tmp_path / "russian-phonemes-refresh.apkg"

    result = export_russian_phoneme_deck(output_path=output_path)
    model = build_russian_phoneme_model()
    template = model.templates[0]
    allowed_references = set(PHONEME_FIELD_NAMES) | {"FrontSide"}

    assert result.output_path == output_path
    assert result.card_count == len(RUSSIAN_PHONEME_CARDS)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
    assert tuple(field["name"] for field in model.fields) == PHONEME_FIELD_NAMES
    assert "{{hint:Sentence Translation}}" not in template["qfmt"]
    assert "{{Sentence Translation}}" in template["qfmt"]
    assert 'style="display:none;"' in template["qfmt"]
    assert "{{Sentence Translation}}" in template["afmt"]
    assert 'document.getElementById("sentenceTranslation").style.display = "block"' in template["afmt"]
    assert _template_references(template["qfmt"]) <= allowed_references
    assert _template_references(template["afmt"]) <= allowed_references
    assert _template_references(template["qfmt"]).isdisjoint(_FORBIDDEN_REFERENCES)
    assert _template_references(template["afmt"]).isdisjoint(_FORBIDDEN_REFERENCES)


def test_russian_phoneme_template_refresh_preserves_audio_fields_on_visible_front() -> None:
    model = build_russian_phoneme_model()
    note = build_russian_phoneme_note(
        RussianPhonemeCard(
            sort_index=999,
            letters="щ",
            ipa="/ɕː/",
            example_word="щука",
            example_word_translation="pike",
            example_sentence="Щенок ищет щётку щедро.",
            example_sentence_translation="A puppy generously looks for a brush.",
            letter_audio="[sound:letter.mp3]",
            word_audio="[sound:word.mp3]",
            sentence_audio="[sound:sentence.mp3]",
        ),
        model=model,
    )
    qfmt = model.templates[0]["qfmt"]

    assert "{{letter_audio}}" in qfmt
    assert "{{word_audio}}" in qfmt
    assert "{{sentence_audio}}" in qfmt
    assert note.fields[2] == "[sound:letter.mp3]"
    assert note.fields[4] == "[sound:word.mp3]"
    assert note.fields[7] == "[sound:sentence.mp3]"
