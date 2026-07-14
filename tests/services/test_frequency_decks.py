"""Tests for deterministic frequency-deck curation."""

from __future__ import annotations

import csv
from dataclasses import replace

from multilang.domain.jobs import SupportedLanguage


def test_iterator_rejects_noise_tokens(monkeypatch) -> None:
    from multilang.services import frequency_decks

    def fake_iter_wordlist(language: str):
        assert language == SupportedLanguage.EN.value
        return iter(
            [
                "the",
                "123",
                "---",
                "www",
                "http",
                "e.g.",
                "O'Neil",
                "co-op",
                "l'amour",
                "word2",
                "&word",
                "https://example.com",
                "user@example.com",
                "#tag",
                "@handle",
                ":)",
                "Google",
            ]
        )

    monkeypatch.setattr(frequency_decks, "iter_wordlist", fake_iter_wordlist)

    results = list(
        frequency_decks.iter_curated_frequency_candidates(
            SupportedLanguage.EN,
            scan_limit=11,
        )
    )

    assert results == [
        (1, "the"),
        (8, "co-op"),
        (9, "l'amour"),
    ]


def test_iterator_normalizes_unicode_variants(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_wordlist",
        lambda language: iter([" l’amour ", "co‑op", "cafe\u0301"]),
    )

    assert list(frequency_decks.iter_curated_frequency_candidates(SupportedLanguage.FR, scan_limit=3)) == [
        (1, "l'amour"),
        (2, "co-op"),
        (3, "café"),
    ]


def test_iterator_rejects_unicode_replacement_character(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_wordlist",
        lambda language: iter(["\ufffd", "ord"]),
    )

    assert list(frequency_decks.iter_curated_frequency_candidates(SupportedLanguage.NB, scan_limit=2)) == [(2, "ord")]


def test_iterator_keeps_function_words(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_wordlist",
        lambda language: iter(["a", "to", "of", "in", "y", "de"]),
    )

    results = list(
        frequency_decks.iter_curated_frequency_candidates(
            SupportedLanguage.ES,
            scan_limit=6,
        )
    )

    assert results == [(1, "a"), (2, "to"), (3, "of"), (4, "in"), (5, "y"), (6, "de")]


def test_iterator_order_is_deterministic(monkeypatch) -> None:
    from multilang.services import frequency_decks

    words = ["uno", "dos", "tres", "cuatro"]
    monkeypatch.setattr(
        frequency_decks,
        "iter_wordlist",
        lambda language: iter(words),
    )

    first = list(
        frequency_decks.iter_curated_frequency_candidates(
            SupportedLanguage.ES,
            scan_limit=4,
        )
    )
    second = list(
        frequency_decks.iter_curated_frequency_candidates(
            SupportedLanguage.ES,
            scan_limit=4,
        )
    )

    assert first == second == [(1, "uno"), (2, "dos"), (3, "tres"), (4, "cuatro")]


def test_build_frequency_deck_returns_three_full_levels(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: (
            (rank, f"word-{rank}") for rank in range(1, 3001)
        ),
    )

    deck = frequency_decks.build_frequency_deck(SupportedLanguage.EN)

    assert sorted(deck) == [1, 2, 3]
    assert [len(deck[level]) for level in (1, 2, 3)] == [1000, 1000, 1000]

    assert deck[1][0].frequency_rank == 1
    assert deck[1][-1].frequency_rank == 1000
    assert deck[2][0].frequency_rank == 1001
    assert deck[2][-1].frequency_rank == 2000
    assert deck[3][0].frequency_rank == 2001
    assert deck[3][-1].frequency_rank == 3000

    assert deck[1][0].frequency_level == 1
    assert deck[2][0].frequency_level == 2
    assert deck[3][0].frequency_level == 3

    assert deck[1][0].provenance.source == "curated-frequency-asset"


