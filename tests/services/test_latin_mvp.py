"""Tests for the deterministic Classical Latin MVP start service."""

from __future__ import annotations

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


def test_latin_mvp_source_pack_override_preserves_item_key_contract() -> None:
    result = LatinMvpGenerationService().start(
        LatinGenerationRequest(source_pack_version="custom-pack")
    )

    assert result.metadata.source_pack_version == "custom-pack"
    assert result.metadata.card_count == 50
    assert result.item_keys == [f"latin-mvp-{index:04d}" for index in range(1, 51)]
