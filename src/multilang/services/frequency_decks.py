"""Deterministic frequency-deck curation helpers."""

from __future__ import annotations

from collections.abc import Iterator

from wordfreq import iter_wordlist

from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance, policy_for_language
from multilang.domain.jobs import SupportedLanguage

WEB_NOISE_TOKENS = {"http", "https", "www", "nbsp"}
LEVEL_WINDOWS = {
    1: (1, 1000),
    2: (1001, 2000),
    3: (2001, 3000),
}


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


def _build_seed_candidate(
    language: SupportedLanguage,
    *,
    token: str,
    frequency_rank: int,
    frequency_level: int,
) -> LexicalCardCandidate:
    policy = policy_for_language(language)
    return LexicalCardCandidate(
        submitted_form=token,
        display_form=token,
        lemma=token,
        lemma_key=token.casefold(),
        frequency_rank=frequency_rank,
        frequency_level=frequency_level,
        definition_language=policy.definition_language,
        translation_target_language=policy.translation_target_language,
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(source="wordfreq"),
    )


def build_frequency_level(
    language: SupportedLanguage,
    *,
    level: int,
    required_count_per_level: int = 1000,
    rejected_lemmas: set[str] | None = None,
    scan_limit: int = 6000,
) -> list[LexicalCardCandidate]:
    """Build one frequency level using explicit windows plus bounded backfill."""

    if level not in LEVEL_WINDOWS:
        raise ValueError(f"unsupported frequency level: {level}")

    start_rank, end_rank = LEVEL_WINDOWS[level]
    rejected_lemmas = {lemma.casefold() for lemma in (rejected_lemmas or set())}
    selected: list[LexicalCardCandidate] = []
    backfill: list[tuple[int, str]] = []

    for rank, token in iter_curated_frequency_candidates(language, scan_limit=scan_limit):
        if rank < start_rank:
            continue
        if token.casefold() in rejected_lemmas:
            continue

        if rank <= end_rank and len(selected) < required_count_per_level:
            selected.append(
                _build_seed_candidate(
                    language,
                    token=token,
                    frequency_rank=rank,
                    frequency_level=level,
                )
            )
            continue

        if rank > end_rank and len(selected) < required_count_per_level:
            backfill.append((rank, token))
            if len(selected) + len(backfill) >= required_count_per_level:
                break

    for rank, token in backfill:
        if len(selected) >= required_count_per_level:
            break
        selected.append(
            _build_seed_candidate(
                language,
                token=token,
                frequency_rank=rank,
                frequency_level=level,
            )
        )

    if len(selected) != required_count_per_level:
        raise ValueError(
            f"could not build level {level} with {required_count_per_level} curated candidates "
            f"within scan limit {scan_limit}"
        )

    return selected


def build_frequency_deck(
    language: SupportedLanguage,
    *,
    required_count_per_level: int = 1000,
    rejected_lemmas_by_level: dict[int, set[str]] | None = None,
    scan_limit: int = 6000,
) -> dict[int, list[LexicalCardCandidate]]:
    """Build the deterministic three-level frequency deck."""

    rejected_lemmas_by_level = rejected_lemmas_by_level or {}
    return {
        level: build_frequency_level(
            language,
            level=level,
            required_count_per_level=required_count_per_level,
            rejected_lemmas={lemma.casefold() for lemma in rejected_lemmas_by_level.get(level, set())},
            scan_limit=scan_limit,
        )
        for level in (1, 2, 3)
    }


__all__ = [
    "build_frequency_deck",
    "build_frequency_level",
    "iter_curated_frequency_candidates",
]
