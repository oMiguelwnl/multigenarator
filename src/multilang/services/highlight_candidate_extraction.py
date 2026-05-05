"""Deterministic vocabulary candidate extraction from normalized highlights."""

from __future__ import annotations

from collections.abc import Sequence
import re
import unicodedata

from multilang.domain.highlights import (
    HighlightCandidate,
    HighlightCandidateExtractionResult,
    NormalizedHighlight,
)
from multilang.domain.jobs import SupportedLanguage


_TOKEN_RE = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.UNICODE)
_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
_WEB_NOISE = {"http", "https", "www", "nbsp", "com", "org", "net", "example", "test"}
_STOPWORDS: dict[SupportedLanguage, set[str]] = {
    SupportedLanguage.PT: {"a", "ao", "as", "de", "do", "da", "e", "em", "o", "os", "um", "uma", "pela"},
    SupportedLanguage.ES: {"a", "de", "del", "el", "en", "la", "las", "los", "un", "una", "y", "otro"},
    SupportedLanguage.EN: {"a", "an", "and", "in", "of", "the", "to"},
    SupportedLanguage.FR: {"au", "de", "des", "du", "et", "la", "le", "les", "un", "une"},
    SupportedLanguage.DE: {"das", "der", "die", "ein", "eine", "und"},
    SupportedLanguage.IT: {"a", "di", "e", "il", "la", "le", "lo", "un", "una"},
    SupportedLanguage.PL: {"a", "i", "ma", "na", "o", "ten", "ta", "to", "w", "z"},
    SupportedLanguage.TR: {"bu", "bir", "ve"},
    SupportedLanguage.RO: {"acest", "aceasta", "cu", "de", "în", "la", "o", "și", "un", "una"},
    SupportedLanguage.RU: {"а", "в", "и", "на", "не", "с", "то", "этот", "это"},
    SupportedLanguage.NL: {"de", "een", "en", "het", "in", "van"},
}


def extract_highlight_candidates(
    highlights: Sequence[NormalizedHighlight],
    *,
    language: SupportedLanguage,
) -> HighlightCandidateExtractionResult:
    """Return first-seen ordered candidate forms with duplicate/noise counters."""

    candidates_by_key: dict[str, HighlightCandidate] = {}
    ordered_keys: list[str] = []
    duplicate_count = 0
    rejected_token_count = 0
    stopwords = _STOPWORDS[language]

    for highlight in sorted(highlights, key=lambda item: item.provenance.source_index):
        text_without_urls, removed_urls = _URL_RE.subn(" ", highlight.text)
        rejected_token_count += removed_urls
        for raw_token in _raw_token_like_parts(highlight.text):
            if _URL_RE.match(raw_token) or any(character.isdigit() for character in raw_token):
                rejected_token_count += 1

        for match in _TOKEN_RE.finditer(text_without_urls):
            display_form = _trim_internal_token(match.group(0))
            lemma_key = _lemma_key(display_form)
            if not _is_usable_token(display_form, lemma_key=lemma_key, stopwords=stopwords):
                rejected_token_count += 1
                continue

            if lemma_key in candidates_by_key:
                duplicate_count += 1
                existing = candidates_by_key[lemma_key]
                candidates_by_key[lemma_key] = existing.model_copy(
                    update={"occurrence_count": existing.occurrence_count + 1}
                )
                continue

            ordered_keys.append(lemma_key)
            candidates_by_key[lemma_key] = HighlightCandidate(
                item_key=f"highlight-{language.value}-{len(ordered_keys):04d}-{lemma_key}",
                source_content_hash=highlight.provenance.content_hash,
                display_form=display_form,
                lemma_key=lemma_key,
                first_highlight_id=highlight.highlight_id,
                first_source_index=highlight.provenance.source_index,
                occurrence_count=1,
            )

    return HighlightCandidateExtractionResult(
        candidates=[candidates_by_key[key] for key in ordered_keys],
        duplicate_count=duplicate_count,
        rejected_token_count=rejected_token_count,
    )


def _raw_token_like_parts(text: str) -> list[str]:
    return [part for part in re.split(r"\s+", text) if part]


def _trim_internal_token(token: str) -> str:
    return token.strip("'’-—-")


def _lemma_key(token: str) -> str:
    normalized = unicodedata.normalize("NFKC", token)
    return " ".join(normalized.casefold().split())


def _is_usable_token(token: str, *, lemma_key: str, stopwords: set[str]) -> bool:
    if len(lemma_key) <= 1:
        return False
    if lemma_key in stopwords or lemma_key in _WEB_NOISE:
        return False
    if any(character.isdigit() for character in token):
        return False
    if not any(character.isalpha() for character in token):
        return False
    for index, character in enumerate(token):
        if character.isalpha():
            continue
        if character in {"'", "’", "-"} and 0 < index < len(token) - 1:
            if token[index - 1].isalpha() and token[index + 1].isalpha():
                continue
        return False
    return True


__all__ = ["extract_highlight_candidates"]
