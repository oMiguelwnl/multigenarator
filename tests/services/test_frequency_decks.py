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
