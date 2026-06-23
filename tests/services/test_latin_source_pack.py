"""Contract tests for the frozen Classical Latin MVP source-pack loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from multilang.services.latin_source_pack import (
    APPROVED_LATIN_CASE_LABELS,
    LatinMvpSourcePack,
    load_latin_mvp_source_pack,
    validate_latin_gramatica,
    validate_latin_target_presence,
)


def _entry(sequence: int = 1, **overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "item_key": f"latin-mvp-{sequence:04d}",
        "sequence": sequence,
        "lemma": f"lemma{sequence}",
        "target_form": f"lemma{sequence}",
        "latin_sentence": f"lemma{sequence} amat.",
        "frequency_rank": sequence,
        "frequency_source": "As mil palavras mais frequentes do latim (mylittlewordland)",
        "frequency_source_url": "https://mylittlewordland.com/course/415114/as-mil-palavras-mais-frequentes-do-latim",
        "source_pack_version": "latin-mvp-50-v1",
        "inclusion_status": "included",
        "inclusion_rationale": "Core DCC lemma retained for the 50-card MVP.",
        "didactic_order_rationale": "Simple early sentence supports Rafael Falcon-style sequencing.",
        "source_type": "adapted_didactic",
        "citation": "Project-authored didactic Latin sentence",
        "work_reference": "Multilang Latin MVP didactic sequence",
        "source_url_or_id": "multilang:latin-mvp:didactic",
        "license_note": "Project-authored didactic text; DCC lemma metadata attributed under CC BY-SA.",
        "license_gate": "approved",
        "target_match_mode": "exact",
        "original_citation_claim": False,
        "morphology_evidence": {
            "lemma": f"lemma{sequence}",
            "part_of_speech": "subst",
            "case_label": "Nominativus",
            "number": "sg",
            "verbal_analysis": None,
            "syntactic_function": "Suj",
            "evidence_note": f"lemma{sequence} is nominative singular subject in the sentence.",
            "grammar_review_status": "approved",
        },
        "gramatica": "subst sg Nominativus Suj",
    }
    data.update(overrides)
    return data


def _pack(**entry_overrides: object) -> dict[str, object]:
    entries = [_entry(index) for index in range(1, 51)]
    if entry_overrides:
        entries[0].update(entry_overrides)
    return {
        "language_code": "la",
        "variant": "classical",
        "source_pack_version": "latin-mvp-50-v1",
        "card_count": 50,
        "frequency_attribution": "As mil palavras mais frequentes do latim (mylittlewordland), CC BY-SA.",
        "license_attribution": "As mil palavras mais frequentes do latim (mylittlewordland) lemma metadata under CC BY-SA; adapted sentences are project-authored.",
        "entries": entries,
    }


def test_source_pack_accepts_exact_50_card_contract() -> None:
    pack = LatinMvpSourcePack.model_validate(_pack())

    assert pack.language_code == "la"
    assert pack.source_pack_version == "latin-mvp-50-v1"
    assert pack.card_count == 50
    assert [entry.item_key for entry in pack.entries][:2] == ["latin-mvp-0001", "latin-mvp-0002"]
    assert pack.entries[0].morphology_evidence.grammar_review_status == "approved"
    assert pack.entries[0].gramatica == "subst sg Nominativus Suj"


def test_gramatica_validator_accepts_short_contract() -> None:
    assert validate_latin_gramatica("subst sg Genitivus Suj") == "subst sg Genitivus Suj"
    assert validate_latin_gramatica("v pres ind act 3sg V") == "v pres ind act 3sg V"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lemma", ""),
        ("target_form", ""),
        ("latin_sentence", ""),
        ("frequency_source", ""),
        ("inclusion_rationale", ""),
        ("didactic_order_rationale", ""),
        ("citation", ""),
        ("license_note", ""),
    ],
)
def test_entry_rejects_blank_required_fields(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        LatinMvpSourcePack.model_validate(_pack(**{field: value}))


@pytest.mark.parametrize(
    "morphology_evidence",
    [
        {
            "lemma": "lemma1",
            "part_of_speech": "subst",
            "case_label": "Nominativus",
            "number": "sg",
            "verbal_analysis": None,
            "syntactic_function": "Suj",
            "evidence_note": " ",
            "grammar_review_status": "approved",
        },
        {
            "lemma": "lemma1",
            "part_of_speech": "subst",
            "case_label": "Nominativus",
            "number": "sg",
            "verbal_analysis": None,
            "syntactic_function": "",
            "evidence_note": "subject in context",
            "grammar_review_status": "approved",
        },
        {
            "lemma": "lemma1",
            "part_of_speech": "subst",
            "case_label": "Nominativus",
            "number": "sg",
            "verbal_analysis": None,
            "syntactic_function": "Suj",
            "evidence_note": "subject in context",
            "grammar_review_status": "unresolved",
        },
    ],
)
def test_entry_rejects_unresolved_or_blank_morphology_evidence(morphology_evidence: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        LatinMvpSourcePack.model_validate(_pack(morphology_evidence=morphology_evidence))


@pytest.mark.parametrize("case_label", ["Nominativus", "Vocativus", "Accusativus", "Genitivus", "Dativus", "Ablativus"])
def test_entry_accepts_required_latin_case_labels(case_label: str) -> None:
    pack = LatinMvpSourcePack.model_validate(
        _pack(
            morphology_evidence={
                "lemma": "lemma1",
                "part_of_speech": "subst",
                "case_label": case_label,
                "number": "sg",
                "verbal_analysis": None,
                "syntactic_function": "Suj",
                "evidence_note": "nominal form resolved in context",
                "grammar_review_status": "approved",
            },
            gramatica=f"subst sg {case_label} Suj",
        )
    )

    assert pack.entries[0].morphology_evidence.case_label == case_label


@pytest.mark.parametrize("case_label", ["Genetivus", "Locativus", "genitive"])
def test_entry_rejects_invalid_case_labels(case_label: str) -> None:
    with pytest.raises(ValidationError):
        LatinMvpSourcePack.model_validate(
            _pack(
                morphology_evidence={
                    "lemma": "lemma1",
                    "part_of_speech": "subst",
                    "case_label": case_label,
                    "number": "sg",
                    "verbal_analysis": None,
                    "syntactic_function": "Suj",
                    "evidence_note": "nominal form resolved in context",
                    "grammar_review_status": "approved",
                },
                gramatica=f"subst sg {case_label} Suj",
            )
        )


@pytest.mark.parametrize("gramatica", ["substantivo sg Nominativus Suj", "noun singular subject", "subst sg Genetivus Suj"])
def test_gramatica_rejects_long_english_or_unapproved_labels(gramatica: str) -> None:
    with pytest.raises(ValueError):
        validate_latin_gramatica(gramatica)


def test_required_case_label_constant_is_exact() -> None:
    assert APPROVED_LATIN_CASE_LABELS == (
        "Nominativus",
        "Vocativus",
        "Accusativus",
        "Genitivus",
        "Dativus",
        "Ablativus",
    )


def test_entry_rejects_blocked_license_gate() -> None:
    with pytest.raises(ValidationError, match="license"):
        LatinMvpSourcePack.model_validate(_pack(license_gate="blocked"))


def test_adapted_didactic_entry_cannot_claim_original_citation() -> None:
    with pytest.raises(ValidationError, match="original citation"):
        LatinMvpSourcePack.model_validate(_pack(original_citation_claim=True))


@pytest.mark.parametrize("count", [49, 51])
def test_pack_requires_exactly_50_entries(count: int) -> None:
    data = _pack()
    data["entries"] = [_entry(index) for index in range(1, count + 1)]

    with pytest.raises(ValidationError, match="exactly 50"):
        LatinMvpSourcePack.model_validate(data)


def test_pack_requires_sequence_and_key_order() -> None:
    data = _pack()
    entries = list(data["entries"])
    entries[1] = dict(entries[1], item_key="latin-mvp-0099")
    data["entries"] = entries

    with pytest.raises(ValidationError, match="item_key"):
        LatinMvpSourcePack.model_validate(data)


def test_validate_latin_target_presence_exact_mode() -> None:
    assert validate_latin_target_presence("arma", "Arma virumque cano.", "exact")
    assert not validate_latin_target_presence("amo", "Arma virumque cano.", "exact")


def test_validate_latin_target_presence_orthographic_mode() -> None:
    assert validate_latin_target_presence("puella", "Puēlla in via stat.", "orthographic_normalization")
    assert not validate_latin_target_presence("puer", "Puēlla in via stat.", "orthographic_normalization")


def test_validate_latin_target_presence_enclitic_mode() -> None:
    assert validate_latin_target_presence("virum", "Arma virumque cano.", "enclitic_normalization")
    assert not validate_latin_target_presence("cano", "Arma virumque canit.", "enclitic_normalization")


def test_entry_validation_uses_declared_target_match_mode() -> None:
    pack = LatinMvpSourcePack.model_validate(
        _pack(target_form="virum", latin_sentence="Arma virumque cano.", target_match_mode="enclitic_normalization")
    )

    assert pack.entries[0].target_form == "virum"


def test_entry_validation_rejects_absent_target_form() -> None:
    with pytest.raises(ValidationError, match="target_form"):
        LatinMvpSourcePack.model_validate(_pack(target_form="amo", latin_sentence="Arma virumque cano."))


def test_loader_returns_typed_pack_from_json(tmp_path: Path) -> None:
    manifest = tmp_path / "latin-mvp-50-v1.json"
    manifest.write_text(json.dumps(_pack()), encoding="utf-8")

    pack = load_latin_mvp_source_pack(manifest)

    assert isinstance(pack, LatinMvpSourcePack)
    assert len(pack.entries) == 50


def test_loader_converts_missing_or_invalid_json_to_concise_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Latin MVP source pack") as missing:
        load_latin_mvp_source_pack(tmp_path / "missing.json")
    assert str(tmp_path) not in str(missing.value)

    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="Latin MVP source pack") as malformed:
        load_latin_mvp_source_pack(bad)
    assert str(tmp_path) not in str(malformed.value)


def test_loader_rejects_wrong_version_json(tmp_path: Path) -> None:
    manifest = tmp_path / "wrong.json"
    data = _pack()
    data["source_pack_version"] = "wrong"
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="latin-mvp-50-v1"):
        load_latin_mvp_source_pack(manifest)
