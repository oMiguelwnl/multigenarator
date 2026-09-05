"""Tests for deterministic generation input fingerprints."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unicodedata

from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.personal_sources import PersonalSourceRow
from multilang.services.input_fingerprint import (
    build_korean_ordered_source_fingerprint,
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


def test_korean_ordered_source_fingerprint_changes_on_reorder() -> None:
    rows = (
        PersonalSourceRow(
            input_position=1,
            line_number=1,
            submitted_form="학교",
            display_form="학교",
            normalized_duplicate_key="학교",
        ),
        PersonalSourceRow(
            input_position=2,
            line_number=2,
            submitted_form="물",
            display_form="물",
            normalized_duplicate_key="물",
        ),
    )
    reordered_rows = (
        PersonalSourceRow(
            input_position=1,
            line_number=1,
            submitted_form="물",
            display_form="물",
            normalized_duplicate_key="물",
        ),
        PersonalSourceRow(
            input_position=2,
            line_number=2,
            submitted_form="학교",
            display_form="학교",
            normalized_duplicate_key="학교",
        ),
    )

    assert [row.stable_item_key for row in rows] == [
        row.stable_item_key for row in reversed(reordered_rows)
    ]
    assert build_korean_ordered_source_fingerprint(rows) != (
        build_korean_ordered_source_fingerprint(reordered_rows)
    )


def test_korean_ordered_source_fingerprint_includes_visible_duplicates() -> None:
    first_only = (
        PersonalSourceRow(
            input_position=1,
            line_number=1,
            submitted_form="학교",
            display_form="학교",
            normalized_duplicate_key="학교",
        ),
    )
    with_duplicate = (
        first_only[0],
        PersonalSourceRow(
            input_position=2,
            line_number=2,
            submitted_form="학교",
            display_form="학교",
            normalized_duplicate_key="학교",
            duplicate_of_position=1,
        ),
    )

    assert build_korean_ordered_source_fingerprint(first_only) != (
        build_korean_ordered_source_fingerprint(with_duplicate)
    )
