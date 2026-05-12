"""Tests for deterministic frequency-deck curation."""

from __future__ import annotations

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
    )

    assert [len(deck[level]) for level in (1, 2, 3)] == [4, 4, 4]
    assert [candidate.frequency_rank for candidate in deck[1]] == [1, 2, 3, 4]
    assert [candidate.frequency_rank for candidate in deck[2]] == [1001, 1002, 1003, 1004]
    assert [candidate.frequency_rank for candidate in deck[3]] == [2001, 2002, 2003, 2004]
