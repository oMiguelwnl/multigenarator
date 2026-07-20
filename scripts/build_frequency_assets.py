"""Build and validate deterministic frequency assets from wordfreq seeds."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from multilang.domain.jobs import SupportedLanguage
from multilang.services.frequency_decks import (
    CURATED_COLUMNS,
    REJECTION_COLUMNS,
    VALID_REJECTION_REASON_CODES,
    _is_curated_token,
    load_curated_frequency_entries,
)
from multilang.settings import DEFAULT_SUPPORTED_LANGUAGES
from wordfreq import iter_wordlist

_WORDFREQ_LANGUAGE_ALIASES = {"hr": "sh"}


def _rejection_reason(token: str) -> str | None:
    if not token:
        return "empty"
    if any(ch.isdigit() for ch in token):
        return "digit"
    lower = token.lower()
    if lower in {"http", "https", "www", "nbsp"}:
        return "web_noise"
    if "." in token:
        return "contains_dot"
    if token != lower:
        return "uppercase"
    if not _is_curated_token(token):
        return "punctuation"
    return None


def build_assets(
    *,
    assets_dir: Path,
    version: str,
    scan_limit: int = 25000,
    language_code: str | None = None,
) -> None:
    for code in _language_codes(language_code):
        _build_language_asset(code=code, assets_dir=assets_dir, version=version, scan_limit=scan_limit)


def _language_codes(language_code: str | None) -> tuple[str, ...]:
    if language_code is None:
        return DEFAULT_SUPPORTED_LANGUAGES
    return (language_code,)


def _build_language_asset(*, code: str, assets_dir: Path, version: str, scan_limit: int) -> None:
    language = SupportedLanguage(code)
    target_dir = assets_dir / code
    target_dir.mkdir(parents=True, exist_ok=True)
    curated_rows: list[dict[str, object]] = []
    rejection_rows: list[dict[str, object]] = []
    seen_lemmas: set[str] = set()
    seen_displays: set[str] = set()
    if code == "la":
        # Latin uses custom frequency list from the site (e.g. https://mylittlewordland.com/course/415114/as-mil-palavras-mais-frequentes-do-latim )
        # Expect a file assets/frequency/la/source-list.txt with one lemma per line, in frequency order.
        source_list_path = target_dir / "source-list.txt"
        if not source_list_path.exists():
            print(f"Warning: {source_list_path} not found. Using sample data. Download the list from the site and save as source-list.txt (one word per line).")
            tokens = ["sum", "et", "in", "non", "qui", "hic", "esse", "cum", "ego", "is"]  # minimal sample
        else:
            with source_list_path.open(encoding="utf-8") as f:
                tokens = [line.strip() for line in f if line.strip()]
        source_rank = 0
        for token in tokens:
            source_rank += 1
            if source_rank > scan_limit or len(curated_rows) >= 3000:
                break
            reason = _rejection_reason(token)
            lemma_key = token.casefold()
            display_key = token.casefold()
            if reason is None and lemma_key in seen_lemmas:
                reason = "duplicate_lemma_key"
            if reason is None and display_key in seen_displays:
                reason = "duplicate_display_form"
            if reason is not None:
                rejection_rows.append(_rejection_row(language, version, source_rank, token, reason))
                continue
            rank = len(curated_rows) + 1
            seen_lemmas.add(lemma_key)
            seen_displays.add(display_key)
            curated_rows.append({
                "language": code,
                "frequency_list_version": version,
                "level": ((rank - 1) // 1000) + 1,
                "rank": rank,
                "source_rank": source_rank,
                "display_form": token,
                "lemma": token,
                "lemma_key": lemma_key,
                "part_of_speech": "unknown",
                "definition_seed": token,
                "source_provenance": f"mylittlewordland:{code}",
                "curation_flags": "mylittlewordland_seeded;deterministically_filtered;structurally_curated",
            })
    else:
        wordfreq_code = _wordfreq_language_code(code)
        for source_rank, token in enumerate(iter_wordlist(wordfreq_code), start=1):
            if source_rank > scan_limit or len(curated_rows) >= 3000:
                break
            reason = _rejection_reason(token)
            lemma_key = token.casefold()
            display_key = token.casefold()
            if reason is None and lemma_key in seen_lemmas:
                reason = "duplicate_lemma_key"
            if reason is None and display_key in seen_displays:
                reason = "duplicate_display_form"
            if reason is not None:
                rejection_rows.append(_rejection_row(language, version, source_rank, token, reason))
                continue
            rank = len(curated_rows) + 1
            seen_lemmas.add(lemma_key)
            seen_displays.add(display_key)
            curated_rows.append(
                {
                    "language": code,
                    "frequency_list_version": version,
                    "level": ((rank - 1) // 1000) + 1,
                    "rank": rank,
                    "source_rank": source_rank,
                    "display_form": token,
                    "lemma": token,
                    "lemma_key": lemma_key,
                    "part_of_speech": "unknown",
                    "definition_seed": token,
                    "source_provenance": f"wordfreq:{wordfreq_code}",
                    "curation_flags": "wordfreq_seeded;deterministically_filtered;structurally_curated",
                }
            )
    if code != "la" and len(curated_rows) != 3000:
        raise RuntimeError(f"could not build 3000 rows for {code}; got {len(curated_rows)}")
    if code == "la" and len(curated_rows) == 0:
        print("No curated rows for la; add source-list.txt from the site to generate.")
    _write_csv(target_dir / f"curated-{version}.csv", CURATED_COLUMNS, curated_rows)
    if not rejection_rows:
        rejection_rows.append(_rejection_row(language, version, 1, "__none__", "punctuation"))
    assert all(row["reason_code"] in VALID_REJECTION_REASON_CODES for row in rejection_rows)
    _write_csv(target_dir / f"rejections-{version}.csv", REJECTION_COLUMNS, rejection_rows)
    load_curated_frequency_entries(language, version=version, assets_dir=assets_dir)


def _rejection_row(language: SupportedLanguage, version: str, source_rank: int, token: str, reason: str) -> dict[str, object]:
    return {
        "language": language.value,
        "frequency_list_version": version,
        "source_rank": source_rank,
        "token": token or "<empty>",
        "reason_code": reason,
    }


def _wordfreq_language_code(language_code: str) -> str:
    return _WORDFREQ_LANGUAGE_ALIASES.get(language_code, language_code)


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def check_assets(*, assets_dir: Path, version: str, language_code: str | None = None) -> None:
    for code in _language_codes(language_code):
        load_curated_frequency_entries(SupportedLanguage(code), version=version, assets_dir=assets_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets-dir", type=Path, default=Path("assets/frequency"))
    parser.add_argument("--version", default="v1")
    parser.add_argument("--language", choices=DEFAULT_SUPPORTED_LANGUAGES, help="Build or check one language code only.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_assets(assets_dir=args.assets_dir, version=args.version, language_code=args.language)
    else:
        build_assets(assets_dir=args.assets_dir, version=args.version, language_code=args.language)


if __name__ == "__main__":
    main()
