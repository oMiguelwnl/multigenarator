"""Phase 16 audit wrappers for phonetics and existing-mode evidence."""

from __future__ import annotations

from pathlib import Path

from multilang.services.russian_phoneme_deck import PHONEME_FIELD_NAMES, build_russian_phoneme_model

from tests.integration import test_russian_phoneme_template_refresh_flow as phonetics_evidence


EXPECTED_PHONEME_FIELDS = (
    "Spellings",
    "Sound",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Example Sentence",
    "sentence_audio",
    "Sentence Translation",
)


def test_phase16_phonetics_audit_reexecutes_refresh_evidence_and_contract(tmp_path: Path) -> None:
    phonetics_evidence.test_russian_phoneme_template_refresh_exports_apkg_with_safe_references(tmp_path)
    phonetics_evidence.test_russian_phoneme_template_refresh_preserves_audio_fields_on_visible_front()

    model = build_russian_phoneme_model()
    template = model.templates[0]
    qfmt = template["qfmt"]
    afmt = template["afmt"]
    allowed_references = set(EXPECTED_PHONEME_FIELDS) | {"FrontSide"}

    assert PHONEME_FIELD_NAMES == EXPECTED_PHONEME_FIELDS
    assert tuple(field["name"] for field in model.fields) == EXPECTED_PHONEME_FIELDS
    assert phonetics_evidence._template_references(qfmt) <= allowed_references
    assert phonetics_evidence._template_references(afmt) <= allowed_references
    assert phonetics_evidence._template_references(qfmt).isdisjoint(phonetics_evidence._FORBIDDEN_REFERENCES)
    assert phonetics_evidence._template_references(afmt).isdisjoint(phonetics_evidence._FORBIDDEN_REFERENCES)
    assert "{{letter_audio}}" in qfmt
    assert "{{word_audio}}" in qfmt
    assert "{{sentence_audio}}" in qfmt
    assert "{{FrontSide}}" in afmt
    assert "{{Sentence Translation}}" in qfmt
    assert "{{Sentence Translation}}" in afmt