def test_build_frequency_level_backfills_rejected_candidates(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: (
            (rank, f"word-{rank}") for rank in range(1, 3010)
        ),
    )

    level = frequency_decks.build_frequency_level(
        SupportedLanguage.EN,
        level=3,
        required_count_per_level=5,
        rejected_lemmas={"word-2001", "word-2003", "word-2005", "word-2007", "word-2009"},
        allow_frequency_seed_fallback=True,
    )

    assert [candidate.frequency_rank for candidate in level] == [2002, 2004, 2006, 2008, 2010]
    assert [candidate.submitted_form for candidate in level] == [
        "word-2002",
        "word-2004",
        "word-2006",
        "word-2008",
        "word-2010",
    ]
    assert all(candidate.frequency_level == 3 for candidate in level)


def test_build_frequency_level_skips_repeated_tokens_within_level(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: iter(
            [
                (2001, "word-a"),
                (2002, "word-a"),
                (2003, "word-b"),
                (2004, "word-c"),
            ]
        ),
    )

    level = frequency_decks.build_frequency_level(
        SupportedLanguage.EN,
        level=3,
        required_count_per_level=3,
        allow_frequency_seed_fallback=True,
    )

    assert [candidate.submitted_form for candidate in level] == ["word-a", "word-b", "word-c"]
    assert [candidate.frequency_rank for candidate in level] == [2001, 2003, 2004]


def test_build_frequency_deck_deduplicates_tokens_across_levels(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: iter(
            [
                (1, "word-1"),
                (2, "word-2"),
                (3, "word-3"),
                (1001, "word-1"),
                (1002, "word-1002"),
                (1003, "word-2"),
                (1004, "word-1004"),
                (1005, "word-1005"),
                (2001, "word-2001"),
                (2002, "word-2002"),
                (2003, "word-2003"),
            ]
        ),
    )

    deck = frequency_decks.build_frequency_deck(
        SupportedLanguage.EN,
        required_count_per_level=3,
        allow_frequency_seed_fallback=True,
    )

    assert [candidate.submitted_form for candidate in deck[1]] == ["word-1", "word-2", "word-3"]
    assert [candidate.submitted_form for candidate in deck[2]] == [
        "word-1002",
        "word-1004",
        "word-1005",
    ]
    assert [candidate.submitted_form for candidate in deck[3]] == [
        "word-2001",
        "word-2002",
        "word-2003",
    ]


def test_build_frequency_level_scans_past_rank_3000_for_backfill(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: (
            (rank, f"word-{rank}") for rank in range(2996, 3006)
        ),
    )

    level = frequency_decks.build_frequency_level(
        SupportedLanguage.EN,
        level=3,
        required_count_per_level=5,
        rejected_lemmas={"word-2997", "word-2998", "word-2999", "word-3000"},
        allow_frequency_seed_fallback=True,
    )

    assert [candidate.frequency_rank for candidate in level] == [2996, 3001, 3002, 3003, 3004]
    assert level[-1].frequency_level == 3


def test_build_frequency_deck_supports_custom_cards_per_level(monkeypatch) -> None:
    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: ((rank, f"word-{rank}") for rank in range(1, 3010)),
    )

    deck = frequency_decks.build_frequency_deck(
        SupportedLanguage.EN,
        required_count_per_level=4,
        allow_frequency_seed_fallback=True,
    )

    assert [len(deck[level]) for level in (1, 2, 3)] == [4, 4, 4]
    assert [candidate.frequency_rank for candidate in deck[1]] == [1, 2, 3, 4]
    assert [candidate.frequency_rank for candidate in deck[2]] == [1001, 1002, 1003, 1004]
    assert [candidate.frequency_rank for candidate in deck[3]] == [2001, 2002, 2003, 2004]


def test_all_supported_frequency_assets_validate() -> None:
    from multilang.services import frequency_decks

    for language in SupportedLanguage:
        entries = frequency_decks.load_curated_frequency_entries(language)
        if language is SupportedLanguage.LA:
            assert entries
            continue
        assert len(entries) == 3000
        assert [sum(1 for entry in entries if entry.level == level) for level in (1, 2, 3)] == [1000, 1000, 1000]
        assert all("needs_human_review" not in entry.curation_flags for entry in entries)
        assert all("structurally_curated" in entry.curation_flags for entry in entries)


