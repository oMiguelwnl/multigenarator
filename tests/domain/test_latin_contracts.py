"""Contract tests for Classical Latin MVP domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from multilang.domain.latin import (
    DEFAULT_LATIN_SOURCE_PACK_VERSION,
    LATIN_LANGUAGE_CODE,
    LATIN_MVP_CARD_COUNT,
    LatinDeckMetadata,
    LatinGenerationRequest,
    LatinVariant,
)


def test_latin_deck_metadata_defaults_to_classical_la_50_card_contract() -> None:
    metadata = LatinDeckMetadata()

    assert metadata.language_code == LATIN_LANGUAGE_CODE == "la"
    assert metadata.variant is LatinVariant.CLASSICAL
    assert metadata.source_pack_version == DEFAULT_LATIN_SOURCE_PACK_VERSION
    assert metadata.source_pack_version
    assert metadata.card_count == LATIN_MVP_CARD_COUNT == 50


def test_latin_generation_request_defaults_to_latin_mvp_contract() -> None:
    request = LatinGenerationRequest()

    assert request.language_code == "la"
    assert request.variant is LatinVariant.CLASSICAL
    assert request.source_type == "latin-mvp"
    assert request.source_pack_version == DEFAULT_LATIN_SOURCE_PACK_VERSION
    assert request.card_count == 50


@pytest.mark.parametrize("blank_version", ["", "   "])
def test_latin_contracts_reject_blank_source_pack_versions(blank_version: str) -> None:
    with pytest.raises(ValidationError):
        LatinDeckMetadata(source_pack_version=blank_version)

    with pytest.raises(ValidationError):
        LatinGenerationRequest(source_pack_version=blank_version)


@pytest.mark.parametrize("card_count", [0, 49, 51, 1000])
def test_latin_contracts_reject_any_card_count_other_than_50(card_count: int) -> None:
    with pytest.raises(ValidationError):
        LatinDeckMetadata(card_count=card_count)

    with pytest.raises(ValidationError):
        LatinGenerationRequest(card_count=card_count)
