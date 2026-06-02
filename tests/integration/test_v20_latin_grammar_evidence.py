"""GRAM Phase 24 scanner-readable Latin grammar evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from multilang.domain.latin import LatinGenerationRequest
from multilang.services.latin_mvp import LatinMvpGenerationService
from multilang.services.latin_source_pack import (
    APPROVED_LATIN_CASE_LABELS,
    load_latin_mvp_source_pack,
    validate_latin_gramatica,
)


PHASE_24_REQUIREMENTS = {
    "GRAM-01": "Every Latin MVP entry carries typed morphology evidence for the target form.",
    "GRAM-02": "Learner-facing Gramatica values use concise approved abbreviations.",
    "GRAM-03": "Case labels use the approved Latin vocabulary with Genitivus.",
    "GRAM-04": "Only approved grammar evidence can pass the Latin MVP grammar gate.",
}


def _asset_payload() -> dict[str, object]:
    return json.loads(Path("data/latin_mvp/latin-mvp-50-v1.json").read_text(encoding="utf-8"))


def test_phase_24_requirement_mapping_covers_exact_gram_ids() -> None:
    assert set(PHASE_24_REQUIREMENTS) == {"GRAM-01", "GRAM-02", "GRAM-03", "GRAM-04"}


def test_gram_01_every_entry_has_required_morphology_evidence_fields() -> None:
    """GRAM-01: committed pack exposes typed morphology for each target form."""

    pack = load_latin_mvp_source_pack()

    assert len(pack.entries) == 50
    for entry in pack.entries:
        evidence = entry.morphology_evidence
        assert evidence.lemma == entry.lemma
        assert evidence.part_of_speech
        assert evidence.syntactic_function
        assert evidence.evidence_note
        assert evidence.grammar_review_status == "approved"
        if evidence.part_of_speech in {"subst", "adj", "pron"}:
            assert evidence.case_label is not None, entry.item_key
            assert evidence.number in {"sg", "pl"}, entry.item_key
        if evidence.part_of_speech == "v":
            assert evidence.verbal_analysis is not None, entry.item_key


def test_gram_02_gramatica_values_use_approved_abbreviations() -> None:
    """GRAM-02: Gramatica is concise and rejects long/English labels."""

    pack = load_latin_mvp_source_pack()
    forbidden_fragments = {"substantivo", "adjetivo", "verbo", "noun", "subject", "singular", "plural"}

    for entry in pack.entries:
        assert validate_latin_gramatica(entry.gramatica) == entry.gramatica
        assert entry.gramatica.strip() == entry.gramatica
        assert len(entry.gramatica) <= 80
        assert not any(fragment in entry.gramatica.casefold() for fragment in forbidden_fragments), entry.item_key

    for bad_value in ("substantivo sg Nominativus Suj", "noun singular subject", "subst singular Nominativus Suj"):
        with pytest.raises(ValueError):
            validate_latin_gramatica(bad_value)


def test_gram_03_case_vocabulary_includes_genitivus_and_excludes_genetivus() -> None:
    """GRAM-03: approved Latin case vocabulary is exact and scanner-readable."""

    assert APPROVED_LATIN_CASE_LABELS == (
        "Nominativus",
        "Vocativus",
        "Accusativus",
        "Genitivus",
        "Dativus",
        "Ablativus",
    )
    assert "Genitivus" in APPROVED_LATIN_CASE_LABELS
    assert "Genetivus" not in APPROVED_LATIN_CASE_LABELS
    for case_label in APPROVED_LATIN_CASE_LABELS:
        assert validate_latin_gramatica(f"subst sg {case_label} Suj")
    with pytest.raises(ValueError):
        validate_latin_gramatica("subst sg Genetivus Suj")


def test_gram_04_service_reports_approved_gate_only_after_loader_validation() -> None:
    """GRAM-04: grammar gate status comes from validated pack data."""

    result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert result.grammar_gate_status == "approved"
    assert result.grammar_evidence_count == 50
    assert result.gramatica_count == 50
    assert result.manifest_summary()["grammar_gate_status"] == "approved"

    def failing_loader(_path):
        raise ValueError("Latin MVP source pack grammar evidence unresolved")

    with pytest.raises(ValueError, match="grammar"):
        LatinMvpGenerationService(source_pack_loader=failing_loader).start(LatinGenerationRequest())
