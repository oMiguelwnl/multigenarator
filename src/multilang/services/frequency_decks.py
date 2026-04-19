"""Deterministic frequency-deck curation helpers."""

from __future__ import annotations

from collections.abc import Iterator

from wordfreq import iter_wordlist

from multilang.domain.jobs import SupportedLanguage

WEB_NOISE_TOKENS = {"http", "https", "www", "nbsp"}


def _is_curated_token(token: str) -> bool:
    if not token:
        return False
    if any(character.isdigit() for character in token):
        return False

    lower_token = token.lower()
    if lower_token in WEB_NOISE_TOKENS:
        return False

    if "." in token:
        return False

    if token != lower_token:
        return False

    saw_letter = False
    for index, character in enumerate(token):
        if character.isalpha():
            saw_letter = True
            continue

        if character in {"'", "-"}:
            if index == 0 or index == len(token) - 1:
                return False
            if not token[index - 1].isalpha() or not token[index + 1].isalpha():
                return False
            continue

        return False

    return saw_letter


def iter_curated_frequency_candidates(
    language: SupportedLanguage,
    scan_limit: int = 6000,
) -> Iterator[tuple[int, str]]:
    """Yield deterministic ranked candidates after mandatory curation filters."""

    for rank, token in enumerate(iter_wordlist(language.value), start=1):
        if rank > scan_limit:
            break
        if _is_curated_token(token):
            yield rank, token


__all__ = ["iter_curated_frequency_candidates"]