def test_norwegian_bokmal_frequency_assets_validate() -> None:
    from multilang.services import frequency_decks

    entries = frequency_decks.load_curated_frequency_entries(SupportedLanguage.NB)

    assert len(entries) == 3000
    assert [sum(1 for entry in entries if entry.level == level) for level in (1, 2, 3)] == [1000, 1000, 1000]
    assert entries[0].display_form == "i"
    assert entries[4].display_form == "å"
    assert all(entry.source_provenance == "wordfreq:nb" for entry in entries)


def test_swedish_frequency_assets_validate() -> None:
    from multilang.services import frequency_decks

    entries = frequency_decks.load_curated_frequency_entries(SupportedLanguage.SV)

    assert len(entries) == 3000
    assert [sum(1 for entry in entries if entry.level == level) for level in (1, 2, 3)] == [1000, 1000, 1000]
    assert all(entry.source_provenance == "wordfreq:sv" for entry in entries)


def test_finnish_frequency_assets_validate() -> None:
    from multilang.services import frequency_decks

    entries = frequency_decks.load_curated_frequency_entries(SupportedLanguage.FI)

    assert len(entries) == 3000
    assert [sum(1 for entry in entries if entry.level == level) for level in (1, 2, 3)] == [1000, 1000, 1000]
    assert all(entry.source_provenance == "wordfreq:fi" for entry in entries)


def test_czech_frequency_assets_validate() -> None:
    from multilang.services import frequency_decks

    entries = frequency_decks.load_curated_frequency_entries(SupportedLanguage.CS)

    assert len(entries) == 3000
    assert [sum(1 for entry in entries if entry.level == level) for level in (1, 2, 3)] == [1000, 1000, 1000]
    assert all(entry.source_provenance == "wordfreq:cs" for entry in entries)


def test_danish_frequency_assets_validate() -> None:
    from multilang.services import frequency_decks

    entries = frequency_decks.load_curated_frequency_entries(SupportedLanguage.DA)

    assert len(entries) == 3000
    assert [sum(1 for entry in entries if entry.level == level) for level in (1, 2, 3)] == [1000, 1000, 1000]
    assert entries[0].display_form == "i"
    assert entries[1].display_form == "og"
    assert all(entry.source_provenance == "wordfreq:da" for entry in entries)


def test_validation_rejects_duplicate_lemma_key(tmp_path) -> None:
    from multilang.services import frequency_decks

    entries = frequency_decks.load_curated_frequency_entries(SupportedLanguage.EN)
    broken = list(entries)
    broken[1] = replace(broken[1], lemma_key=broken[0].lemma_key)

    try:
        frequency_decks.validate_curated_frequency_entries(broken, language=SupportedLanguage.EN)
    except ValueError as exc:
        assert "duplicate lemma_key" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("expected duplicate lemma_key validation failure")


def test_rejection_validation_rejects_bad_reason(tmp_path) -> None:
    from multilang.services import frequency_decks

    lang_dir = tmp_path / "en"
    lang_dir.mkdir(parents=True)
    source_dir = frequency_decks.Path("assets/frequency/en")
    (lang_dir / "curated-v1.csv").write_text((source_dir / "curated-v1.csv").read_text(encoding="utf-8"), encoding="utf-8")
    with (lang_dir / "rejections-v1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=frequency_decks.REJECTION_COLUMNS)
        writer.writeheader()
        writer.writerow({"language": "en", "frequency_list_version": "v1", "source_rank": 1, "token": "x", "reason_code": "bad"})

    try:
        frequency_decks.load_curated_frequency_entries(SupportedLanguage.EN, assets_dir=tmp_path)
    except ValueError as exc:
        assert "reason_code" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("expected rejection reason validation failure")
