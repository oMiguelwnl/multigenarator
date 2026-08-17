"""Tests for deterministic generation input fingerprints."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unicodedata

from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.services.input_fingerprint import (
    build_input_fingerprint,
    build_run_key,
    normalize_requested_item_keys,
)


def test_korean_canonical_equivalents_share_fingerprint_and_run_key() -> None:
    nfc = "학교"
    nfd = unicodedata.normalize("NFD", nfc)
    request = GenerationRequest(
        language=SupportedLanguage.KO,
        source_type="word-list",
        input_file=Path("reviewed-fixture.txt"),
    )

    assert normalize_requested_item_keys([nfd, nfc]) == [nfc]
    assert build_input_fingerprint(request, requested_item_keys=[nfd]) == build_input_fingerprint(
        request,
        requested_item_keys=[nfc],
    )
    assert build_run_key(request, requested_item_keys=[nfd]) == build_run_key(
        request,
        requested_item_keys=[nfc],
    )


def test_existing_whitespace_case_and_non_korean_fingerprint_contract_is_unchanged() -> None:
    request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=Path("words.txt"),
    )
    expected_digest = sha256("alpha\nbeta".encode("utf-8")).hexdigest()

    normalized = normalize_requested_item_keys([" Alpha ", "alpha", "BETA", "", "  "])

    assert normalized == ["alpha", "beta"]
    assert build_input_fingerprint(request, requested_item_keys=normalized) == (
        f"items:{expected_digest}"
    )
    assert build_run_key(request, requested_item_keys=normalized) == (
        f"en:word-list:items:{expected_digest}"
    )


def test_frequency_fingerprint_remains_independent_of_requested_item_keys() -> None:
    request = GenerationRequest(
        language=SupportedLanguage.KO,
        source_type="frequency",
        level=2,
        cards_per_level=25,
    )

    assert build_input_fingerprint(request, requested_item_keys=["학교"]) == "level:2:cards:25"
    assert build_run_key(request, requested_item_keys=["학교"]) == "ko:frequency:level:2:cards:25"
