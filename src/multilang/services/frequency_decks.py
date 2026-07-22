"""Deterministic frequency-deck curation helpers."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from wordfreq import iter_wordlist

from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance, policy_for_language
from multilang.domain.jobs import SupportedLanguage
from multilang.services.mandarin_orthography import (
    MandarinOrthographyError,
    script_counts,
    validate_simplified_mandarin,
)
from opencc import OpenCC

WEB_NOISE_TOKENS = {"http", "https", "www", "nbsp"}
_WORDFREQ_LANGUAGE_ALIASES = {"hr": "sh"}
_URL_OR_EMAIL_RE = re.compile(r"(?:https?://|www\.|\S+@\S+\.\S+)", re.IGNORECASE)
_HANDLE_OR_HASHTAG_RE = re.compile(r"^[#@]\w+")
_EMOTICON_RE = re.compile(r"^(?:[:;=8][\-o\*']?[)D(P/\\]|[)D(P/\\][\-o\*']?[:;=8])$")
_SENSITIVE_PROPER_NAME_WORDS = {
    "trump",
    "biden",
    "putin",
    "facebook",
    "google",
    "microsoft",
    "apple",
    "amazon",
}
LEVEL_WINDOWS = {
    1: (1, 1000),
    2: (1001, 2000),
    3: (2001, 3000),
}
CURATED_COLUMNS = (
    "language",
    "frequency_list_version",
    "level",
    "rank",
    "source_rank",
    "display_form",
    "lemma",
    "lemma_key",
    "part_of_speech",
    "definition_seed",
    "source_provenance",
    "curation_flags",
)
REJECTION_COLUMNS = ("language", "frequency_list_version", "source_rank", "token", "reason_code")
VALID_REJECTION_REASON_CODES = {
    "digit",
    "empty",
    "web_noise",
    "contains_dot",
    "uppercase",
    "punctuation",
    "duplicate_lemma_key",
    "duplicate_display_form",
    "url_or_email",
    "hashtag_or_handle",
    "emoji_or_symbol",
    "sensitive_name_or_brand",
    "non_han",
    "invalid_script",
}

_T2S = OpenCC("t2s")


@dataclass(frozen=True, slots=True)
class CuratedFrequencyEntry:
    language: SupportedLanguage
    frequency_list_version: str
    level: int
    rank: int
    source_rank: int
    display_form: str
    lemma: str
    lemma_key: str
    part_of_speech: str
    definition_seed: str
    source_provenance: str
    curation_flags: str


def _is_curated_token(token: str) -> bool:
    token = _normalize_frequency_token(token)
    if not token:
        return False
    if "\ufffd" in token:
        return False
    if _URL_OR_EMAIL_RE.search(token):
        return False
    if _HANDLE_OR_HASHTAG_RE.match(token):
        return False
    if _EMOTICON_RE.match(token):
        return False
    if any(character.isdigit() for character in token):
        return False

    lower_token = token.lower()
    if lower_token in WEB_NOISE_TOKENS:
        return False

    if lower_token in _SENSITIVE_PROPER_NAME_WORDS:
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


def _normalize_frequency_token(token: str) -> str:
    normalized = unicodedata.normalize("NFC", str(token or ""))
    normalized = " ".join(normalized.strip().split())
    normalized = normalized.replace("’", "'").replace("‐", "-").replace("‑", "-").replace("–", "-").replace("—", "-")
    return normalized


def normalize_frequency_token_for_language(
    language: SupportedLanguage,
    token: str,
) -> tuple[str, bool]:
    """Normalize one frequency token and report a Traditional-to-Simplified change."""

    normalized = _normalize_frequency_token(token)
    if language is not SupportedLanguage.ZH:
        return normalized, False
    normalized = unicodedata.normalize("NFKC", normalized)
    simplified = _T2S.convert(normalized)
    return simplified, simplified != normalized


def is_curated_token_for_language(language: SupportedLanguage, token: str) -> bool:
    if not _is_curated_token(token):
        return False
    if language is not SupportedLanguage.ZH:
        return True
    try:
        validate_simplified_mandarin(token)
    except MandarinOrthographyError:
        return False
    return True


def iter_curated_frequency_candidates(
    language: SupportedLanguage,
    scan_limit: int = 6000,
) -> Iterator[tuple[int, str]]:
    """Yield deterministic ranked candidates after mandatory curation filters."""

    for rank, token in enumerate(iter_wordlist(_wordfreq_language_code(language.value)), start=1):
        if rank > scan_limit:
            break
        normalized, _ = normalize_frequency_token_for_language(language, token)
        if is_curated_token_for_language(language, normalized):
            yield rank, normalized


def _wordfreq_language_code(language_code: str) -> str:
    return _WORDFREQ_LANGUAGE_ALIASES.get(language_code, language_code)


def _asset_path(*, language: SupportedLanguage, version: str, assets_dir: Path, kind: str) -> Path:
    return Path(assets_dir) / language.value / f"{kind}-{version}.csv"


def load_curated_frequency_entries(
    language: SupportedLanguage,
    *,
    version: str = "v1",
    assets_dir: Path | str = Path("assets/frequency"),
) -> list[CuratedFrequencyEntry]:
    path = _asset_path(language=language, version=version, assets_dir=Path(assets_dir), kind="curated")
    if not path.is_file():
        raise FileNotFoundError(f"missing curated frequency asset: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CURATED_COLUMNS:
            raise ValueError(f"malformed curated frequency header for {path}")
        entries = [_entry_from_row(row, path=path) for row in reader]
    validate_curated_frequency_entries(entries, language=language, version=version)
    validate_frequency_rejection_rows(language, version=version, assets_dir=assets_dir)
    return entries


def _entry_from_row(row: dict[str, str], *, path: Path) -> CuratedFrequencyEntry:
    try:
        language = SupportedLanguage(row["language"])
        level = int(row["level"])
        rank = int(row["rank"])
        source_rank = int(row["source_rank"])
    except Exception as exc:  # noqa: BLE001 - include asset path in validation error.
        raise ValueError(f"malformed curated frequency row in {path}: {row}") from exc
    return CuratedFrequencyEntry(
        language=language,
        frequency_list_version=row["frequency_list_version"],
        level=level,
        rank=rank,
        source_rank=source_rank,
        display_form=row["display_form"].strip(),
        lemma=row["lemma"].strip(),
        lemma_key=row["lemma_key"].strip(),
        part_of_speech=row["part_of_speech"].strip(),
        definition_seed=row["definition_seed"].strip(),
        source_provenance=row["source_provenance"].strip(),
        curation_flags=row["curation_flags"].strip(),
    )


def validate_curated_frequency_entries(
    entries: Iterable[CuratedFrequencyEntry],
    *,
    language: SupportedLanguage,
    version: str = "v1",
    required_count_per_level: int = 1000,
) -> None:
    rows = list(entries)
    expected_total = required_count_per_level * len(LEVEL_WINDOWS)
    if language.value == "la":
        # Latin uses custom shorter list from the site ( ~1000 words max)
        if len(rows) == 0:
            raise ValueError("no curated rows for la")
    elif len(rows) != expected_total:
        raise ValueError(f"expected {expected_total} curated rows for {language.value}, found {len(rows)}")
    if any(row.language is not language for row in rows):
        raise ValueError("curated asset contains rows for the wrong language")
    if any(row.frequency_list_version != version for row in rows):
        raise ValueError("curated asset contains rows for the wrong version")
    lemma_counts = Counter(row.lemma_key.casefold() for row in rows)
    if duplicates := [key for key, count in lemma_counts.items() if count > 1]:
        raise ValueError(f"duplicate lemma_key values: {duplicates[:5]}")
    display_counts = Counter(row.display_form.casefold() for row in rows)
    if duplicates := [key for key, count in display_counts.items() if count > 1]:
        raise ValueError(f"duplicate display_form values: {duplicates[:5]}")
    for level, (start_rank, end_rank) in LEVEL_WINDOWS.items():
        level_rows = sorted((row for row in rows if row.level == level), key=lambda row: row.rank)
        if language.value == "la":
            # Allow partial and non-strict for Latin custom list from the site
            continue
        if len(level_rows) != required_count_per_level:
            raise ValueError(f"expected {required_count_per_level} rows for level {level}")
        expected_ranks = list(range(start_rank, end_rank + 1))[:required_count_per_level]
        actual_ranks = [row.rank for row in level_rows]
        if actual_ranks != expected_ranks:
            raise ValueError(f"non-contiguous ranks for level {level}")
    for row in rows:
        if row.source_rank <= 0 or not row.display_form or not row.lemma or not row.lemma_key:
            raise ValueError("curated asset contains empty or invalid lexical fields")
        if not row.source_provenance:
            raise ValueError("curated asset contains missing source_provenance")
        if language is SupportedLanguage.ZH:
            try:
                display_form = validate_simplified_mandarin(row.display_form)
                lemma = validate_simplified_mandarin(row.lemma)
            except MandarinOrthographyError as exc:
                raise ValueError(f"Mandarin curated asset contains invalid script: {exc}") from exc
            if display_form != row.display_form or lemma != row.lemma:
                raise ValueError("Mandarin curated asset contains non-canonical normalization")
            if script_counts(row.lemma_key).han == 0:
                raise ValueError("Mandarin curated asset contains a non-Han lemma_key")
            if row.source_provenance != "wordfreq:zh":
                raise ValueError("Mandarin curated asset must use wordfreq:zh provenance")


def validate_frequency_rejection_rows(
    language: SupportedLanguage,
    *,
    version: str = "v1",
    assets_dir: Path | str = Path("assets/frequency"),
) -> None:
    path = _asset_path(language=language, version=version, assets_dir=Path(assets_dir), kind="rejections")
    if not path.is_file():
        raise FileNotFoundError(f"missing frequency rejection asset: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REJECTION_COLUMNS:
            raise ValueError(f"malformed rejection header for {path}")
        for row in reader:
            if row["language"] != language.value or row["frequency_list_version"] != version:
                raise ValueError(f"malformed rejection row language/version in {path}")
            if int(row["source_rank"]) <= 0 or not row["token"].strip():
                raise ValueError(f"malformed rejection row token/rank in {path}")
            if row["reason_code"] not in VALID_REJECTION_REASON_CODES:
                raise ValueError(f"malformed rejection reason_code in {path}: {row['reason_code']}")


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


def _build_asset_candidate(language: SupportedLanguage, entry: CuratedFrequencyEntry) -> LexicalCardCandidate:
    policy = policy_for_language(language)
    return LexicalCardCandidate(
        submitted_form=entry.display_form,
        display_form=entry.display_form,
        lemma=entry.lemma,
        lemma_key=entry.lemma_key,
        frequency_rank=entry.rank,
        frequency_level=entry.level,
        definition_language=policy.definition_language,
        translation_target_language=policy.translation_target_language,
        grounding_status=GroundingStatus.PENDING,
        provenance=LexicalProvenance(
            source="curated-frequency-asset",
            notes=[
                f"frequency_list_version={entry.frequency_list_version}",
                f"source_rank={entry.source_rank}",
                f"source_provenance={entry.source_provenance}",
                f"curation_flags={entry.curation_flags}",
            ],
        ),
    )


def build_frequency_level(
    language: SupportedLanguage,
    *,
    level: int,
    required_count_per_level: int = 1000,
    rejected_lemmas: set[str] | None = None,
    scan_limit: int = 6000,
    assets_dir: Path | str = Path("assets/frequency"),
    version: str = "v1",
    allow_frequency_seed_fallback: bool = False,
) -> list[LexicalCardCandidate]:
    """Build one frequency level using explicit windows plus bounded backfill."""

    if level not in LEVEL_WINDOWS:
        raise ValueError(f"unsupported frequency level: {level}")

    if not allow_frequency_seed_fallback:
        entries = load_curated_frequency_entries(language, version=version, assets_dir=assets_dir)
        seen_lemmas = {lemma.casefold() for lemma in (rejected_lemmas or set())}
        candidates = [
            _build_asset_candidate(language, entry)
            for entry in entries
            if entry.level == level and entry.lemma_key.casefold() not in seen_lemmas
        ]
        if len(candidates) != required_count_per_level:
            raise ValueError(f"asset level {level} did not provide {required_count_per_level} usable candidates")
        return candidates

    start_rank, end_rank = LEVEL_WINDOWS[level]
    seen_lemmas = {lemma.casefold() for lemma in (rejected_lemmas or set())}
    selected: list[LexicalCardCandidate] = []
    backfill: list[tuple[int, str]] = []

    for rank, token in iter_curated_frequency_candidates(language, scan_limit=scan_limit):
        if rank < start_rank:
            continue
        lemma_key = token.casefold()
        if lemma_key in seen_lemmas:
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
            seen_lemmas.add(lemma_key)
            if len(selected) >= required_count_per_level:
                break
            continue

        if rank > end_rank and len(selected) < required_count_per_level:
            backfill.append((rank, token))
            seen_lemmas.add(lemma_key)
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
    assets_dir: Path | str = Path("assets/frequency"),
    version: str = "v1",
    allow_frequency_seed_fallback: bool = False,
) -> dict[int, list[LexicalCardCandidate]]:
    """Build the deterministic three-level frequency deck."""

    rejected_lemmas_by_level = rejected_lemmas_by_level or {}
    deck: dict[int, list[LexicalCardCandidate]] = {}
    selected_lemmas: set[str] = set()
    for level in (1, 2, 3):
        level_rejections = {lemma.casefold() for lemma in rejected_lemmas_by_level.get(level, set())}
        candidates = build_frequency_level(
            language,
            level=level,
            required_count_per_level=required_count_per_level,
            rejected_lemmas=selected_lemmas | level_rejections,
            scan_limit=scan_limit,
            assets_dir=assets_dir,
            version=version,
            allow_frequency_seed_fallback=allow_frequency_seed_fallback,
        )
        deck[level] = candidates
        selected_lemmas.update(candidate.lemma_key.casefold() for candidate in candidates)

    return deck


__all__ = [
    "build_frequency_deck",
    "build_frequency_level",
    "CuratedFrequencyEntry",
    "load_curated_frequency_entries",
    "validate_curated_frequency_entries",
    "validate_frequency_rejection_rows",
    "iter_curated_frequency_candidates",
]
