"""Phase 16 audit wrappers for phonetics and existing-mode evidence."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from pytest import MonkeyPatch

from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
)
from multilang.services.export_anki_package import HIGHLIGHT_NOTE_TYPE_NAME, MANUAL_NOTE_TYPE_NAME, NOTE_TYPE_NAME
from multilang.services.russian_phoneme_deck import PHONEME_FIELD_NAMES, build_russian_phoneme_model


def _load_integration_module(name: str) -> ModuleType:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


phonetics_evidence = _load_integration_module("test_russian_phoneme_template_refresh_flow")
existing_mode_evidence = _load_integration_module("test_v12_existing_mode_regression_boundary")


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


def test_phase16_existing_mode_audit_reexecutes_regression_boundaries(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    existing_mode_evidence.test_frequency_existing_mode_still_generates_audio_exports_and_uses_default_contract(
        tmp_path / "frequency",
        monkeypatch,
    )
    existing_mode_evidence.test_custom_word_list_existing_mode_still_generates_audio_exports_without_highlight_fields(
        tmp_path / "custom",
        monkeypatch,
    )
    existing_mode_evidence.test_cli_accepts_public_highlights_but_rejects_internal_kindle_highlights()
    existing_mode_evidence.test_highlight_generation_audio_qa_evidence_is_source_aware_and_private_safe(
        tmp_path / "privacy"
    )

    assert "Translation" in FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert "Translation" in MANUAL_EXPORT_CARD_FIELD_NAMES
    assert "Translation" not in HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert FREQUENCY_EXPORT_CARD_FIELD_NAMES == MANUAL_EXPORT_CARD_FIELD_NAMES
    assert HIGHLIGHT_EXPORT_CARD_FIELD_NAMES != FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert {NOTE_TYPE_NAME, MANUAL_NOTE_TYPE_NAME, HIGHLIGHT_NOTE_TYPE_NAME} == {
        "Multilang::Card",
        "Multilang::Manual Card",
        "Multilang::Highlight Card",
    }
