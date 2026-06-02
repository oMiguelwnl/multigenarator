"""Integration evidence for the committed Latin MVP grammar asset."""

from __future__ import annotations

import pytest

from multilang.services.latin_source_pack import (
    APPROVED_LATIN_CASE_LABELS,
    load_latin_mvp_source_pack,
    validate_latin_gramatica,
)


def test_committed_latin_mvp_asset_loads_with_approved_grammar_evidence() -> None:
    pack = load_latin_mvp_source_pack()

    assert len(pack.entries) == 50
    assert all(entry.morphology_evidence.grammar_review_status == "approved" for entry in pack.entries)


def test_committed_latin_mvp_asset_has_resolved_target_form_morphology() -> None:
    pack = load_latin_mvp_source_pack()

    for entry in pack.entries:
        evidence = entry.morphology_evidence
        assert evidence.lemma == entry.lemma
        assert evidence.syntactic_function
        if evidence.part_of_speech in {"subst", "adj", "pron"}:
            assert evidence.case_label is not None, entry.item_key
            assert evidence.number is not None, entry.item_key
        if evidence.part_of_speech == "v":
            assert evidence.verbal_analysis is not None, entry.item_key


def test_committed_latin_mvp_asset_has_concise_validated_gramatica() -> None:
    pack = load_latin_mvp_source_pack()
    forbidden = ("Genetivus", "substantivo", "noun", "subject", "singular")

    for entry in pack.entries:
        assert entry.gramatica.strip() == entry.gramatica
        assert len(entry.gramatica) <= 80
        assert validate_latin_gramatica(entry.gramatica) == entry.gramatica
        assert not any(label in entry.gramatica for label in forbidden), entry.item_key


@pytest.mark.parametrize("case_label", APPROVED_LATIN_CASE_LABELS)
def test_validator_accepts_required_latin_case_vocabulary(case_label: str) -> None:
    assert validate_latin_gramatica(f"subst sg {case_label} Suj")


def test_required_case_vocabulary_uses_genitivus_not_genetivus() -> None:
    assert "Genitivus" in APPROVED_LATIN_CASE_LABELS
    assert "Genetivus" not in APPROVED_LATIN_CASE_LABELS
    with pytest.raises(ValueError):
        validate_latin_gramatica("subst sg Genetivus Suj")
