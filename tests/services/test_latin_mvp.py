"""Tests for the deterministic Classical Latin MVP start service."""

from __future__ import annotations

import pytest

from multilang.domain.latin import LatinGenerationRequest, LatinVariant
from multilang.services.latin_mvp import LatinMvpGenerationService


def test_latin_mvp_start_returns_latin_metadata_and_source_type() -> None:
    result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert result.metadata.language_code == "la"
    assert result.metadata.variant is LatinVariant.CLASSICAL
    assert result.metadata.source_pack_version == "latin-mvp-50-v1"
    assert result.metadata.card_count == 50
    assert result.source_type == "latin-mvp"


def test_latin_mvp_start_returns_exactly_50_deterministic_item_keys() -> None:
    result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert len(result.item_keys) == 50
    assert result.item_keys[0] == "latin-mvp-0001"
    assert result.item_keys[-1] == "latin-mvp-0050"
    assert result.item_keys == [f"latin-mvp-{index:04d}" for index in range(1, 51)]


def test_latin_mvp_start_exposes_manifest_backed_summary_fields() -> None:
    result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert result.manifest_path == "data/latin_mvp/latin-mvp-50-v1.json"
    assert result.first_item_key == "latin-mvp-0001"
    assert result.last_item_key == "latin-mvp-0050"
    assert result.license_gate_status == "approved"
    assert result.source_type_counts["adapted_didactic"] > 0
    assert result.frequency_source_count == 1
    assert "50 entries" in result.didactic_sequence_summary


def test_latin_mvp_start_exposes_approved_grammar_readiness_fields() -> None:
    result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert result.grammar_gate_status == "approved"
    assert result.grammar_evidence_count == 50
    assert result.gramatica_count == 50
    assert result.required_case_labels == [
        "Nominativus",
        "Vocativus",
        "Accusativus",
        "Genitivus",
        "Dativus",
        "Ablativus",
    ]


def test_latin_mvp_manifest_summary_includes_grammar_readiness_fields() -> None:
    summary = LatinMvpGenerationService().start(LatinGenerationRequest()).manifest_summary()

    assert summary["grammar_gate_status"] == "approved"
    assert summary["grammar_evidence_count"] == 50
    assert summary["gramatica_count"] == 50
    assert "Genitivus" in summary["required_case_labels"]


def test_latin_mvp_start_cannot_approve_unresolved_grammar_loader_data() -> None:
    def unresolved_loader(_path):
        raise ValueError("Latin MVP source pack grammar evidence unresolved")

    with pytest.raises(ValueError, match="grammar"):
        LatinMvpGenerationService(source_pack_loader=unresolved_loader).start(LatinGenerationRequest())


def test_latin_mvp_source_pack_version_mismatch_raises_value_error() -> None:
    with pytest.raises(ValueError, match="source_pack_version"):
        LatinMvpGenerationService().start(LatinGenerationRequest(source_pack_version="custom-pack"))


def test_latin_mvp_item_keys_come_from_manifest_order() -> None:
    result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert result.item_keys == [f"latin-mvp-{index:04d}" for index in range(1, 51)]
